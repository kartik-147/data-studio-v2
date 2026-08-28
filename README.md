# 📊 DATA STUDIO v2

> **A modern, deterministic data exploration, automated analytics, visualization studio, and data quality intelligence platform built with Python, Streamlit, Plotly, and Firebase Firestore.**

Inspired by the design aesthetics and engineering rigor of **Linear**, **Stripe**, **Mixpanel**, and **Notion**, Data Studio v2 empowers data scientists, business analysts, and engineering teams to ingest, profile, clean, analyze, visualize, and ask questions of tabular datasets in real-time with zero manual boilerplate.

---

## 💡 Executive Summary

### 1. What is Data Studio v2?
**Data Studio v2** is an enterprise-grade, cloud-ready data analytics web application that transforms raw, messy tabular files (CSV, Excel) into structured analytical workspaces, automated executive dashboards, 25-chart BI visualization suites, deterministic quality scorecards, and AI-powered natural language insights in milliseconds.

### 2. Why Was It Built?
- **The Problem**: Traditional data workflows require repetitive, manual Python/Pandas scripts (missing value checks, type casting, outlier detection, distribution plots, correlation heatmaps) or cumbersome, heavyweight enterprise BI tools (Tableau, PowerBI) that require extensive infrastructure setup and data pipeline engineering.
- **The Solution**: Data Studio v2 provides a unified, deterministic environment where uploading a single file instantly unlocks automatic schema profiling, 5-dimension health audits, 25 interactive chart types, full ETL preparation with history rollback, multi-turn AI data chat, and privacy-first cloud telemetry.

### 3. Key Value & Benefits
- ⚡ **10x Faster Exploratory Data Analysis (EDA)**: Eliminates hours of writing repetitive Pandas profiling scripts.
- 🛡️ **Deterministic 0–100 Data Quality Scoring**: Evaluates dataset health across Completeness, Uniqueness, Consistency, Validity, and Outlier Health.
- 🎨 **Unified 25-Chart Visualization Studio**: Interactive 2-column BI studio with instant customization, facets, color palettes, and PNG/SVG/HTML vector exports.
- 🧹 **Interactive Data Preparation & Cleaning**: 1-click missing value imputation, outlier handling, type conversions, column derivation, and instant rollback.
- 🤖 **Multilingual AI Analyst**: Multi-turn data conversation powered by Google Gemini (2.0 Flash / 1.5 Flash / 1.5 Pro) or OpenAI with a built-in zero-key mathematical NLP query engine.
- 🔒 **Privacy-First & Secure**: User datasets stay strictly in ephemeral memory; cloud databases (Firebase Firestore) record only high-level structural metadata, never raw records.
- 👥 **Enterprise Admin Visibility**: Protected administrative portal with date filters, user directories, upload logs, and schema frequency telemetry in real time.

---

## 🛠️ Technology Stack

| Technology | Role & Purpose |
| :--- | :--- |
| **Python 3.10+** | Core computational runtime, statistical calculation engine, and backend logic |
| **Streamlit (v1.35+)** | Reactive single-page web framework, component tree, and dynamic routing |
| **Pandas (v2.0+) & NumPy (v1.24+)** | High-performance tabular manipulation, memory profiling, and vector calculations |
| **Plotly (v5.20+)** | Interactive, theme-adaptive, high-contrast vector charts, heatmaps, and 3D plots |
| **SciPy (v1.12+) & Statsmodels** | Distribution testing, Shapiro-Wilk/D'Agostino normality audits, and regression modeling |
| **Google Gemini API & OpenAI API** | Multilingual generative AI reasoning, automated insights, and narrative storytelling |
| **Firebase Admin SDK & Firestore** | Cloud activity logging, user tracking, and administrative telemetry |
| **OpenPyXL (v3.1+) & xlrd (v1.2+)** | Multi-sheet Excel workbook parsing and sheet inspection |
| **Bcrypt (v4.1+)** | 12-round salted password hashing and timing-attack-safe credential verification |
| **Vanilla CSS3** | Custom design system, BaseWeb UI popovers, and universal Light/Dark mode tokens |

---

## 🏛️ System Architecture

Data Studio v2 follows a strict modular architecture with clean separation of concerns between presentation views, computational engines, cloud telemetry, session management, and persistence layers.

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
                 │ - bcrypt (12 rounds)│          │ - Top Navigation    │
                 │ - Session Guard     │          │ - Theme Engine      │
                 │ - Activity Tracker  │          │ - Workflow Stepper  │
                 └──────────┬──────────┘          └──────────┬──────────┘
                            │                                │
                            ▼                                ▼
        ┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
        │        AUTHENTICATION PERSISTENCE    │  │         MODULAR WORKSPACE SUITE      │
        │                                      │  │                                      │
        │ - user_data/users_db.json            │  │ 1. Overview       (overview.py)      │
        │ - modules/user_storage.py            │  │ 2. Dataset        (data_profiler.py) │
        └──────────────────┬───────────────────┘  │ 3. Data Quality   (data_quality.py)  │
                           │                      │ 4. Data Prep      (data_preparation) │
                           │                      │ 5. Analyze (EDA)  (eda_tools.py)     │
                           │                      │ 6. Visualize      (visualization.py) │
                           │                      │ 7. Dashboard      (dashboard.py)     │
                           │                      │ 8. AI Analyst     (ai_analyst.py)    │
                           │                      │ 9. Settings       (settings.py)      │
                           │                      │ 10. Admin Portal  (admin_analytics)  │
                           │                      └──────────────────┬───────────────────┘
                           ▼                                         │
        ┌──────────────────────────────────────┐                     │
        │       CLOUD ACTIVITY & TELEMETRY     │                     │
        │     (modules/firebase_service.py)    │                     │
        │                                      │                     │
        │ ├── users Collection                 │                     ▼
        │ ├── login_logs Collection            │  ┌──────────────────────────────────────┐
        │ └── dataset_uploads (Metadata Only)  │  │         COMPUTATIONAL ENGINES        │
        └──────────────────┬───────────────────┘  │                                      │
                           ▲                      │ - data_loader.py (ETL & Classifier)  │
                           │                      │ - data_quality_engine.py (5-Dim QA)  │
                           └──────────────────────┤ - eda_engine.py (Stats & Insights)   │
                               (Guarded Logging)  │ - visualization_engine.py (25 Charts)│
                                                  │ - llm_service.py (Gemini & NLP Engine)
                                                  └──────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
data-studio-v2/
│
├── app.py                      # Application entry point, dynamic sidebar navigation & route dispatcher
├── requirements.txt            # Project dependencies (pinned for stability)
├── README.md                   # Complete architectural & platform documentation
├── .gitignore                  # Git exclusion rules (credentials & environment protected)
│
├── modules/                    # Modular UI workspaces and computational processing engines
│   ├── __init__.py             # Package descriptor
│   ├── config.py               # Canonical routes, metadata models, session defaults & workflow helpers
│   ├── ui_components.py        # Reusable design system cards, headers, BaseWeb CSS & navigation steppers
│   ├── auth.py                 # Bcrypt password hashing, session guards & user authentication
│   ├── login_page.py           # Full-screen login, account registration & guest demo interface
│   ├── user_storage.py         # Local user repository interface with atomic file writes
│   ├── firebase_service.py     # Firebase Admin SDK singleton, logging & admin query engine
│   │
│   ├── data_loader.py          # Multi-encoding CSV/XLSX parser & semantic 5-type classifier
│   ├── data_profiler.py        # Dataset Workspace (Preview, Columns, Stat Profiles, Integrity)
│   ├── data_quality_engine.py  # Deterministic 5-dimension quality auditor & scoring engine
│   ├── data_quality.py         # Quality workspace with hero score, gauge & 5 diagnostic tabs
│   ├── data_preparation.py     # Data cleaning, missing value imputation, outlier clipping & export
│   │
│   ├── eda_engine.py           # Statistical calculation engine (Distributions, Correlations, PCA, Outliers)
│   ├── eda_tools.py            # Exploratory Data Analysis studio with 5 analytical diagnostic tabs
│   ├── visualization_engine.py # High-contrast, theme-adaptive Plotly generator (25 Chart Types)
│   ├── visualization.py        # 2-Column BI Visualization Studio with instant customization & exports
│   ├── dashboard_engine.py     # Primary KPI detection & automatic executive dashboard generator
│   ├── dashboard.py            # Dynamic executive dashboard view with 2x2 grid & KPI summary cards
│   │
│   ├── llm_service.py          # Google Gemini & OpenAI API caller + Deterministic NLP Query Engine
│   ├── ai_analyst.py           # Interactive AI Workspace (Chat Q&A, Root-Cause Investigation, Story)
│   ├── admin_analytics.py      # Protected admin dashboard for user activity & telemetry monitoring
│   ├── overview.py             # Platform welcome hub, feature showcase & dataset upload landing view
│   └── settings.py             # Workspace preferences, theme toggles & session memory management
│
├── assets/
│   └── css/
│       └── style.css           # Design tokens, typography hierarchy, universal dark/light mode styles
│
├── sample_data/
│   ├── saas_sales_data.csv     # Sample SaaS recurring revenue, churn & retention dataset
│   ├── ecommerce_orders.csv    # Sample global e-commerce retail transaction dataset
│   └── customer_demographics.csv # Sample demographic, income & categorical dataset
│
├── user_data/                  # Local user database repository (git-ignored)
│   └── users_db.json
│
├── scratch/                    # Automated unit and integration test suites
│   ├── test_module2.py         # Ingestion and schema profiling test suite
│   ├── test_module3.py         # Dashboard and KPI engine test suite
│   ├── test_module4.py         # Data quality scoring & audit test suite
│   ├── test_module5.py         # Authentication and bcrypt security test suite
│   ├── test_firebase_analytics.py # Cloud tracking, deduplication & admin auth test suite
│   ├── test_visualization_engine.py # Comprehensive 25-chart visualization test suite
│   └── test_ai_analyst.py      # AI Analyst natural language engine & story generator test suite
│
└── .streamlit/
    ├── config.toml             # Streamlit server, port, CORS, and base theme configuration
    └── secrets.toml            # (Local development only - git-ignored)
```

---

## 🔍 Detailed Module Guide

### 🔹 Module 1 — Foundation, Design System & Theme Engine
- **Curated Palette**: Standardized CSS variables for surfaces, borders, text, and brand accents (`assets/css/style.css`).
- **BaseWeb Dark Mode Popovers**: Injected BaseWeb portal overrides ensuring selectboxes, multiselect tags, and dropdowns have high contrast in Dark Mode.
- **Lucide Vector Icons**: Lightweight SVG icons rendered inline with zero external webfont dependencies.
- **Universal Theme Switcher**: Seamless toggling between **Dark Mode** (Obsidian Slate `#0b0f19`) and **Light Mode** (Crisp Off-White `#f8fafc`).
- **Standardized Navigation Stepper**: Universal bottom workflow buttons (`render_next_workflow_steps`) across every module to guide users naturally through the analytical journey.

### 🔹 Module 2 — Dataset Workspace & Profiler (`modules/data_profiler.py`)
- **Multi-Encoding Parser**: Ingests CSV and Excel files with automatic fallback across `utf-8`, `latin1`, and `cp1252`.
- **Excel Multi-Sheet Explorer**: Dynamically enumerates sheets in multi-page workbooks for targeted loading.
- **Semantic 5-Type Classifier**: Automatically infers column semantics:
  - **Numeric**: Continuous metrics, monetary values, counts.
  - **Categorical**: Discrete classes, status flags, regions.
  - **Date/Time**: Temporal timestamps and ISO date strings.
  - **Text**: Free-form text and unique identifiers.
  - **Boolean**: Binary flags (`true/false`, `0/1`, `yes/no`).
- **5 Structured Workspace Tabs**:
  1. `DATA PREVIEW & EXPLORER`: Searchable, filterable interactive table with adjustable sample sizes.
  2. `COLUMN SCHEMA & ATTRIBUTES`: Complete inventory of completeness, uniqueness, and memory footprint.
  3. `STATISTICAL PROFILES`: Metric summaries, mean, median, IQR bounds, and cardinality.
  4. `HEALTH & INTEGRITY`: Quick snapshot of missing cells and duplicate rates.
  5. `UPLOAD & SAMPLE DATASETS`: Switch datasets or load pre-bundled sample datasets with 1 click.

### 🔹 Module 3 — Data Quality Intelligence (`modules/data_quality.py`)
- **Deterministic 0–100 Health Score**: Evaluates dataset hygiene across 5 mathematically weighted dimensions:
  1. **Completeness (30%)**: Missing value counts, null rates, and blank field penalties.
  2. **Uniqueness (20%)**: Duplicate rows and identical redundant columns.
  3. **Consistency (20%)**: Constant zero-variance features and mixed data types.
  4. **Validity (15%)**: Whitespace strings, invalid negative numbers, and out-of-range values.
  5. **Outlier Health (15%)**: Interquartile range (IQR 1.5×) anomaly rates.
- **Hero Score Display**: Visual score gauge with color-coded grade badges (A+ to F).
- **5 Diagnostic Audit Tabs**: Deep-dive inspection tables for missing value matrices, duplicate rows, column consistency, validation rules, and statistical outlier bounds.

### 🔹 Module 4 — Interactive Data Preparation & Cleaning (`modules/data_preparation.py`)
- **Missing Value Handling**: Impute missing cells via Mean, Median, Mode, Constant Value, or drop null rows/columns.
- **Outlier Remediation**: Cap outliers at IQR bounds (winsorization) or remove anomalous rows.
- **Type Conversions**: Cast column data types (e.g. String to DateTime, Float to Integer, String to Categorical).
- **Column Derivations**: Create new mathematical features, text extractions, and standardized transformations.
- **Deduplication**: Remove exact duplicate rows with 1 click.
- **Audit Log & Rollback**: Complete step-by-step transformation history with instant undo/reset capability.
- **Cleaned Data Export**: Download cleaned datasets in CSV or Excel format.

### 🔹 Module 5 — Exploratory Data Analysis (EDA) Studio (`modules/eda_tools.py`)
- **5 Diagnostic Analysis Tabs**:
  1. `UNIVARIATE DISTRIBUTIONS`: Histograms, KDE curves, box plots, and normality test scores (Shapiro-Wilk / D'Agostino).
  2. `BIVARIATE & MULTIVARIATE`: Scatter plots, hue group coloring, trendlines, and joint distribution hexbins.
  3. `CORRELATION MATRIX`: Interactive Pearson/Spearman correlation heatmaps and strongest pair extractors.
  4. `OUTLIER ANALYSIS`: IQR anomaly detection with interactive scatter boundary plots.
  5. `DIMENSIONALITY REDUCTION`: PCA 2D/3D projection plots showing variance explained.
- **Automated Statistical Insights**: Algorithmic observations detailing high-skew features, dominant categories, and multicollinearity warnings.

### 🔹 Module 6 — 25-Chart Visualization Studio (`modules/visualization.py`)
- **2-Column BI Studio Layout**: Left control builder panel + right live interactive canvas.
- **25 Theme-Adaptive Chart Types**:
  - *Comparisons & Distributions*: Bar Chart, Grouped Bar, Stacked Bar, Histogram, Box Plot, Violin Plot.
  - *Trends & Time-Series*: Line Chart, Multi-Line, Area Chart, Stacked Area, Step Line.
  - *Relationships & Correlation*: Scatter Plot, Bubble Chart, Correlation Heatmap, Density Heatmap, 3D Scatter.
  - *Proportions & Parts-to-Whole*: Pie Chart, Donut Chart, Treemap, Sunburst Chart, Funnel Chart.
  - *Financial, Geographical & Specialized*: Candlestick, Radar Chart, Waterfall Chart, Choropleth Map.
- **Customization Controls**: Color palette picker (Indigo, Emerald, Cyberpunk, Sunset, etc.), facet splits, aggregation functions (Sum, Mean, Median, Min, Max), custom chart heights, and opacity sliders.
- **Multi-Format Vector Export**: Export charts to PNG, SVG, or interactive standalone HTML.

### 🔹 Module 7 — Automatic Dataset Dashboard (`modules/dashboard.py`)
- **Dynamic Executive KPIs**: Identifies the dataset's primary numeric metric (e.g. Total Revenue, Active Users) and displays high-impact metric cards.
- **2x2 Visual Insights Grid**: Four automated charts visualizing distribution, category share, and temporal trends.
- **Correlation Overview**: Compact correlation matrix highlighting significant statistical relationships.
- **Automated Summary Bullets**: Clear, fact-checked bullet points summarizing dataset shape, primary category drivers, and distribution variance.

### 🔹 Module 8 — AI Analyst Workspace (`modules/ai_analyst.py` & `modules/llm_service.py`)
- **3 Analytical Modes**:
  1. `AI DATA CHAT & Q&A`: Multi-turn conversational interface with Enter-key submission, 1-click suggested prompts, follow-up buttons, and embedded data tables.
  2. `ROOT-CAUSE INVESTIGATION`: Target metric vs comparison dimension driver analysis with grouped bar charts, correlation drivers, and confidence scoring.
  3. `EXECUTIVE DATA STORY`: 7-chapter automated narrative briefing summarizing data context, health, preparation, EDA patterns, statistical relationships, outliers, and next steps with 1-click Markdown export.
- **Multi-Model Generative AI**: Native integration with Google Gemini (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) and OpenAI (`gpt-4o-mini`) supporting multilingual inquiries in any language (English, Hindi, Spanish, etc.).
- **Deterministic Natural Language Query Engine**: High-performance offline fallback that computes real mathematical answers directly from dataset memory without requiring an API key.

### 🔹 Module 9 — Authentication & Security (`modules/auth.py`)
- **Bcrypt 12-Round Password Hashing**: Industry-standard salted cryptographic hashing.
- **Account Registration & Validation**: Email regex formatting and duplicate prevention.
- **Guest Demo Sandboxing**: 1-click instant guest access for immediate exploration without signup.
- **Session Isolation**: Complete session state purge upon signing out.

### 🔹 Module 10 — Firebase Activity Logging & Admin Analytics (`modules/admin_analytics.py`)
- **Cloud Telemetry**: Records user logins and dataset upload events to **Google Cloud Firestore**.
- **Privacy-First Metadata Logging**: Strictly records dataset dimensions, column names, detected data types, missing percentages, and file sizes. **Zero row records or cell values are ever transmitted to Firestore.**
- **Session Deduplication**: Dedicated session state flags prevent duplicate Firestore writes during normal Streamlit reruns.
- **Protected Admin Dashboard**: Real-time administrative portal with date range filters, KPI metrics, user directories, upload logs, and format distribution charts.

---

## 🔒 Configuration & Deployment

### Streamlit Community Cloud Configuration

Configure your secrets in the Streamlit Cloud Dashboard (**App Settings &rarr; Secrets**) or locally in `.streamlit/secrets.toml`:

```toml
[admin]
email = "admin@example.com"

# Optional: Google Gemini API Key for AI Analyst Generative Mode
GEMINI_API_KEY = "AIzaSy..."

# Optional: OpenAI API Key for AI Analyst
OPENAI_API_KEY = "sk-..."

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
# Ingestion and schema profiling
python scratch/test_module2.py

# Dashboard and KPI engine
python scratch/test_module3.py

# Data quality scoring & 5-dimension audit
python scratch/test_module4.py

# Authentication and bcrypt security
python scratch/test_module5.py

# 25-Chart visualization studio engine
python scratch/test_visualization_engine.py

# AI Analyst NLP engine & story generator
python scratch/test_ai_analyst.py

# Firebase cloud telemetry & admin auth
python scratch/test_firebase_analytics.py
```

### 5. Launch Application
```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## 📄 License & Acknowledgements

- **License**: MIT Open Source License.
- **Built with**: Streamlit, Plotly, Pandas, Google Gemini API, and Firebase Firestore.
