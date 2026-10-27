# 📦 Enterprise Warehouse Management System (WMS)

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Plotly](https://img.shields.io/badge/Analytics-Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

A production-grade, relational database-driven **Warehouse Management System (WMS)** built with **Python**, **Streamlit**, and **SQLite**. Features real-time inbound stock intake, outbound dispatch fulfillment, storage rack/bin coordinate tracking, automated reorder triggers, and transaction audit ledgers.

---

## 📌 System Workflow & Database Architecture

The application connects to an embedded relational SQLite database (`warehouse.db`) containing seeded representation entries across multiple product categories:

```
                             ┌──────────────────────────────────────┐
                             │       SQLite Database Hub            │
                             │         (warehouse.db)               │
                             └──────────────────┬───────────────────┘
                                                │
         ┌──────────────────────────────────────┴──────────────────────────────────────┐
         ▼                                                                             ▼
┌─────────────────────────────────┐                                           ┌─────────────────────────────────┐
│ 📥 INBOUND DOCK (STOCK INTAKE)  │                                           │ 📤 OUTBOUND DOCK (DISPATCH)     │
├─────────────────────────────────┤                                           ├─────────────────────────────────┤
│ • Supplier PO & Delivery Intake │                                           │ • Customer Order Picking & Pack │
│ • Quality Inspection Checks     │                                           │ • Carrier Logistics & Waybills  │
│ • Zone & Rack Bin Allocation    │                                           │ • Real-time Stock Deduction     │
│ • Immediate Database Restock    │                                           │ • Safety Buffer Alert System    │
│ • Goods Receipt Notes (GRN)     │                                           │ • Goods Dispatch Notes (GDN)    │
└────────────────┬────────────────┘                                           └────────────────┬────────────────┘
                 │                                                                             │
                 └──────────────────────────────┬──────────────────────────────────────────────┘
                                                ▼
                             ┌──────────────────────────────────────┐
                             │       LIVE INVENTORY MASTER          │
                             ├──────────────────────────────────────┤
                             │ • Real-time Active Stock Levels      │
                             │ • Storage Zones A, B, C, and D       │
                             │ • Automated Reorder Alerts           │
                             │ • SKU Edit & Quick Stock Adjustment  │
                             │ • Full Audit Ledgers & CSV Reports   │
                             └──────────────────────────────────────┘
```

---

## ✨ Core Management Features

### 1. 📥 Inbound Stock Intake & Receiving Dock
- **Replenish Existing Catalog SKUs**: Record incoming delivery batches, assign rack bin coordinates (`BIN-A-101`), record supplier PO numbers, inspector approvals, and lot tracking numbers. Immediately increments database stock.
- **Register New Product SKUs**: Onboard brand new items into the database with custom categories, initial quantities, unit valuations, and reorder points.
- **Goods Receipt Notes (GRN)**: Automatically issues official verifiable intake receipts (`GRN-2026-XXXX`).

### 2. 📤 Outbound Stock Dispatch & Order Fulfillment
- **Fulfillment Picking**: Pick items from storage bins, allocate to logistics carriers (DHL, FedEx, Blue Dart, Internal Fleet), and assign destination tracking waybills.
- **Negative Stock Protection**: Database-level validation prevents dispatching quantities exceeding available inventory.
- **Goods Dispatch Notes (GDN)**: Automatically issues official dispatch notes (`GDN-2026-XXXX`).

### 3. 📋 Live Inventory & Master Catalog
- Real-time catalog with full CRUD operations (search, filter, quick stock adjustment, edit reorder thresholds, and CSV export).

### 4. ⚠️ Automated Reorder Alerts
- Live monitor of all items falling below safety reorder thresholds.
- **⚡ 1-Click Expedited Restock**: Instantly generates an emergency intake order to restore inventory safety buffers.

### 5. 🏢 Storage Zones & Facility Layout Master
- Visualizes storage capacity and occupancy across four dedicated facility zones:
  - **Zone A**: Fast-Moving & High Value Bay (Ambient 20°C - 24°C)
  - **Zone B**: Medium Turnover & Automotive Rack (Ambient 18°C - 25°C)
  - **Zone C**: Heavy Bulk & Industrial Storage (Drive-In Racks)
  - **Zone D**: Specialized & Cold Storage (Climate Controlled 2°C - 6°C)

### 6. 📊 Executive Warehouse Dashboard
- Instant valuation across all inventory items, Pareto ABC 80/20 classification, and category breakdown.

### 7. 📜 Transaction Audit Ledgers
- Searchable, immutable history of all Goods Receipt Notes (GRNs) and Goods Dispatch Notes (GDNs) stored in SQLite.

---

## 🛠️ Database Schema

- `inventory`: `item_id`, `item_name`, `category`, `stock_level`, `reorder_point`, `unit_price`, `zone`, `bin_location`, `supplier`, `lead_time_days`, `daily_demand`, `last_restocked`
- `intake_orders`: `grn_number`, `item_id`, `item_name`, `quantity`, `zone`, `bin_location`, `supplier`, `po_number`, `batch_no`, `inspector`, `condition`, `created_at`
- `dispatch_orders`: `gdn_number`, `item_id`, `item_name`, `quantity`, `destination`, `carrier`, `waybill`, `dispatcher`, `priority`, `created_at`
- `zones`: `zone_code`, `zone_name`, `zone_type`, `total_bays`, `temperature_control`

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
streamlit run app.py
```
*(The SQLite database `warehouse.db` is initialized and seeded with representative fake entries automatically on first launch).*

Open **[http://localhost:8501](http://localhost:8501)** in your browser!

---

## 📜 License
Distributed under the **MIT License**. Developed by **Yug Meshram**.
