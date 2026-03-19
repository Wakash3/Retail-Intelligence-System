# Rubis POS — Power BI Dashboard

## Overview
This dashboard connects directly to the PostgreSQL database and visualises
live KPI data from the Rubis POS pipeline across all 5 branches.

## Prerequisites
- Power BI Desktop (free) — https://powerbi.microsoft.com/desktop
- PostgreSQL ODBC Driver — install via Stack Builder (comes with PostgreSQL)
- Access to the rubis_pos PostgreSQL database

## Setting Up the ODBC Connection

### Step 1 — Create the ODBC Data Source
1. Open **ODBC Data Sources (64-bit)** from the Windows Start menu
2. Click **System DSN** tab → **Add**
3. Select **PostgreSQL ODBC Driver(UNICODE)** → **Finish**
4. Fill in the connection details:

| Field       | Value       |
|-------------|-------------|
| Data Source | RubisPOS    |
| Database    | rubis_pos   |
| Server      | localhost   |
| Port        | 5432        |
| User Name   | rubis_user  |
| SSL Mode    | disable     |

5. Click **Test** — should return **Connection successful**
6. Click **Save**

### Step 2 — Connect Power BI
1. Open Power BI Desktop
2. Click **Get Data → ODBC**
3. Select **RubisPOS** from the dropdown
4. Click **OK**
5. Enter credentials: `rubis_user` / your password
6. Click **Connect**

### Step 3 — Load the Views
In the Navigator window select these 6 views:
- `vw_branch_performance`
- `vw_department_performance`
- `vw_top_products`
- `vw_branch_department`
- `vw_low_margin_products`
- `vw_high_value_products`

Click **Load**.

## Dashboard Pages

| Page | Name | Description |
|------|------|-------------|
| 1 | Branch Overview | KPI cards, branch revenue bar chart, sales donut chart |
| 2 | Department Performance | Department bar chart, margin vs contribution scatter, table |
| 3 | Product Intelligence | Top 15 products bar chart, full product table |
| 4 | Margin Alert | Low margin products table with color coding, branch slicer |
| 5 | Branch X Department | Margin heatmap matrix across all branches and departments |

## Data Sources

All visuals pull from PostgreSQL views defined in `database/analytics_views.sql`.
The pipeline refreshes the database daily at 6AM Nairobi time via GitHub Actions.
Refresh Power BI manually after each pipeline run or set up scheduled refresh
via Power BI Service.

## Refreshing the Data
To get the latest data after the pipeline runs:
1. Open the `.pbix` file in Power BI Desktop
2. Click **Home → Refresh**
3. All visuals will update from the database

## Key Metrics Tracked
- Total Net Sales per branch and department
- Gross Sales, Discount, and Net Contribution
- Average Margin % and Contribution Margin %
- Top products by net sales and contribution
- Low margin products (margin < 10%) flagged for review
- Branch x Department margin heatmap

## Database Views Reference

| View | Description |
|------|-------------|
| `vw_branch_performance` | KPI summary per branch |
| `vw_department_performance` | KPI summary per department |
| `vw_top_products` | Products ranked by net sales |
| `vw_branch_department` | Branch x department breakdown |
| `vw_low_margin_products` | Products with margin below 10% |
| `vw_high_value_products` | Products with contribution above KES 50,000 |