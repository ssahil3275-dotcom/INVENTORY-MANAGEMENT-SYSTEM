# database.py
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DB_FILE = "hyundai_dealership.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        vin TEXT PRIMARY KEY,
        model TEXT NOT NULL,
        variant TEXT NOT NULL,
        fuel_type TEXT NOT NULL,
        transmission TEXT NOT NULL,
        color TEXT NOT NULL,
        status TEXT NOT NULL,
        ex_showroom_price REAL NOT NULL,
        dispatch_date TEXT,
        eta_days INTEGER,
        days_in_yard INTEGER,
        service_stage TEXT,
        customer_name TEXT,
        sales_consultant TEXT,
        notes TEXT
    )
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        seed_database(conn)
    conn.close()

def seed_database(conn):
    np.random.seed(42)
    n = 160

    models_data = {
        "Creta": (["E", "EX", "S(O)", "SX Tech", "SX(O)"], 11.0, 20.15),
        "Venue": (["E", "S", "S(O)", "SX", "SX(O)"], 7.94, 13.48),
        "Exter": (["EX", "S", "SX", "SX(O) Connect"], 6.13, 10.28),
        "Verna": (["EX", "S", "SX", "SX(O) Turbo"], 11.00, 17.42),
        "Alcazar": (["Prestige", "Platinum", "Signature"], 16.78, 21.28),
        "i20": (["Era", "Magna", "Sportz", "Asta(O)"], 7.04, 11.21),
        "Ioniq 5": (["Long Range RWD"], 46.05, 46.05),
        "Tucson": (["Platinum", "Signature AWD"], 29.02, 35.94)
    }

    model_names = list(models_data.keys())
    model_probs = [0.28, 0.22, 0.16, 0.12, 0.08, 0.08, 0.03, 0.03]
    statuses = ["In Stock (Yard)", "In Transit (Dispatched)", "Allocated / Booked", "Under PDI / Service", "Delivered"]
    status_probs = [0.38, 0.22, 0.18, 0.12, 0.10]
    
    colors = ["Atlas White", "Abyss Black", "Titan Grey", "Ranger Khaki", "Fiery Red", "Starry Night"]
    consultants = ["Amit Sharma", "Priya Nair", "Rahul Verma", "Sneha Patel", "Vikram Das"]
    services = ["None", "Pre-Delivery Inspection (PDI)", "1st Free Service", "Periodic Maintenance", "Bodyshop / Repair"]

    chosen_models = np.random.choice(model_names, n, p=model_probs)
    records = []

    for i, model in enumerate(chosen_models):
        vin = f"MALC{np.random.randint(10000, 99999)}{i:03d}"
        variants, min_p, max_p = models_data[model]
        variant = np.random.choice(variants)
        fuel = np.random.choice(["Petrol", "Diesel", "EV", "CNG"], p=[0.55, 0.25, 0.05, 0.15] if model != "Ioniq 5" else [0, 0, 1.0, 0])
        trans = "Automatic" if ("Turbo" in variant or "(O)" in variant or model in ["Ioniq 5", "Tucson"]) else np.random.choice(["Manual", "Automatic"], p=[0.65, 0.35])
        color = np.random.choice(colors)
        status = np.random.choice(statuses, p=status_probs)
        price = round(float(np.random.uniform(min_p, max_p)), 2)

        if status == "In Transit (Dispatched)":
            dispatch_date = (datetime.today() - timedelta(days=int(np.random.randint(1, 6)))).strftime("%Y-%m-%d")
            eta_days = int(np.random.randint(1, 8))
            days_in_yard = 0
            service = "None"
        elif status == "In Stock (Yard)":
            dispatch_date = (datetime.today() - timedelta(days=int(np.random.randint(10, 85)))).strftime("%Y-%m-%d")
            eta_days = 0
            days_in_yard = int(np.random.randint(2, 75))
            service = "None"
        elif status == "Under PDI / Service":
            dispatch_date = (datetime.today() - timedelta(days=25)).strftime("%Y-%m-%d")
            eta_days = 0
            days_in_yard = int(np.random.randint(4, 28))
            service = np.random.choice(services[1:], p=[0.40, 0.25, 0.20, 0.15])
        else:
            dispatch_date = (datetime.today() - timedelta(days=35)).strftime("%Y-%m-%d")
            eta_days = 0
            days_in_yard = int(np.random.randint(1, 35))
            service = "None"

        cust = f"Customer_{1000 + i}" if status in ["Allocated / Booked", "Delivered"] else "Available"
        consultant = np.random.choice(consultants)
        notes = "Standard allocation"

        records.append((
            vin, model, variant, fuel, trans, color, status, price,
            dispatch_date, eta_days, days_in_yard, service, cust, consultant, notes
        ))

    conn.executemany("""
    INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    conn.commit()

def fetch_inventory():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    return df

def update_single_vehicle(vin, status, days_in_yard, eta_days, service_stage, customer_name, sales_consultant, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE inventory
    SET status = ?, days_in_yard = ?, eta_days = ?, service_stage = ?,
        customer_name = ?, sales_consultant = ?, notes = ?
    WHERE vin = ?
    """, (status, days_in_yard, eta_days, service_stage, customer_name, sales_consultant, notes, vin))
    conn.commit()
    conn.close()

def batch_update_inventory(updated_df):
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in updated_df.iterrows():
        cursor.execute("""
        UPDATE inventory
        SET status = ?, days_in_yard = ?, eta_days = ?, service_stage = ?,
            customer_name = ?, sales_consultant = ?, notes = ?
        WHERE vin = ?
        """, (row["status"], row["days_in_yard"], row["eta_days"], row["service_stage"],
              row["customer_name"], row["sales_consultant"], row["notes"], row["vin"]))
    conn.commit()
    conn.close()

def insert_vehicle(vin, model, variant, fuel, trans, color, status, price, eta, consultant, notes):
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.today().strftime("%Y-%m-%d")
    cursor.execute("""
    INSERT INTO inventory (vin, model, variant, fuel_type, transmission, color, status,
                           ex_showroom_price, dispatch_date, eta_days, days_in_yard,
                           service_stage, customer_name, sales_consultant, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'None', 'Available', ?, ?)
    """, (vin, model, variant, fuel, trans, color, status, price, today_str, eta, consultant, notes))
    conn.commit()
    conn.close()

def delete_vehicle(vin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE vin = ?", (vin,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database hyundai_dealership.db ready with seed data.")