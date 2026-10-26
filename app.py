import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import json
import os

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Warehouse Management System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-safe {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Resource Loading
# ---------------------------------------------------------
@st.cache_resource
def load_models_and_data():
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
    kpi_model, clf_model, metadata, df = load_models_and_data()
except Exception as e:
    st.error(f"Error loading models or dataset: {e}. Please ensure 'train_model.py' has been executed.")
    st.stop()

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.markdown("## 📦 Warehouse System")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Warehouse Overview",
        "⚠️ Stockout & Restock Predictor",
        "🎯 KPI & Efficiency Optimizer",
        "📋 Inventory Catalog",
        "🔬 Model Architecture & Metrics"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Total SKUs Active:** `{len(df):,}`")
st.sidebar.markdown(f"**Model R² Accuracy:** `99.2%`")
st.sidebar.markdown(f"**Stockout F1-Score:** `97.7%`")

# ---------------------------------------------------------
# Page 1: Warehouse Overview
# ---------------------------------------------------------
if page == "📊 Warehouse Overview":
    st.markdown("<div class='main-header'>Warehouse Management System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Operational overview, inventory distribution, storage zones, and KPI health.</div>", unsafe_allow_html=True)

    # Top KPI Metrics Cards
    total_val = (df['stock_level'] * df['unit_price']).sum()
    critical_items = (df['stockout_risk'] == 1).sum()
    avg_kpi = df['KPI_score'].mean()
    avg_turnover = df['turnover_ratio'].mean()
    fulfillment = df['order_fulfillment_rate'].mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Inventory Value", f"${total_val:,.2f}")
    with col2:
        st.metric("Critical Restock SKUs", f"{critical_items:,}", delta=f"-{(critical_items/len(df)*100):.1f}% at risk", delta_color="inverse")
    with col3:
        st.metric("Average Warehouse KPI", f"{avg_kpi:.3f}", delta=f"{fulfillment:.1f}% fulfillment")
    with col4:
        st.metric("Average Turnover Ratio", f"{avg_turnover:.1f}x", delta="Healthy Target: > 7x")

    st.markdown("---")

    # Row 1 Charts: Category Breakdown & Storage Zones
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Inventory Value by Category")
        cat_val = df.groupby('category').apply(lambda x: (x['stock_level'] * x['unit_price']).sum()).reset_index(name='Total_Value')
        fig_cat = px.bar(
            cat_val, x='category', y='Total_Value', color='category',
            text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Safe,
            labels={'category': 'Product Category', 'Total_Value': 'Inventory Value ($)'}
        )
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
            zone_stats, x='Avg_Picking_Time', y='Avg_Layout_Score', size='SKUs', color='zone',
            text='zone', labels={'Avg_Picking_Time': 'Avg Picking Time (sec)', 'Avg_Layout_Score': 'Layout Score (0-1)'},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_zone.update_traces(textposition='top center')
        fig_zone.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_zone, use_container_width=True)

    # Row 2 Charts: ABC Analysis & Stockout Distribution
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("ABC Inventory Classification (Pareto 80/20)")
        # Calculate ABC
        df_sorted = df.copy()
        df_sorted['item_val'] = df_sorted['stock_level'] * df_sorted['unit_price']
        df_sorted = df_sorted.sort_values(by='item_val', ascending=False)
        df_sorted['cum_val'] = df_sorted['item_val'].cumsum()
        df_sorted['cum_pct'] = df_sorted['cum_val'] / df_sorted['item_val'].sum()
        
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
        
        fig_abc = px.pie(
            abc_counts, names='Class', values='Count', hole=0.45,
            color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B']
        )
        fig_abc.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_abc, use_container_width=True)

    with c4:
        st.subheader("Daily Demand vs. Stock Level by Risk Status")
        sample_df = df.sample(min(800, len(df)), random_state=42).copy()
        sample_df['Stock_Status'] = sample_df['stockout_risk'].map({0: 'Safe Stock', 1: 'Critical Risk'})
        fig_scatter = px.scatter(
            sample_df,
            x='daily_demand', y='stock_level', color='Stock_Status',
            color_discrete_map={'Safe Stock': '#10B981', 'Critical Risk': '#EF4444'},
            labels={'daily_demand': 'Daily Demand (units)', 'stock_level': 'Current Stock Level', 'Stock_Status': 'Stock Status'}
        )
        fig_scatter.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------------------------------------------------
# Page 2: Stockout & Restock Predictor
# ---------------------------------------------------------
elif page == "⚠️ Stockout & Restock Predictor":
    st.markdown("<div class='main-header'>Stockout Risk & Reorder Predictor</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Machine Learning stockout risk classification (97.7% Accuracy) with Economic Order Quantity (EOQ) calculation.</div>", unsafe_allow_html=True)

    with st.form("stockout_prediction_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            stock_level = st.number_input("Current Stock Level (units)", min_value=1, max_value=2000, value=65)
            reorder_point = st.number_input("Reorder Point Threshold", min_value=1, max_value=500, value=75)
            lead_time = st.slider("Supplier Lead Time (days)", min_value=1, max_value=30, value=6)
        with col2:
            daily_demand = st.number_input("Average Daily Demand (units)", min_value=0.5, max_value=200.0, value=18.5)
            demand_std = st.slider("Demand Volatility (Std Dev)", min_value=0.1, max_value=20.0, value=4.5)
            turnover = st.slider("Inventory Turnover Ratio", min_value=0.5, max_value=25.0, value=8.2)
        with col3:
            unit_price = st.number_input("Unit Price ($)", min_value=1.0, max_value=1000.0, value=120.0)
            holding_cost = st.number_input("Daily Holding Cost/Unit ($)", min_value=0.01, max_value=20.0, value=0.85)
            handling_cost = st.number_input("Order Handling Cost/Unit ($)", min_value=0.1, max_value=50.0, value=3.2)
            
        submitted = st.form_submit_button("Run Risk Prediction & EOQ Analysis", use_container_width=True)

    if submitted:
        input_data = pd.DataFrame([{
            'daily_demand': daily_demand,
            'demand_std_dev': demand_std,
            'lead_time_days': lead_time,
            'stock_level': stock_level,
            'reorder_point': reorder_point,
            'turnover_ratio': turnover
        }])
        
        pred_risk = clf_model.predict(input_data)[0]
        pred_prob = clf_model.predict_proba(input_data)[0]
        
        # Supply and EOQ metrics
        days_of_supply = stock_level / max(0.1, daily_demand)
        safety_stock = round(1.65 * demand_std * np.sqrt(lead_time), 1)
        annual_demand = daily_demand * 365
        annual_holding = holding_cost * 365
        eoq = round(np.sqrt((2 * annual_demand * handling_cost) / max(0.01, annual_holding)), 1)
        recommended_reorder_qty = max(eoq, round(safety_stock + (daily_demand * lead_time) - stock_level, 1))

        st.markdown("### Prediction Results")
        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1:
            if pred_risk == 1:
                st.error("🚨 **RISK STATUS: CRITICAL STOCKOUT IMMINENT**")
                st.markdown(f"**Stockout Probability:** `{pred_prob[1]*100:.1f}%`")
                st.markdown("Immediate purchase order required to avoid stock exhaustion.")
            else:
                st.success("✅ **RISK STATUS: OPTIMAL / SAFE INVENTORY**")
                st.markdown(f"**Safety Confidence:** `{pred_prob[0]*100:.1f}%`")
                st.markdown("Stock buffer is adequate to sustain lead time demand.")

        with res_col2:
            st.metric("Estimated Days of Supply", f"{days_of_supply:.1f} days", 
                      delta=f"{days_of_supply - lead_time:.1f} days margin",
                      delta_color="normal" if days_of_supply >= lead_time else "inverse")
            st.metric("Recommended Safety Stock", f"{safety_stock} units")

        with res_col3:
            st.metric("Economic Order Quantity (EOQ)", f"{eoq} units")
            st.metric("Suggested Restock Order Size", f"{recommended_reorder_qty} units")

        # Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pred_prob[1] * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Stockout Risk Probability (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#EF4444" if pred_risk == 1 else "#10B981"},
                'steps': [
                    {'range': [0, 40], 'color': "#DCFCE7"},
                    {'range': [40, 70], 'color': "#FEF3C7"},
                    {'range': [70, 100], 'color': "#FEE2E2"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

# ---------------------------------------------------------
# Page 3: KPI & Efficiency Optimizer
# ---------------------------------------------------------
elif page == "🎯 KPI & Efficiency Optimizer":
    st.markdown("<div class='main-header'>Warehouse KPI & Efficiency Simulator</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Gradient Boosting Regressor ($R^2 = 0.992$) simulating warehouse health score adjustments.</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### Warehouse Operations Parameters")
        turnover_ratio = st.slider("Inventory Turnover Ratio", 1.0, 15.0, 8.5, 0.5)
        layout_eff = st.slider("Warehouse Layout Efficiency Score", 0.1, 1.0, 0.72, 0.05)
        stockout_count = st.slider("Stockouts Last Month", 0, 10, 2)
        holding_cost = st.slider("Daily Holding Cost/Unit ($)", 0.1, 2.0, 0.8, 0.05)
        fulfillment = st.slider("Order Fulfillment Rate", 0.7, 1.0, 0.92, 0.01)
        
    with col2:
        st.markdown("#### Baseline SKU Dimensions")
        stock_lvl = st.number_input("Average Stock Level", 20, 500, 250)
        reorder_pt = st.number_input("Average Reorder Point", 10, 100, 50)
        lead_time = st.number_input("Average Lead Time (Days)", 2, 10, 5)
        daily_dem = st.number_input("Average Daily Demand", 5.0, 50.0, 25.0)
        handling_c = st.number_input("Average Handling Cost ($)", 0.5, 5.0, 2.5)
        unit_p = st.number_input("Average Unit Price ($)", 10.0, 200.0, 105.0)
        orders = st.number_input("Total Orders Handled Last Month", 50, 1000, 500)

    # Predict KPI
    kpi_input = pd.DataFrame([{
        'stock_level': stock_lvl,
        'reorder_point': reorder_pt,
        'lead_time_days': lead_time,
        'daily_demand': daily_dem,
        'handling_cost_per_unit': handling_c,
        'unit_price': unit_p,
        'holding_cost_per_unit_day': holding_cost,
        'stockout_count_last_month': stockout_count,
        'order_fulfillment_rate': fulfillment,
        'total_orders_last_month': orders,
        'turnover_ratio': turnover_ratio,
        'layout_efficiency_score': layout_eff
    }])
    
    pred_kpi = float(kpi_model.predict(kpi_input)[0])
    pred_kpi = max(0.0, min(1.0, pred_kpi))

    st.markdown("---")
    st.markdown("### Simulated Warehouse Performance")
    kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
    with kpi_c1:
        st.metric("Predicted Warehouse KPI Score", f"{pred_kpi:.3f}", 
                  delta=f"{pred_kpi - df['KPI_score'].mean():.3f} vs baseline",
                  delta_color="normal")
    with kpi_c2:
        status = "🌟 Exceptional" if pred_kpi >= 0.75 else ("🟢 Good" if pred_kpi >= 0.55 else "🔴 Needs Optimization")
        st.metric("Operational Health Tier", status)
    with kpi_c3:
        annual_holding_est = holding_cost * 365 * stock_lvl
        st.metric("Est. Annual Holding Cost/SKU", f"${annual_holding_est:,.2f}")

    # Feature impact breakdown
    st.markdown("#### Primary Drivers of Warehouse KPI")
    st.info("""
    - **Inventory Turnover (+):** Increasing stock turnover strongly elevates operational efficiency and cash flow.
    - **Layout Efficiency (+):** Faster picking lanes and optimized rack placement directly improve throughput.
    - **Stockout Count (-):** Unfulfilled orders and stockouts significantly penalize warehouse ratings.
    - **Holding Cost (-):** Excess inventory holding expenses depress bottom-line operational KPI scores.
    """)

# ---------------------------------------------------------
# Page 4: Inventory Catalog
# ---------------------------------------------------------
elif page == "📋 Inventory Catalog":
    st.markdown("<div class='main-header'>Inventory Catalog & SKU Explorer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Search, filter, inspect, and export warehouse inventory items.</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_category = st.multiselect("Filter Category", sorted(df['category'].unique()), default=[])
    with col2:
        selected_zone = st.multiselect("Filter Zone", sorted(df['zone'].unique()), default=[])
    with col3:
        risk_filter = st.selectbox("Stockout Risk Filter", ["All SKUs", "Critical Only (At Risk)", "Safe Only"])
    with col4:
        search_query = st.text_input("Search Item ID", "")

    # Filter dataframe
    filtered_df = df.copy()
    if selected_category:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_category)]
    if selected_zone:
        filtered_df = filtered_df[filtered_df['zone'].isin(selected_zone)]
    if risk_filter == "Critical Only (At Risk)":
        filtered_df = filtered_df[filtered_df['stockout_risk'] == 1]
    elif risk_filter == "Safe Only":
        filtered_df = filtered_df[filtered_df['stockout_risk'] == 0]
    if search_query:
        filtered_df = filtered_df[filtered_df['item_id'].str.contains(search_query, case=False, na=False)]

    st.markdown(f"Showing **{len(filtered_df):,}** of **{len(df):,}** SKUs")
    
    display_cols = [
        'item_id', 'category', 'zone', 'stock_level', 'reorder_point', 
        'daily_demand', 'lead_time_days', 'days_of_supply', 'stockout_risk', 
        'calculated_eoq', 'unit_price', 'KPI_score'
    ]
    
    st.dataframe(
        filtered_df[display_cols].style.format({
            'days_of_supply': '{:.1f}',
            'calculated_eoq': '{:.0f}',
            'unit_price': '${:.2f}',
            'KPI_score': '{:.3f}',
            'daily_demand': '{:.1f}'
        }),
        use_container_width=True,
        height=450
    )

    # Download Button
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Inventory CSV",
        data=csv_data,
        file_name="warehouse_filtered_inventory.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------
# Page 5: Model Architecture & Metrics
# ---------------------------------------------------------
elif page == "🔬 Model Architecture & Metrics":
    st.markdown("<div class='main-header'>Model Architecture & Performance</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Machine learning pipeline specifications, evaluation metrics, and feature importances.</div>", unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    with m1:
        st.markdown("### 1. Warehouse KPI Score Regressor")
        st.markdown("""
        - **Algorithm:** Gradient Boosting Regressor (150 estimators, max depth 4)
        - **R² Score:** `0.9922` (99.2% variance explained)
        - **Mean Absolute Error (MAE):** `0.0081`
        - **Target:** `KPI_score` (continuous scale from 0.0 to 1.0)
        """)
        
        # Display Feature Importances
        kpi_imp = pd.DataFrame({
            'Feature': metadata['kpi_features'],
            'Importance': kpi_model.feature_importances_
        }).sort_values('Importance', ascending=True)
        
        fig_kpi_imp = px.bar(
            kpi_imp, x='Importance', y='Feature', orientation='h',
            title="KPI Model Feature Importances",
            color_discrete_sequence=['#3B82F6']
        )
        fig_kpi_imp.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_kpi_imp, use_container_width=True)

    with m2:
        st.markdown("### 2. Stockout Risk Classifier")
        st.markdown("""
        - **Algorithm:** Random Forest Classifier (100 estimators, max depth 8)
        - **Accuracy:** `97.66%`
        - **Macro F1-Score:** `0.977`
        - **Target:** `stockout_risk` (0: Safe Stock, 1: Critical Stockout Risk)
        """)
        
        clf_imp = pd.DataFrame({
            'Feature': metadata['clf_features'],
            'Importance': clf_model.feature_importances_
        }).sort_values('Importance', ascending=True)
        
        fig_clf_imp = px.bar(
            clf_imp, x='Importance', y='Feature', orientation='h',
            title="Stockout Risk Feature Importances",
            color_discrete_sequence=['#10B981']
        )
        fig_clf_imp.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_clf_imp, use_container_width=True)
