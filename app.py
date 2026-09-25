import streamlit as st
import plotly.express as px
import pandas as pd
from data_loader import generate_dealership_data

st.set_page_config(page_title="Hyundai Dealership Analytics", page_icon="🚗", layout="wide")

df = generate_dealership_data()

# Sidebar Filters
st.sidebar.title("Dealership Controls")
selected_models = st.sidebar.multiselect(
    "Filter by Model", 
    options=df["Model"].unique(), 
    default=df["Model"].unique()
)
selected_status = st.sidebar.multiselect(
    "Filter by Vehicle Status", 
    options=df["Status"].unique(), 
    default=df["Status"].unique()
)

filtered_df = df[
    (df["Model"].isin(selected_models)) & 
    (df["Status"].isin(selected_status))
]

# Header & KPIs
st.title("🚗 Hyundai Dealership Operations & Inventory")
col1, col2, col3, col4 = st.columns(4)

total_units = len(filtered_df)
in_stock = len(filtered_df[filtered_df["Status"] == "In Stock"])
dispatched = len(filtered_df[filtered_df["Status"] == "In Transit (Dispatched)"])
service_queue = len(filtered_df[filtered_df["Service_Flag"] != "None"])

col1.metric("Total Filtered Fleet", f"{total_units} Units")
col2.metric("Available on Lot", f"{in_stock} Units")
col3.metric("Dispatched / Transit", f"{dispatched} Units")
col4.metric("Active Service Jobs", f"{service_queue} Cars")

st.divider()

# Charts
c1, c2 = st.columns(2)
with c1:
    st.subheader("Inventory by Model & Status")
    fig_bar = px.bar(filtered_df, x="Model", color="Status", barmode="stack", template="plotly_white")
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader("Holding Time (Yard Age)")
    fig_box = px.box(filtered_df[filtered_df["Status"] == "In Stock"], x="Model", y="Days_in_Yard", color="Model", template="plotly_white")
    st.plotly_chart(fig_box, use_container_width=True)

# Data Table
st.subheader("Live Vehicle Master Data")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)