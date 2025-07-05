#!/usr/bin/env python3
"""
Initialize SQLite database for Inventory Management System (IMS)
Creates all required tables with proper relationships and sample data
"""

import sqlite3
import os
import hashlib
from datetime import datetime, timedelta

DB_NAME = "myapp.db"
DB_USER = "kaviasqlite"  # Not used for SQLite, but kept for consistency
DB_PASSWORD = "kaviadefaultpassword"  # Not used for SQLite, but kept for consistency
DB_PORT = "5000"  # Not used for SQLite, but kept for consistency

# PUBLIC_INTERFACE
def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

print("Starting Inventory Management System SQLite setup...")

# Check if database already exists
db_exists = os.path.exists(DB_NAME)
if db_exists:
    print(f"SQLite database already exists at {DB_NAME}")
    # Verify it's accessible
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("SELECT 1")
        conn.close()
        print("Database is accessible and working.")
    except Exception as e:
        print(f"Warning: Database exists but may be corrupted: {e}")
else:
    print("Creating new SQLite database...")

# Create database with inventory management schema
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Enable foreign key constraints
cursor.execute("PRAGMA foreign_keys = ON")

print("Creating inventory management tables...")

# 1. Roles table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        permissions TEXT, -- JSON string of permissions
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# 2. Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        role_id INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (role_id) REFERENCES roles(id)
    )
""")

# 3. Storerooms table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS storerooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        location TEXT,
        capacity INTEGER,
        manager_id INTEGER,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (manager_id) REFERENCES users(id)
    )
""")

# 4. Items table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        sku TEXT UNIQUE,
        category TEXT,
        unit_of_measure TEXT DEFAULT 'pcs',
        minimum_stock INTEGER DEFAULT 0,
        maximum_stock INTEGER,
        unit_cost DECIMAL(10,2),
        barcode TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# 5. Storeroom Items table (junction table with inventory levels)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS storeroom_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        storeroom_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 0,
        reserved_quantity INTEGER DEFAULT 0,
        last_counted_at TIMESTAMP,
        last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (storeroom_id) REFERENCES storerooms(id),
        FOREIGN KEY (item_id) REFERENCES items(id),
        UNIQUE(storeroom_id, item_id)
    )
""")

# 6. Transfers table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfer_number TEXT UNIQUE NOT NULL,
        source_storeroom_id INTEGER,
        destination_storeroom_id INTEGER,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        transfer_type TEXT NOT NULL, -- 'transfer', 'adjustment', 'receive', 'issue'
        status TEXT DEFAULT 'pending', -- 'pending', 'in_transit', 'completed', 'cancelled'
        reason TEXT,
        requested_by INTEGER NOT NULL,
        approved_by INTEGER,
        completed_by INTEGER,
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP,
        completed_at TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (source_storeroom_id) REFERENCES storerooms(id),
        FOREIGN KEY (destination_storeroom_id) REFERENCES storerooms(id),
        FOREIGN KEY (item_id) REFERENCES items(id),
        FOREIGN KEY (requested_by) REFERENCES users(id),
        FOREIGN KEY (approved_by) REFERENCES users(id),
        FOREIGN KEY (completed_by) REFERENCES users(id)
    )
""")

# 7. Transfer Logs table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS transfer_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfer_id INTEGER NOT NULL,
        action TEXT NOT NULL, -- 'created', 'approved', 'in_transit', 'completed', 'cancelled'
        previous_status TEXT,
        new_status TEXT,
        user_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (transfer_id) REFERENCES transfers(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# 8. App Info table for system metadata
cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("Tables created successfully. Inserting sample data...")

# Insert sample roles
roles_data = [
    ("admin", "System Administrator", '{"all": true}'),
    ("manager", "Storeroom Manager", '{"storerooms": ["read", "write"], "items": ["read", "write"], "transfers": ["read", "write", "approve"]}'),
    ("clerk", "Inventory Clerk", '{"items": ["read"], "transfers": ["read", "create"], "storerooms": ["read"]}'),
    ("viewer", "Read-only User", '{"items": ["read"], "transfers": ["read"], "storerooms": ["read"]}')
]

cursor.executemany("""
    INSERT OR REPLACE INTO roles (name, description, permissions) VALUES (?, ?, ?)
""", roles_data)

# Insert sample users
users_data = [
    ("admin", "admin@inventory.com", hash_password("admin123"), "System", "Administrator", 1, 1),
    ("manager1", "manager1@inventory.com", hash_password("manager123"), "John", "Manager", 2, 1),
    ("manager2", "manager2@inventory.com", hash_password("manager123"), "Jane", "Manager", 2, 1),
    ("clerk1", "clerk1@inventory.com", hash_password("clerk123"), "Bob", "Clerk", 3, 1),
    ("clerk2", "clerk2@inventory.com", hash_password("clerk123"), "Alice", "Clerk", 3, 1),
    ("viewer1", "viewer1@inventory.com", hash_password("viewer123"), "Tom", "Viewer", 4, 1)
]

cursor.executemany("""
    INSERT OR REPLACE INTO users (username, email, password_hash, first_name, last_name, role_id, is_active) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", users_data)

# Insert sample storerooms
storerooms_data = [
    ("Main Warehouse", "Primary storage facility", "Building A, Floor 1", 10000, 2, 1),
    ("Electronics Storage", "Electronic components and devices", "Building B, Floor 2", 5000, 2, 1),
    ("Raw Materials", "Raw materials and supplies", "Building A, Floor 2", 8000, 3, 1),
    ("Finished Goods", "Completed products ready for shipment", "Building C, Floor 1", 12000, 3, 1),
    ("Quality Control", "Items under quality inspection", "Building B, Floor 1", 2000, 2, 1)
]

cursor.executemany("""
    INSERT OR REPLACE INTO storerooms (name, description, location, capacity, manager_id, is_active) 
    VALUES (?, ?, ?, ?, ?, ?)
""", storerooms_data)

# Insert sample items
items_data = [
    ("Laptop Computer", "Dell Latitude 7420 Business Laptop", "LAP-DEL-7420", "Electronics", "pcs", 5, 50, 1200.00, "123456789012", 1),
    ("Wireless Mouse", "Logitech MX Master 3 Wireless Mouse", "MOU-LOG-MX3", "Electronics", "pcs", 10, 100, 99.99, "123456789013", 1),
    ("Office Chair", "Ergonomic Office Chair with Lumbar Support", "CHR-ERG-001", "Furniture", "pcs", 2, 25, 299.99, "123456789014", 1),
    ("Printer Paper", "A4 White Copy Paper, 500 sheets", "PAP-A4-500", "Office Supplies", "ream", 20, 200, 8.99, "123456789015", 1),
    ("USB Cable", "USB-C to USB-A Cable, 6ft", "CBL-USC-6FT", "Electronics", "pcs", 25, 500, 12.99, "123456789016", 1),
    ("Desk Lamp", "LED Desk Lamp with USB Charging Port", "LAM-LED-USB", "Electronics", "pcs", 5, 30, 45.99, "123456789017", 1),
    ("Keyboard", "Mechanical Gaming Keyboard RGB", "KEY-MEC-RGB", "Electronics", "pcs", 8, 60, 89.99, "123456789018", 1),
    ("Monitor", "24-inch LED Monitor Full HD", "MON-24-FHD", "Electronics", "pcs", 3, 40, 199.99, "123456789019", 1),
    ("Notebook", "Spiral Bound Notebook, 200 pages", "NOT-SPI-200", "Office Supplies", "pcs", 50, 300, 3.99, "123456789020", 1),
    ("Stapler", "Heavy Duty Office Stapler", "STA-HVY-001", "Office Supplies", "pcs", 5, 25, 24.99, "123456789021", 1)
]

cursor.executemany("""
    INSERT OR REPLACE INTO items (name, description, sku, category, unit_of_measure, minimum_stock, maximum_stock, unit_cost, barcode, is_active) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", items_data)

# Insert sample storeroom inventory
storeroom_items_data = [
    # Main Warehouse
    (1, 1, 25, 0), (1, 2, 75, 5), (1, 3, 15, 0), (1, 4, 150, 10),
    (1, 5, 300, 20), (1, 6, 20, 0), (1, 7, 45, 3), (1, 8, 30, 2),
    (1, 9, 200, 15), (1, 10, 18, 0),
    
    # Electronics Storage
    (2, 1, 15, 2), (2, 2, 50, 5), (2, 5, 200, 15), (2, 6, 25, 0),
    (2, 7, 35, 5), (2, 8, 25, 3),
    
    # Raw Materials
    (3, 4, 100, 20), (3, 5, 150, 10), (3, 9, 250, 25),
    
    # Finished Goods
    (4, 1, 20, 0), (4, 2, 40, 0), (4, 3, 12, 0), (4, 6, 15, 0),
    (4, 7, 25, 0), (4, 8, 20, 0), (4, 10, 12, 0),
    
    # Quality Control
    (5, 1, 5, 5), (5, 2, 10, 10), (5, 8, 8, 8)
]

cursor.executemany("""
    INSERT OR REPLACE INTO storeroom_items (storeroom_id, item_id, quantity, reserved_quantity) 
    VALUES (?, ?, ?, ?)
""", storeroom_items_data)

# Insert sample transfers
base_date = datetime.now() - timedelta(days=30)
transfers_data = [
    (f"TRF-{(base_date + timedelta(days=i)).strftime('%Y%m%d')}-{str(i+1).zfill(3)}", 
     1, 2, i % 10 + 1, (i % 3) + 1, 
     "transfer", "completed", "Restock electronics storage", 
     2, 2, 3, 
     (base_date + timedelta(days=i)).isoformat(),
     (base_date + timedelta(days=i, hours=2)).isoformat(),
     (base_date + timedelta(days=i, hours=4)).isoformat())
    for i in range(10)
]

cursor.executemany("""
    INSERT OR REPLACE INTO transfers (transfer_number, source_storeroom_id, destination_storeroom_id, item_id, quantity, 
                                     transfer_type, status, reason, requested_by, approved_by, completed_by, 
                                     requested_at, approved_at, completed_at) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", transfers_data)

# Insert sample transfer logs
transfer_logs_data = []
for i in range(10):
    transfer_id = i + 1
    base_time = base_date + timedelta(days=i)
    
    # Created log
    transfer_logs_data.append((transfer_id, "created", None, "pending", 2, base_time.isoformat(), "Transfer request created"))
    
    # Approved log
    transfer_logs_data.append((transfer_id, "approved", "pending", "in_transit", 2, (base_time + timedelta(hours=2)).isoformat(), "Transfer approved"))
    
    # Completed log
    transfer_logs_data.append((transfer_id, "completed", "in_transit", "completed", 3, (base_time + timedelta(hours=4)).isoformat(), "Transfer completed"))

cursor.executemany("""
    INSERT OR REPLACE INTO transfer_logs (transfer_id, action, previous_status, new_status, user_id, timestamp, notes) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", transfer_logs_data)

# Insert app info
app_info_data = [
    ("project_name", "Inventory Management System"),
    ("version", "1.0.0"),
    ("author", "IMS Development Team"),
    ("description", "Complete inventory management system with multi-storeroom support"),
    ("database_version", "1.0"),
    ("last_migration", datetime.now().isoformat())
]

cursor.executemany("""
    INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)
""", app_info_data)

# Create indexes for better performance
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_sku ON items(sku)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_storeroom_items_storeroom_id ON storeroom_items(storeroom_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_storeroom_items_item_id ON storeroom_items(item_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_transfer_number ON transfers(transfer_number)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_requested_at ON transfers(requested_at)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfer_logs_transfer_id ON transfer_logs(transfer_id)")

conn.commit()

# Get database statistics
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
table_count = cursor.fetchone()[0]

# Get record counts for each table
tables = ['roles', 'users', 'storerooms', 'items', 'storeroom_items', 'transfers', 'transfer_logs', 'app_info']
table_stats = {}
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    table_stats[table] = cursor.fetchone()[0]

conn.close()

# Save connection information to a file
current_dir = os.getcwd()
connection_string = f"sqlite:///{current_dir}/{DB_NAME}"

try:
    with open("db_connection.txt", "w") as f:
        f.write(f"# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {current_dir}/{DB_NAME}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

# Create environment variables file for Node.js viewer
db_path = os.path.abspath(DB_NAME)

# Ensure db_visualizer directory exists
if not os.path.exists("db_visualizer"):
    os.makedirs("db_visualizer", exist_ok=True)
    print("Created db_visualizer directory")

try:
    with open("db_visualizer/sqlite.env", "w") as f:
        f.write(f'export SQLITE_DB="{db_path}"\n')
    print(f"Environment variables saved to db_visualizer/sqlite.env")
except Exception as e:
    print(f"Warning: Could not save environment variables: {e}")

print("\nInventory Management System SQLite setup complete!")
print(f"Database: {DB_NAME}")
print(f"Location: {current_dir}/{DB_NAME}")
print()

print("Database Statistics:")
print(f"  Total Tables: {table_count}")
for table, count in table_stats.items():
    print(f"  {table}: {count} records")

print("\nSample Users Created:")
print("  admin/admin123 (Administrator)")
print("  manager1/manager123 (Manager)")
print("  clerk1/clerk123 (Clerk)")
print("  viewer1/viewer123 (Viewer)")

print("\nTo use with Node.js viewer, run: source db_visualizer/sqlite.env")

print("\nTo connect to the database, use one of the following methods:")
print(f"1. Python: sqlite3.connect('{DB_NAME}')")
print(f"2. Connection string: {connection_string}")
print(f"3. Direct file access: {current_dir}/{DB_NAME}")
print()

# If sqlite3 CLI is available, show how to use it
try:
    import subprocess
    result = subprocess.run(['which', 'sqlite3'], capture_output=True, text=True)
    if result.returncode == 0:
        print("SQLite CLI is available. You can also use:")
        print(f"  sqlite3 {DB_NAME}")
except:
    pass

print("\nDatabase Schema Summary:")
print("  - roles: User roles and permissions")
print("  - users: System users with authentication")
print("  - storerooms: Storage locations")
print("  - items: Inventory items with details")
print("  - storeroom_items: Item quantities per storeroom")
print("  - transfers: Item transfer requests and history")
print("  - transfer_logs: Audit trail for transfers")
print("  - app_info: System metadata")

print("\nScript completed successfully.")
