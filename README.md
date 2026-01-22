# TraderStats-style Trading Journal (URL)

This is a Streamlit app that:
- lets you upload TradingView `.xlsx` exports
- shows Monthly Performance, KPI cards, and a calendar (dark mode)

## Deploy as a URL (Streamlit Community Cloud)

### 1) Create a GitHub account
If you don't have one, create one.

### 2) Create a new repository
- Click **New**
- Name it: `trading-journal`
- Keep it **Public** (Streamlit free tier requires public repos)
- Click **Create repository**

### 3) Upload these files to the repo
Upload everything from this folder:
- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`

(You can upload by clicking **Add file → Upload files**.)

### 4) Deploy on Streamlit Community Cloud
- Go to Streamlit Community Cloud and click **New app**
- Choose your repo: `trading-journal`
- Branch: `main`
- Main file path: `app.py`
- Click **Deploy**

### 5) Use your dashboard
Open your new URL and upload your TradingView exports in the sidebar.

## Notes
- Your trades are processed in memory when you upload files.
- If you want Notes/Tags to persist, we can add a lightweight database later.
