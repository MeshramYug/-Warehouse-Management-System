import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import random
from datetime import datetime

from database import (
    init_db, seed_database, get_all_inventory, get_inventory_item,
    record_intake_shipment, record_dispatch_shipment, add_new_inventory_item,
    update_inventory_stock, delete_inventory_item, get_intake_records,
    get_dispatch_records, get_zones
)

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Warehouse Management System (WMS)",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize and seed database if not already done
init_db()
seed_database()

# Custom Styling CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
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
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Load Live Data from SQLite
# ---------------------------------------------------------
inventory_list = get_all_inventory()
inv_df = pd.DataFrame(inventory_list) if inventory_list else pd.DataFrame()

# Compute live KPIs
total_skus = len(inv_df)
total_units = int(inv_df['stock_level'].sum()) if not inv_df.empty else 0
total_val = float((inv_df['stock_level'] * inv_df['unit_price']).sum()) if not inv_df.empty else 0.0
critical_df = inv_df[inv_df['stock_level'] <= inv_df['reorder_point']] if not inv_df.empty else pd.DataFrame()
critical_count = len(critical_df)

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.markdown("## 📦 Warehouse WMS")
st.sidebar.caption("Enterprise Database Inventory Platform")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Operations Navigation",
    [
        "📥 Stock Intake & Inbound Receiving",
        "📤 Stock Dispatch & Fulfillment",
        "📋 Live Inventory & Master Catalog",
        "⚠️ Automated Reorder Alerts",
        "📊 Warehouse Executive Dashboard",
        "🏢 Storage Zones & Facility Layout",
        "📜 Transaction Audit Ledgers"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Database:** `SQLite (warehouse.db)`")
st.sidebar.markdown(f"**Active SKUs:** `{total_skus:,}`")
st.sidebar.markdown(f"**Total Physical Units:** `{total_units:,}`")
st.sidebar.markdown(f"**Inventory Valuation:** `${total_val:,.2f}`")
st.sidebar.markdown(f"**Items Below Reorder:** `{critical_count:,}`")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data from Database", use_container_width=True):
    st.rerun()

# =========================================================
# Page 1: 📥 Stock Intake & Inbound Receiving
# =========================================================
if page == "📥 Stock Intake & Inbound Receiving":
    st.markdown('<span class="wms-badge badge-inbound">Dock Management • Inbound Receiving</span>', unsafe_allow_html=True)
    st.markdown("<div class='main-header'>📥 Inbound Stock Intake & Receiving Dock</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Receive incoming supplier shipments, log physical inspections, allocate storage rack bins, and update database inventory in real time.</div>", unsafe_allow_html=True)

    intake_records = get_intake_records()
    total_received_units = sum(r['quantity'] for r in intake_records) if intake_records else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Intake Shipments", f"{len(intake_records):,}")
    with m2:
        st.metric("Total Inbound Units Logged", f"{total_received_units:,}")
    with m3:
        st.metric("Receiving Dock Status", "🟢 Bays 1-4 Active")
    with m4:
        st.metric("Database Sync", "⚡ SQLite Live")

    st.markdown("---")

    intake_tab1, intake_tab2 = st.tabs([
        "📦 Intake Shipment for Existing SKU",
        "✨ Register & Intake Brand New Product"
    ])

    # Tab 1: Existing SKU Intake
    with intake_tab1:
        st.markdown("### Record Inbound Delivery (Existing Catalog SKU)")
        st.caption("Select an existing catalog item to record received quantities and replenish warehouse stock.")

        if inv_df.empty:
            st.warning("No inventory items found in database.")
        else:
            col_sel, col_prev = st.columns([1.5, 1])

            with col_sel:
                sku_choices = {r['item_id']: f"{r['item_id']} - {r['item_name']} (In Stock: {r['stock_level']})" for r in inventory_list}
                selected_item_id = st.selectbox("Select Catalog SKU", options=list(sku_choices.keys()), format_func=lambda x: sku_choices[x])
                
                selected_item = get_inventory_item(selected_item_id)

                with st.form("intake_existing_form"):
                    f1, f2 = st.columns(2)
                    with f1:
                        intake_qty = st.number_input("Intake Quantity (Units)", min_value=1, max_value=10000, value=100, step=10)
                        po_num = st.text_input("Purchase Order (PO) Number", value=f"PO-{random.randint(10000, 99999)}")
                        supp = st.text_input("Supplier / Carrier Name", value=selected_item['supplier'])
                        batch_code = st.text_input("Batch / Lot #", value=f"BAT-2026-{datetime.now().strftime('%m%d')}")

                    with f2:
                        target_zone = st.selectbox("Assigned Storage Zone", ["Zone A", "Zone B", "Zone C", "Zone D"], index=["Zone A", "Zone B", "Zone C", "Zone D"].index(selected_item['zone']) if selected_item['zone'] in ["Zone A", "Zone B", "Zone C", "Zone D"] else 0)
                        bin_loc = st.text_input("Rack / Bin Location", value=selected_item['bin_location'])
                        inspector_name = st.text_input("Receiving Inspector / Officer", value="Arya Rai")
                        qc_status = st.selectbox("Quality Inspection Status", ["Passed Quality Check", "Packaging Defect - Verified", "Quarantined for QA Testing"])

                    notes = st.text_area("Intake Notes", "Shipment received in good condition and count verified against supplier manifest.")

                    submit_intake = st.form_submit_button("📥 Receive & Update Database Inventory", type="primary", use_container_width=True)

                    if submit_intake:
                        success, res = record_intake_shipment(
                            selected_item_id, intake_qty, target_zone, bin_loc,
                            supp, po_num, batch_code, inspector_name, qc_status
                        )
                        if success:
                            st.balloons()
                            updated_item = get_inventory_item(selected_item_id)
                            st.success(f"✅ Inbound delivery recorded! Stock for **{selected_item['item_name']}** updated: `{selected_item['stock_level']}` ➔ `{updated_item['stock_level']}` units.")
                            st.markdown(f"""
                            <div class="receipt-box">
                                <div style="font-size: 1.15rem; font-weight: bold; color: #166534; margin-bottom: 6px;">
                                    📄 OFFICIAL GOODS RECEIPT NOTE (GRN)
                                </div>
                                <strong>Receipt Reference:</strong> <code>{res}</code><br>
                                <strong>Item:</strong> {selected_item['item_name']} (<code>{selected_item_id}</code>)<br>
                                <strong>Quantity Added:</strong> {intake_qty} units<br>
                                <strong>New Live In-Stock:</strong> {updated_item['stock_level']} units<br>
                                <strong>Storage Location:</strong> {target_zone} ({bin_loc})<br>
                                <strong>PO Number:</strong> {po_num} | <strong>Batch:</strong> {batch_code}<br>
                                <strong>Verified By:</strong> {inspector_name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                                <strong>Inspection:</strong> {qc_status}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"Error: {res}")

            with col_prev:
                st.markdown("##### 🔍 SKU Profile")
                st.markdown(f"""
                <div class="card-box">
                    <h4 style="margin-top:0; color:#1E3A8A;">{selected_item['item_name']}</h4>
                    <p><strong>SKU ID:</strong> <code>{selected_item['item_id']}</code></p>
                    <p><strong>Category:</strong> {selected_item['category']}</p>
                    <p><strong>Current Stock:</strong> <span style="font-size:1.3rem; font-weight:bold; color:{'#16A34A' if selected_item['stock_level'] > selected_item['reorder_point'] else '#DC2626'}">{selected_item['stock_level']} units</span></p>
                    <p><strong>Reorder Threshold:</strong> {selected_item['reorder_point']} units</p>
                    <p><strong>Storage Location:</strong> {selected_item['zone']} ({selected_item['bin_location']})</p>
                    <p><strong>Unit Valuation:</strong> ${selected_item['unit_price']:,.2f}</p>
                    <p><strong>Health Status:</strong> {'🟢 Safe Stock' if selected_item['stock_level'] > selected_item['reorder_point'] else '🔴 Critical Restock Required'}</p>
                </div>
                """, unsafe_allow_html=True)

    # Tab 2: New SKU Registration
    with intake_tab2:
        st.markdown("### Register & Stock Brand New SKU")
        st.caption("Receive a new item not previously cataloged in the warehouse database.")

        with st.form("new_sku_form"):
            n1, n2, n3 = st.columns(3)
            with n1:
                new_id = st.text_input("New Item ID / SKU", value=f"SKU-{random.randint(7000, 7999)}")
                new_name = st.text_input("Product Full Name", placeholder="e.g. Industrial Digital Caliper 150mm")
                new_cat = st.selectbox("Product Category", ["Electronics", "Automotive", "Pharmaceuticals", "Industrial Tools", "Apparel & Safety", "Food & Beverages"])

            with n2:
                new_stock = st.number_input("Initial Intake Quantity", min_value=1, max_value=5000, value=200)
                new_price = st.number_input("Unit Price ($)", min_value=0.5, max_value=2000.0, value=35.0, step=5.0)
                new_zone = st.selectbox("Target Storage Zone", ["Zone A", "Zone B", "Zone C", "Zone D"])

            with n3:
                new_bin = st.text_input("Bin Location", value=f"BIN-{new_zone[-1]}-105")
                new_reorder = st.number_input("Reorder Point Threshold", min_value=5, max_value=500, value=40)
                new_lead = st.slider("Supplier Lead Time (Days)", 1, 30, 5)

            s1, s2 = st.columns(2)
            with s1:
                new_supp = st.text_input("Supplier Organization", "Global Precision Logistics Ltd")
            with s2:
                new_demand = st.number_input("Estimated Daily Demand (Units)", min_value=0.5, max_value=100.0, value=8.5)

            submit_new = st.form_submit_button("✨ Register New SKU & Stock In Database", type="primary", use_container_width=True)

            if submit_new:
                if not new_id or not new_name:
                    st.error("Please fill out both the SKU ID and Product Name.")
                else:
                    success, res = add_new_inventory_item(
                        new_id, new_name, new_cat, new_stock, new_reorder,
                        new_price, new_zone, new_bin, new_supp, new_lead, new_demand
                    )
                    if success:
                        st.balloons()
                        st.success(f"🎉 New SKU **{new_id}** ({new_name}) registered and initial intake recorded with receipt `{res}`!")
                    else:
                        st.error(res)

# =========================================================
# Page 2: 📤 Stock Dispatch & Fulfillment
# =========================================================
elif page == "📤 Stock Dispatch & Fulfillment":
    st.markdown('<span class="wms-badge badge-outbound">Outbound Operations • Shipping Dock</span>', unsafe_allow_html=True)
    st.markdown("<div class='main-header'>📤 Outbound Stock Dispatch & Order Fulfillment</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Pick, verify, and dispatch stock orders for client shipments, branch warehouses, and retail distribution centers.</div>", unsafe_allow_html=True)

    if inv_df.empty:
        st.warning("No inventory items found in database.")
    else:
        dcol1, dcol2 = st.columns([1.5, 1])

        with dcol1:
            st.markdown("### Process Outbound Shipment")
            sku_choices = {r['item_id']: f"{r['item_id']} - {r['item_name']} (In Stock: {r['stock_level']})" for r in inventory_list}
            dispatch_item_id = st.selectbox("Select SKU for Outbound Picking", options=list(sku_choices.keys()), format_func=lambda x: sku_choices[x])
            
            d_item = get_inventory_item(dispatch_item_id)
            avail_stock = d_item['stock_level']

            with st.form("dispatch_form"):
                st.markdown(f"**Available Physical Stock:** `{avail_stock}` units | Reorder Threshold: `{d_item['reorder_point']}` units")

                dp1, dp2 = st.columns(2)
                with dp1:
                    dispatch_qty = st.number_input("Dispatch Quantity (Units)", min_value=1, max_value=max(1, avail_stock), value=min(25, max(1, avail_stock)))
                    destination = st.text_input("Destination Facility / Customer", "Central Fulfillment Hub North")
                    carrier = st.selectbox("Freight Carrier", ["DHL Express", "FedEx Supply Chain", "Blue Dart Logistics", "Internal Fleet Van"])

                with dp2:
                    waybill = st.text_input("Waybill / Tracking Number", f"WB-{random.randint(100000, 999999)}")
                    dispatcher = st.text_input("Dispatching Officer", "Arya Rai")
                    priority = st.selectbox("Dispatch Priority", ["Standard Ground", "Expedited 24h Priority", "Critical Emergency Restock"])

                submit_dispatch = st.form_submit_button("📤 Confirm & Dispatch Shipment", type="primary", use_container_width=True)

                if submit_dispatch:
                    success, res, new_stock, reorder_pt = record_dispatch_shipment(
                        dispatch_item_id, dispatch_qty, destination, carrier, waybill, dispatcher, priority
                    )
                    if success:
                        st.success(f"✅ Dispatch confirmed! **{dispatch_qty} units** of `{d_item['item_name']}` deducted. Remaining stock: `{new_stock}` units.")
                        if new_stock <= reorder_pt:
                            st.warning(f"⚠️ **Attention:** `{dispatch_item_id}` stock ({new_stock} units) has dropped BELOW its reorder threshold ({reorder_pt} units)! Restock alert generated.")

                        st.markdown(f"""
                        <div class="dispatch-box">
                            <div style="font-size: 1.15rem; font-weight: bold; color: #92400E; margin-bottom: 6px;">
                                🚚 GOODS DISPATCH NOTE (GDN)
                            </div>
                            <strong>Dispatch Reference:</strong> <code>{res}</code><br>
                            <strong>Product:</strong> {d_item['item_name']} (<code>{dispatch_item_id}</code>)<br>
                            <strong>Quantity Shipped:</strong> {dispatch_qty} units<br>
                            <strong>Remaining Stock:</strong> {new_stock} units<br>
                            <strong>Destination:</strong> {destination}<br>
                            <strong>Carrier:</strong> {carrier} | <strong>Waybill:</strong> {waybill}<br>
                            <strong>Priority:</strong> {priority}<br>
                            <strong>Dispatched By:</strong> {dispatcher} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(res)

        with dcol2:
            st.markdown("### Picking Guidelines")
            st.markdown("""
            <div class="card-box">
                <h4 style="margin-top:0; color:#92400E;">📦 Quality & Safety Rules</h4>
                <ul style="font-size:0.9rem; line-height:1.6; color:#475569;">
                    <li><strong>FIFO Principle:</strong> Pick from oldest received lot codes first.</li>
                    <li><strong>Stock Protection:</strong> System prevents dispatching beyond physical database stock.</li>
                    <li><strong>Inspection Scan:</strong> Scan item barcode prior to packing in dispatch bay.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# Page 3: 📋 Live Inventory & Master Catalog
# =========================================================
elif page == "📋 Live Inventory & Master Catalog":
    st.markdown("<div class='main-header'>📋 Live Inventory & Master SKU Catalog</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Search, filter, edit stock levels, or adjust bin locations directly in the warehouse database.</div>", unsafe_allow_html=True)

    if inv_df.empty:
        st.info("Database is empty.")
    else:
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            sel_cat = st.multiselect("Filter Category", sorted(inv_df['category'].unique()), default=[])
        with fc2:
            sel_zone = st.multiselect("Filter Zone", sorted(inv_df['zone'].unique()), default=[])
        with fc3:
            health_filter = st.selectbox("Stock Health", ["All SKUs", "Critical Restock Only", "Safe Stock Only"])
        with fc4:
            search_query = st.text_input("Search SKU ID, Name or Bin", "")

        filtered = inv_df.copy()
        if sel_cat:
            filtered = filtered[filtered['category'].isin(sel_cat)]
        if sel_zone:
            filtered = filtered[filtered['zone'].isin(sel_zone)]
        if health_filter == "Critical Restock Only":
            filtered = filtered[filtered['stock_level'] <= filtered['reorder_point']]
        elif health_filter == "Safe Stock Only":
            filtered = filtered[filtered['stock_level'] > filtered['reorder_point']]
        if search_query:
            filtered = filtered[
                filtered['item_id'].str.contains(search_query, case=False, na=False) |
                filtered['item_name'].str.contains(search_query, case=False, na=False) |
                filtered['bin_location'].str.contains(search_query, case=False, na=False)
            ]

        filtered_val = (filtered['stock_level'] * filtered['unit_price']).sum()
        st.markdown(f"Showing **{len(filtered):,}** of **{len(inv_df):,}** SKUs | Total Valuation: **${filtered_val:,.2f}**")

        st.dataframe(
            filtered[[
                'item_id', 'item_name', 'category', 'stock_level', 'reorder_point',
                'unit_price', 'zone', 'bin_location', 'supplier', 'last_restocked'
            ]].rename(columns={
                'item_id': 'SKU ID',
                'item_name': 'Product Name',
                'category': 'Category',
                'stock_level': 'Current Stock',
                'reorder_point': 'Reorder Point',
                'unit_price': 'Unit Price ($)',
                'zone': 'Zone',
                'bin_location': 'Bin Location',
                'supplier': 'Supplier',
                'last_restocked': 'Last Restocked'
            }),
            use_container_width=True,
            height=400
        )

        csv_data = filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Filtered Inventory Master (CSV)",
            data=csv_data,
            file_name="wms_inventory_catalog.csv",
            mime="text/csv"
        )

        st.markdown("---")
        st.markdown("### ✏️ Quick SKU Edit & Stock Adjustment")
        with st.expander("Click to edit an existing SKU or adjust bin / reorder values"):
            edit_sku_id = st.selectbox("Select SKU to Edit", inv_df['item_id'].tolist(), key="edit_sku_sel")
            e_item = get_inventory_item(edit_sku_id)

            with st.form("edit_sku_form"):
                ec1, ec2, ec3, ec4 = st.columns(4)
                with ec1:
                    adj_stock = st.number_input("Stock Level", value=int(e_item['stock_level']))
                with ec2:
                    adj_reorder = st.number_input("Reorder Point", value=int(e_item['reorder_point']))
                with ec3:
                    adj_price = st.number_input("Unit Price ($)", value=float(e_item['unit_price']), step=1.0)
                with ec4:
                    adj_bin = st.text_input("Bin Location", value=e_item['bin_location'])

                sub_edit = st.form_submit_button("Save Changes to Database", type="primary")
                if sub_edit:
                    update_inventory_stock(edit_sku_id, adj_stock, adj_reorder, adj_price, adj_bin)
                    st.success(f"SKU {edit_sku_id} updated successfully!")
                    st.rerun()

# =========================================================
# Page 4: ⚠️ Automated Reorder Alerts
# =========================================================
elif page == "⚠️ Automated Reorder Alerts":
    st.markdown('<span class="wms-badge badge-critical">Automated Triggers • Safety Buffer Alert</span>', unsafe_allow_html=True)
    st.markdown("<div class='main-header'>⚠️ Automated Reorder & Stockout Alerts</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Real-time monitor of items currently below reorder thresholds, with 1-click emergency replenishment.</div>", unsafe_allow_html=True)

    if critical_df.empty:
        st.success("🎉 All inventory SKUs are currently operating safely above their reorder thresholds!")
    else:
        st.markdown(f"### Critical SKUs Requiring Replenishment ({len(critical_df)} Items)")
        
        st.dataframe(
            critical_df[['item_id', 'item_name', 'category', 'stock_level', 'reorder_point', 'unit_price', 'zone', 'bin_location', 'supplier', 'lead_time_days']].rename(columns={
                'item_id': 'SKU ID',
                'item_name': 'Item Name',
                'category': 'Category',
                'stock_level': 'Current Stock',
                'reorder_point': 'Reorder Point',
                'unit_price': 'Unit Price ($)',
                'zone': 'Zone',
                'bin_location': 'Bin',
                'supplier': 'Supplier',
                'lead_time_days': 'Lead Time (Days)'
            }),
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### ⚡ 1-Click Expedited Restock Intake")
        st.write("Select any critical item to immediately trigger an emergency intake and restore warehouse safety buffer.")

        rc1, rc2 = st.columns([1.5, 1])
        with rc1:
            crit_choices = {r['item_id']: f"{r['item_id']} - {r['item_name']} (In Stock: {r['stock_level']} | Reorder Point: {r['reorder_point']})" for _, r in critical_df.iterrows()}
            restock_id = st.selectbox("Select Critical SKU", options=list(crit_choices.keys()), format_func=lambda x: crit_choices[x])
            r_item = get_inventory_item(restock_id)
            
            # Recommended restock quantity: 2x reorder point - current stock
            rec_qty = max(50, (r_item['reorder_point'] * 2) - r_item['stock_level'])

            st.write(f"**Recommended Intake Batch:** `{rec_qty}` units | Supplier: **{r_item['supplier']}**")

            if st.button(f"📥 Execute Emergency Restock ({rec_qty} Units) for {restock_id}", type="primary"):
                success, res = record_intake_shipment(
                    restock_id, rec_qty, r_item['zone'], r_item['bin_location'],
                    r_item['supplier'], f"PO-EMERGENCY-{random.randint(1000, 9999)}",
                    f"BAT-EXP-{datetime.now().strftime('%m%d')}", "Auto-WMS Expediter", "Passed Quality Check"
                )
                if success:
                    st.balloons()
                    st.success(f"🎉 Emergency Restock Completed! Receipt `{res}` generated. Risk cleared.")
                    st.rerun()

        with rc2:
            st.markdown("""
            <div class="card-box">
                <h4 style="margin-top:0; color:#991B1B;">🛡️ Safety Stock Strategy</h4>
                <p style="font-size:0.9rem; color:#64748B;">
                    When stock level $\le$ reorder point, an immediate replenishment PO is generated to bridge the supplier lead time.
                </p>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# Page 5: 📊 Warehouse Executive Dashboard
# =========================================================
elif page == "📊 Warehouse Executive Dashboard":
    st.markdown("<div class='main-header'>📊 Warehouse Executive Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>High-level metrics on inventory valuation, category distributions, storage zone capacities, and operations velocity.</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Warehouse Valuation", f"${total_val:,.2f}")
    with c2:
        st.metric("Total Catalog SKUs", f"{total_skus:,}")
    with c3:
        st.metric("Total Physical Units", f"{total_units:,} units")
    with c4:
        st.metric("Critical Restock SKUs", f"{critical_count:,}", delta=f"-{(critical_count/max(1, total_skus)*100):.1f}% below reorder", delta_color="inverse")

    st.markdown("---")

    r1, r2 = st.columns(2)
    with r1:
        st.subheader("Inventory Valuation by Category")
        cat_df = inv_df.groupby('category').apply(lambda x: (x['stock_level'] * x['unit_price']).sum()).reset_index(name='Total_Value')
        fig_cat = px.bar(cat_df, x='category', y='Total_Value', color='category', text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Safe)
        fig_cat.update_layout(showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_cat, use_container_width=True)

    with r2:
        st.subheader("Stock Units Distribution by Storage Zone")
        zone_df = inv_df.groupby('zone')['stock_level'].sum().reset_index()
        fig_zone = px.pie(zone_df, names='zone', values='stock_level', hole=0.45, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_zone.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_zone, use_container_width=True)

    r3, r4 = st.columns(2)
    with r3:
        st.subheader("ABC Inventory Pareto Classification")
        inv_sorted = inv_df.copy()
        inv_sorted['item_val'] = inv_sorted['stock_level'] * inv_sorted['unit_price']
        inv_sorted = inv_sorted.sort_values(by='item_val', ascending=False)
        inv_sorted['cum_val'] = inv_sorted['item_val'].cumsum()
        inv_sorted['cum_pct'] = inv_sorted['cum_val'] / max(1.0, inv_sorted['item_val'].sum())

        def get_abc(p):
            if p <= 0.80: return 'Class A (High Value 80%)'
            elif p <= 0.95: return 'Class B (Medium Value 15%)'
            else: return 'Class C (Low Value 5%)'

        inv_sorted['Class'] = inv_sorted['cum_pct'].apply(get_abc)
        abc_counts = inv_sorted['Class'].value_counts().reset_index()
        abc_counts.columns = ['Class', 'Count']
        fig_abc = px.pie(abc_counts, names='Class', values='Count', color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B'])
        fig_abc.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_abc, use_container_width=True)

    with r4:
        st.subheader("Unit Price vs. In-Stock Level")
        fig_scatter = px.scatter(
            inv_df, x='unit_price', y='stock_level', color='category',
            hover_name='item_name', size='stock_level',
            labels={'unit_price': 'Unit Price ($)', 'stock_level': 'In-Stock Quantity'}
        )
        fig_scatter.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# Page 6: 🏢 Storage Zones & Facility Layout
# =========================================================
elif page == "🏢 Storage Zones & Facility Layout":
    st.markdown("<div class='main-header'>🏢 Storage Zones & Warehouse Layout Master</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Physical layout specifications, bay capacities, temperature control, and rack occupancy across facility zones.</div>", unsafe_allow_html=True)

    zones_list = get_zones()
    z_cols = st.columns(len(zones_list))

    for idx, z in enumerate(zones_list):
        with z_cols[idx]:
            z_items = inv_df[inv_df['zone'] == z['zone_code']] if not inv_df.empty else pd.DataFrame()
            z_units = int(z_items['stock_level'].sum()) if not z_items.empty else 0
            z_skus = len(z_items)

            st.markdown(f"""
            <div class="card-box">
                <h3 style="margin-top:0; color:#1E3A8A;">{z['zone_code']}</h3>
                <p><strong>{z['zone_name']}</strong></p>
                <hr style="margin:8px 0;">
                <p><strong>Racking Type:</strong> {z['zone_type']}</p>
                <p><strong>Environment:</strong> {z['temperature_control']}</p>
                <p><strong>Total Pallet Bays:</strong> {z['total_bays']} Bays</p>
                <p><strong>Active SKUs:</strong> <code>{z_skus}</code></p>
                <p><strong>Stored Units:</strong> <strong>{z_units:,}</strong></p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### SKUs by Storage Zone")
    zone_choice = st.selectbox("Select Zone to View Stored Items", [z['zone_code'] for z in zones_list])
    zone_items = inv_df[inv_df['zone'] == zone_choice]

    if zone_items.empty:
        st.info("No items currently mapped to this zone.")
    else:
        st.dataframe(
            zone_items[['item_id', 'item_name', 'bin_location', 'category', 'stock_level', 'unit_price', 'supplier']],
            use_container_width=True
        )

# =========================================================
# Page 7: 📜 Transaction Audit Ledgers
# =========================================================
elif page == "📜 Transaction Audit Ledgers":
    st.markdown("<div class='main-header'>📜 Transaction Audit Ledgers</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Complete, immutable history of all Goods Receipt Notes (GRNs) and Goods Dispatch Notes (GDNs) stored in SQLite.</div>", unsafe_allow_html=True)

    ltab1, ltab2 = st.tabs([
        "📥 Inbound Goods Receipt Notes (GRN) Ledger",
        "📤 Outbound Goods Dispatch Notes (GDN) Ledger"
    ])

    with ltab1:
        intake_rows = get_intake_records()
        if not intake_rows:
            st.info("No intake records found.")
        else:
            in_df = pd.DataFrame(intake_rows)
            st.markdown(f"### Inbound Intake Ledger ({len(in_df)} Records)")
            st.dataframe(in_df, use_container_width=True)

            csv_in = in_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Inbound GRN Ledger (CSV)",
                data=csv_in,
                file_name="wms_inbound_grn_ledger.csv",
                mime="text/csv"
            )

    with ltab2:
        dispatch_rows = get_dispatch_records()
        if not dispatch_rows:
            st.info("No dispatch records found.")
        else:
            out_df = pd.DataFrame(dispatch_rows)
            st.markdown(f"### Outbound Dispatch Ledger ({len(out_df)} Records)")
            st.dataframe(out_df, use_container_width=True)

            csv_out = out_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Outbound GDN Ledger (CSV)",
                data=csv_out,
                file_name="wms_outbound_gdn_ledger.csv",
                mime="text/csv"
            )
