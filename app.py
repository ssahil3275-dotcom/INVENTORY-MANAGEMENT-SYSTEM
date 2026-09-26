# app.py
import io
import streamlit as st
import plotly.express as px
import pandas as pd
from database import init_db, fetch_inventory, update_single_vehicle, batch_update_inventory, insert_vehicle, delete_vehicle

init_db()

st.set_page_config(
    page_title="Hyundai Dealership Management System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Corporate Design
st.markdown("""
<style>
    :root {
        --primary-blue: #00287A;
        --secondary-navy: #001A4E;
        --border-gray: #E2E8F0;
        --card-bg: #FFFFFF;
    }
    
    /* Header Bar */
    .corporate-header {
        background-color: #00287A;
        padding: 20px 24px;
        border-radius: 6px;
        color: #FFFFFF;
        margin-bottom: 24px;
    }
    .corporate-header h1 {
        color: #FFFFFF !important;
        font-size: 24px;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .corporate-header p {
        color: #BAC7E0;
        font-size: 13px;
        margin: 4px 0 0 0;
    }

    /* KPI Cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 16px 20px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetricLabel"] {
        color: #64748B;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #0F172A;
        font-size: 26px;
        font-weight: 700;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        font-weight: 500;
        font-size: 14px;
        padding: 12px 18px;
    }
</style>
""", unsafe_allow_html=True)

df = fetch_inventory()

# --- SIDEBAR: STRICT ENTERPRISE FILTERING ---
st.sidebar.markdown("### Dealership Controls")
st.sidebar.caption("Dealer Management System Filters")

search_term = st.sidebar.text_input("Search VIN or Customer", "")

model_options = sorted(list(df["model"].unique()))
selected_models = st.sidebar.multiselect("Vehicle Line", model_options, default=model_options)

fuel_options = sorted(list(df["fuel_type"].unique()))
selected_fuels = st.sidebar.multiselect("Powertrain", fuel_options, default=fuel_options)

status_options = sorted(list(df["status"].unique()))
selected_statuses = st.sidebar.multiselect("Vehicle Lifecycle Status", status_options, default=status_options)

# Filter logic
filtered = df[
    (df["model"].isin(selected_models)) &
    (df["fuel_type"].isin(selected_fuels)) &
    (df["status"].isin(selected_statuses))
]

if search_term:
    filtered = filtered[
        filtered["vin"].str.contains(search_term, case=False, na=False) |
        filtered["customer_name"].str.contains(search_term, case=False, na=False)
    ]

# Header
st.markdown("""
<div class="corporate-header">
    <h1>Hyundai Motor India • Dealer Management Portal</h1>
    <p>Operational Analytics, Supply Chain Dispatches, Stock Aging & Workshop Queues</p>
</div>
""", unsafe_allow_html=True)

# Main Navigation
tab_summary, tab_dispatch, tab_aging, tab_service, tab_table_edit, tab_form_edit, tab_new_inward = st.tabs([
    "Executive Summary",
    "Dispatch Logistics",
    "Stock Aging Analysis",
    "Service Workshop",
    "Inline Table Editor",
    "Record Form Editor",
    "Inward Factory Unit"
])

# ==========================================
# TAB 1: EXECUTIVE SUMMARY
# ==========================================
with tab_summary:
    tot_fleet = len(filtered)
    tot_val = filtered["ex_showroom_price"].sum()
    yard_units = len(filtered[filtered["status"] == "In Stock (Yard)"])
    transit_units = len(filtered[filtered["status"] == "In Transit (Dispatched)"])
    aging_risk = len(filtered[(filtered["status"] == "In Stock (Yard)") & (filtered["days_in_yard"] > 45)])

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Active Portfolio", f"{tot_fleet} Units")
    k2.metric("Inventory Capital", f"₹ {tot_val:,.1f} L")
    k3.metric("Yard Available", f"{yard_units} Units")
    k4.metric("Dispatched In-Transit", f"{transit_units} Units")
    k5.metric("Aging Warning (>45D)", f"{aging_risk} Units", delta="Capital Risk" if aging_risk > 0 else "Normal", delta_color="inverse")

    st.markdown("---")

    col_chart_a, col_chart_b = st.columns([3, 2])
    with col_chart_a:
        st.markdown("##### Model Volume by Status")
        fig_bar = px.bar(
            filtered, x="model", color="status",
            barmode="stack",
            template="plotly_white",
            color_discrete_sequence=["#00287A", "#4A72B2", "#94A3B8", "#D97706", "#059669"]
        )
        fig_bar.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="",
            yaxis_title="Vehicles",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart_b:
        st.markdown("##### Powertrain Distribution")
        fig_donut = px.pie(
            filtered, names="fuel_type", hole=0.6,
            color_discrete_sequence=["#00287A", "#2563EB", "#60A5FA", "#93C5FD"]
        )
        fig_donut.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_donut, use_container_width=True)

# ==========================================
# TAB 2: DISPATCH LOGISTICS
# ==========================================
with tab_dispatch:
    st.markdown("##### Carrier Dispatches In-Transit")
    st.caption("Factory-invoiced shipments en-route to showroom yard.")

    transit_data = filtered[filtered["status"] == "In Transit (Dispatched)"]

    if not transit_data.empty:
        td1, td2 = st.columns([1, 1])
        with td1:
            fig_hist = px.histogram(
                transit_data, x="eta_days", color="model",
                nbins=8, template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Prism,
                labels={"eta_days": "Estimated Carrier Arrival (Days)"}
            )
            fig_hist.update_layout(margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Unit Count")
            st.plotly_chart(fig_hist, use_container_width=True)

        with td2:
            st.dataframe(
                transit_data[["vin", "model", "variant", "fuel_type", "color", "eta_days", "sales_consultant"]].sort_values(by="eta_days"),
                column_config={
                    "eta_days": st.column_config.ProgressColumn(
                        "Delivery ETA",
                        format="%d Days",
                        min_value=0,
                        max_value=10
                    )
                },
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No in-transit shipments matching selected filters.")

# ==========================================
# TAB 3: STOCK AGING ANALYSIS
# ==========================================
with tab_aging:
    st.markdown("##### Dealership Yard Age & Carrying Cost Analysis")
    st.caption("Dealer floor-plan interest applies on vehicles held in yard stock beyond 45 days.")

    yard_cars = filtered[filtered["status"] == "In Stock (Yard)"]

    if not yard_cars.empty:
        ag1, ag2 = st.columns([3, 2])
        with ag1:
            fig_box = px.box(
                yard_cars, x="model", y="days_in_yard",
                color_discrete_sequence=["#00287A"],
                template="plotly_white"
            )
            fig_box.add_hline(y=45, line_dash="dash", line_color="#DC2626", annotation_text="45-Day Benchmark")
            fig_box.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="", yaxis_title="Days in Yard")
            st.plotly_chart(fig_box, use_container_width=True)

        with ag2:
            st.markdown("##### High-Risk Units (>45 Days)")
            critical_cars = yard_cars[yard_cars["days_in_yard"] > 45][["vin", "model", "variant", "days_in_yard", "sales_consultant"]]
            if not critical_cars.empty:
                st.dataframe(critical_cars.sort_values(by="days_in_yard", ascending=False), use_container_width=True, hide_index=True)
            else:
                st.success("All inventory is currently within the safe 45-day cycle.")
    else:
        st.info("No vehicles currently in yard stock.")

# ==========================================
# TAB 4: SERVICE WORKSHOP
# ==========================================
with tab_service:
    st.markdown("##### Workshop Load & Pre-Delivery Inspection")
    service_units = filtered[filtered["service_stage"] != "None"]

    if not service_units.empty:
        ws1, ws2 = st.columns([1, 2])
        with ws1:
            st.metric("Workplace Active Bay Load", f"{len(service_units)} Units")
            fig_pie_srv = px.pie(
                service_units, names="service_stage", hole=0.5,
                color_discrete_sequence=["#00287A", "#3B82F6", "#93C5FD", "#F59E0B"]
            )
            fig_pie_srv.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie_srv, use_container_width=True)

        with ws2:
            st.dataframe(
                service_units[["vin", "model", "variant", "service_stage", "days_in_yard", "sales_consultant"]],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No active service or PDI tickets under current filter selection.")

# ==========================================
# TAB 5: INLINE TABLE EDITOR (EXCEL-STYLE)
# ==========================================
with tab_table_edit:
    st.markdown("##### Interactive Inventory Data Editor")
    st.caption("Double-click any cell below to update statuses, service stages, customer names, or days in yard. Click the save button to persist changes to SQLite.")

    editable_cols = ["vin", "model", "variant", "status", "days_in_yard", "eta_days", "service_stage", "customer_name", "sales_consultant", "notes"]
    
    # Configure editable grid
    edited_data = st.data_editor(
        filtered[editable_cols],
        column_config={
            "vin": st.column_config.TextColumn("VIN", disabled=True),
            "model": st.column_config.TextColumn("Model", disabled=True),
            "variant": st.column_config.TextColumn("Variant", disabled=True),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["In Stock (Yard)", "In Transit (Dispatched)", "Allocated / Booked", "Under PDI / Service", "Delivered"],
                required=True
            ),
            "days_in_yard": st.column_config.NumberColumn("Days in Yard", min_value=0, max_value=365, step=1),
            "eta_days": st.column_config.NumberColumn("Carrier ETA", min_value=0, max_value=30, step=1),
            "service_stage": st.column_config.SelectboxColumn(
                "Service Stage",
                options=["None", "Pre-Delivery Inspection (PDI)", "1st Free Service", "Periodic Maintenance", "Bodyshop / Repair"],
                required=True
            ),
            "customer_name": st.column_config.TextColumn("Customer"),
            "sales_consultant": st.column_config.TextColumn("Consultant"),
            "notes": st.column_config.TextColumn("Remarks")
        },
        use_container_width=True,
        hide_index=True,
        key="inventory_editor"
    )

    if st.button("Save Table Changes to Database", type="primary"):
        batch_update_inventory(edited_data)
        st.success("Database updated successfully.")
        st.rerun()

# ==========================================
# TAB 6: RECORD FORM EDITOR (DETAILED)
# ==========================================
with tab_form_edit:
    st.markdown("##### Individual Vehicle Record Maintenance")
    st.caption("Modify specific vehicle records with complete validation.")

    vins_list = df["vin"].tolist()
    target_vin = st.selectbox("Select VIN", vins_list)
    rec = df[df["vin"] == target_vin].iloc[0]

    with st.form("single_edit_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("Model & Variant", value=f"{rec['model']} {rec['variant']}", disabled=True)
            new_status = st.selectbox(
                "Lifecycle Status",
                ["In Stock (Yard)", "In Transit (Dispatched)", "Allocated / Booked", "Under PDI / Service", "Delivered"],
                index=["In Stock (Yard)", "In Transit (Dispatched)", "Allocated / Booked", "Under PDI / Service", "Delivered"].index(rec["status"])
            )
        with col2:
            new_yard = st.number_input("Days in Yard", min_value=0, max_value=365, value=int(rec["days_in_yard"]))
            new_eta = st.number_input("Logistics ETA (Days)", min_value=0, max_value=30, value=int(rec["eta_days"]))
            new_service = st.selectbox(
                "Service Bay Stage",
                ["None", "Pre-Delivery Inspection (PDI)", "1st Free Service", "Periodic Maintenance", "Bodyshop / Repair"],
                index=["None", "Pre-Delivery Inspection (PDI)", "1st Free Service", "Periodic Maintenance", "Bodyshop / Repair"].index(rec["service_stage"])
            )
        with col3:
            new_cust = st.text_input("Customer Allocation", value=rec["customer_name"])
            new_rep = st.text_input("Sales Consultant", value=rec["sales_consultant"])
            new_notes = st.text_area("Operational Remarks", value=rec["notes"])

        save_single = st.form_submit_button("Update Vehicle Record", type="primary")
        if save_single:
            update_single_vehicle(target_vin, new_status, new_yard, new_eta, new_service, new_cust, new_rep, new_notes)
            st.success(f"Record for {target_vin} committed to database.")
            st.rerun()

    st.markdown("---")
    with st.expander("Record Deletion"):
        st.caption("Permanently remove this vehicle from the database.")
        if st.button("Delete Record", type="secondary"):
            delete_vehicle(target_vin)
            st.warning(f"Vehicle {target_vin} removed from system.")
            st.rerun()

# ==========================================
# TAB 7: INWARD FACTORY UNIT
# ==========================================
with tab_new_inward:
    st.markdown("##### Inward Plant Invoiced Vehicle")
    st.caption("Register a new dispatch originating from the Hyundai manufacturing plant.")

    with st.form("inward_unit_form"):
        i1, i2, i3 = st.columns(3)
        with i1:
            in_vin = st.text_input("Chassis Number (VIN)", value=f"MALC{pd.Timestamp.now().strftime('%M%S')}700")
            in_model = st.selectbox("Vehicle Model", ["Creta", "Venue", "Exter", "Verna", "Alcazar", "i20", "Ioniq 5", "Tucson"])
            in_variant = st.text_input("Variant", value="SX(O)")
        with i2:
            in_fuel = st.selectbox("Powertrain", ["Petrol", "Diesel", "EV", "CNG"])
            in_trans = st.selectbox("Transmission", ["Manual", "Automatic"])
            in_color = st.selectbox("Exterior Color", ["Atlas White", "Abyss Black", "Titan Grey", "Ranger Khaki", "Fiery Red"])
        with i3:
            in_price = st.number_input("Ex-Showroom Price (Lakhs)", min_value=5.0, max_value=60.0, value=15.5)
            in_eta = st.slider("Logistics ETA (Days)", min_value=1, max_value=14, value=4)
            in_rep = st.selectbox("Allocated Consultant", ["Amit Sharma", "Priya Nair", "Rahul Verma", "Sneha Patel", "Vikram Das"])
            in_remarks = st.text_input("Intake Notes", value="Factory Invoice Logged")

        submit_inward = st.form_submit_button("Register Vehicle", type="primary")
        if submit_inward:
            insert_vehicle(in_vin, in_model, in_variant, in_fuel, in_trans, in_color, "In Transit (Dispatched)", in_price, in_eta, in_rep, in_remarks)
            st.success(f"VIN {in_vin} registered into system as In Transit.")
            st.rerun()

# --- FOOTER & EXCEL EXPORT ---
st.markdown("---")
f1, f2 = st.columns([3, 1])
with f1:
    st.caption("Hyundai Motor India Dealer Operations System • Relational Engine: SQLite3")
with f2:
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        filtered.to_excel(writer, index=False, sheet_name="DMS_Export")
    st.download_button(
        label="Download Filtered Data (Excel)",
        data=excel_buf.getvalue(),
        file_name="Hyundai_DMS_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )