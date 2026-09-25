import numpy as np
import pandas as pd

def generate_dealership_data():
    np.random.seed(42)
    models = ["Creta", "Venue", "Verna", "Tucson", "Ioniq 5", "Exter", "i20"]
    fuel_types = ["Petrol", "Diesel", "EV"]
    statuses = ["In Stock", "In Transit (Dispatched)", "Sold / Delivered", "Under PDI / Service"]
    
    n_records = 300
    data = {
        "VIN": [f"MAL{100000 + i}" for i in range(n_records)],
        "Model": np.random.choice(models, n_records, p=[0.25, 0.20, 0.15, 0.05, 0.05, 0.20, 0.10]),
        "Fuel": np.random.choice(fuel_types, n_records, p=[0.6, 0.3, 0.1]),
        "Status": np.random.choice(statuses, n_records, p=[0.35, 0.20, 0.35, 0.10]),
        "Price_Lakhs": np.random.uniform(8.0, 45.0, n_records).round(2),
        "Days_in_Yard": np.random.randint(2, 65, n_records),
        "Service_Flag": np.random.choice(["None", "First Free Service", "Periodic", "Repair"], n_records, p=[0.7, 0.15, 0.1, 0.05]),
    }
    return pd.DataFrame(data)