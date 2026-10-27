# 📦 Enterprise Warehouse Management System (WMS)

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Plotly](https://img.shields.io/badge/Analytics-Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

An enterprise-grade, end-to-end **Warehouse Management System (WMS)** featuring live inbound stock intake, outbound dispatch fulfillment, rack/bin coordinate tracking, automated reorder triggers, and machine learning operational analytics built with Python, Scikit-Learn, Plotly, and Streamlit.

---

## 📌 System Workflow & Management Architecture

```
                             ┌──────────────────────────────────────┐
                             │    Enterprise WMS Operations Hub     │
                             └──────────────────┬───────────────────┘
                                                │
         ┌──────────────────────────────────────┴──────────────────────────────────────┐
         ▼                                                                             ▼
┌─────────────────────────────────┐                                           ┌─────────────────────────────────┐
│ 📥 INBOUND DOCK (STOCK INTAKE)  │                                           │ 📤 OUTBOUND DOCK (DISPATCH)     │
├─────────────────────────────────┤                                           ├─────────────────────────────────┤
│ • Supplier PO & Delivery Intake │                                           │ • Customer Order Picking & Pack │
│ • Physical Quality Inspection   │                                           │ • Carrier Logistics & Waybills  │
│ • Zone & Rack Bin Allocation    │                                           │ • Immediate Stock Level Deduct  │
│ • Instant Live Inventory Update │                                           │ • Below-Reorder Warning System  │
│ • Goods Receipt Notes (GRN)     │                                           │ • Goods Dispatch Notes (GDN)    │
└────────────────┬────────────────┘                                           └────────────────┬────────────────┘
                 │                                                                             │
                 └──────────────────────────────┬──────────────────────────────────────────────┘
                                                ▼
                             ┌──────────────────────────────────────┐
                             │     LIVE INVENTORY & BIN MASTER      │
                             ├──────────────────────────────────────┤
                             │ • Real-time Active Stock Levels      │
                             │ • Storage Zones A, B, C, and D       │
                             │ • Days of Supply & Critical Alerts   │
                             │ • Automated EOQ Smart Replenishment  │
                             │ • Full Audit Ledgers & CSV Reports   │
                             └──────────────────────────────────────┘
```

---

## ✨ Core Management Modules

### 1. 📥 Inbound Stock Intake & Receiving Dock
- **Replenish Existing SKUs**: Select an existing catalog item to record newly arrived shipments. Immediately updates warehouse stock, recalculates days of supply, clears stockout risk, and logs an official **Goods Receipt Note (GRN)**.
- **Register & Intake Brand New SKUs**: Receive new items into the catalog with customizable category, initial stock, unit valuation, storage zone, and reorder thresholds.
- **Receiving Quality Inspection**: Track inspector approvals, batch/lot tracking codes, and supplier PO numbers.

### 2. 📤 Outbound Stock Dispatch & Fulfillment
- **Order Picking & Dispatch**: Select items, verify physical available inventory, and process outbound fulfillment orders with destination tracking and shipping carrier waybills.
- **Stock Guard Protection**: Prevents negative inventory picking and instantly warns operators when stock drops below safety reorder thresholds.
- **Official Goods Dispatch Note (GDN)**: Automatically generates printable dispatch notes with audit timestamps.

### 3. 📋 Live Inventory & Bin Master
- Searchable and filterable master table across Categories, Zones (A, B, C, D), and Stockout Status.
- Real-time days-of-supply tracking and instantaneous CSV export for enterprise accounting.

### 4. ⚠️ Automated Reorder & Stockout Alerts
- Real-time queue of all critical inventory items operating below safety stock.
- **⚡ 1-Click Expedited Restock**: Instantly generates an automated intake for the mathematically recommended **Economic Order Quantity (EOQ)**.

### 5. 🎯 Warehouse KPI & Efficiency Optimizer
- Interactive simulation powered by a Gradient Boosting Regressor ($R^2 = 0.992$) to model how picking speeds, rack layouts, and turnover rates impact facility health scores.

### 6. 📜 Inbound & Outbound Audit Ledgers
- Searchable ledgers for both **Goods Receipt Notes (GRNs)** and **Goods Dispatch Notes (GDNs)** with exportable CSV reports for enterprise audits.

---

## 🧠 Operations Research & ML Specifications

| Model / Formulation | Algorithm / Formula | Target Objective | Accuracy / Output |
| :--- | :--- | :--- | :---: |
| **Warehouse KPI Regressor** | Gradient Boosting Regressor | `KPI_score` (Facility Health) | **$R^2 = 0.992$**, MAE = 0.008 |
| **Stockout Risk Classifier** | Random Forest Classifier | `stockout_risk` (Safe vs. Critical) | **97.66% Accuracy**, F1 = 0.977 |
| **Economic Order Quantity (EOQ)** | $\text{EOQ} = \sqrt{\frac{2 \cdot D \cdot S}{H}}$ | Optimal Restock Batch Size | Minimizes total ordering + holding cost |
| **Safety Stock ($SS$)** | $SS = Z \cdot \sigma_d \cdot \sqrt{L}$ | Buffer Reserve Calculation | Protects against demand variability |

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Retrain Models
```bash
python train_model.py
```

### 3. Launch the Warehouse Management System
```bash
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser!

---

## 📜 License
Distributed under the **MIT License**. Developed by **Yug Meshram**.
