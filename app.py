import streamlit as st
import sqlite3
import pandas as pd
import time
import hashlib
import datetime

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# INITIALIZE SESSION STATE

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

def get_data(query):
    conn = sqlite3.connect('inventory.db')
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def log_action(username, action, details):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO audit_logs (timestamp, username, action, details) VALUES (?, ?, ?, ?)", 
              (current_time, username, action, details))
    conn.commit()
    conn.close()

# PAGE CONFIGURATION
st.set_page_config(page_title="Smart Asset Manager", layout="wide")
st.title("Cultural Council Asset Manager")


# AUTHENTICATION GATEWAY

if not st.session_state['logged_in']:
    st.subheader("Login / Register")
    
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        with st.form("login_form"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                hashed_pass = hash_password(login_pass)
                conn = sqlite3.connect('inventory.db')
                c = conn.cursor()
                c.execute("SELECT role FROM users WHERE username=? AND password=?", (login_user, hashed_pass))
                result = c.fetchone()
                conn.close()
                
                if result:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = login_user
                    st.session_state['role'] = result[0]
                    st.success("Logged in successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    with auth_tab2:
        with st.form("register_form"):
            new_user = st.text_input("Choose a Username")
            new_pass = st.text_input("Choose a Password", type="password")
            new_role = st.selectbox("Role", ["Student / User", "Administrator"])
            reg_btn = st.form_submit_button("Register")
            
            if reg_btn:
                if new_user and new_pass:
                    hashed_pass = hash_password(new_pass)
                    conn = sqlite3.connect('inventory.db')
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                                  (new_user, hashed_pass, new_role))
                        conn.commit()
                        st.success("Account created! Please switch to the Login tab.")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists. Please choose another.")
                    finally:
                        conn.close()
                else:
                    st.warning("Please fill in all fields.")
                    
    st.stop() 

#LOGOUT SIDEBAR 

st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
st.sidebar.write(f"Role: {st.session_state['role']}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['role'] = ''
    st.rerun()


# ADMIN VIEW
if st.session_state['role'] == "Administrator":
    st.subheader("Admin Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Manage Inventory", "Pending Approvals", "Analytics", "Security Audit Logs"])
    
    with tab1:
        st.write("### Add New Asset")
        with st.form("add_asset_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Asset Name (e.g., DSLR Camera)")
            category = col2.selectbox("Category", ["Electronics", "Props", "Audio", "Lighting", "Miscellaneous"])
            description = st.text_area("Description / Specifications")
            
            col3, col4 = st.columns(2)
            qty = col3.number_input("Total Quantity", min_value=1, value=1)
            status = col4.selectbox("Initial Status", ["Active", "Under Maintenance", "Retired"])
            
            submitted = st.form_submit_button("Add to Inventory")
            
            if submitted and name:
                conn = sqlite3.connect('inventory.db')
                c = conn.cursor()
                c.execute('''INSERT INTO assets 
                             (name, category, description, status, total_quantity, available_quantity) 
                             VALUES (?, ?, ?, ?, ?, ?)''', 
                          (name, category, description, status, qty, qty))
                conn.commit()
                conn.close()
                log_action(st.session_state['username'], "CREATE_ASSET", f"Added {qty}x {name} to category {category}")
                st.success(f"Added {qty}x {name} to inventory!")
                time.sleep(1)
                st.rerun()

        st.write("### Current Inventory")
        inventory_df = get_data("SELECT * FROM assets")
        st.dataframe(inventory_df, use_container_width=True, hide_index=True)

        # EDIT AND DELETE SECTION
        st.markdown("---")
        if not inventory_df.empty:
            col_action1, col_action2 = st.columns(2)
            
            # EDIT LOGIC
            with col_action1:
                st.write("### Edit Asset")
                edit_id = st.selectbox("Select Asset ID to Edit", inventory_df['id'].tolist(), key="edit_select")
                
                current_data = inventory_df[inventory_df['id'] == edit_id].iloc[0]

                current_total = int(current_data['total_quantity'])
   
                try:
                    current_avail = int(current_data['available_quantity'])
                except ValueError:
                    current_avail = 0 
                    
                checked_out_qty = current_total - current_avail
                
                with st.form("edit_asset_form"):
                    new_desc = st.text_input("Update Description", value=current_data['description'] if pd.notna(current_data['description']) else "")
                    new_status = st.selectbox("Update Status", ["Active", "Under Maintenance", "Retired"], 
                                              index=["Active", "Under Maintenance", "Retired"].index(current_data['status']) if current_data['status'] in ["Active", "Under Maintenance", "Retired"] else 0)

                    new_total = st.number_input("Update Total Quantity", min_value=checked_out_qty, value=current_total)
                    
                    update_btn = st.form_submit_button("Save Changes")
                    
                    if update_btn:
                        qty_difference = int(new_total) - current_total
                        new_available = current_avail + qty_difference
                        
                        conn = sqlite3.connect('inventory.db')
                        c = conn.cursor()
                        c.execute('''UPDATE assets 
                                     SET description = ?, status = ?, total_quantity = ?, available_quantity = ? 
                                     WHERE id = ?''', 
                                  (new_desc, new_status, int(new_total), int(new_available), int(edit_id)))
                        conn.commit()
                        conn.close()
                        st.success("Asset updated successfully!")
                        time.sleep(1)
                        st.rerun()

            #DELETE LOGIC
            with col_action2:
                st.write("### Delete Asset")
                delete_id = st.selectbox("Select Asset ID to Delete", inventory_df['id'].tolist(), key="del_select")
                st.warning("⚠️ Deleting an asset will remove it permanently.")
                
                with st.form("delete_asset_form"):
                    confirm_delete = st.checkbox("I confirm I want to delete this asset.")
                    delete_btn = st.form_submit_button("Delete Asset")
                    
                    if delete_btn:
                        if confirm_delete:
                            conn = sqlite3.connect('inventory.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM assets WHERE id = ?", (delete_id,))
                            c.execute("DELETE FROM bookings WHERE asset_id = ?", (delete_id,))
                            conn.commit()
                            conn.close()
                            st.success("Asset deleted.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Please check the confirmation box.")

    with tab2:
        st.write("### 📥 Pending Booking Requests")
        pending_query = """
            SELECT b.id, b.user_name, a.name as asset_name, b.quantity, b.start_date, b.end_date 
            FROM bookings b
            JOIN assets a ON b.asset_id = a.id
            WHERE b.status = 'pending'
        """
        pending_df = get_data(pending_query)
        st.dataframe(pending_df, use_container_width=True, hide_index=True)

        if not pending_df.empty:
            st.write("### Process Request")
            with st.form("approve_form"):
                booking_to_process = st.selectbox("Select Booking ID to Process", pending_df['id'].tolist())
                
                col_btn1, col_btn2 = st.columns(2)
                approve_btn = col_btn1.form_submit_button("✅ Approve Request")
                reject_btn = col_btn2.form_submit_button("❌ Reject Request")

                if approve_btn:
                    conn = sqlite3.connect('inventory.db')
                    c = conn.cursor()
                    c.execute("SELECT asset_id, quantity FROM bookings WHERE id = ?", (booking_to_process,))
                    booking_data = c.fetchone()
                    asset_id, req_qty = booking_data[0], booking_data[1]
                    
                    c.execute("SELECT available_quantity FROM assets WHERE id = ?", (asset_id,))
                    current_avail = c.fetchone()[0]
                    
                    if req_qty > current_avail:
                        st.error(f"Cannot approve! Only {current_avail} left in stock, but {req_qty} requested. Please reject this request.")
                    else:
                        c.execute("UPDATE bookings SET status = 'approved' WHERE id = ?", (booking_to_process,))
                        c.execute("UPDATE assets SET available_quantity = available_quantity - ? WHERE id = ?", (req_qty, asset_id))
                        conn.commit()
                        log_action(st.session_state['username'], "APPROVE_BOOKING", f"Approved booking ID {booking_to_process} for {req_qty} items.")
                        st.success(f"Booking {booking_to_process} approved!")
                        time.sleep(1.5)
                        st.rerun()
                    conn.close()
                    
                if reject_btn:
                    conn = sqlite3.connect('inventory.db')
                    c = conn.cursor()
                    c.execute("UPDATE bookings SET status = 'rejected' WHERE id = ?", (booking_to_process,))
                    conn.commit()
                    conn.close()
                    st.success(f"Booking {booking_to_process} has been rejected.")
                    time.sleep(1.5)
                    st.rerun()
        else:
            st.info("No pending requests right now.")
            
        st.markdown("---") 
        st.write("### 📦 Active Allocations (Awaiting Return)")
        
        active_query = """
            SELECT b.id, b.user_name, a.name as asset_name, b.quantity, b.start_date, b.end_date 
            FROM bookings b
            JOIN assets a ON b.asset_id = a.id
            WHERE b.status = 'approved'
        """
        active_df = get_data(active_query)

        #Due Date Management Logic
        if not active_df.empty:
            active_df['end_date_obj'] = pd.to_datetime(active_df['end_date']).dt.date
            today = datetime.date.today()
            
            active_df['Return Status'] = active_df['end_date_obj'].apply(
                lambda x: "🔴 OVERDUE" if x < today else "🟢 On Time"
            )
            active_df = active_df.drop(columns=['end_date_obj'])
            
        st.dataframe(active_df, use_container_width=True, hide_index=True)

        if not active_df.empty:
            with st.form("return_form"):
                booking_to_return = st.selectbox("Select Booking ID to Mark Returned", active_df['id'].tolist())
                return_btn = st.form_submit_button("Mark as Returned")

                if return_btn:
                    conn = sqlite3.connect('inventory.db')
                    c = conn.cursor()
                    
                    c.execute("UPDATE bookings SET status = 'returned' WHERE id = ?", (booking_to_return,))

                    c.execute("SELECT asset_id, quantity FROM bookings WHERE id = ?", (booking_to_return,))
                    booking_data = c.fetchone()
                    asset_id, req_qty = booking_data[0], booking_data[1]
                    
                    c.execute("UPDATE assets SET available_quantity = available_quantity + ? WHERE id = ?", (req_qty, asset_id))
                    
                    conn.commit()
                    conn.close()
                    log_action(st.session_state['username'], "RETURN_ASSET", f"Marked booking ID {booking_to_return} as returned to inventory.")
                    st.success(f"Items for Booking {booking_to_return} successfully returned to inventory! 🔄")
                    time.sleep(1.5)
                    st.rerun()

    with tab3:
        st.write("### 📊 Operational Analytics")
        
        conn = sqlite3.connect('inventory.db')
        
        metrics_df = pd.read_sql_query("""
            SELECT 
                COUNT(id) as total_types,
                SUM(total_quantity) as total_items,
                SUM(available_quantity) as total_available
            FROM assets
        """, conn)
        
        active_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM bookings WHERE status = 'approved'", conn)
        pending_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM bookings WHERE status = 'pending'", conn)

        overdue_df = pd.read_sql_query("SELECT COUNT(id) as count FROM bookings WHERE status = 'approved' AND end_date < date('now')", conn)
        
        total_types = metrics_df['total_types'].iloc[0] or 0
        total_items = metrics_df['total_items'].iloc[0] or 0
        total_available = metrics_df['total_available'].iloc[0] or 0
        active_loans = active_count_df['count'].iloc[0] or 0
        pending_requests = pending_count_df['count'].iloc[0] or 0
        overdue_count = overdue_df['count'].iloc[0] or 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Assets", total_items)
        col2.metric("Available Inventory", total_available)
        col3.metric("Active Loans", active_loans)
        col4.metric("Pending Approvals", pending_requests)
        col5.metric("Overdue Returns", overdue_count, delta=-int(overdue_count) if overdue_count > 0 else 0, delta_color="inverse")
        
        st.markdown("---")
        st.write("#### ⚙️ System Utilization Rate")
        if total_items > 0:
            checked_out = total_items - total_available
            util_rate = checked_out / total_items
            st.progress(float(util_rate), text=f"{util_rate*100:.1f}% of total inventory is currently checked out.")
        else:
            st.info("Add inventory to see utilization rates.")
            
        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.write("#### 📈 Most Frequently Utilized Assets")
            popularity_df = pd.read_sql_query("""
                SELECT assets.name as "Asset Name", COUNT(bookings.id) as "Total Bookings"
                FROM bookings
                JOIN assets ON bookings.asset_id = assets.id
                GROUP BY assets.id
                ORDER BY "Total Bookings" DESC
            """, conn)
            
            if not popularity_df.empty:
                st.bar_chart(popularity_df.set_index("Asset Name"))
            else:
                st.info("No booking data available yet to chart popularity.")
                
        with chart_col2:
            st.write("#### 📉 Current Stock Availability")
            stock_df = pd.read_sql_query("""
                SELECT name as "Asset Name", total_quantity as "Total", available_quantity as "Available"
                FROM assets
            """, conn)
            
            if not stock_df.empty:
                st.bar_chart(stock_df.set_index("Asset Name"))
            else:
                st.info("No inventory items found.")
                
        conn.close()
    with tab4:
        st.write("### 🛡️ System Audit Logs")
        st.caption("Immutable record of system actions for security and compliance.")

        logs_df = get_data("SELECT timestamp, username, action, details FROM audit_logs ORDER BY timestamp DESC")
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True, hide_index=True)
        else:
            st.info("No system actions have been logged yet.")

# USER VIEW
elif st.session_state['role'] == "Student / User":
    current_user = st.session_state['username']
    st.subheader("Student Portal")
    
    if not current_user:
        st.warning("Please enter your name in the sidebar to access the portal.")
    else:
        st.write(f"Welcome, {current_user}!")

        user_tab1, user_tab2 = st.tabs(["Browse & Request", "My Dashboard"])
        
        with user_tab1:
            st.write("### 🔍 Browse & Search Assets")

            col_search, col_filter = st.columns([2, 1])
            search_term = col_search.text_input("Search by Asset Name")
            category_filter = col_filter.selectbox("Filter by Category", ["All", "Electronics", "Props", "Audio", "Lighting", "Miscellaneous"])

            query = "SELECT id, name, category, description, available_quantity FROM assets WHERE available_quantity > 0"
            if category_filter != "All":
                query += f" AND category = '{category_filter}'"
                
            available_assets = get_data(query)
 
            if search_term and not available_assets.empty:
                available_assets = available_assets[available_assets['name'].str.contains(search_term, case=False, na=False)]
                
            st.dataframe(available_assets, use_container_width=True, hide_index=True)

            st.write("### 📅 Request an Asset")
            with st.form("request_form"):
                if not available_assets.empty:
                    item_to_book = st.selectbox("Select Item ID", available_assets['id'].tolist())
                    req_qty = st.number_input("Quantity Required", min_value=1, value=1)
                    
                    col_date1, col_date2 = st.columns(2)
                    start_date = col_date1.date_input("Start Date", datetime.date.today())
                    end_date = col_date2.date_input("End Date", datetime.date.today() + datetime.timedelta(days=1))
                    
                    request_btn = st.form_submit_button("Submit Request")
                    
                    if request_btn:
                        if start_date > end_date:
                            st.error("End Date must be after Start Date.")
                        else:
                            conn = sqlite3.connect('inventory.db')
                            c = conn.cursor()
                            c.execute("SELECT available_quantity, name FROM assets WHERE id = ?", (item_to_book,))
                            asset_data = c.fetchone()
                            current_avail = asset_data[0]
                            asset_name = asset_data[1]
                            
                            if req_qty > current_avail:
                                st.error(f"❌ Cannot request {req_qty}. Only {current_avail} '{asset_name}' available.")
                            else:
                                c.execute('''INSERT INTO bookings 
                                             (user_name, asset_id, quantity, start_date, end_date, status) 
                                             VALUES (?, ?, ?, ?, ?, ?)''', 
                                          (current_user, item_to_book, req_qty, str(start_date), str(end_date), 'pending'))
                                conn.commit()
                                st.success("Request submitted to Admin for approval! ✅")
                                time.sleep(1.5)
                                st.rerun()
                            conn.close()
                else:
                    st.info("No items currently match your search/filters.")
                    st.form_submit_button("Submit Request", disabled=True)

        with user_tab2:
            st.write("### My Borrowing History")
            
            conn = sqlite3.connect('inventory.db')
            my_history_df = pd.read_sql_query("SELECT * FROM bookings WHERE user_name = ?", conn, params=(current_user,))
            conn.close()
            
            if my_history_df.empty:
                st.info("You haven't requested any items yet.")
            else:
                st.write("#### Currently in my possession (Approved)")
                active_items = my_history_df[my_history_df['status'] == 'approved']
                st.dataframe(active_items, use_container_width=True,hide_index=True)
                if not active_items.empty:
                    st.caption("⚠️ Please physically return these items to the Admin to clear them from your account.")
                
                st.write("#### Pending Requests")
                pending_items = my_history_df[my_history_df['status'] == 'pending']
                st.dataframe(pending_items, use_container_width=True,hide_index=True)
                
                st.write("#### Past Returns")
                returned_items = my_history_df[my_history_df['status'] == 'returned']
                st.dataframe(returned_items, use_container_width=True,hide_index=True)