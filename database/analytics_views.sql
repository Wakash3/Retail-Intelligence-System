-- =============================================================
-- database/analytics_views.sql
-- Rubis POS Analytics Engine — KPI Views
-- Run: psql -U rubis_user -d rubis_pos -f database/analytics_views.sql
-- =============================================================

-- VIEW 1: Branch Performance Summary
CREATE OR REPLACE VIEW vw_branch_performance AS
SELECT
    branch,
    COUNT(*)                                 AS total_products,
    SUM(quantity)                            AS total_units_sold,
    ROUND(SUM(gross_sales)::NUMERIC, 2)      AS total_gross_sales,
    ROUND(SUM(discount)::NUMERIC, 2)         AS total_discount,
    ROUND(SUM(net_sale)::NUMERIC, 2)         AS total_net_sales,
    ROUND(SUM(net_contribution)::NUMERIC, 2) AS total_contribution,
    ROUND(AVG(margin_pct)::NUMERIC, 2)       AS avg_margin_pct,
    ROUND(
        (SUM(net_contribution) / NULLIF(SUM(net_sale), 0) * 100)::NUMERIC, 2
    )                                        AS contribution_margin_pct
FROM pos_sales
WHERE net_sale IS NOT NULL
GROUP BY branch
ORDER BY total_net_sales DESC;

-- VIEW 2: Department Performance Summary
CREATE OR REPLACE VIEW vw_department_performance AS
SELECT
    department,
    COUNT(*)                                 AS total_products,
    SUM(quantity)                            AS total_units_sold,
    ROUND(SUM(gross_sales)::NUMERIC, 2)      AS total_gross_sales,
    ROUND(SUM(net_sale)::NUMERIC, 2)         AS total_net_sales,
    ROUND(SUM(net_contribution)::NUMERIC, 2) AS total_contribution,
    ROUND(AVG(margin_pct)::NUMERIC, 2)       AS avg_margin_pct
FROM pos_sales
WHERE net_sale IS NOT NULL
GROUP BY department
ORDER BY total_net_sales DESC;

-- VIEW 3: Top Products by Net Sales
CREATE OR REPLACE VIEW vw_top_products AS
SELECT
    sku_code,
    product_name,
    department,
    -- Join branch info if needed, but summary usually returns aggregated
    'All Branches'                          AS branch, 
    COUNT(DISTINCT branch)                   AS branches_selling,
    SUM(quantity)                            AS total_qty,
    ROUND(SUM(gross_sales)::NUMERIC, 2)      AS total_gross_sales,
    ROUND(SUM(net_sale)::NUMERIC, 2)         AS total_revenue,
    ROUND(SUM(net_contribution)::NUMERIC, 2) AS total_contribution,
    ROUND(AVG(margin_pct)::NUMERIC, 2)       AS avg_margin_pct
FROM pos_sales
WHERE net_sale IS NOT NULL
GROUP BY sku_code, product_name, department
ORDER BY total_revenue DESC;

-- VIEW 4: Branch x Department Matrix
CREATE OR REPLACE VIEW vw_branch_department AS
SELECT
    branch,
    department,
    COUNT(*)                                 AS total_products,
    SUM(quantity)                            AS total_units_sold,
    ROUND(SUM(net_sale)::NUMERIC, 2)         AS total_net_sales,
    ROUND(SUM(net_contribution)::NUMERIC, 2) AS total_contribution,
    ROUND(AVG(margin_pct)::NUMERIC, 2)       AS avg_margin_pct
FROM pos_sales
WHERE net_sale IS NOT NULL
GROUP BY branch, department
ORDER BY branch, total_net_sales DESC;

-- VIEW 5: Low Margin Products (margin < 10%)
CREATE OR REPLACE VIEW vw_low_margin_products AS
SELECT
    sku_code,
    product_name,
    branch,
    department,
    quantity                                AS total_qty,
    ROUND(net_sale::NUMERIC, 2)              AS total_revenue,
    ROUND(net_contribution::NUMERIC, 2)      AS total_contribution,
    ROUND(margin_pct::NUMERIC, 2)            AS margin_pct
FROM pos_sales
WHERE margin_pct < 10
  AND margin_pct IS NOT NULL
  AND net_sale > 0
ORDER BY margin_pct ASC;

-- VIEW 6: High Value Products (top contributors)
CREATE OR REPLACE VIEW vw_high_value_products AS
SELECT
    sku_code,
    product_name,
    department,
    COUNT(DISTINCT branch)                   AS branches_selling,
    SUM(quantity)                            AS total_qty,
    ROUND(SUM(net_sale)::NUMERIC, 2)         AS total_revenue,
    ROUND(SUM(net_contribution)::NUMERIC, 2) AS total_contribution,
    ROUND(AVG(margin_pct)::NUMERIC, 2)       AS avg_margin_pct
FROM pos_sales
WHERE net_sale IS NOT NULL
GROUP BY sku_code, product_name, department
HAVING SUM(net_contribution) > 50000
ORDER BY total_contribution DESC;