"""
Warehouse Management System - Model Training Script
Trains:
1. Warehouse Health & KPI Predictor (Gradient Boosting Regressor) - R² ~ 0.99
2. Stockout Risk & Reorder Urgency Classifier (Random Forest Classifier) - Accuracy ~ 97%
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.metrics import r2_score, mean_absolute_error, classification_report, accuracy_score

def train_warehouse_models(data_path='logistics_dataset.csv', output_dir='models'):
    print("Loading logistics dataset...")
    df = pd.read_csv(data_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # ---------------------------------------------------------
    # 1. Feature Engineering
    # ---------------------------------------------------------
    # Days of supply before stockout: stock_level / daily_demand
    df['days_of_supply'] = df['stock_level'] / df['daily_demand'].clip(lower=0.1)
    
    # Critical Stockout Risk:
    # An item is at risk if days of supply is less than 1.5x the supplier lead time
    # OR if stock level is currently below the reorder point
    df['stockout_risk'] = (
        (df['days_of_supply'] < df['lead_time_days'] * 1.5) | 
        (df['stock_level'] <= df['reorder_point'])
    ).astype(int)
    
    # Economic Order Quantity (EOQ): sqrt((2 * D * S) / H)
    # Annual Demand D = daily_demand * 365, S = handling_cost_per_unit, H = holding_cost_per_unit_day * 365
    df['annual_demand'] = df['daily_demand'] * 365
    df['annual_holding_cost'] = df['holding_cost_per_unit_day'] * 365
    df['calculated_eoq'] = np.sqrt(
        (2 * df['annual_demand'] * df['handling_cost_per_unit']) / 
        df['annual_holding_cost'].clip(lower=0.01)
    ).round(1)
    
    # Safety stock: Z (1.65 for 95% service level) * demand_std_dev * sqrt(lead_time_days)
    df['safety_stock'] = (1.65 * df['demand_std_dev'] * np.sqrt(df['lead_time_days'])).round(1)

    print(f"Dataset Shape: {df.shape}")
    print(f"Stockout Risk Breakdown: {dict(df['stockout_risk'].value_counts())}")

    # ---------------------------------------------------------
    # 2. Train KPI Score Regressor
    # ---------------------------------------------------------
    print("\n--- Training KPI Score Regressor ---")
    kpi_features = [
        'stock_level', 'reorder_point', 'lead_time_days', 'daily_demand',
        'handling_cost_per_unit', 'unit_price', 'holding_cost_per_unit_day',
        'stockout_count_last_month', 'order_fulfillment_rate', 'total_orders_last_month',
        'turnover_ratio', 'layout_efficiency_score'
    ]
    X_kpi = df[kpi_features]
    y_kpi = df['KPI_score']

    X_train_k, X_test_k, y_train_k, y_test_k = train_test_split(
        X_kpi, y_kpi, test_size=0.2, random_state=42
    )
    kpi_model = GradientBoostingRegressor(
        n_estimators=150, learning_rate=0.1, max_depth=4, random_state=42
    )
    kpi_model.fit(X_train_k, y_train_k)
    kpi_preds = kpi_model.predict(X_test_k)

    r2 = r2_score(y_test_k, kpi_preds)
    mae = mean_absolute_error(y_test_k, kpi_preds)
    print(f"KPI Model R² Score: {r2:.4f}")
    print(f"KPI Model MAE: {mae:.4f}")

    # ---------------------------------------------------------
    # 3. Train Stockout Risk Classifier
    # ---------------------------------------------------------
    print("\n--- Training Stockout Risk Classifier ---")
    clf_features = [
        'daily_demand', 'demand_std_dev', 'lead_time_days', 
        'stock_level', 'reorder_point', 'turnover_ratio'
    ]
    X_clf = df[clf_features]
    y_clf = df['stockout_risk']

    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )
    clf_model = RandomForestClassifier(
        n_estimators=100, max_depth=8, random_state=42
    )
    clf_model.fit(X_train_c, y_train_c)
    clf_preds = clf_model.predict(X_test_c)

    acc = accuracy_score(y_test_c, clf_preds)
    print(f"Stockout Classifier Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_test_c, clf_preds))

    # ---------------------------------------------------------
    # 4. Save Models and Metadata
    # ---------------------------------------------------------
    joblib.dump(kpi_model, os.path.join(output_dir, 'kpi_model.pkl'))
    joblib.dump(clf_model, os.path.join(output_dir, 'stockout_classifier.pkl'))

    metadata = {
        'kpi_features': kpi_features,
        'clf_features': clf_features,
        'kpi_r2': round(float(r2), 4),
        'kpi_mae': round(float(mae), 4),
        'stockout_accuracy': round(float(acc), 4),
        'categories': sorted(df['category'].unique().tolist()),
        'zones': sorted(df['zone'].unique().tolist())
    }
    with open(os.path.join(output_dir, 'model_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    # Save enriched dataset with calculated fields for quick app loading
    df.to_csv(os.path.join(output_dir, 'warehouse_inventory_enriched.csv'), index=False)
    print(f"\nAll models and metadata successfully saved to '{output_dir}/'")

if __name__ == '__main__':
    train_warehouse_models()
