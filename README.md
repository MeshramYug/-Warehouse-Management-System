# Warehouse Management System

An interactive inventory control, stockout risk prediction, and warehouse operations management platform built with Python, Scikit-Learn, Plotly, and Streamlit.

---

## 📌 Project Overview

The **Warehouse Management System** provides warehouse managers, supply chain planners, and inventory controllers with data-driven tools to maintain optimal stock levels, prevent inventory stockouts, minimize holding expenses, and optimize warehouse storage zones.

The application leverages predictive machine learning models trained on realistic warehouse logistics data, achieving **99.2% R² accuracy** on warehouse efficiency scoring and **97.7% classification accuracy** on stockout risk prediction.

---

## ✨ Key Features

- **Warehouse Overview Dashboard**: Live inventory valuation, category distributions (Pharma, Automotive, Electronics, Groceries, Apparel), storage zone throughput, and Pareto ABC classification.
- **Predictive Stockout & Restock Urgency**: Machine learning classifier predicting whether an SKU is at risk of stockout before lead time delivery, combined with real-time **Economic Order Quantity (EOQ)** and safety stock recommendations.
- **Warehouse KPI & Efficiency Simulator**: Interactive "What-If" simulator powered by a Gradient Boosting Regressor ($R^2 = 0.992$) to evaluate how adjustments in turnover ratio, picking layout efficiency, and holding costs impact operational performance.
- **Interactive Inventory Catalog**: Filterable table with multi-select category, zone, and risk filters, SKU search, and CSV export.
- **Model Architecture & Transparency**: Feature importance plots and evaluation metrics for model explainability.

---

## 🧠 Machine Learning Models

| Model | Algorithm | Target Variable | Performance |
| :--- | :--- | :--- | :--- |
| **Warehouse KPI Regressor** | Gradient Boosting Regressor | `KPI_score` (0.0 – 1.0) | **$R^2 = 0.992$**, MAE = 0.008 |
| **Stockout Risk Classifier** | Random Forest Classifier | `stockout_risk` (Safe vs. Critical) | **Accuracy = 97.66%**, F1 = 0.977 |

### Operations Research Formulations
- **Economic Order Quantity (EOQ):**
  $$\text{EOQ} = \sqrt{\frac{2 \cdot D \cdot S}{H}}$$
  *(where $D$ is annual demand, $S$ is order handling cost, and $H$ is annual unit holding cost)*
- **Safety Stock ($SS$):**
  $$SS = Z \cdot \sigma_d \cdot \sqrt{L}$$
  *(where $Z=1.65$ for 95% service level, $\sigma_d$ is demand standard deviation, and $L$ is lead time in days)*

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+ (tested on Python 3.11)
- `pip` package manager

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone <your-repository-url>
cd "Arya rai"
pip install -r requirements.txt
```

### 3. Model Training (Optional)
The pre-trained models are already provided in `models/`. To retrain the models from the dataset:
```bash
python train_model.py
```

### 4. Running the Application
Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```
The app will open automatically in your browser at `http://localhost:8501`.

---

## 🌐 Streamlit Cloud Deployment Guide

1. Create a new GitHub repository and push the contents of this folder (`Arya rai/`).
2. Log into [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **"New app"**.
4. Select your GitHub repository, set branch to `main`, and set **Main file path** to `app.py`.
5. Click **"Deploy!"**.

---

## 📁 Repository Structure

```text
├── app.py                      # Main interactive Streamlit application
├── train_model.py              # Machine learning training & evaluation script
├── requirements.txt            # Python dependencies for deployment
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
├── logistics_dataset.csv       # Raw warehouse logistics dataset
└── models/                     # Saved model artifacts
    ├── kpi_model.pkl           # Gradient Boosting Regressor for KPI prediction
    ├── stockout_classifier.pkl # Random Forest Classifier for stockout risk
    ├── model_metadata.json     # Feature list & model performance metrics
    └── warehouse_inventory_enriched.csv # Processed dataset with calculated fields
```
