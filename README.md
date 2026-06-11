# Smart Asset Management and Resource Allocation Platform

## 📖 Project Overview
The Smart Asset Management Platform is a full-stack, role-based web application designed to solve the operational bottlenecks of managing shared resources for the Cultural Council. It replaces fragmented communication channels and physical registers with a centralized digital handshake. The platform provides real-time inventory visibility, strict approval workflows, due-date tracking, and immutable audit logging, ensuring that the digital state of assets always accurately reflects physical reality.

**Developed by:** Devansh Saxena (24115052)

## 💻 Technology Stack
* **Frontend UI:** Streamlit (Python)
* **Backend Logic:** Python 3
* **Database:** SQLite3 (Relational Database)
* **Data Manipulation & Analytics:** Pandas
* **Security / Authentication:** SHA-256 Hashing (`hashlib`)

## ⚙️ Setup Instructions
This project is designed to be easily reproducible and runs locally without the need for heavy external server configurations.

**1. Clone the repository:**
```bash
git clone https://github.com/harsh7335/Cultural-Council-Asset-Manager.git

python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

pip install -r requirements.txt

python db.py #Initialize the Database:

streamlit run app.py #Start the Server

#default Admin Credentials:
#Username: admin
#Password: admin123
```
## Feature List

**Core Functionality (Mandatory)
Role-Based Authentication:** Secure, session-based login system separating 'Administrators' and 'Student / User' portals using SHA-256 password hashing.

**Inventory Management:** Full CRUD (Create, Read, Update, Delete) capabilities for assets, including dynamic stock calculation to prevent impossible total/available quantity mismatches.

**Asset Discovery & Booking:** Searchable and filterable asset catalog that dynamically hides out-of-stock items. Users can specify request quantities and start/end dates.

**Approval Workflow:** Admins can review, approve, or reject pending requests. The system strictly validates available inventory before allowing an approval.

**Issue & Return Management:** Digital-to-physical handshake. Admins log physical returns to automatically restore available inventory counts.

**Analytics Dashboard:** Live metrics displaying total assets, utilization rates (with progress bars), overdue return flags, and charts mapping current stock availability and asset popularity.

**Personal Borrowing History:** Students possess a private dashboard tracking their active possessions, pending requests, and historical returns.

**Security & Compliance (Bonus)
Immutable Audit Logging:** A background security helper function silently records all critical state mutations (Asset Creation, Deletion, Booking Approvals, and Returns) with timestamps and executing user IDs to an audit_logs database table, viewable via the Admin dashboard.

************************************************************



