# 📊 Retail Intelligence System

A high-performance retail analytics platform designed to provide actionable insights and branch benchmarking

## 🚀 Key Features

- **Store Benchmarking**: Compare branch performance using a multi-metric composite scorecard.
- **Data Quality Suite**: Comprehensive health checks for your POS data ingestion pipeline.
- **Product Insights**: Detailed tracking of top products, high-value items, and low-margin anomalies.

## 🛠 Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Frontend**: [Streamlit](https://streamlit.io/)
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) (Supports PostgreSQL & SQLite)
- **Analytics**: [Pandas](https://pandas.pydata.org/), [Plotly](https://plotly.com/)

## 🏁 Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- A `.env` file in the root directory

### 2. Installation
```powershell
# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Backend (FastAPI)
```powershell
uvicorn main:app --reload
```
The API documentation will be available at `http://localhost:8000/docs`.

### 4. Run the Frontend (Streamlit)
```powershell
streamlit run my_dashboard/app.py
```
The dashboard will open automatically at `http://localhost:8501`.

*Built with ❤️ for Retail Excellence.*
