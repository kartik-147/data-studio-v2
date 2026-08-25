# 📊 DATA STUDIO v2

> **A modern, deterministic data exploration, automated analytics, and data quality profiling platform built with Python, Streamlit, and Firebase Firestore.**

Inspired by the design aesthetics and engineering rigor of **Linear**, **Stripe**, **Mixpanel**, and **Notion**, Data Studio v2 empowers data scientists, business analysts, and engineering teams to upload, profile, audit, and visualize datasets instantly with zero manual boilerplate.

---

## 💡 Executive Summary

### 1. What is this Web App?
**Data Studio v2** is a cloud-ready, self-service data intelligence web application that transforms raw, unorganized tabular files (CSV, Excel) into structured analytical workspaces, automated executive dashboards, and transparent data quality scorecards in milliseconds.

### 2. Why Did We Make It?
- **The Problem**: Traditional data analysis requires repetitive, manual Python/Pandas boilerplate (writing missing value checks, data type casting, summary statistics, correlation heatmaps) or expensive, heavyweight enterprise BI tools (Tableau, PowerBI) that require complex setup and data pipeline configurations.
- **The Solution**: Data Studio v2 provides a unified, deterministic environment where uploading a single file instantly triggers automated schema profiling, data health scoring across 5 dimensions, dynamic executive visualizations, and privacy-first cloud activity auditing.

### 3. How is It Useful For Us?
- ⚡ **10x Faster Exploratory Data Analysis (EDA)**: Eliminates hours of writing repetitive Pandas profiling scripts.
- 🛡️ **Deterministic Data Quality Audits**: Surfaces missing rates, duplicates, constant columns, mixed data types, out-of-bound values, and outliers before bad data corrupts production pipelines.
- 🔒 **Privacy-First & Secure**: User datasets stay strictly in ephemeral application memory; cloud databases (Firebase Firestore) record only high-level structural metadata (schema, dimensions, data types), never raw records.
- 📈 **Executive-Ready Dashboards**: Automatically detects primary KPIs, feature distributions, and correlation matrices formatted in clean, theme-adaptive vector graphics.
- 👥 **Enterprise Admin Visibility**: Provides application owners with a dedicated, protected analytics dashboard to track platform usage, active users, and ingestion volumes in real time.

### 4. What Does This Web App Do?
1. **Multi-Format Ingestion**: Parses CSV and multi-sheet Excel files with multi-encoding fallback (`utf-8`, `latin1`, `cp1252`).
2. **Semantic Type Classification**: Distinguishes between **Numeric**, **Categorical**, **Date/Time**, **Text**, and **Boolean** columns while preserving high-cardinality IDs.
3. **Dynamic Dashboard Generation**: Computes primary KPIs, 2x2 visual insight grids, and Pearson correlation matrices on the fly.
4. **Deterministic 0–100 Data Quality Scoring**: Evaluates dataset health across Completeness, Uniqueness, Consistency, Validity, and Outlier Health.
5. **Secure Authentication**: Bcrypt 12-round salted password hashing, duplicate prevention, and one-click guest demo sandboxing.
6. **Cloud Activity Logging**: Automatically tracks logins, sessions, and dataset upload metadata to Google Cloud Firestore with zero duplicate events.
7. **Protected Admin Analytics**: Real-time administrative portal with date filters, user directories, upload logs, and schema frequency distributions.

---

## 🛠️ Technology Stack

| Technology | Role & Purpose |
| :--- | :--- |
| **Python 3.10+** | Core computational runtime and statistical backend |
| **Streamlit (v1.35+)** | Reactive single-page application framework and UI routing |
| **Firebase Admin SDK & Firestore** | Cloud activity logging, user tracking, and administrative analytics |
| **Pandas (v2.0+) & NumPy (v1.24+)** | High-performance tabular data manipulation, memory profiling, and vector calculations |
| **Plotly (v5.20+)** | Interactive, theme-adaptive, high-contrast vector charts and heatmaps |
| **OpenPyXL (v3.1+) & xlrd (v1.2+)** | Multi-sheet Excel workbook parsing and sheet inspection |
| **Bcrypt (v4.1+)** | 12-round salted password hashing and timing-attack-safe credential verification |
| **Vanilla CSS3** | Custom design system, typography hierarchy, and universal Light/Dark mode tokens |

---

## 🏛️ System Architecture

Data Studio v2 follows a strict layered architecture with clear separation of concerns between presentation, computational engines, cloud logging, session state, and persistence layers.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               DATA STUDIO APPLICATION SHELL                            │
│                                          (app.py)                                      │
└───────────────────────────┬────────────────────────────────┬───────────────────────────┘
                            │                                │
                 [ Unauthenticated ]                  [ Authenticated ]
                            ▼                                │
                 ┌─────────────────────┐                     │
                 │ modules/login_page  │                     │
                 │ - Email / Password  │                     │
                 │ - Registration      │                     │
                 │ - Guest Demo Mode   │                     │
                 └──────────┬──────────┘                     │
                            │                                │
                            ▼                                ▼
                 ┌─────────────────────┐          ┌─────────────────────┐
                 │   modules/auth.py   │          │ modules/ui_component│
                 │ - bcrypt (12 rounds)│          │ - Sidebar Navigator │
                 │ - Session Guard     │          │ - Theme Switcher    │
                 │ - Login Tracker     │          │ - User Identity Bar │
                 └──────────┬──────────┘          └──────────┬──────────┘
                            │                                │
                            ▼                                ▼
        ┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
        │        AUTHENTICATION PERSISTENCE    │  │           ACTIVE WORKSPACE           │
        │                                      │  │                                      │
        │ - user_data/users_db.json            │  │ 1. Overview       (overview.py)      │
        │ - modules/user_storage.py            │  │ 2. Dashboard      (dashboard.py)     │
        └──────────────────┬───────────────────┘  │ 3. Dataset        (data_profiler.py) │
                           │                      │ 4. Data Quality   (data_quality.py)  │
                           │                      │ 5. Settings       (settings.py)      │
                           │                      │ 6. Admin Portal   (admin_analytic.py)│
                           │                      └──────────────────┬───────────────────┘
                           ▼                                         │
        ┌──────────────────────────────────────┐                     │
        │       CLOUD ACTIVITY & ANALYTICS     │                     │
        │     (modules/firebase_service.py)    │                     │
        │                                      │                     │
        │ ├── users Collection                 │                     ▼
        │ ├── login_logs Collection            │  ┌──────────────────────────────────────┐
        │ └── dataset_uploads (Metadata Only)  │  │         COMPUTATIONAL ENGINES        │
        └──────────────────┬───────────────────┘  │                                      │
                           ▲                      │ - data_loader.py (ETL & Classifier)  │
                           │                      │ - dashboard_engine.py (KPIs & Visual)│
                           └──────────────────────┤ - data_quality_engine.py (5-Dim QA)  │
                               (Guarded Logging)  └──────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
data-studio-v2/
│
├── app.py                      # Application entry point, dynamic sidebar, & route dispatcher
├── requirements.txt            # Project dependencies (pinned for stability)
├── README.md                   # Complete architectural & platform documentation
├── .gitignore                  # Git exclusion rules (credentials & secrets protected)
│
├── modules/                    # Modular UI views and computational processing engines
│   ├── __init__.py             # Package descriptor
│   ├── config.py               # Canonical routes, metadata models & session state defaults
│   ├── firebase_service.py     # Firebase Admin SDK singleton, logging & admin query engine
│   ├── user_storage.py         # Local user repository interface with atomic writes
│   ├── auth.py                 # Bcrypt password hashing, session guards & user auth
│   ├── login_page.py           # Full-screen login, account registration & guest demo interface
│   ├── data_loader.py          # CSV/XLSX multi-sheet parsing & semantic type classifier
│   ├── data_profiler.py        # Dataset Workspace with overview, preview, schema, & types
│   ├── dashboard_engine.py     # Analytical column prioritization & Plotly chart generators
│   ├── dashboard.py            # Automatic dynamic executive dashboard view
│   ├── data_quality_engine.py  # Deterministic 5-dimension quality auditor & scoring engine
│   ├── data_quality.py         # Quality workspace with hero score & 6 diagnostic tabs
│   ├── admin_analytics.py      # Protected admin dashboard for user activity & upload telemetry
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
│       └── style.css           # Design tokens, typography hierarchy, & dark/light themes
│
├── sample_data/
│   ├── saas_sales_data.csv     # Sample SaaS recurring revenue & retention dataset
│   └── ecommerce_orders.csv    # Sample global e-commerce retail transaction dataset
│
├── user_data/                  # Local user database repository (git-ignored)
│   └── users_db.json
│
├── scratch/                    # Automated unit and integration test suites
│   ├── test_module2.py         # Ingestion and schema profiling test suite
│   ├── test_module3.py         # Dashboard and KPI engine test suite
│   ├── test_module4.py         # Data quality scoring & audit test suite
│   ├── test_module5.py         # Authentication and bcrypt security test suite
│   └── test_firebase_analytics.py # Cloud tracking, deduplication, & admin auth test suite
│
└── .streamlit/
    ├── config.toml             # Streamlit server and theme configuration
    └── secrets.toml            # (Local development only - git-ignored)
```

---

## 🔍 Detailed Module Explanations

### 🔹 Module 1 — Foundation & Design System
- **Design Tokens**: Standardized CSS variables for surfaces, borders, and typography (`assets/css/style.css`).
- **Lucide Vector Icons**: Lightweight SVG paths embedded directly into HTML with zero external font dependencies.
- **Universal Theme Engine**: Seamless switching between **Dark Mode** (Obsidian/Slate `#0b0f19`) and **Light Mode** (Soft Off-White `#f8fafc`).
- **Standardized UI Components**: Reusable `render_page_header`, `render_section_header`, `render_metric_card`, `render_notification`, and `render_skeleton_loader`.

### 🔹 Module 2 — Dataset Ingestion & Workspace
- **Multi-Encoding Engine**: Robust fallback parser attempting `utf-8`, `latin1`, and `cp1252` encoding.
- **Excel Multi-Sheet Support**: Detects and exposes worksheets in multi-sheet Excel files for targeted loading.
- **Semantic Data Classifier**: Automatically assigns columns into 5 semantic categories:
  - **Numeric**: Continuous metrics, counts, monetary values.
  - **Categorical**: Discrete classes, status flags, regions.
  - **Date/Time**: Temporal timestamps and date strings.
  - **Text**: Free-form textual descriptions and unique identifiers.
  - **Boolean**: Binary flags (`true/false`, `0/1`, `yes/no`, `active/inactive`).
- **4-Tab Exploration Workspace**:
  - `OVERVIEW`: Summary cards, type distribution chips, and dimension breakdown.
  - `PREVIEW`: Scrollable interactive data table with adjustable row preview limits.
  - `COLUMNS`: Column-by-column inventory of completeness, uniqueness, and memory size.
  - `DATA TYPES`: Inferred vs Pandas dtypes and schema type breakdowns.

### 🔹 Module 3 — Automatic Dataset Dashboard
- **Dynamic Executive KPIs**: Identifies the dataset's primary numeric metric (e.g. Total Revenue, Volume) and computes aggregates, medians, and spreads.
- **Visual Insights Grid**: 2x2 layout of automated distributions, categorical breakdown bars, and time-series trends.
- **Correlation Heatmap**: Pearson correlation matrix identifying strong linear relationships between numeric features.
- **Deterministic Factual Insights**: Algorithmic bullet points highlighting dominant categories, high-variability metrics, and data distributions.

### 🔹 Module 4 — Data Quality Audit Engine
- **Deterministic 0–100 Health Score**: Evaluates dataset hygiene across 5 mathematically weighted dimensions:
  1. **Completeness (30%)**: Missing value ratios and empty column penalties.
  2. **Uniqueness (20%)**: Duplicate rows and identical column detection.
  3. **Consistency (20%)**: Constant features (zero variance) and mixed data types.
  4. **Validity (15%)**: Blank whitespace strings, invalid negative numbers, and out-of-range values.
  5. **Outlier Health (15%)**: Interquartile range (IQR) detection on numeric distributions.
- **6 Diagnostic Tabs**: `OVERVIEW`, `MISSING VALUES`, `DUPLICATES`, `DATA CONSISTENCY`, `VALIDITY`, `OUTLIERS`.
- **Read-Only Invariant**: Audits datasets without altering underlying session data.

### 🔹 Module 5 — Authentication & Security
- **Bcrypt Password Security**: 12-round salted bcrypt hashing. Plaintext passwords are never saved.
- **Account Registration & Validation**: Email regex formatting, minimum 8-character password enforcement, and duplicate account prevention.
- **Guest Demo Sandboxing**: Single-click guest access enabling exploration without registration.
- **Session Isolation**: Complete session state purge upon signing out.

### 🔹 Module 6 — Firebase Activity Logging & Admin Analytics
- **Cloud Telemetry**: Records user logins and dataset upload events to **Firebase Firestore**.
- **Privacy-First Metadata Logging**: Strictly records dataset dimensions, column names, detected data types, missing percentages, and file sizes. **Zero row data or cell contents are ever sent to Firestore.**
- **Session Deduplication Guards**: Dedicated session state flags (`login_event_logged`, `logged_dataset_signature`) prevent duplicate Firestore writes during normal Streamlit reruns.
- **Server-Side Admin Authorization**: Protects the **Admin Analytics** view by validating the active user's email against the configured admin secret.
- **Executive Admin Portal**:
  - Top 6 KPIs: Registered Users, Total Logins, Total Uploads, Active Users, Today's Logins, Today's Uploads.
  - Interactive Format Distribution & Ingestion Averages charts.
  - 4 Audit Tables: `RECENT ACTIVITY` (chronological feed), `USER DIRECTORY`, `DATASET UPLOADS`, and `SCHEMA ANALYTICS`.

---

## 🔒 Configuration & Deployment

### Streamlit Community Cloud Configuration

Configure your secrets in the Streamlit Cloud Dashboard (**App Settings &rarr; Secrets**) or locally in `.streamlit/secrets.toml`:

```toml
[admin]
email = "admin@example.com"

[firebase]
type = "service_account"
project_id = "your-firebase-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxx@your-firebase-project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

---

## 🚀 Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/kartik-147/data-studio-v2.git
cd data-studio-v2
```

### 2. Create and Activate Virtual Environment
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

### 4. Run Automated Test Suites
```bash
python scratch/test_module2.py
python scratch/test_module3.py
python scratch/test_module4.py
python scratch/test_module5.py
python scratch/test_firebase_analytics.py
```

### 5. Launch Application
```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## 🔮 Upcoming Roadmap Modules

- [ ] **Module 7 — Data Preparation & Transformation**: Missing value imputation, type casting, outlier removal, and export to CSV/Excel.
- [ ] **Module 8 — Exploratory Data Analysis (EDA)**: Descriptive statistics, skewness, kurtosis, and distribution plots.
- [ ] **Module 9 — Interactive Visualization Builder**: Multi-axis custom chart designer and facet plots.
- [ ] **Module 10 — AI Analyst Assistant**: Natural language querying for automated dataset question answering.
