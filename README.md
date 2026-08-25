# 📊 DATA STUDIO v2

> **A modern, deterministic data exploration, automated analytics, and data quality profiling platform built with Python and Streamlit.**

Inspired by the design aesthetics and functionality of **Mixpanel**, **Linear**, **Tableau**, and **Notion**, Data Studio v2 empowers data scientists, analysts, and business teams to upload, profile, audit, and visualize datasets instantly with zero manual boilerplate.

---

## 🛠️ Technology Stack

| Technology | Role & Purpose |
| :--- | :--- |
| **Python 3.10+** | Core programming language and analytical runtime |
| **Streamlit (v1.35+)** | Reactive single-page application framework and UI routing |
| **Pandas (v2.0+) & NumPy (v1.24+)** | High-performance tabular data processing, type inference, and statistical calculation |
| **Plotly (v5.20+)** | Responsive, interactive, theme-adaptive vector visualizations |
| **OpenPyXL (v3.1+) & xlrd (v1.2+)** | Multi-sheet Excel workbook inspection and ingestion |
| **Bcrypt (v4.1+)** | 12-round salted password hashing and timing-attack-safe credential verification |
| **Vanilla CSS3** | Custom design system, typography, glassmorphic cards, and dark/light theme tokens |

---

## 🏛️ Platform Architecture

Data Studio v2 is architected with strict separation of concerns between UI presentation, statistical computation engines, session state management, and persistence layers.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA STUDIO APPLICATION SHELL                    │
│                                (app.py)                                 │
└───────────────────┬─────────────────────────────────┬───────────────────┘
                    │                                 │
         [ Unauthenticated ]                   [ Authenticated ]
                    ▼                                 ▼
         ┌─────────────────────┐           ┌─────────────────────┐
         │ modules/login_page  │           │ modules/ui_component│
         │ - Email / Password  │           │ - Sidebar Navigator │
         │ - Registration      │           │ - Theme Switcher    │
         │ - Guest Demo Mode   │           │ - User Identity Bar │
         └──────────┬──────────┘           └──────────┬──────────┘
                    │                                 │
                    ▼                                 ▼
         ┌─────────────────────┐           ┌──────────────────────────────────────────────┐
         │   modules/auth.py   │           │               ACTIVE WORKSPACE               │
         │ - bcrypt hashing    │           │                                              │
         │ - Session lifecycle │           │ 1. Overview       (modules/overview.py)      │
         └──────────┬──────────┘           │ 2. Dashboard      (modules/dashboard.py)     │
                    ▼                      │ 3. Dataset        (modules/data_profiler.py) │
         ┌─────────────────────┐           │ 4. Data Quality   (modules/data_quality.py)  │
         │modules/user_storage │           │ 5. Settings       (modules/settings.py)      │
         │ (user_data/db.json) │           └──────────────────────┬───────────────────────┘
         └─────────────────────┘                                  │
                                                                  ▼
                                           ┌──────────────────────────────────────────────┐
                                           │             ANALYTICAL ENGINES               │
                                           │                                              │
                                           │ - data_loader.py          (Multi-format ETL) │
                                           │ - dashboard_engine.py     (KPIs & Insights)  │
                                           │ - data_quality_engine.py  (5-Dim QA Scoring) │
                                           └──────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
data-studio-v2/
│
├── app.py                      # Application entry point, dynamic reload, & route protection
├── requirements.txt            # Project dependencies
├── README.md                   # Platform documentation
├── .gitignore                  # Git exclusion rules
│
├── modules/                    # Modular UI and computational engines
│   ├── __init__.py             # Package descriptor
│   ├── config.py               # Canonical routes, metadata & session state defaults
│   ├── user_storage.py         # Decoupled user database interface (JSON / future DB)
│   ├── auth.py                 # Bcrypt password hashing, validation & session manager
│   ├── login_page.py           # Full-screen professional authentication & guest view
│   ├── data_loader.py          # CSV/XLSX multi-sheet parsing & semantic type classifier
│   ├── data_profiler.py        # Dataset Workspace with overview, preview, schema, & types
│   ├── dashboard_engine.py     # Analytical column prioritization & Plotly chart generators
│   ├── dashboard.py            # Automatic dynamic executive dashboard view
│   ├── data_quality_engine.py  # Deterministic 5-dimension quality auditor & scoring engine
│   ├── data_quality.py         # Quality workspace with hero score & 6 diagnostic tabs
│   ├── overview.py             # Platform welcome hub & dataset upload landing view
│   ├── data_preparation.py     # Data cleaning & transformation view (Roadmap)
│   ├── eda_tools.py            # Exploratory Data Analysis & statistics view (Roadmap)
│   ├── visualization.py        # Interactive visualization builder (Roadmap)
│   ├── ai_analyst.py           # Natural language data assistant view (Roadmap)
│   ├── ui_components.py        # Reusable design system cards, headers, & CSS injector
│   └── settings.py             # Workspace preferences & theme toggles
│
├── assets/
│   └── css/
│       └── style.css           # Design tokens, Streamlit component bindings & themes
│
├── sample_data/
│   ├── saas_sales_data.csv     # Sample SaaS recurring revenue & retention dataset
│   └── ecommerce_orders.csv    # Sample global e-commerce retail transaction dataset
│
├── user_data/                  # Local user database repository (git-ignored)
│   └── users_db.json
│
├── scratch/                    # Automated unit and integration test suites
│   ├── test_module2.py         # Loader and profiling tests
│   ├── test_module3.py         # Dashboard and analytical engine tests
│   ├── test_module4.py         # Data quality scoring & audit tests
│   └── test_module5.py         # Authentication and bcrypt security tests
│
└── .streamlit/
    └── config.toml             # Streamlit server and theme configuration
```

---

## ✨ Implemented Modules & Features

### 🔹 Module 1 — Foundation & Design System
- **Design System Tokens:** Custom CSS with CSS variables (`--bg-primary`, `--surface`, `--accent`, `--border`), Inter typography, and crisp border geometry.
- **Lucide SVG Icon Engine:** Pure vector paths embedded inline with zero external icon font dependencies or emojis.
- **Unified Component Library:** Standardized metric cards, section headers, notifications (`info`, `success`, `warning`, `error`), and shimmer skeleton loaders.

### 🔹 Module 2 — Dataset Upload & Workspace
- **Multi-Format Ingestion:** Robust CSV, XLSX, and XLS ingestion with fallback encoding detection (`utf-8`, `latin1`, `cp1252`).
- **Multi-Sheet Excel Support:** Interactive sheet selector allowing users to inspect and choose specific sheets from Excel workbooks.
- **Semantic Type Classification:** Automatic column categorization into **Numeric**, **Categorical**, **Date/Time**, **Text**, and **Boolean** with smart ID column preservation.
- **Active Dataset Workspace:** 4-tab exploration workspace:
  - `OVERVIEW`: Semantic type distribution cards and dataset health overview.
  - `PREVIEW`: Interactive dataset explorer with configurable row previews.
  - `COLUMNS`: Column schema table with completeness, uniqueness, and memory footprint.
  - `DATA TYPES`: Complete type breakdown and casting suggestions.

### 🔹 Module 3 — Automatic Dataset Dashboard
- **Dynamic Executive KPIs:** Prioritizes high-variance numeric metrics (e.g. Total Revenue, Average Profit) and calculates medians, spreads, and dataset size indicators.
- **Visual Insights Grid:** 2x2 grid of automated distributions, categorical breakdown bars, and time-series trends.
- **Feature Correlation Snapshot:** High-contrast Pearson correlation matrix heatmap discovering key inter-feature linear relationships.
- **Deterministic Factual Insights:** Factual, algorithmic bullet points highlighting dominant segments, high-variability distributions, and temporal ranges.

### 🔹 Module 4 — Data Quality Audit Engine
- **Deterministic 0–100 Scoring:** Transparent, deterministic composite health score across 5 weighted dimensions:
  - **Completeness (30%)**: Missing cell ratios and empty column penalties.
  - **Uniqueness (20%)**: Duplicate row count and identical column pair detection.
  - **Consistency (20%)**: Constant features (zero variance) and mixed data type anomalies.
  - **Validity (15%)**: Whitespace strings, unexpected negative values, infinite floats, and out-of-bound percentages.
  - **Outlier Health (15%)**: Interquartile range (IQR) detection on numeric features ($Q_1 - 1.5\text{IQR}, Q_3 + 1.5\text{IQR}$).
- **6 Diagnostic Workspace Tabs:** `OVERVIEW`, `MISSING VALUES`, `DUPLICATES`, `DATA CONSISTENCY`, `VALIDITY`, `OUTLIERS`.
- **Read-Only Guarantee:** Audits and diagnoses quality defects without modifying or mutating working datasets.

### 🔹 Module 5 — Authentication & Security
- **Email & Password Authentication:** Validates email formatting, requires $\ge 8$ character passwords, and rejects invalid credentials with generic non-revealing error messages.
- **Account Registration:** Automatic duplicate prevention, password confirmation matching, and immediate login dispatch.
- **Bcrypt Security:** 12-round salted bcrypt password hashing. Plaintext passwords are never stored in memory or on disk.
- **Session Lifecycle & Logout:** Session state isolation, route-level protection, and complete dataset state purge upon signing out.
- **Guest Demo Mode:** Ephemeral sandbox session allowing users to test sample datasets without creating an account.

### 🔹 Universal Light & Dark Theming
- Native support for both **Dark Mode** and **Light Mode** across every page, input, tab, data table, and Plotly visualization.
- Instant theme toggle available in the sidebar, on the login screen, and in the Settings page.

---

## 🔮 Roadmap / Upcoming Modules

- [ ] **Module 6 — Data Preparation & Transformation** (Missing value imputation, type casting, outlier removal, column renaming, and CSV/Excel export).
- [ ] **Module 7 — Exploratory Data Analysis (EDA)** (Descriptive statistics, skewness, kurtosis, violin plots, and group-by aggregations).
- [ ] **Module 8 — Interactive Visualization Builder** (Custom multi-axis chart creator, color encodings, and facet plots).
- [ ] **Module 9 — AI Analyst Assistant** (Natural language query interface for conversational dataset exploration).

---

## 🚀 Getting Started

### 1. Clone Repository
```bash
git clone https://github.com/kartik-147/data-studio-v2.git
cd data-studio-v2
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch Data Studio
```bash
streamlit run app.py
```

Open your browser and navigate to `http://localhost:8501`.
