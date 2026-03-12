CREATE TABLE IF NOT EXISTS pos_sales (
    id              SERIAL PRIMARY KEY,
    branch          VARCHAR(100),
    department      VARCHAR(100),
    class           VARCHAR(100),
    sku_code        VARCHAR(50),
    product_name    VARCHAR(255),
    quantity        NUMERIC(12,2),
    gross_sales     NUMERIC(12,2),
    discount        NUMERIC(12,2),
    sales_after_discount NUMERIC(12,2),
    vat_amount      NUMERIC(12,2),
    net_sale        NUMERIC(12,2),
    cost_ex_vat     NUMERIC(12,2),
    net_contribution NUMERIC(12,2),
    margin_pct      NUMERIC(8,4),
    markup_pct      NUMERIC(8,4),
    source_file     VARCHAR(255),
    source_branch   VARCHAR(100),
    loaded_at       TIMESTAMP DEFAULT NOW()
);
 
-- Index for fast queries by branch and department
CREATE INDEX idx_pos_branch     ON pos_sales(branch);
CREATE INDEX idx_pos_department ON pos_sales(department);
CREATE INDEX idx_pos_sku        ON pos_sales(sku_code);
