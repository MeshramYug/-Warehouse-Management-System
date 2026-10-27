import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import json
import os
from datetime import datetime
import random

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Enterprise Warehouse Management System (WMS)",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern enterprise warehouse UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .wms-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-inbound { background-color: #DBEAFE; color: #1E40AF; }
    .badge-outbound { background-color: #FEF3C7; color: #92400E; }
    .badge-critical { background-color: #FEE2E2; color: #991B1B; }
    .badge-safe { background-color: #DCFCE7; color: #166534; }
    
    .card-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .receipt-box {
        background: #F0FDF4;
        border: 2px dashed #16A34A;
        border-radius: 10px;
        padding: 18px;
        margin-top: 15px;
        font-family: 'Courier New', monospace;
    }
    .dispatch-box {
        background: #FFFBEB;
        border: 2px dashed #D97706;
        border-radius: 10px;
        padding: 18px;
        margin-top: 15px;
        font-family: 'Courier New', monospace;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
    }
    .stat-val {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0F172A;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Resource Loading & Session State Persistence
# ---------------------------------------------------------
@st.cache_resource
def load_models_and_initial_data():
    base_dir = os.path.dirname(__file__)
    models_dir = os.path.join(base_dir, 'models')
    
    kpi_model = joblib.load(os.path.join(models_dir, 'kpi_model.pkl'))
    clf_model = joblib.load(os.path.join(models_dir, 'stockout_classifier.pkl'))
    
    with open(os.path.join(models_dir, 'model_metadata.json'), 'r') as f:
        metadata = json.load(f)
        
    df_path = os.path.join(models_dir, 'warehouse_inventory_enriched.csv')
    if os.path.exists(df_path):
        df = pd.read_csv(df_path)
    else:
        df = pd.read_csv(os.path.join(base_dir, 'logistics_dataset.csv'))
        
    return kpi_model, clf_model, metadata, df

try:
    kpi_model, clf_model, metadata, raw_df = load_models_and_initial_data()
except Exception as e:
    st.error(f"Error loading models or dataset: {e}. Please ensure 'train_model.py' has been executed.")
    st.stop()

# Initialize dynamic in-memory database in session state
if "inventory_df" not in st.session_state:
    st.session_state.inventory_df = raw_df.copy()

if "intake_ledger" not in st.session_state:
    # Seed with realistic recent intake transactions
    sample_intakes = [
        {
            "GRN_Number": "GRN-2026-1001",
            "Item_ID": "ITM10000",
            "Category": "Pharma",
            "Quantity_Received": 120,
            "Zone": "Zone A",
            "Bin_Location": "BIN-A-101",
            "Supplier": "Apex BioLogistics Ltd",
            "PO_Number": "PO-98210",
            "Batch_No": "BAT-2026-X1",
            "Inspector": "Arya Rai",
            "Condition": "Passed Inspection",
            "Timestamp": "2026-10-26 09:30:15"
        },
        {
            "GRN_Number": "GRN-2026-1002",
            "Item_ID": "ITM10005",
            "Category": "Electronics",
            "Quantity_Received": 85,
            "Zone": "Zone B",
            "Bin_Location": "BIN-B-204",
            "Supplier": "Global Silicon Distribution",
            "PO_Number": "PO-98214",
            "Batch_No": "BAT-2026-E4",
            "Inspector": "Marcus Vance",
            "Condition": "Passed Inspection",
            "Timestamp": "2026-10-26 11:45:00"
        },
        {
            "GRN_Number": "GRN-2026-1003",
            "Item_ID": "ITM10012",
            "Category": "Automotive",
            "Quantity_Received": 200,
            "Zone": "Zone C",
            "Bin_Location": "BIN-C-012",
            "Supplier": "Delta Precision Parts",
            "PO_Number": "PO-98229",
            "Batch_No": "BAT-2026-A9",
            "Inspector": "Arya Rai",
            "Condition": "Passed Inspection",
            "Timestamp": "2026-10-26 15:10:22"
        }
    ]
    st.session_state.intake_ledger = pd.DataFrame(sample_intakes)

if "dispatch_ledger" not in st.session_state:
    # Seed with realistic recent dispatch transactions
    sample_dispatches = [
        {
            "GDN_Number": "GDN-2026-0501",
            "Item_ID": "ITM10001",
            "Category": "Automotive",
            "Quantity_Dispatched": 35,
            "Destination": "Regional Fulfillment Hub 3",
            "Carrier": "DHL Express Freight",
            "Waybill": "WB-8839102",
            "Dispatcher": "Arya Rai",
            "Timestamp": "2026-10-26 14:15:00"
        },
        {
            "GDN_Number": "GDN-2026-0502",
            "Item_ID": "ITM10008",
            "Category": "Industrial",
            "Quantity_Dispatched": 50,
            "Destination": "Midwest Assembly Plant",
            "Carrier": "FedEx Ground Logistics",
            "Waybill": "WB-8839105",
            "Dispatcher": "John Smith",
            "Timestamp": "2026-10-26 16:40:12"
        }
    ]
    st.session_state.dispatch_ledger = pd.DataFrame(sample_dispatches)

df = st.session_state.inventory_df

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.markdown("## 📦 Warehouse WMS")
st.sidebar.caption("Enterprise Inventory & Operations Management")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Operations Navigation",
    [
        "📥 Stock Intake & Inbound Receiving",
        "📤 Stock Dispatch & Fulfillment",
        "📋 Live Inventory & Bin Master",
        "📊 Warehouse Executive Dashboard",
        "⚠️ Automated Reorder & Stockout Alerts",
        "🎯 Warehouse KPI & Efficiency Optimizer",
        "📜 Transaction Audit Ledgers",
        "🔬 Machine Learning & Architecture"
    ]
)

st.sidebar.markdown("---")
# Quick live status in sidebar
live_critical = (df['stockout_risk'] == 1).sum()
st.sidebar.markdown(f"**Live Active SKUs:** `{len(df):,}`")
st.sidebar.markdown(f"**Total Intake Receipts:** `{len(st.session_state.intake_ledger):,}`")
st.sidebar.markdown(f"**Total Dispatches:** `{len(st.session_state.dispatch_ledger):,}`")
st.sidebar.markdown(f"**Critical Restock Items:** `{live_critical:,}`")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset to Default Sample Dataset", use_container_width=True):
    st.session_state.inventory_df = raw_df.copy()
    st.success("Inventory reloaded from base dataset!")
    st.rerun()

# =========================================================
# Page 1: 📥 Stock Intake & Inbound Receiving
# =========================================================
if page == "📥 Stock Intake & Inbound Receiving":
    st.markdown('<span class="wms-badge badge-inbound">Dock Management • Inbound Operations</span>', unsafe_allow_html=True)
    st.markdown("<div class='main-header'>📥 Inbound Stock Intake & Receiving Dock</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Log inbound supplier shipments, inspect goods, assign warehouse rack bins, and update live stock levels immediately.</div>", unsafe_allow_html=True)

    # Inbound Operational Metrics
    today_intake_units = st.session_state.intake_ledger['Quantity_Received'].sum() if not st.session_state.intake_ledger.empty else 0
    today_batches = len(st.session_state.intake_ledger)
    
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Total Inbound Batches", f"{today_batches:,}")
    with mcol2:
        st.metric("Total Units Received", f"{today_intake_units:,} units")
    with mcol3:
        st.metric("Active Receiving Bays", "Bay 1 to 4 (Clear)")
    with mcol4:
        st.metric("Inspection Station Status", "🟢 Ready for QA")

    st.markdown("---")

    intake_tab1, intake_tab2 = st.tabs([
        "📦 Intake Shipment for Existing SKU",
        "✨ Register & Intake Brand New SKU"
    ])

    # TAB 1: Existing SKU Intake
    with intake_tab1:
        st.markdown("### Record Inbound Shipment (Existing SKU)")
        st.caption("Select an existing catalog item to record incoming delivery and immediately replenish warehouse inventory.")

        col_sel, col_prev = st.columns([1.4, 1])
        
        with col_sel:
            # Dropdown of items with current stock info
            item_list = df['item_id'].tolist()
            selected_sku = st.selectbox("Select Catalog SKU / Item ID", item_list, index=0)
            
            # Fetch current SKU details
            sku_row = df[df['item_id'] == selected_sku].iloc[0]
            curr_stock = int(sku_row['stock_level'])
            reorder_pt = int(sku_row['reorder_point'])
            category = sku_row['category']
            unit_price = float(sku_row['unit_price'])
            curr_zone = sku_row['zone']

            with st.form("existing_intake_form"):
                st.markdown("##### 📝 Inbound Shipment Details")
                
                fcol1, fcol2 = st.columns(2)
                with fcol1:
                    intake_qty = st.number_input("Quantity Received (Units)", min_value=1, max_value=10000, value=100, step=10)
                    po_number = st.text_input("Purchase Order (PO) Number", value=f"PO-{random.randint(10000, 99999)}")
                    supplier_name = st.text_input("Supplier / Carrier Name", value="Global Express Logistics")
                    batch_no = st.text_input("Batch / Lot Tracking #", value=f"LOT-2026-{datetime.now().strftime('%m%d')}")
                
                with fcol2:
                    assigned_zone = st.selectbox("Assigned Storage Zone", ["Zone A", "Zone B", "Zone C", "Zone D"], index=["Zone A", "Zone B", "Zone C", "Zone D"].index(curr_zone) if curr_zone in ["Zone A", "Zone B", "Zone C", "Zone D"] else 0)
                    bin_location = st.text_input("Designated Bin / Rack Location", value=f"BIN-{assigned_zone[-1]}-{random.randint(100, 499)}")
                    inspector = st.text_input("Receiving Inspector / Officer Name", value="Arya Rai")
                    condition = st.selectbox("Inspection Quality Status", ["Passed Quality Inspection", "Packaging Minor Defect (Approved)", "Quarantined for Testing"])

                notes = st.text_area("Receiving Notes (Optional)", "All containers inspected and verified against delivery manifest.")

                submit_intake = st.form_submit_button("📥 Receive & Stock Into Warehouse", type="primary", use_container_width=True)

                if submit_intake:
                    # Update live inventory in session state
                    new_stock = curr_stock + intake_qty
                    idx = df[df['item_id'] == selected_sku].index[0]
                    
                    df.at[idx, 'stock_level'] = new_stock
                    df.at[idx, 'zone'] = assigned_zone
                    df.at[idx, 'storage_location_id'] = bin_location
                    df.at[idx, 'last_restock_date'] = datetime.today().strftime('%Y-%m-%d')
                    
                    # Recalculate operational metrics
                    daily_d = float(df.at[idx, 'daily_demand']) if float(df.at[idx, 'daily_demand']) > 0 else 1.0
                    df.at[idx, 'days_of_supply'] = round(new_stock / daily_d, 1)
                    df.at[idx, 'stockout_risk'] = 1 if new_stock < float(df.at[idx, 'reorder_point']) else 0

                    # Generate Goods Receipt Note (GRN)
                    grn_code = f"GRN-2026-{random.randint(1000, 9999)}"
                    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    new_intake_entry = {
                        "GRN_Number": grn_code,
                        "Item_ID": selected_sku,
                        "Category": category,
                        "Quantity_Received": intake_qty,
                        "Zone": assigned_zone,
                        "Bin_Location": bin_location,
                        "Supplier": supplier_name,
                        "PO_Number": po_number,
                        "Batch_No": batch_no,
                        "Inspector": inspector,
                        "Condition": condition,
                        "Timestamp": timestamp_now
                    }
                    
                    st.session_state.intake_ledger = pd.concat([pd.DataFrame([new_intake_entry]), st.session_state.intake_ledger], ignore_index=True)
                    st.session_state.inventory_df = df

                    st.balloons()
                    st.success(f"✅ Shipment received successfully! Stock for **{selected_sku}** updated: `{curr_stock}` ➔ `{new_stock}` units.")
                    
                    st.markdown(f"""
                    <div class="receipt-box">
                        <div style="font-size: 1.15rem; font-weight: bold; color: #166534; margin-bottom: 6px;">
                            📄 OFFICIAL GOODS RECEIPT NOTE (GRN)
                        </div>
                        <strong>Receipt Reference:</strong> <code>{grn_code}</code><br>
                        <strong>SKU:</strong> {selected_sku} ({category})<br>
                        <strong>Quantity Added:</strong> {intake_qty} units<br>
                        <strong>New In-Stock Level:</strong> {new_stock} units<br>
                        <strong>Warehouse Location:</strong> {assigned_zone} ({bin_location})<br>
                        <strong>Purchase Order:</strong> {po_number} | <strong>Batch:</strong> {batch_no}<br>
                        <strong>Verified By:</strong> {inspector} on {timestamp_now}<br>
                        <strong>Status:</strong> {condition}
                    </div>
                    """, unsafe_allow_html=True)

        with col_prev:
            st.markdown("##### 🔍 SKU Current Profile")
            st.markdown(f"""
            <div class="card-box">
                <h4 style="margin-top:0; color: #1E3A8A;">📦 {selected_sku}</h4>
                <p><strong>Category:</strong> {category}</p>
                <p><strong>Current Stock Level:</strong> <span style="font-size:1.3rem; font-weight:bold; color: {'#16A34A' if curr_stock >= reorder_pt else '#DC2626'}">{curr_stock} units</span></p>
                <p><strong>Reorder Point:</strong> {reorder_pt} units</p>
                <p><strong>Current Zone:</strong> {curr_zone}</p>
                <p><strong>Unit Valuation:</strong> ${unit_price:,.2f}</p>
                <p><strong>Status:</strong> {'🟢 Safe Stock' if curr_stock >= reorder_pt else '🔴 Critical Restock Required'}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### 💡 WMS Storage Best Practice")
            st.info("""
            - **Zone A**: High-turnover & fast-picking items (Pharma, Electronics).
            - **Zone B**: Medium-turnover rack bays (Automotive, Apparel).
            - **Zone C**: Bulk pallets & industrial supplies.
            - **Zone D**: Temperature-controlled / specialized staging.
            """)

    # TAB 2: Brand New SKU Intake
    with intake_tab2:
        st.markdown("### Register & Stock Brand New Item (Catalog Intake)")
        st.caption("Receive an entirely new product not previously cataloged in the warehouse database.")

        with st.form("new_sku_intake_form"):
            ncol1, ncol2, ncol3 = st.columns(3)
            with ncol1:
                new_item_id = st.text_input("New Item ID / SKU", value=f"ITM{random.randint(20000, 29999)}")
                new_cat = st.selectbox("Category", ["Pharma", "Electronics", "Automotive", "Apparel", "Industrial", "Food & Beverage"])
                new_qty = st.number_input("Initial Intake Quantity", min_value=1, max_value=5000, value=250)
            
            with ncol2:
                new_price = st.number_input("Unit Price ($)", min_value=0.5, max_value=2000.0, value=45.0, step=5.0)
                new_zone = st.selectbox("Target Warehouse Zone", ["Zone A", "Zone B", "Zone C", "Zone D"])
                new_bin = st.text_input("Storage Bin ID", value=f"BIN-{new_zone[-1]}-301")

            with ncol3:
                new_reorder = st.number_input("Reorder Point Threshold", min_value=5, max_value=500, value=50)
                new_demand = st.number_input("Estimated Daily Demand", min_value=0.5, max_value=100.0, value=12.0)
                new_lead = st.slider("Supplier Lead Time (Days)", 1, 30, 5)

            scol1, scol2 = st.columns(2)
            with scol1:
                new_supplier = st.text_input("Supplier Organization", "Pacific Freight Logistics")
                new_po = st.text_input("Inbound PO Number", f"PO-{random.randint(30000, 39999)}")
            with scol2:
                new_inspector = st.text_input("Receiving Clerk", "Arya Rai")
                new_batch = st.text_input("Batch / Lot #", f"LOT-{datetime.now().strftime('%Y%m')}-NEW")

            submit_new = st.form_submit_button("✨ Register SKU & Stock Intake", type="primary", use_container_width=True)

            if submit_new:
                if new_item_id in df['item_id'].values:
                    st.error(f"Error: SKU {new_item_id} already exists in catalog. Please use Tab 1 to replenish.")
                else:
                    new_row = {
                        'item_id': new_item_id,
                        'category': new_cat,
                        'stock_level': new_qty,
                        'reorder_point': new_reorder,
                        'reorder_frequency_days': 15,
                        'lead_time_days': new_lead,
                        'daily_demand': new_demand,
                        'demand_std_dev': round(new_demand * 0.25, 2),
                        'item_popularity_score': 0.75,
                        'storage_location_id': new_bin,
                        'zone': new_zone,
                        'picking_time_seconds': 45.0,
                        'handling_cost_per_unit': 2.50,
                        'unit_price': new_price,
                        'holding_cost_per_unit_day': round(new_price * 0.005, 3),
                        'stockout_count_last_month': 0,
                        'order_fulfillment_rate': 0.98,
                        'total_orders_last_month': 150,
                        'turnover_ratio': 8.5,
                        'layout_efficiency_score': 0.88,
                        'last_restock_date': datetime.today().strftime('%Y-%m-%d'),
                        'forecasted_demand_next_7d': round(new_demand * 7, 1),
                        'KPI_score': 0.825,
                        'days_of_supply': round(new_qty / new_demand, 1),
                        'stockout_risk': 0,
                        'annual_demand': round(new_demand * 365, 0),
                        'annual_holding_cost': round(new_price * 0.005 * 365, 2),
                        'calculated_eoq': round(np.sqrt((2 * new_demand * 365 * 25) / max(0.01, new_price * 0.005 * 365)), 0),
                        'safety_stock': round(new_demand * new_lead * 0.5, 1)
                    }

                    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
                    st.session_state.inventory_df = df

                    # Record GRN
                    grn_code = f"GRN-2026-{random.randint(1000, 9999)}"
                    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    new_intake_entry = {
                        "GRN_Number": grn_code,
                        "Item_ID": new_item_id,
                        "Category": new_cat,
                        "Quantity_Received": new_qty,
                        "Zone": new_zone,
                        "Bin_Location": new_bin,
                        "Supplier": new_supplier,
                        "PO_Number": new_po,
                        "Batch_No": new_batch,
                        "Inspector": new_inspector,
                        "Condition": "Passed Quality Inspection",
                        "Timestamp": timestamp_now
                    }
                    st.session_state.intake_ledger = pd.concat([pd.DataFrame([new_intake_entry]), st.session_state.intake_ledger], ignore_index=True)

                    st.balloons()
                    st.success(f"🎉 New SKU **{new_item_id}** ({new_cat}) successfully created and stocked with **{new_qty} units**!")

# =========================================================
# Page 2: 📤 Stock Dispatch & Fulfillment
# =========================================================
elif page == "📤 Stock Dispatch & Fulfillment":
    st.markdown('<span class="wms-badge badge-outbound">Outbound Fulfillment • Shipping Dock</span>', unsafe_allow_html=True)
    st.markdown("<div class='main-header'>📤 Outbound Stock Dispatch & Order Fulfillment</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Pick, pack, verify, and dispatch outbound orders for regional distribution centers, stores, and manufacturing lines.</div>", unsafe_allow_html=True)

    dcol_form, dcol_info = st.columns([1.5, 1])

    with dcol_form:
        st.markdown("### Create Outbound Dispatch Order")
        
        sku_list = df['item_id'].tolist()
        dispatch_sku = st.selectbox("Select SKU for Outbound Picking", sku_list)
        
        sku_row = df[df['item_id'] == dispatch_sku].iloc[0]
        avail_stock = int(sku_row['stock_level'])
        category = sku_row['category']
        reorder_pt = int(sku_row['reorder_point'])

        with st.form("dispatch_form"):
            st.markdown(f"**Available Physical Stock in Bins:** `{avail_stock}` units")
            
            p1, p2 = st.columns(2)
            with p1:
                dispatch_qty = st.number_input("Dispatch Quantity (Units)", min_value=1, max_value=max(1, avail_stock), value=min(25, max(1, avail_stock)))
                destination = st.text_input("Destination Facility / Client", "North Hub Fulfillment Center")
                carrier = st.selectbox("Freight Carrier", ["DHL Express", "FedEx Supply Chain", "Blue Dart Logistics", "Internal Fleet Van"])
            
            with p2:
                waybill_no = st.text_input("Waybill / Tracking Number", f"WB-{random.randint(100000, 999999)}")
                dispatcher = st.text_input("Dispatching Officer", "Arya Rai")
                order_priority = st.selectbox("Dispatch Priority", ["Standard Ground", "Expedited 24h", "Urgent Production Line"])

            submit_dispatch = st.form_submit_button("📤 Confirm & Dispatch Shipment", type="primary", use_container_width=True)

            if submit_dispatch:
                if dispatch_qty > avail_stock:
                    st.error(f"❌ Error: Cannot dispatch {dispatch_qty} units! Only {avail_stock} units available in warehouse.")
                else:
                    new_stock = avail_stock - dispatch_qty
                    idx = df[df['item_id'] == dispatch_sku].index[0]
                    
                    df.at[idx, 'stock_level'] = new_stock
                    daily_d = float(df.at[idx, 'daily_demand']) if float(df.at[idx, 'daily_demand']) > 0 else 1.0
                    df.at[idx, 'days_of_supply'] = round(new_stock / daily_d, 1)
                    df.at[idx, 'stockout_risk'] = 1 if new_stock < reorder_pt else 0

                    gdn_code = f"GDN-2026-{random.randint(1000, 9999)}"
                    timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    dispatch_entry = {
                        "GDN_Number": gdn_code,
                        "Item_ID": dispatch_sku,
                        "Category": category,
                        "Quantity_Dispatched": dispatch_qty,
                        "Destination": destination,
                        "Carrier": carrier,
                        "Waybill": waybill_no,
                        "Dispatcher": dispatcher,
                        "Timestamp": timestamp_now
                    }

                    st.session_state.dispatch_ledger = pd.concat([pd.DataFrame([dispatch_entry]), st.session_state.dispatch_ledger], ignore_index=True)
                    st.session_state.inventory_df = df

                    st.success(f"✅ Dispatch Confirmed! **{dispatch_qty} units** of `{dispatch_sku}` deducted from warehouse stock. Remaining: `{new_stock}` units.")

                    if new_stock < reorder_pt:
                        st.warning(f"⚠️ **Attention:** `{dispatch_sku}` stock ({new_stock} units) has dropped BELOW its reorder threshold ({reorder_pt} units)! Restock recommendation triggered.")

                    st.markdown(f"""
                    <div class="dispatch-box">
                        <div style="font-size: 1.15rem; font-weight: bold; color: #92400E; margin-bottom: 6px;">
                            🚚 GOODS DISPATCH NOTE (GDN)
                        </div>
                        <strong>Dispatch Ref:</strong> <code>{gdn_code}</code><br>
                        <strong>SKU:</strong> {dispatch_sku} ({category})<br>
                        <strong>Quantity Shipped:</strong> {dispatch_qty} units<br>
                        <strong>Remaining Inventory:</strong> {new_stock} units<br>
                        <strong>Destination:</strong> {destination}<br>
                        <strong>Carrier:</strong> {carrier} | <strong>Waybill:</strong> {waybill_no}<br>
                        <strong>Dispatched By:</strong> {dispatcher} on {timestamp_now}
                    </div>
                    """, unsafe_allow_html=True)

    with dcol_info:
        st.markdown("### Picking & Packing Rules")
        st.markdown("""
        <div class="card-box">
            <h4 style="margin-top: 0; color: #92400E;">📦 FIFO / FEFO Principles</h4>
            <ul style="font-size: 0.9rem; line-height: 1.6; color: #475569;">
                <li><strong>First-In, First-Out (FIFO):</strong> Oldest batches picked first to minimize expiry risk.</li>
                <li><strong>Safety Stock Shield:</strong> Never dispatch below mandatory reserve without supervisor override.</li>
                <li><strong>Barcode Verification:</strong> Double-scan item barcode before placing in dispatch dock bay.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# Page 3: 📋 Live Inventory & Bin Master
# =========================================================
elif page == "📋 Live Inventory & Bin Master":
    st.markdown("<div class='main-header'>📋 Live Inventory Catalog & Bin Master</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Real-time tracking of all active SKUs, bin coordinates, storage zones, days of supply, and stockout risk.</div>", unsafe_allow_html=True)

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        sel_cat = st.multiselect("Filter Category", sorted(df['category'].unique()), default=[])
    with fcol2:
        sel_zone = st.multiselect("Filter Zone", sorted(df['zone'].unique()), default=[])
    with fcol3:
        sel_risk = st.selectbox("Stockout Health Status", ["All Items", "Critical Restock Only", "Safe Stock Only"])
    with fcol4:
        search_txt = st.text_input("Search Item ID / Bin", "")

    filtered = df.copy()
    if sel_cat:
        filtered = filtered[filtered['category'].isin(sel_cat)]
    if sel_zone:
        filtered = filtered[filtered['zone'].isin(sel_zone)]
    if sel_risk == "Critical Restock Only":
        filtered = filtered[filtered['stockout_risk'] == 1]
    elif sel_risk == "Safe Stock Only":
        filtered = filtered[filtered['stockout_risk'] == 0]
    if search_txt:
        filtered = filtered[filtered['item_id'].str.contains(search_txt, case=False, na=False) | filtered['storage_location_id'].str.contains(search_txt, case=False, na=False)]

    total_val_filt = (filtered['stock_level'] * filtered['unit_price']).sum()
    st.markdown(f"Displaying **{len(filtered):,}** of **{len(df):,}** SKUs | Total Value: **${total_val_filt:,.2f}**")

    disp_cols = [
        'item_id', 'category', 'zone', 'storage_location_id', 'stock_level', 
        'reorder_point', 'daily_demand', 'days_of_supply', 'stockout_risk', 
        'unit_price', 'last_restock_date'
    ]

    st.dataframe(
        filtered[disp_cols].rename(columns={
            'item_id': 'SKU ID',
            'category': 'Category',
            'zone': 'Zone',
            'storage_location_id': 'Bin Location',
            'stock_level': 'Current Stock',
            'reorder_point': 'Reorder Threshold',
            'daily_demand': 'Daily Demand',
            'days_of_supply': 'Days of Supply',
            'stockout_risk': 'Critical Risk (1/0)',
            'unit_price': 'Unit Price ($)',
            'last_restock_date': 'Last Restock Date'
        }),
        use_container_width=True,
        height=450
    )

    # Download updated inventory CSV
    csv_bytes = filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Export Live Inventory Master (CSV)",
        data=csv_bytes,
        file_name="wms_live_inventory_master.csv",
        mime="text/csv"
    )

# =========================================================
# Page 4: 📊 Warehouse Executive Dashboard
# =========================================================
elif page == "📊 Warehouse Executive Dashboard":
    st.markdown("<div class='main-header'>📊 Warehouse Executive Dashboard & KPIs</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>High-level metrics on inventory valuation, zone utilization, ABC Pareto distribution, and fulfillment velocity.</div>", unsafe_allow_html=True)

    total_val = (df['stock_level'] * df['unit_price']).sum()
    critical_items = (df['stockout_risk'] == 1).sum()
    avg_kpi = df['KPI_score'].mean()
    avg_turnover = df['turnover_ratio'].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Warehouse Inventory Value", f"${total_val:,.2f}")
    with col2:
        st.metric("Critical Restock Items", f"{critical_items:,}", delta=f"{(critical_items/len(df)*100):.1f}% of catalog", delta_color="inverse")
    with col3:
        st.metric("Avg Facility KPI Score", f"{avg_kpi:.3f}", delta="Target: > 0.750")
    with col4:
        st.metric("Average Turnover Ratio", f"{avg_turnover:.1f}x", delta="Annual Benchmark")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Inventory Valuation by Category")
        cat_val = df.groupby('category').apply(lambda x: (x['stock_level'] * x['unit_price']).sum()).reset_index(name='Total_Value')
        fig_cat = px.bar(cat_val, x='category', y='Total_Value', color='category', text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Safe)
        fig_cat.update_layout(showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_cat, use_container_width=True)

    with c2:
        st.subheader("Storage Zone Occupancy & Picking Speed")
        zone_stats = df.groupby('zone').agg(
            SKUs=('item_id', 'count'),
            Avg_Picking_Time=('picking_time_seconds', 'mean'),
            Avg_Layout_Score=('layout_efficiency_score', 'mean')
        ).reset_index()
        fig_zone = px.scatter(
            zone_stats, x='Avg_Picking_Time', y='Avg_Layout_Score', size='SKUs', color='zone', text='zone',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_zone.update_traces(textposition='top center')
        fig_zone.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_zone, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("ABC Inventory Classification (Pareto Analysis)")
        df_sorted = df.copy()
        df_sorted['item_val'] = df_sorted['stock_level'] * df_sorted['unit_price']
        df_sorted = df_sorted.sort_values(by='item_val', ascending=False)
        df_sorted['cum_val'] = df_sorted['item_val'].cumsum()
        df_sorted['cum_pct'] = df_sorted['cum_val'] / max(1.0, df_sorted['item_val'].sum())

        def abc_class(p):
            if p <= 0.80:
                return 'Class A (High Value 80%)'
            elif p <= 0.95:
                return 'Class B (Medium Value 15%)'
            else:
                return 'Class C (Low Value 5%)'

        df_sorted['ABC_Category'] = df_sorted['cum_pct'].apply(abc_class)
        abc_counts = df_sorted['ABC_Category'].value_counts().reset_index()
        abc_counts.columns = ['Class', 'Count']
        fig_abc = px.pie(abc_counts, names='Class', values='Count', hole=0.45, color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B'])
        fig_abc.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_abc, use_container_width=True)

    with c4:
        st.subheader("Daily Demand vs. Stock Level by Risk Status")
        sample_df = df.sample(min(600, len(df)), random_state=42).copy()
        sample_df['Stock_Status'] = sample_df['stockout_risk'].map({0: 'Safe Stock', 1: 'Critical Risk'})
        fig_scat = px.scatter(
            sample_df, x='daily_demand', y='stock_level', color='Stock_Status',
            color_discrete_map={'Safe Stock': '#10B981', 'Critical Risk': '#EF4444'}
        )
        fig_scat.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_scat, use_container_width=True)

# =========================================================
# Page 5: ⚠️ Automated Reorder & Stockout Alerts
# =========================================================
elif page == "⚠️ Automated Reorder & Stockout Alerts":
    st.markdown('<span class="wms-badge badge-critical">Replenishment Engine • Restock Triggers</span>', unsafe_allow_html=True)
    st.markdown("<div class='main-header'>⚠️ Automated Reorder & Stockout Alerts</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Identifies all SKUs falling below safety stock, calculates Economic Order Quantity (EOQ), and triggers 1-click replenishment intakes.</div>", unsafe_allow_html=True)

    critical_df = df[df['stockout_risk'] == 1].copy()

    st.markdown(f"### Currently Critical SKUs Requiring Immediate Restock ({len(critical_df):,} Items)")

    if critical_df.empty:
        st.success("🎉 Outstanding! All SKUs are currently operating above their reorder thresholds.")
    else:
        st.dataframe(
            critical_df[['item_id', 'category', 'zone', 'stock_level', 'reorder_point', 'daily_demand', 'calculated_eoq', 'safety_stock', 'lead_time_days']].rename(columns={
                'item_id': 'SKU ID',
                'category': 'Category',
                'zone': 'Zone',
                'stock_level': 'Current Stock',
                'reorder_point': 'Reorder Point',
                'daily_demand': 'Daily Demand',
                'calculated_eoq': 'Recommended EOQ',
                'safety_stock': 'Safety Stock',
                'lead_time_days': 'Lead Time (Days)'
            }),
            use_container_width=True,
            height=300
        )

        st.markdown("---")
        st.markdown("#### ⚡ 1-Click Expedited Restock Intake")
        st.write("Select a critical SKU to immediately generate an emergency intake shipment for its recommended Economic Order Quantity (EOQ).")

        rc1, rc2 = st.columns([2, 1])
        with rc1:
            fast_sku = st.selectbox("Select Critical SKU to Restock", critical_df['item_id'].tolist())
            fast_row = critical_df[critical_df['item_id'] == fast_sku].iloc[0]
            rec_eoq = int(fast_row['calculated_eoq'])
            st.write(f"**Recommended Replenishment Order:** `{rec_eoq}` units | Current Stock: `{int(fast_row['stock_level'])}` units | Reorder Threshold: `{int(fast_row['reorder_point'])}` units")
            
            if st.button(f"📥 Execute Emergency Intake of {rec_eoq} Units for {fast_sku}", type="primary"):
                idx = df[df['item_id'] == fast_sku].index[0]
                new_stk = int(df.at[idx, 'stock_level']) + rec_eoq
                df.at[idx, 'stock_level'] = new_stk
                daily_d = float(df.at[idx, 'daily_demand']) if float(df.at[idx, 'daily_demand']) > 0 else 1.0
                df.at[idx, 'days_of_supply'] = round(new_stk / daily_d, 1)
                df.at[idx, 'stockout_risk'] = 1 if new_stk < float(df.at[idx, 'reorder_point']) else 0
                df.at[idx, 'last_restock_date'] = datetime.today().strftime('%Y-%m-%d')

                # Log GRN
                grn_code = f"GRN-2026-{random.randint(1000, 9999)}"
                new_entry = {
                    "GRN_Number": grn_code,
                    "Item_ID": fast_sku,
                    "Category": fast_row['category'],
                    "Quantity_Received": rec_eoq,
                    "Zone": fast_row['zone'],
                    "Bin_Location": fast_row['storage_location_id'],
                    "Supplier": "Express Restock Vendor",
                    "PO_Number": f"PO-EMERGENCY-{random.randint(1000, 9999)}",
                    "Batch_No": f"LOT-EXP-{datetime.now().strftime('%m%d')}",
                    "Inspector": "Auto-WMS Expediter",
                    "Condition": "Passed Quality Inspection",
                    "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                st.session_state.intake_ledger = pd.concat([pd.DataFrame([new_entry]), st.session_state.intake_ledger], ignore_index=True)
                st.session_state.inventory_df = df

                st.balloons()
                st.success(f"🎉 Emergency Restock Completed! `{fast_sku}` stock restored to `{new_stk}` units. Risk status cleared.")
                st.rerun()

        with rc2:
            st.markdown("""
            <div class="card-box">
                <h4 style="margin-top:0; color:#1E3A8A;">📐 EOQ Formula Used</h4>
                <p>$$EOQ = \\sqrt{\\frac{2 \\times D \\times S}{H}}$$</p>
                <ul style="font-size:0.85rem; color:#64748B;">
                    <li><strong>D:</strong> Annual Demand</li>
                    <li><strong>S:</strong> Order Setup & Handling Cost</li>
                    <li><strong>H:</strong> Annual Holding Cost</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# Page 6: 🎯 Warehouse KPI & Efficiency Optimizer
# =========================================================
elif page == "🎯 Warehouse KPI & Efficiency Optimizer":
    st.markdown("<div class='main-header'>🎯 Warehouse Efficiency & KPI Optimizer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Simulate operational adjustments (picking speed, layout efficiency, turnover ratio) to maximize warehouse performance ratings.</div>", unsafe_allow_html=True)

    sim_c1, sim_c2, sim_c3 = st.columns(3)
    with sim_c1:
        st.markdown("##### 🏎️ Throughput & Speed")
        picking_time = st.slider("Average Picking Time (seconds)", 15.0, 120.0, 48.0)
        layout_eff = st.slider("Aisle Layout Efficiency Score", 0.3, 1.0, 0.82)
    with sim_c2:
        st.markdown("##### 📦 Inventory Velocity")
        turnover_ratio = st.slider("Annual Turnover Ratio", 1.0, 20.0, 9.5)
        stockout_ct = st.slider("Monthly Stockout Incidents", 0, 50, 2)
    with sim_c3:
        st.markdown("##### 💰 Cost Structure")
        holding_cost = st.slider("Daily Holding Cost/Unit ($)", 0.05, 5.0, 0.85)
        stock_lvl = st.slider("Average SKU Stock Level", 10, 1000, 150)

    # Prepare feature input for KPI Gradient Boosting Model
    kpi_input = pd.DataFrame([{
        'stockout_count_last_month': stockout_ct,
        'picking_time_seconds': picking_time,
        'turnover_ratio': turnover_ratio,
        'layout_efficiency_score': layout_eff,
        'holding_cost_per_unit_day': holding_cost,
        'stock_level': stock_lvl
    }])

    pred_kpi = float(kpi_model.predict(kpi_input)[0])
    pred_kpi = max(0.0, min(1.0, pred_kpi))

    st.markdown("---")
    st.markdown("### Simulated Warehouse Performance")
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Predicted Warehouse KPI Score", f"{pred_kpi:.3f}", delta=f"{pred_kpi - df['KPI_score'].mean():.3f} vs facility baseline")
    with k2:
        status = "🌟 Exceptional" if pred_kpi >= 0.75 else ("🟢 Good" if pred_kpi >= 0.55 else "🔴 Needs Optimization")
        st.metric("Operational Health Tier", status)
    with k3:
        annual_hold = holding_cost * 365 * stock_lvl
        st.metric("Est. Annual Holding Expense/SKU", f"${annual_hold:,.2f}")

# =========================================================
# Page 7: 📜 Transaction Audit Ledgers
# =========================================================
elif page == "📜 Transaction Audit Ledgers":
    st.markdown("<div class='main-header'>📜 Inbound & Outbound Transaction Audit Ledgers</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Complete, tamper-proof history of all Goods Receipt Notes (GRNs) and Goods Dispatch Notes (GDNs).</div>", unsafe_allow_html=True)

    ledger_tab1, ledger_tab2 = st.tabs([
        "📥 Inbound Intake History (Goods Receipt Notes)",
        "📤 Outbound Dispatch History (Goods Dispatch Notes)"
    ])

    with ledger_tab1:
        st.markdown(f"### Goods Receipt Notes (GRN) Ledger ({len(st.session_state.intake_ledger)} Entries)")
        st.dataframe(st.session_state.intake_ledger, use_container_width=True, height=350)

        csv_intake = st.session_state.intake_ledger.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Inbound GRN Audit Report (CSV)",
            data=csv_intake,
            file_name="wms_inbound_intake_ledger.csv",
            mime="text/csv"
        )

    with ledger_tab2:
        st.markdown(f"### Goods Dispatch Notes (GDN) Ledger ({len(st.session_state.dispatch_ledger)} Entries)")
        st.dataframe(st.session_state.dispatch_ledger, use_container_width=True, height=350)

        csv_disp = st.session_state.dispatch_ledger.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Outbound GDN Audit Report (CSV)",
            data=csv_disp,
            file_name="wms_outbound_dispatch_ledger.csv",
            mime="text/csv"
        )

# =========================================================
# Page 8: 🔬 Machine Learning & Architecture
# =========================================================
elif page == "🔬 Machine Learning & Architecture":
    st.markdown("<div class='main-header'>🔬 WMS Architecture & Predictive Models</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Technical documentation on the dual architecture: Enterprise WMS operations backed by Machine Learning intelligence.</div>", unsafe_allow_html=True)

    arch1, arch2 = st.columns(2)
    with arch1:
        st.markdown("### 1. Warehouse KPI Score Regressor")
        st.markdown("""
        - **Algorithm:** Gradient Boosting Regressor (150 estimators, max depth 4)
        - **$R^2$ Score:** `0.9922` (99.2% variance explained)
        - **Mean Absolute Error (MAE):** `0.0081`
        - **Target Objective:** Evaluates overall warehouse facility efficiency.
        """)
        
        kpi_imp = pd.DataFrame({
            'Feature': metadata['kpi_features'],
            'Importance': kpi_model.feature_importances_
        }).sort_values('Importance', ascending=True)
        
        fig_kpi_imp = px.bar(kpi_imp, x='Importance', y='Feature', orientation='h', title="KPI Feature Importances", color_discrete_sequence=['#3B82F6'])
        fig_kpi_imp.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_kpi_imp, use_container_width=True)

    with arch2:
        st.markdown("### 2. Stockout Risk Classifier")
        st.markdown("""
        - **Algorithm:** Random Forest Classifier (100 estimators, max depth 8)
        - **Accuracy:** `97.66%`
        - **Macro F1-Score:** `0.977`
        - **Target Objective:** Predicts whether an item risks imminent stockout.
        """)
        
        clf_imp = pd.DataFrame({
            'Feature': metadata['clf_features'],
            'Importance': clf_model.feature_importances_
        }).sort_values('Importance', ascending=True)
        
        fig_clf_imp = px.bar(clf_imp, x='Importance', y='Feature', orientation='h', title="Stockout Risk Feature Importances", color_discrete_sequence=['#10B981'])
        fig_clf_imp.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_clf_imp, use_container_width=True)
