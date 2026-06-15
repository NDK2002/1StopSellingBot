-- Function to get low-stock inventory items
CREATE OR REPLACE FUNCTION get_low_stock_inventory()
RETURNS TABLE (
    id uuid,
    product_id uuid,
    sku text,
    quantity integer,
    low_stock_threshold integer,
    updated_at timestamptz,
    product_name text,
    category text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.product_id,
        i.sku,
        i.quantity,
        i.low_stock_threshold,
        i.updated_at,
        p.name AS product_name,
        p.category
    FROM inventory i
    JOIN products p ON p.id = i.product_id
    WHERE i.quantity <= i.low_stock_threshold;
END;
$$;
