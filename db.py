import sqlite3
import hashlib

# Helper function to hash passwords for security
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # 1. Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # Create Assets Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            status TEXT,
            total_quantity INTEGER,
            available_quantity INTEGER
        )
    ''')
    
    # Create Bookings Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            asset_id INTEGER,
            quantity INTEGER,
            start_date TEXT,
            end_date TEXT,
            status TEXT, 
            FOREIGN KEY(asset_id) REFERENCES assets(id)
        )
    ''')
    
    # --- DEFAULT ADMIN CREATION ---
    # We inject a default admin so you can actually log in the first time!
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ('admin', hash_password('admin123'), 'Administrator'))
    # Create Audit Logs Table (BONUS FEATURE)
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            action TEXT,
            details TEXT
        )
    ''')
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database and Auth tables initialized successfully!")