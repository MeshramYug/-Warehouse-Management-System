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
# Page Configuration & Modern Theme Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="NexusWMS - Smart Warehouse Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()
seed_database()

# Theme-Adaptive, High-Contrast Modern CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* High-contrast gradient header */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 50%, #DB2777 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
    }
    
    .hero-caption {
        font-size: 0.95rem;
        opacity: 0.85;
        margin-bottom: 1.2rem;
    }
    
    /* Theme-Adaptive Translucent Cards */
    .glass-card {
        background: rgba(125, 125, 125, 0.08);
        border: 1px solid rgba(125, 125, 125, 0.22);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.12);
    }

    /* Status Badges */
    .status-pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .pill-safe {
        background: rgba(16, 185, 129, 0.18);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .pill-danger {
        background: rgba(239, 68, 68, 0.18);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .pill-info {
        background: rgba(59, 130, 246, 0.18);
        color: #3B82F6;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    .pill-warning {
        background: rgba(245, 158, 11, 0.18);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }

    /* High-contrast receipt boxes */
    .receipt-container {
        background: rgba(16, 185, 129, 0.08);
        border: 2px dashed #10B981;
        border-radius: 12px;
        padding: 18px;
        margin-top: 14px;
        font-family: 'Courier New', monospace;
    }
    .dispatch-container {
        background: rgba(245, 158, 11, 0.08);
        border: 2px dashed #F59E0B;
        border-radius: 12px;
        padding: 18px;
        margin-top: 14px;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Live Database Sync & Metrics Calculation
# ---------------------------------------------------------
inventory_list = get_all_inventory()
inv_df = pd.DataFrame(inventory_list) if inventory_list else pd.DataFrame()

total_skus = len(inv_df)
total_units = int(inv_df['stock_level'].sum()) if not inv_df.empty else 0
total_val = float((inv_df['stock_level'] * inv_df['unit_price']).sum()) if not inv_df.empty else 0.0
critical_df = inv_df[inv_df['stock_level'] <= inv_df['reorder_point']] if not inv_df.empty else pd.DataFrame()
critical_count = len(critical_df)

# Top Bar Header
col_header, col_refresh = st.columns([4, 1])
with col_header:
    st.markdown('<div class="hero-title">📦 NexusWMS Enterprise Operations</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-caption">High-Performance Real-Time Warehouse Management System • SQLite Connected</div>', unsafe_allow_html=True)
with col_refresh:
    st.write("")
    if st.button("🔄 Sync Database", use_container_width=True, type="secondary"):
        st.toast("⚡ Database refreshed successfully!", icon="✅")
        st.rerun()

# ---------------------------------------------------------
# Interactive Live KPI Metric Bar (4 High-Contrast Cards)
# ---------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Total Warehouse Valuation", f"${total_val:,.2f}", delta=f"{total_units:,} units in stock")
with kpi2:
    st.metric("Active Catalog SKUs", f"{total_skus:,}", delta="100% Tracked")
with kpi3:
    st.metric(
        "Critical Restock Items", 
        f"{critical_count:,}", 
        delta=f"{(critical_count/max(1, total_skus)*100):.1f}% needs attention",
        delta_color="inverse"
    )
with kpi4:
    intakes_count = len(get_intake_records())
    dispatches_count = len(get_dispatch_records())
    st.metric("Total Logged Transactions", f"{intakes_count + dispatches_count:,}", delta=f"+{intakes_count} IN / +{dispatches_count} OUT")

st.markdown("---")

# ---------------------------------------------------------
# Streamlined 3 Core Sections Navigation
# ---------------------------------------------------------
main_tab = st.radio(
    "Select System View",
    [
        "📦 Live Inventory & Stock Controller",
        "🔄 Inbound Intake & Outbound Shipping Dock",
        "📊 Warehouse Intelligence & Audit History"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

# =========================================================
# SECTION 1: 📦 Live Inventory & Stock Controller
# =========================================================
if main_tab == "📦 Live Inventory & Stock Controller":
    st.markdown("### 📋 Real-Time Warehouse Inventory Master")
    
    # Interactive Search & Filter Controls
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.2, 1.2, 1.1])
    with f_col1:
        search_txt = st.text_input("🔍 Quick Search", placeholder="Search by SKU, Product Name, or Bin...", label_visibility="collapsed")
    with f_col2:
        cat_options = sorted(inv_df['category'].unique()) if not inv_df.empty else []
        sel_cat = st.multiselect("Filter Category", cat_options, default=[], placeholder="All Categories")
    with f_col3:
        zone_options = sorted(inv_df['zone'].unique()) if not inv_df.empty else []
        sel_zone = st.multiselect("Filter Zone", zone_options, default=[], placeholder="All Storage Zones")
    with f_col4:
        health_filter = st.selectbox("Stock Status", ["All Items", "🔴 Critical (Below Reorder)", "🟢 Healthy Stock"])

    # Filter logic
    filtered = inv_df.copy()
    if sel_cat:
        filtered = filtered[filtered['category'].isin(sel_cat)]
    if sel_zone:
        filtered = filtered[filtered['zone'].isin(sel_zone)]
    if health_filter == "🔴 Critical (Below Reorder)":
        filtered = filtered[filtered['stock_level'] <= filtered['reorder_point']]
    elif health_filter == "🟢 Healthy Stock":
        filtered = filtered[filtered['stock_level'] > filtered['reorder_point']]
    if search_txt:
        filtered = filtered[
            filtered['item_id'].str.contains(search_txt, case=False, na=False) |
            filtered['item_name'].str.contains(search_txt, case=False, na=False) |
            filtered['bin_location'].str.contains(search_txt, case=False, na=False)
        ]

    # Add health status column for display
    if not filtered.empty:
        filtered['Status'] = filtered.apply(
            lambda r: '🔴 Low Stock' if r['stock_level'] <= r['reorder_point'] else '🟢 In Stock', 
            axis=1
        )
        filtered['Stock_Valuation'] = filtered['stock_level'] * filtered['unit_price']

    # Table Display
    disp_cols = [
        'Status', 'item_id', 'item_name', 'category', 'stock_level', 
        'reorder_point', 'unit_price', 'Stock_Valuation', 'zone', 
        'bin_location', 'supplier', 'last_restocked'
    ]

    st.dataframe(
        filtered[disp_cols].rename(columns={
            'item_id': 'SKU ID',
            'item_name': 'Product Description',
            'category': 'Category',
            'stock_level': 'Stock Qty',
            'reorder_point': 'Reorder At',
            'unit_price': 'Unit Price ($)',
            'Stock_Valuation': 'Total Val ($)',
            'zone': 'Zone',
            'bin_location': 'Bin Rack',
            'supplier': 'Primary Supplier',
            'last_restocked': 'Last Restocked'
        }),
        use_container_width=True,
        height=380,
        column_config={
            "Unit Price ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Total Val ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Stock Qty": st.column_config.ProgressColumn(
                "Stock Quantity",
                format="%d units",
                min_value=0,
                max_value=int(inv_df['stock_level'].max() if not inv_df.empty else 1000)
            )
        }
    )

    # Quick Action Buttons & Modals
    act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
    
    with act_col1:
        csv_download = filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export Filtered Inventory (CSV)",
            data=csv_download,
            file_name="warehouse_live_inventory.csv",
            mime="text/csv",
            use_container_width=True
        )

    with act_col2:
        with st.popover("⚡ Instant Stock Restock / Pick Action", use_container_width=True):
            st.markdown("#### ⚡ 1-Click Fast Stock Adjuster")
            st.caption("Quickly add or deduct units on the fly without writing a full PO.")
            
            sku_picker = st.selectbox("Choose SKU to adjust", inv_df['item_id'].tolist(), key="fast_sku_picker")
            current_sku_data = get_inventory_item(sku_picker)
            
            st.write(f"**Item:** {current_sku_data['item_name']} | **Current Stock:** `{current_sku_data['stock_level']}` units")
            
            q_col1, q_col2 = st.columns(2)
            with q_col1:
                if st.button("➕ Quick Restock +50 Units", use_container_width=True, type="primary"):
                    record_intake_shipment(
                        sku_picker, 50, current_sku_data['zone'], current_sku_data['bin_location'],
                        current_sku_data['supplier'], "PO-FAST-RESTOCK", "LOT-QUICK", "Quick Restock", "Passed Quality Check"
                    )
                    st.toast(f"✅ Added +50 units to {sku_picker}!")
                    st.rerun()
            with q_col2:
                if st.button("➖ Quick Pick -10 Units", use_container_width=True):
                    if current_sku_data['stock_level'] >= 10:
                        record_dispatch_shipment(
                            sku_picker, 10, "Fast Pick Dock", "Internal Courier", "WB-FAST", "Quick Picker", "Express"
                        )
                        st.toast(f"📦 Picked 10 units from {sku_picker}!")
                        st.rerun()
                    else:
                        st.error("Insufficient stock!")

    with act_col3:
        with st.popover("➕ Register Brand New SKU", use_container_width=True):
            st.markdown("#### ✨ Register New Warehouse Product")
            with st.form("new_sku_modal_form"):
                n_id = st.text_input("New Item ID / SKU", value=f"SKU-{random.randint(8000, 8999)}")
                n_name = st.text_input("Product Name", placeholder="e.g. Ergonomic Industrial Barcode Scanner")
                n_cat = st.selectbox("Category", ["Electronics", "Automotive", "Pharmaceuticals", "Industrial Tools", "Apparel & Safety", "Food & Beverages"])
                n_qty = st.number_input("Initial Intake Units", min_value=1, max_value=5000, value=150)
                n_price = st.number_input("Unit Cost ($)", min_value=0.5, value=45.0, step=5.0)
                n_zone = st.selectbox("Storage Zone", ["Zone A", "Zone B", "Zone C", "Zone D"])
                n_bin = st.text_input("Rack Location", f"BIN-{n_zone[-1]}-201")
                n_reorder = st.number_input("Reorder Threshold", min_value=5, value=30)
                n_supp = st.text_input("Supplier Organization", "Global Apex Supply Corp")
                
                sub_new = st.form_submit_button("✨ Save & Create SKU", type="primary", use_container_width=True)
                if sub_new:
                    if not n_name:
                        st.error("Please enter a valid product name.")
                    else:
                        success, res = add_new_inventory_item(
                            n_id, n_name, n_cat, n_qty, n_reorder, n_price,
                            n_zone, n_bin, n_supp, 5, 10.0
                        )
                        if success:
                            st.toast(f"🎉 New SKU {n_id} registered successfully!", icon="✅")
                            st.rerun()
                        else:
                            st.error(res)

    # Quick Edit Expander
    with st.expander("✏️ Edit Existing SKU Details (Price, Reorder Point, Rack Bin)"):
        e_col1, e_col2, e_col3, e_col4, e_col5 = st.columns(5)
        edit_target = e_col1.selectbox("Select SKU", inv_df['item_id'].tolist(), key="sku_edit_target")
        e_data = get_inventory_item(edit_target)
        
        with st.form("inline_edit_form"):
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            val_stock = c_f1.number_input("Adjusted Stock", value=int(e_data['stock_level']))
            val_reorder = c_f2.number_input("Reorder Threshold", value=int(e_data['reorder_point']))
            val_price = c_f3.number_input("Unit Price ($)", value=float(e_data['unit_price']), step=1.0)
            val_bin = c_f4.text_input("Bin Location", value=e_data['bin_location'])
            
            if st.form_submit_button("💾 Commit Updates to Database", type="primary"):
                update_inventory_stock(edit_target, val_stock, val_reorder, val_price, val_bin)
                st.toast(f"✅ SKU {edit_target} updated successfully!")
                st.rerun()


# =========================================================
# SECTION 2: 🔄 Inbound Intake & Outbound Shipping Dock
# =========================================================
elif main_tab == "🔄 Inbound Intake & Outbound Shipping Dock":
    st.markdown("### 🔄 Operations Dock: Inbound & Outbound Movement")
    st.caption("Perform physical warehouse receiving of supplier stock or fulfill outgoing orders with immediate database updates.")

    dock_in, dock_out = st.tabs([
        "📥 Inbound Receiving Dock (Stock Intake)",
        "📤 Outbound Shipping Dock (Order Dispatch)"
    ])

    # 1. INBOUND RECEIVING DOCK
    with dock_in:
        col_in_form, col_in_info = st.columns([1.6, 1])
        
        with col_in_form:
            st.markdown("#### 📥 Receive Inbound Supplier Shipment")
            
            sku_options = {r['item_id']: f"{r['item_id']} - {r['item_name']} (In-Stock: {r['stock_level']})" for r in inventory_list}
            target_sku = st.selectbox("Select Item to Restock", options=list(sku_options.keys()), format_func=lambda x: sku_options[x], key="inbound_sku_sel")
            
            item_info = get_inventory_item(target_sku)
            
            with st.form("dock_intake_form"):
                row1_c1, row1_c2 = st.columns(2)
                with row1_c1:
                    in_quantity = st.number_input("Units Received", min_value=1, max_value=10000, value=100, step=10)
                    in_po = st.text_input("Purchase Order (PO) #", value=f"PO-{random.randint(10000, 99999)}")
                    in_supplier = st.text_input("Supplier Name", value=item_info['supplier'])
                with row1_c2:
                    in_zone = st.selectbox("Storage Zone", ["Zone A", "Zone B", "Zone C", "Zone D"], index=["Zone A", "Zone B", "Zone C", "Zone D"].index(item_info['zone']) if item_info['zone'] in ["Zone A", "Zone B", "Zone C", "Zone D"] else 0)
                    in_bin = st.text_input("Assigned Rack Bin", value=item_info['bin_location'])
                    in_batch = st.text_input("Batch / Lot #", value=f"LOT-2026-{datetime.now().strftime('%m%d')}")
                
                row2_c1, row2_c2 = st.columns(2)
                with row2_c1:
                    in_inspector = st.text_input("Receiving Officer", value="Arya Rai")
                with row2_c2:
                    in_condition = st.selectbox("Inspection Result", ["Passed Quality Check", "Packaging Defect (Approved)", "Quarantined for QA Testing"])

                submit_in = st.form_submit_button("📥 Receive & Update Live Inventory", type="primary", use_container_width=True)

                if submit_in:
                    success, grn_code = record_intake_shipment(
                        target_sku, in_quantity, in_zone, in_bin,
                        in_supplier, in_po, in_batch, in_inspector, in_condition
                    )
                    if success:
                        st.balloons()
                        new_data = get_inventory_item(target_sku)
                        st.toast(f"✅ Inbound delivery received! Stock: {item_info['stock_level']} ➔ {new_data['stock_level']}", icon="📦")
                        st.markdown(f"""
                        <div class="receipt-container">
                            <div style="font-size: 1.15rem; font-weight: 800; color: #10B981; margin-bottom: 6px;">
                                📄 OFFICIAL GOODS RECEIPT NOTE (GRN)
                            </div>
                            <strong>Receipt Number:</strong> <code>{grn_code}</code><br>
                            <strong>Product:</strong> {item_info['item_name']} (<code>{target_sku}</code>)<br>
                            <strong>Quantity Received:</strong> +{in_quantity} units<br>
                            <strong>Updated Total Stock:</strong> <strong>{new_data['stock_level']} units</strong><br>
                            <strong>Assigned Location:</strong> {in_zone} • {in_bin}<br>
                            <strong>PO Reference:</strong> {in_po} | <strong>Lot:</strong> {in_batch}<br>
                            <strong>Inspector:</strong> {in_inspector} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </div>
                        """, unsafe_allow_html=True)

        with col_in_info:
            st.markdown("#### 🔍 Live SKU Card")
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="margin-top:0; color:#3B82F6;">{item_info['item_name']}</h4>
                <p><strong>SKU ID:</strong> <code>{item_info['item_id']}</code></p>
                <p><strong>Category:</strong> {item_info['category']}</p>
                <p><strong>Current In-Stock:</strong> <span style="font-size:1.4rem; font-weight:800; color:{'#10B981' if item_info['stock_level'] > item_info['reorder_point'] else '#EF4444'}">{item_info['stock_level']} units</span></p>
                <p><strong>Reorder Threshold:</strong> {item_info['reorder_point']} units</p>
                <p><strong>Unit Valuation:</strong> ${item_info['unit_price']:,.2f}</p>
                <p><strong>Location:</strong> {item_info['zone']} ({item_info['bin_location']})</p>
            </div>
            """, unsafe_allow_html=True)

    # 2. OUTBOUND SHIPPING DOCK
    with dock_out:
        col_out_form, col_out_info = st.columns([1.6, 1])

        with col_out_form:
            st.markdown("#### 📤 Dispatch Outbound Customer Shipment")
            
            sku_options_out = {r['item_id']: f"{r['item_id']} - {r['item_name']} (Available: {r['stock_level']})" for r in inventory_list}
            dispatch_target = st.selectbox("Select Item to Dispatch", options=list(sku_options_out.keys()), format_func=lambda x: sku_options_out[x], key="outbound_sku_sel")
            
            d_item = get_inventory_item(dispatch_target)
            curr_avail = d_item['stock_level']

            with st.form("dock_dispatch_form"):
                st.write(f"**Available Warehouse Stock:** `{curr_avail}` units | Reorder Threshold: `{d_item['reorder_point']}` units")
                
                d_c1, d_c2 = st.columns(2)
                with d_c1:
                    out_qty = st.number_input("Dispatch Units", min_value=1, max_value=max(1, curr_avail), value=min(20, max(1, curr_avail)))
                    out_dest = st.text_input("Destination Hub / Client", "North City Distribution Center")
                    out_carrier = st.selectbox("Logistics Carrier", ["DHL Express", "FedEx Freight", "Blue Dart Logistics", "Internal Fleet Van"])
                with d_c2:
                    out_waybill = st.text_input("Waybill / Tracking #", f"WB-{random.randint(100000, 999999)}")
                    out_dispatcher = st.text_input("Dispatch Officer", "Arya Rai")
                    out_priority = st.selectbox("Shipping Priority", ["Standard Ground", "Expedited 24h", "Critical Emergency"])

                submit_out = st.form_submit_button("📤 Confirm & Dispatch Shipment", type="primary", use_container_width=True)

                if submit_out:
                    success, res_gdn, remaining_stock, reorder_val = record_dispatch_shipment(
                        dispatch_target, out_qty, out_dest, out_carrier, out_waybill, out_dispatcher, out_priority
                    )
                    if success:
                        st.toast(f"🚚 Shipment dispatched! Deducted {out_qty} units.", icon="📦")
                        st.markdown(f"""
                        <div class="dispatch-container">
                            <div style="font-size: 1.15rem; font-weight: 800; color: #F59E0B; margin-bottom: 6px;">
                                🚚 OFFICIAL GOODS DISPATCH NOTE (GDN)
                            </div>
                            <strong>Dispatch Reference:</strong> <code>{res_gdn}</code><br>
                            <strong>Product:</strong> {d_item['item_name']} (<code>{dispatch_target}</code>)<br>
                            <strong>Quantity Dispatched:</strong> -{out_qty} units<br>
                            <strong>Remaining Stock:</strong> <strong>{remaining_stock} units</strong><br>
                            <strong>Destination:</strong> {out_dest}<br>
                            <strong>Carrier:</strong> {out_carrier} | <strong>Waybill:</strong> {out_waybill}<br>
                            <strong>Officer:</strong> {out_dispatcher} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </div>
                        """, unsafe_allow_html=True)

                        if remaining_stock <= reorder_val:
                            st.warning(f"⚠️ **Attention:** `{dispatch_target}` has dropped below its reorder point ({reorder_val} units)! Restock alert queued.")
                    else:
                        st.error(res_gdn)

        with col_out_info:
            st.markdown("#### 📦 Outbound Fulfillment Rules")
            st.markdown("""
            <div class="glass-card">
                <h4 style="margin-top:0; color:#F59E0B;">🛡️ Stock Guard System</h4>
                <ul style="font-size:0.9rem; line-height:1.6; opacity:0.9;">
                    <li><strong>No Negative Inventory:</strong> Database constraints prevent picking above physical stock.</li>
                    <li><strong>FIFO Protocol:</strong> Always prioritize oldest received lot batches.</li>
                    <li><strong>Real-time Waybill:</strong> Every dispatch logs directly to the immutable SQLite audit ledger.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# SECTION 3: 📊 Warehouse Intelligence & Audit History
# =========================================================
elif main_tab == "📊 Warehouse Intelligence & Audit History":
    st.markdown("### 📊 Warehouse Intelligence & Audit Logs")
    st.caption("Visual facility zone tracking, category valuation analytics, and searchable Goods Receipt & Dispatch ledgers.")

    sub_intel, sub_ledgers = st.tabs([
        "🏢 Facility Storage Zones & Layout Map",
        "📜 Inbound (GRN) & Outbound (GDN) Audit Ledgers"
    ])

    with sub_intel:
        # Zone Visual Cards with Interactive Progress Bars
        zones = get_zones()
        z_cols = st.columns(len(zones))
        
        for idx, z in enumerate(zones):
            with z_cols[idx]:
                z_items = inv_df[inv_df['zone'] == z['zone_code']] if not inv_df.empty else pd.DataFrame()
                z_units = int(z_items['stock_level'].sum()) if not z_items.empty else 0
                z_skus = len(z_items)
                pct_occupied = min(1.0, (z_units / max(1, z['total_bays'] * 25)))

                st.markdown(f"""
                <div class="glass-card">
                    <h3 style="margin-top:0; color:#3B82F6;">{z['zone_code']}</h3>
                    <p style="font-weight:600; font-size:0.95rem;">{z['zone_name']}</p>
                    <hr style="margin:6px 0; opacity:0.2;">
                    <p style="font-size:0.85rem;"><strong>Rack Type:</strong> {z['zone_type']}</p>
                    <p style="font-size:0.85rem;"><strong>Climate:</strong> {z['temperature_control']}</p>
                    <p style="font-size:0.85rem;"><strong>Stored Units:</strong> <strong>{z_units:,} units</strong></p>
                    <p style="font-size:0.85rem;"><strong>Active SKUs:</strong> <code>{z_skus}</code></p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(pct_occupied, text=f"Bay Capacity: {int(pct_occupied*100)}%")

        st.markdown("---")
        
        # High-Contrast Plotly Charts
        ch1, ch2 = st.columns(2)
        with ch1:
            st.subheader("Inventory Valuation by Category")
            cat_df = inv_df.groupby('category').apply(lambda x: (x['stock_level'] * x['unit_price']).sum()).reset_index(name='Total_Value')
            fig_cat = px.bar(
                cat_df, x='category', y='Total_Value', color='category',
                text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Prism,
                labels={'category': 'Category', 'Total_Value': 'Total Value ($)'}
            )
            fig_cat.update_layout(showlegend=False, margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig_cat, use_container_width=True)

        with ch2:
            st.subheader("Units Stored by Facility Zone")
            zone_df = inv_df.groupby('zone')['stock_level'].sum().reset_index()
            fig_zone = px.pie(
                zone_df, names='zone', values='stock_level', hole=0.45,
                color_discrete_sequence=['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B']
            )
            fig_zone.update_layout(margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig_zone, use_container_width=True)

    with sub_ledgers:
        st.markdown("#### 📜 Immutable Transaction Ledgers (Stored in SQLite)")
        
        l_in_tab, l_out_tab = st.tabs([
            "📥 Goods Receipt Notes (GRN) - Inbound History",
            "📤 Goods Dispatch Notes (GDN) - Outbound History"
        ])

        with l_in_tab:
            intake_records = get_intake_records()
            if intake_records:
                in_ledger_df = pd.DataFrame(intake_records)
                st.dataframe(in_ledger_df, use_container_width=True, height=320)
                csv_grn = in_ledger_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Inbound GRN Ledger (CSV)", data=csv_grn, file_name="wms_inbound_grn.csv", mime="text/csv")
            else:
                st.info("No intake records logged yet.")

        with l_out_tab:
            dispatch_records = get_dispatch_records()
            if dispatch_records:
                out_ledger_df = pd.DataFrame(dispatch_records)
                st.dataframe(out_ledger_df, use_container_width=True, height=320)
                csv_gdn = out_ledger_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Outbound GDN Ledger (CSV)", data=csv_gdn, file_name="wms_outbound_gdn.csv", mime="text/csv")
            else:
                st.info("No dispatch records logged yet.")
