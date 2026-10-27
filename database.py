import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "warehouse.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Inventory Master Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_id TEXT PRIMARY KEY,
        item_name TEXT NOT NULL,
        category TEXT NOT NULL,
        stock_level INTEGER NOT NULL,
        reorder_point INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        zone TEXT NOT NULL,
        bin_location TEXT NOT NULL,
        supplier TEXT NOT NULL,
        lead_time_days INTEGER NOT NULL,
        daily_demand REAL NOT NULL,
        last_restocked TEXT NOT NULL
    )
    """)

    # 2. Inbound Stock Intake Table (Goods Receipt Notes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intake_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grn_number TEXT UNIQUE NOT NULL,
        item_id TEXT NOT NULL,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        zone TEXT NOT NULL,
        bin_location TEXT NOT NULL,
        supplier TEXT NOT NULL,
        po_number TEXT NOT NULL,
        batch_no TEXT NOT NULL,
        inspector TEXT NOT NULL,
        condition TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (item_id) REFERENCES inventory(item_id)
    )
    """)

    # 3. Outbound Stock Dispatch Table (Goods Dispatch Notes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dispatch_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gdn_number TEXT UNIQUE NOT NULL,
        item_id TEXT NOT NULL,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        destination TEXT NOT NULL,
        carrier TEXT NOT NULL,
        waybill TEXT NOT NULL,
        dispatcher TEXT NOT NULL,
        priority TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (item_id) REFERENCES inventory(item_id)
    )
    """)

    # 4. Storage Zones Master
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zones (
        zone_code TEXT PRIMARY KEY,
        zone_name TEXT NOT NULL,
        zone_type TEXT NOT NULL,
        total_bays INTEGER NOT NULL,
        temperature_control TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def seed_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM inventory")
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        return

    # Seed Storage Zones
    zones_data = [
        ("Zone A", "Fast-Moving & High Value Bay", "High-Velocity Pallet Rack", 120, "Ambient (20°C - 24°C)"),
        ("Zone B", "Medium Turnover & Automotive Rack", "Standard Industrial Racking", 180, "Ambient (18°C - 25°C)"),
        ("Zone C", "Heavy Bulk & Industrial Storage", "Floor Pallet Staging & Drive-In Racks", 250, "Standard Warehouse"),
        ("Zone D", "Specialized & Cold Storage", "Climate Controlled Refrigeration", 80, "Cold Chain (2°C - 6°C)")
    ]
    cursor.executemany("INSERT INTO zones VALUES (?, ?, ?, ?, ?)", zones_data)

    # 40 Realistic Seed Inventory SKUs
    seed_items = [
        ("SKU-1001", "Amoxicillin Trihydrate 500mg", "Pharmaceuticals", 420, 150, 48.50, "Zone D", "BIN-D-101", "Pfizer Global Logistics", 3, 25.0, "2026-10-25 10:30"),
        ("SKU-1002", "Paracetamol Suspension 100ml", "Pharmaceuticals", 680, 200, 12.20, "Zone D", "BIN-D-102", "Novartis Pharma Supply", 4, 35.0, "2026-10-24 14:15"),
        ("SKU-1003", "Insulin Glargine Pen Cartridges", "Pharmaceuticals", 45, 80, 125.00, "Zone D", "BIN-D-103", "Sanofi Cold Chain", 2, 14.0, "2026-10-22 09:00"),
        ("SKU-1004", "Sterile Surgical Gloves (Box 100)", "Pharmaceuticals", 550, 150, 24.90, "Zone D", "BIN-D-104", "MediHealth Supplies", 5, 28.0, "2026-10-26 11:20"),
        ("SKU-1005", "Digital Infrared Thermometer", "Pharmaceuticals", 32, 60, 38.00, "Zone D", "BIN-D-105", "Apex BioDevices", 7, 6.5, "2026-10-18 16:40"),

        ("SKU-2001", "ARM Cortex-M4 Microcontroller", "Electronics", 890, 300, 8.40, "Zone A", "BIN-A-201", "STMicroelectronics Direct", 6, 42.0, "2026-10-26 08:30"),
        ("SKU-2002", "OLED Display Module 128x64 I2C", "Electronics", 320, 120, 14.50, "Zone A", "BIN-A-202", "Adafruit Electronic Imports", 8, 18.0, "2026-10-23 13:10"),
        ("SKU-2003", "Lithium Polymer Battery 3.7V 2500mAh", "Electronics", 65, 150, 18.90, "Zone A", "BIN-A-203", "Panasonic Energy Supply", 5, 22.0, "2026-10-19 12:00"),
        ("SKU-2004", "Surface Mount Resistor Reel 10k Ohm", "Electronics", 2400, 500, 4.20, "Zone A", "BIN-A-204", "Vishay Intertechnology", 10, 85.0, "2026-10-25 15:45"),
        ("SKU-2005", "ESP32-WROOM-32D Wi-Fi & BT Module", "Electronics", 740, 250, 6.75, "Zone A", "BIN-A-205", "Espressif Systems", 7, 36.0, "2026-10-24 10:00"),
        ("SKU-2006", "Step-Down DC-DC Buck Converter 5A", "Electronics", 18, 50, 11.30, "Zone A", "BIN-A-206", "Texas Instruments Dist.", 9, 7.2, "2026-10-15 11:30"),

        ("SKU-3001", "Hydraulic Brake Disc Rotors Front", "Automotive", 140, 50, 84.00, "Zone B", "BIN-B-301", "Brembo Automotive Parts", 6, 9.0, "2026-10-25 17:00"),
        ("SKU-3002", "Synthetic Engine Oil 5W-30 4L", "Automotive", 310, 100, 42.50, "Zone B", "BIN-B-302", "Mobil 1 Lubricants Ltd", 4, 16.0, "2026-10-26 12:30"),
        ("SKU-3003", "Ceramic Brake Pad Set Front & Rear", "Automotive", 28, 70, 56.00, "Zone B", "BIN-B-303", "Bosch Aftermarket Supply", 5, 11.5, "2026-10-20 14:00"),
        ("SKU-3004", "High-Flow Cabin Air Filter HEPA", "Automotive", 210, 80, 19.80, "Zone B", "BIN-B-304", "Mann+Hummel Filters", 7, 14.0, "2026-10-23 09:45"),
        ("SKU-3005", "Lead-Acid 12V 65Ah Car Battery", "Automotive", 48, 40, 135.00, "Zone B", "BIN-B-305", "Exide Industries", 4, 5.0, "2026-10-22 16:15"),
        ("SKU-3006", "Iridium Spark Plugs Set of 4", "Automotive", 420, 120, 32.00, "Zone B", "BIN-B-306", "NGK Spark Plug Co.", 6, 21.0, "2026-10-26 09:10"),

        ("SKU-4001", "Heavy Duty Hydraulic Floor Jack 3T", "Industrial Tools", 35, 20, 185.00, "Zone C", "BIN-C-401", "Torin Big Red Jacks", 12, 2.5, "2026-10-21 11:00"),
        ("SKU-4002", "Cordless Brushless Impact Wrench 20V", "Industrial Tools", 75, 30, 145.00, "Zone C", "BIN-C-402", "DeWalt Industrial Tools", 8, 4.8, "2026-10-24 15:30"),
        ("SKU-4003", "Industrial Grade Steel Cable Wire 50m", "Industrial Tools", 60, 25, 95.00, "Zone C", "BIN-C-403", "National Wire & Cable", 14, 3.2, "2026-10-19 10:20"),
        ("SKU-4004", "Heavy Duty Steel Pallet Racking Beam", "Industrial Tools", 12, 30, 210.00, "Zone C", "BIN-C-404", "Dexion Storage Systems", 15, 2.0, "2026-10-14 13:00"),
        ("SKU-4005", "Precision Digital Torque Wrench 1/2\"", "Industrial Tools", 85, 40, 115.00, "Zone C", "BIN-C-405", "Snap-on Industrial", 9, 5.5, "2026-10-25 16:20"),

        ("SKU-5001", "High-Visibility Safety Reflective Vest", "Apparel & Safety", 480, 150, 14.50, "Zone A", "BIN-A-501", "3M Safety Products", 5, 26.0, "2026-10-26 14:00"),
        ("SKU-5002", "Steel Toe Cap Waterproof Work Boots", "Apparel & Safety", 95, 50, 89.00, "Zone B", "BIN-B-502", "Timberland PRO Industrial", 7, 7.5, "2026-10-23 11:45"),
        ("SKU-5003", "Cut-Resistant Kevlar Work Gloves L", "Apparel & Safety", 22, 60, 18.20, "Zone A", "BIN-A-503", "Ansell Protective Gear", 6, 9.0, "2026-10-17 15:30"),
        ("SKU-5004", "Industrial ANSI Hard Hat Ratchet Suspension", "Apparel & Safety", 260, 100, 28.00, "Zone A", "BIN-A-504", "MSA Safety Equipment", 8, 16.0, "2026-10-25 10:15"),

        ("SKU-6001", "Organic Arabica Coffee Beans 1kg", "Food & Beverages", 340, 100, 22.50, "Zone D", "BIN-D-601", "Highland Coffee Roasters", 4, 18.0, "2026-10-26 13:10"),
        ("SKU-6002", "Almond Milk Barista Edition 1L Case 12", "Food & Beverages", 180, 60, 36.00, "Zone D", "BIN-D-602", "Oatly Beverage Corp", 5, 12.0, "2026-10-24 11:00"),
        ("SKU-6003", "Cold Brew Coffee Concentrate 5L Keg", "Food & Beverages", 15, 40, 68.00, "Zone D", "BIN-D-603", "Nitro Cold Brew Ltd", 3, 6.0, "2026-10-20 08:30")
    ]

    cursor.executemany("""
    INSERT INTO inventory (
        item_id, item_name, category, stock_level, reorder_point,
        unit_price, zone, bin_location, supplier, lead_time_days,
        daily_demand, last_restocked
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, seed_items)

    # 10 Realistic Intake Records
    seed_intakes = [
        ("GRN-2026-1001", "SKU-1001", "Amoxicillin Trihydrate 500mg", 150, "Zone D", "BIN-D-101", "Pfizer Global Logistics", "PO-98210", "BAT-2026-X1", "Arya Rai", "Passed Quality Check", "2026-10-25 10:30:00"),
        ("GRN-2026-1002", "SKU-2001", "ARM Cortex-M4 Microcontroller", 300, "Zone A", "BIN-A-201", "STMicroelectronics Direct", "PO-98214", "BAT-2026-E4", "Marcus Vance", "Passed Quality Check", "2026-10-26 08:30:00"),
        ("GRN-2026-1003", "SKU-3002", "Synthetic Engine Oil 5W-30 4L", 120, "Zone B", "BIN-B-302", "Mobil 1 Lubricants Ltd", "PO-98229", "BAT-2026-A9", "Arya Rai", "Passed Quality Check", "2026-10-26 12:30:00"),
        ("GRN-2026-1004", "SKU-5001", "High-Visibility Safety Reflective Vest", 200, "Zone A", "BIN-A-501", "3M Safety Products", "PO-98235", "BAT-2026-S2", "Sarah Connor", "Passed Quality Check", "2026-10-26 14:00:00"),
        ("GRN-2026-1005", "SKU-6001", "Organic Arabica Coffee Beans 1kg", 100, "Zone D", "BIN-D-601", "Highland Coffee Roasters", "PO-98240", "BAT-2026-F1", "Arya Rai", "Passed Quality Check", "2026-10-26 13:10:00")
    ]

    cursor.executemany("""
    INSERT INTO intake_orders (
        grn_number, item_id, item_name, quantity, zone, bin_location,
        supplier, po_number, batch_no, inspector, condition, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, seed_intakes)

    # 10 Realistic Dispatch Records
    seed_dispatches = [
        ("GDN-2026-0501", "SKU-1002", "Paracetamol Suspension 100ml", 50, "Regional Hospital Central", "DHL Express Medical", "WB-8839101", "Arya Rai", "Urgent Clinical", "2026-10-26 09:15:00"),
        ("GDN-2026-0502", "SKU-3001", "Hydraulic Brake Disc Rotors Front", 20, "North City Auto Service Hub", "FedEx Freight", "WB-8839102", "John Smith", "Standard Ground", "2026-10-26 11:45:00"),
        ("GDN-2026-0503", "SKU-2005", "ESP32-WROOM-32D Wi-Fi & BT Module", 80, "Apex Robotics Manufacturing", "Blue Dart Express", "WB-8839103", "Arya Rai", "Expedited 24h", "2026-10-26 13:20:00"),
        ("GDN-2026-0504", "SKU-5004", "Industrial ANSI Hard Hat Ratchet Suspension", 45, "Metro Metro Construction Site 4", "Internal Fleet Van 2", "WB-8839104", "David Miller", "Standard Ground", "2026-10-26 15:30:00"),
        ("GDN-2026-0505", "SKU-6002", "Almond Milk Barista Edition 1L Case 12", 30, "Downtown Gourmet Coffeehouse", "FreshWay Courier", "WB-8839105", "Arya Rai", "Standard Ground", "2026-10-26 16:50:00")
    ]

    cursor.executemany("""
    INSERT INTO dispatch_orders (
        gdn_number, item_id, item_name, quantity, destination, carrier,
        waybill, dispatcher, priority, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, seed_dispatches)

    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# Database CRUD Operations
# -----------------------------------------------------------------------------
def get_all_inventory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory ORDER BY category, item_id")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_inventory_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE item_id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def record_intake_shipment(item_id, quantity, zone, bin_location, supplier, po_number, batch_no, inspector, condition):
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch item
    cursor.execute("SELECT item_name, stock_level FROM inventory WHERE item_id = ?", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        return False, "Item ID not found in inventory master."

    item_name = item["item_name"]
    old_stock = item["stock_level"]
    new_stock = old_stock + quantity
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    grn_code = f"GRN-2026-{random.randint(1000, 9999)}"

    # 2. Insert into intake ledger
    cursor.execute("""
    INSERT INTO intake_orders (
        grn_number, item_id, item_name, quantity, zone, bin_location,
        supplier, po_number, batch_no, inspector, condition, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (grn_code, item_id, item_name, quantity, zone, bin_location, supplier, po_number, batch_no, inspector, condition, now_str))

    # 3. Update inventory
    cursor.execute("""
    UPDATE inventory 
    SET stock_level = ?, zone = ?, bin_location = ?, last_restocked = ?
    WHERE item_id = ?
    """, (new_stock, zone, bin_location, now_str, item_id))

    conn.commit()
    conn.close()
    return True, grn_code

def record_dispatch_shipment(item_id, quantity, destination, carrier, waybill, dispatcher, priority):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT item_name, stock_level, reorder_point FROM inventory WHERE item_id = ?", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        return False, "Item ID not found.", 0, 0

    item_name = item["item_name"]
    current_stock = item["stock_level"]
    reorder_point = item["reorder_point"]

    if quantity > current_stock:
        conn.close()
        return False, f"Insufficient stock! Available: {current_stock} units.", current_stock, reorder_point

    new_stock = current_stock - quantity
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    gdn_code = f"GDN-2026-{random.randint(1000, 9999)}"

    cursor.execute("""
    INSERT INTO dispatch_orders (
        gdn_number, item_id, item_name, quantity, destination, carrier,
        waybill, dispatcher, priority, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (gdn_code, item_id, item_name, quantity, destination, carrier, waybill, dispatcher, priority, now_str))

    cursor.execute("UPDATE inventory SET stock_level = ? WHERE item_id = ?", (new_stock, item_id))

    conn.commit()
    conn.close()
    return True, gdn_code, new_stock, reorder_point

def add_new_inventory_item(item_id, item_name, category, stock_level, reorder_point, unit_price, zone, bin_location, supplier, lead_time_days, daily_demand):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id FROM inventory WHERE item_id = ?", (item_id,))
    if cursor.fetchone():
        conn.close()
        return False, f"SKU {item_id} already exists."

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
    INSERT INTO inventory (
        item_id, item_name, category, stock_level, reorder_point, unit_price,
        zone, bin_location, supplier, lead_time_days, daily_demand, last_restocked
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (item_id, item_name, category, stock_level, reorder_point, unit_price, zone, bin_location, supplier, lead_time_days, daily_demand, now_str))

    # Also log initial intake
    grn_code = f"GRN-2026-{random.randint(1000, 9999)}"
    cursor.execute("""
    INSERT INTO intake_orders (
        grn_number, item_id, item_name, quantity, zone, bin_location,
        supplier, po_number, batch_no, inspector, condition, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (grn_code, item_id, item_name, stock_level, zone, bin_location, supplier, "PO-INITIAL", "LOT-INITIAL", "System Admin", "Initial Stock", now_str))

    conn.commit()
    conn.close()
    return True, grn_code

def update_inventory_stock(item_id, new_stock, new_reorder, new_price, new_bin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE inventory 
    SET stock_level = ?, reorder_point = ?, unit_price = ?, bin_location = ?
    WHERE item_id = ?
    """, (new_stock, new_reorder, new_price, new_bin, item_id))
    conn.commit()
    conn.close()
    return True

def delete_inventory_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()
    return True

def get_intake_records():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM intake_orders ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_dispatch_records():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dispatch_orders ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_zones():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM zones")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
