-- =============================================================
-- database/verify.sql
-- Rubis POS Pipeline — Post-Load Verification
-- Run: psql -U rubis_user -d rubis_pos -f database/verify.sql
-- =============================================================

\echo '============================================='
\echo 'RUBIS POS — DATABASE VERIFICATION'
\echo '============================================='

-- 1. Total rows
\echo ''
\echo '--- 1. Total rows in database ---'
SELECT COUNT(*) AS total_rows FROM pos_sales;

-- 2. Rows per branch
\echo ''
\echo '--- 2. Rows per branch (expect all 5) ---'
SELECT
    source_branch,
    COUNT(*) AS row_count
FROM pos_sales
GROUP BY source_branch
ORDER BY row_count DESC;

-- 3. Sales per branch
\echo ''
\echo '--- 3. Gross sales per branch (KES) ---'
SELECT
    branch,
    SUM(gross_sales)  AS total_gross_sales,
    SUM(net_sale)     AS total_net_sale,
    SUM(discount)     AS total_discount
FROM pos_sales
GROUP BY branch
ORDER BY total_gross_sales DESC;

-- 4. Top 10 products
\echo ''
\echo '--- 4. Top 10 products by net sale ---'
SELECT
    sku_code,
    product_name,
    SUM(quantity)  AS total_qty,
    SUM(net_sale)  AS total_net_sale
FROM pos_sales
GROUP BY sku_code, product_name
ORDER BY total_net_sale DESC
LIMIT 10;

-- 5. Rows per department
\echo ''
\echo '--- 5. Rows per department ---'
SELECT
    department,
    COUNT(*)       AS row_count,
    SUM(net_sale)  AS total_net_sale
FROM pos_sales
GROUP BY department
ORDER BY total_net_sale DESC;

-- 6. Null check
\echo ''
\echo '--- 6. Null check on critical columns (all should be 0) ---'
SELECT
    SUM(CASE WHEN sku_code     IS NULL THEN 1 ELSE 0 END) AS null_skus,
    SUM(CASE WHEN branch       IS NULL THEN 1 ELSE 0 END) AS null_branches,
    SUM(CASE WHEN department   IS NULL THEN 1 ELSE 0 END) AS null_depts,
    SUM(CASE WHEN product_name IS NULL THEN 1 ELSE 0 END) AS null_products,
    SUM(CASE WHEN net_sale     IS NULL THEN 1 ELSE 0 END) AS null_net_sales
FROM pos_sales;

-- 7. Missing branch check
\echo ''
\echo '--- 7. Missing branches (should return 0 rows) ---'
SELECT branch_name AS missing_branch
FROM (VALUES
    ('Jogoo Road'),
    ('Kingo'),
    ('Membley'),
    ('Thome'),
    ('Tigoni')
) AS expected(branch_name)
WHERE branch_name NOT IN (
    SELECT DISTINCT branch FROM pos_sales
);

-- 8. Negative quantity rows
\echo ''
\echo '--- 8. Negative quantity rows (ideally 0) ---'
SELECT
    branch, department, sku_code, product_name, quantity
FROM pos_sales
WHERE quantity < 0
ORDER BY quantity ASC
LIMIT 20;

-- 9. Gross sales less than net sale
\echo ''
\echo '--- 9. Gross sales < net sale (data quality flag) ---'
SELECT COUNT(*) AS suspicious_rows
FROM pos_sales
WHERE gross_sales < net_sale;

-- 10. Last 5 pipeline runs
\echo ''
\echo '--- 10. Last 5 pipeline runs (load_log) ---'
SELECT
    run_at,
    rows_loaded,
    branches_loaded,
    status,
    error_message
FROM load_log
ORDER BY run_at DESC
LIMIT 5;

\echo ''
\echo '============================================='
\echo 'VERIFICATION COMPLETE'
\echo '============================================='