# DATA STUDIO — AI DATA ANALYST

A web-based data analytics platform built with Python, Streamlit, Pandas, NumPy, and Plotly. Designed with aesthetics inspired by Mixpanel, Linear, Tableau, and Notion.

---

## 🚀 Features (Module 1 — Foundation)

- **Application Shell & Design System:** Modern UI with custom CSS tokens, Inter typography, Lucide SVG icons, subtle glassmorphism cards, and responsive data density.
- **Dual Theme Engine:** Native support for both **Dark Mode** (default) and **Light Mode**.
- **Dataset-Aware Page Routing:** Canonical navigation across core modules:
  1. `Overview` — Welcome landing screen, dataset upload hub, and sample data loaders.
  2. `Dashboard` — Dynamic KPIs, automatic insights, and adaptive visualization.
  3. `Dataset` — Schema detection, column semantic classification (Numeric, Categorical, Date/Time, Text, Boolean), and data inspector.
  4. `Data Quality` — Data health score (0-100), missing value analysis, duplicate row detection.
  5. `Data Preparation` — Clean, drop, transform, and export tools.
  6. `EDA` — Descriptive statistics, skewness, kurtosis, and correlation explorer.
  7. `Visualization` — Multi-dimensional Plotly chart builder.
  8. `AI Analyst` — Conversational data question-answering assistant.
  9. `Settings` — Session preferences, theme toggles, and memory cleanup.
- **Empty Dataset Resilience:** Helpful, polished empty states on every page with one-click sample dataset loaders (`SaaS Sales & Revenue`, `E-Commerce Global Orders`).
- **Session Identity:** Guest demo mode with bcrypt password hashing foundation ready for authentication.

---

## 📁 Architecture & Project Structure

```
data-studio/
│
├── app.py                      # Main Streamlit application entry point & router
├── requirements.txt            # Project dependencies
├── README.md                   # Documentation & setup guide
├── .gitignore                  # Git ignore rules
│
├── modules/                    # Clean modular business logic & UI layers
│   ├── __init__.py             # Package init
│   ├── config.py               # Constants, navigation routes & session state manager
│   ├── auth.py                 # Authentication architecture & bcrypt helpers
│   ├── data_loader.py          # CSV/Excel parsing & sample dataset loaders
│   ├── data_profiler.py        # Column semantic classifier & quality scoring
│   ├── overview.py             # Landing welcome & upload hero workspace view
│   ├── dashboard.py            # Automatic analytical dashboard view
│   ├── data_quality.py         # Data quality audit & health reports
│   ├── data_preparation.py     # Data cleaning & transformation view
│   ├── eda_tools.py            # Exploratory Data Analysis & stats view
│   ├── visualization.py        # Interactive Plotly chart builder
│   ├── ai_analyst.py           # AI Analyst conversational interface
│   ├── ui_components.py        # Reusable design system UI components
│   └── settings.py             # Workspace preferences & theme toggles
│
├── assets/
│   └── css/
│       └── style.css           # Design tokens, dark/light theme CSS
│
├── .streamlit/
│   └── config.toml             # Streamlit server and theme configuration
│
└── sample_data/
    ├── saas_sales_data.csv     # Sample SaaS recurring revenue & churn dataset
    └── ecommerce_orders.csv    # Sample global e-commerce retail dataset
```

---

## 💻 How to Run the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
streamlit run app.py
```

### 3. Open in Browser
The application will be available at `http://localhost:8501`.
