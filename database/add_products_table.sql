-- =====================================================================
-- PRODUCTS TABLE FOR NIGERIAN E-COMMERCE PLATFORM
-- Realistic product catalog with Nigerian market focus
-- =====================================================================

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    brand VARCHAR(100),
    description TEXT,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    currency CHAR(3) DEFAULT 'NGN',
    in_stock BOOLEAN DEFAULT true,
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    weight_kg NUMERIC(5,2),
    dimensions_cm VARCHAR(50), -- "L x W x H"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add comments for products table
COMMENT ON TABLE products IS 'Product catalog for Nigerian e-commerce platform with pricing in Naira';
COMMENT ON COLUMN products.product_id IS 'Auto-incrementing primary key for product identification';
COMMENT ON COLUMN products.product_name IS 'Full product name including model/variant details';
COMMENT ON COLUMN products.category IS 'Product category matching order categories';
COMMENT ON COLUMN products.brand IS 'Brand or manufacturer name';
COMMENT ON COLUMN products.description IS 'Detailed product description with features';
COMMENT ON COLUMN products.price IS 'Product price in Nigerian Naira';
COMMENT ON COLUMN products.in_stock IS 'Current availability status';
COMMENT ON COLUMN products.stock_quantity IS 'Current stock level for inventory management';

-- Create indexes for products table
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_in_stock ON products(in_stock);
CREATE INDEX idx_products_name_gin ON products USING gin(product_name gin_trgm_ops);

-- Add product_id column to orders table
ALTER TABLE orders ADD COLUMN IF NOT EXISTS product_id INTEGER;
ALTER TABLE orders ADD CONSTRAINT fk_orders_product_id
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL;

-- Create index for the new foreign key
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);

-- =====================================================================
-- NIGERIAN E-COMMERCE PRODUCT CATALOG
-- =====================================================================

-- ELECTRONICS CATEGORY
INSERT INTO products (product_name, category, brand, description, price, stock_quantity, weight_kg, dimensions_cm) VALUES
('Samsung Galaxy A24 128GB Smartphone', 'Electronics', 'Samsung', 'Android smartphone with 6.6" display, 50MP camera, 128GB storage, dual SIM support', 425000.00, 45, 0.195, '16.1 x 7.7 x 0.8'),
('iPhone 14 Pro Max 256GB', 'Electronics', 'Apple', 'Premium iPhone with A16 Bionic chip, ProRAW camera system, 6.7" Super Retina XDR display', 1850000.00, 12, 0.240, '16.1 x 7.8 x 0.8'),
('Tecno Camon 20 Pro 5G', 'Electronics', 'Tecno', 'Nigerian popular smartphone with 64MP portrait camera, 8GB RAM, 256GB storage', 345000.00, 78, 0.203, '16.4 x 7.5 x 0.8'),
('Infinix Note 30 VIP', 'Electronics', 'Infinix', 'Premium smartphone with 108MP camera, 12GB RAM, 256GB storage, wireless charging', 389000.00, 56, 0.207, '16.8 x 7.8 x 0.8'),
('LG 55" 4K Smart TV', 'Electronics', 'LG', '55-inch 4K UHD Smart TV with webOS, HDR10, built-in WiFi and streaming apps', 890000.00, 23, 18.5, '123 x 72 x 8'),
('Sony 65" OLED Smart TV', 'Electronics', 'Sony', 'Premium 65-inch OLED TV with 4K HDR, Android TV, perfect blacks and infinite contrast', 2850000.00, 8, 28.2, '145 x 84 x 5'),
('Haier Thermocool Washing Machine 8kg', 'Electronics', 'Haier Thermocool', 'Top-loading automatic washing machine, 8kg capacity, multiple wash programs', 485000.00, 15, 45.0, '56 x 59 x 91'),
('Scanfrost Deep Freezer 300L', 'Electronics', 'Scanfrost', 'Energy-efficient chest freezer, 300L capacity, suitable for Nigerian homes and businesses', 675000.00, 18, 65.0, '120 x 60 x 85');

-- FASHION CATEGORY
INSERT INTO products (product_name, category, brand, description, price, stock_quantity, weight_kg, dimensions_cm) VALUES
('Ankara Print Maxi Dress', 'Fashion', 'Adunni Clothings', 'Beautiful handcrafted Ankara maxi dress, authentic Nigerian print, perfect for special occasions', 25000.00, 124, 0.3, '40 x 30 x 5'),
('Agbada Traditional Outfit (Men)', 'Fashion', 'Royal Threads', 'Classic white Agbada with gold embroidery, includes cap and pants, perfect for traditional ceremonies', 85000.00, 45, 1.2, '60 x 40 x 10'),
('Gele Headtie (Aso Oke)', 'Fashion', 'Eko Fashion', 'Premium Aso Oke gele in royal blue, hand-woven traditional headtie for special occasions', 35000.00, 89, 0.2, '120 x 30 x 2'),
('Nike Air Max 270 Sneakers', 'Fashion', 'Nike', 'Popular lifestyle sneakers with Max Air unit, available in multiple colors', 95000.00, 67, 0.8, '35 x 25 x 12'),
('Adidas Originals Trefoil Hoodie', 'Fashion', 'Adidas', 'Classic hoodie with trefoil logo, cotton blend, available in black and grey', 45000.00, 156, 0.6, '30 x 25 x 5'),
('Zara Slim Fit Chinos', 'Fashion', 'Zara', 'Premium cotton chinos in navy blue, slim fit, perfect for casual and semi-formal wear', 28000.00, 89, 0.4, '35 x 25 x 3'),
('Louis Vuitton Handbag (Replica)', 'Fashion', 'LV Style', 'High-quality replica Louis Vuitton handbag, PU leather, multiple compartments', 65000.00, 34, 0.8, '35 x 25 x 15'),
('Gold-plated Jewelry Set', 'Fashion', 'Naija Gold', 'Beautiful gold-plated necklace and earrings set, hypoallergenic, Nigerian design', 42000.00, 78, 0.1, '15 x 10 x 3');

-- BEAUTY CATEGORY
INSERT INTO products (product_name, category, brand, description, price, stock_quantity, weight_kg, dimensions_cm) VALUES
('Shea Butter Body Cream 500ml', 'Beauty', 'Ori Natural', 'Pure Nigerian shea butter body cream, moisturizing, suitable for all skin types', 8500.00, 234, 0.5, '15 x 8 x 8'),
('Black Soap (Dudu Osun)', 'Beauty', 'Tropical Naturals', 'Traditional African black soap with natural ingredients, deep cleansing, 150g bar', 3500.00, 456, 0.15, '8 x 6 x 3'),
('Skin Lightening Cream', 'Beauty', 'Fair & White', 'Skin brightening cream with vitamin C, evens skin tone, reduces dark spots', 15000.00, 178, 0.3, '12 x 8 x 5'),
('Hair Relaxer Kit (Mega Growth)', 'Beauty', 'Mega Growth', 'Complete hair relaxer kit for textured hair, includes neutralizing shampoo', 12000.00, 145, 0.8, '25 x 15 x 8'),
('Coconut Oil Hair Treatment', 'Beauty', 'Coconut Magic', 'Pure coconut oil for hair treatment, strengthens and adds shine, 250ml bottle', 6500.00, 289, 0.25, '12 x 6 x 6'),
('MAC Lipstick Ruby Woo', 'Beauty', 'MAC Cosmetics', 'Classic red lipstick, matte finish, long-lasting, iconic shade', 25000.00, 89, 0.05, '8 x 2 x 2'),
('Maybelline Mascara Lash Sensational', 'Beauty', 'Maybelline', 'Volumizing mascara with curved brush, waterproof formula', 8500.00, 167, 0.03, '12 x 2 x 2'),
('L\'Oreal Foundation True Match', 'Beauty', 'L\'Oreal', 'Liquid foundation with SPF 17, available in multiple shades for Nigerian skin tones', 18000.00, 123, 0.15, '10 x 4 x 4');

-- COMPUTING CATEGORY
INSERT INTO products (product_name, category, brand, description, price, stock_quantity, weight_kg, dimensions_cm) VALUES
('HP Pavilion Laptop 15.6" Intel i5', 'Computing', 'HP', 'Laptop with Intel Core i5, 8GB RAM, 512GB SSD, Windows 11, perfect for work and studies', 875000.00, 34, 1.8, '36 x 24 x 2'),
('Dell OptiPlex Desktop Computer', 'Computing', 'Dell', 'Business desktop with Intel i7, 16GB RAM, 1TB HDD, includes monitor and keyboard', 1250000.00, 18, 15.5, '35 x 15 x 35'),
('MacBook Air M2 13-inch', 'Computing', 'Apple', 'Latest MacBook Air with M2 chip, 8GB RAM, 256GB SSD, exceptional battery life', 1650000.00, 12, 1.24, '30 x 21 x 1'),
('Lenovo ThinkPad E15 Business Laptop', 'Computing', 'Lenovo', 'Professional laptop with Intel i7, 16GB RAM, 512GB SSD, business-grade reliability', 1150000.00, 23, 1.9, '36 x 25 x 2'),
('Canon PIXMA Printer', 'Computing', 'Canon', 'All-in-one wireless printer with scanner and copier, supports mobile printing', 185000.00, 45, 8.5, '43 x 35 x 16'),
('Logitech Wireless Mouse and Keyboard', 'Computing', 'Logitech', 'Wireless desktop set with ergonomic design, long battery life, includes receiver', 35000.00, 145, 1.2, '45 x 18 x 8'),
('Samsung 32" Curved Gaming Monitor', 'Computing', 'Samsung', 'Curved gaming monitor with 144Hz refresh rate, 1ms response time, FHD resolution', 485000.00, 28, 7.2, '71 x 43 x 25'),
('External Hard Drive 2TB WD', 'Computing', 'Western Digital', 'Portable external hard drive, 2TB capacity, USB 3.0, backup software included', 125000.00, 78, 0.25, '12 x 8 x 2');

-- AUTOMOTIVE CATEGORY
INSERT INTO products (product_name, category, brand, description, price, stock_quantity, weight_kg, dimensions_cm) VALUES
('Car Engine Oil 5W-30 (5 Liters)', 'Automotive', 'Mobil 1', 'Synthetic engine oil for modern engines, improves fuel economy, 5-liter container', 45000.00, 156, 4.5, '25 x 15 x 30'),
('Car Battery 12V 75Ah', 'Automotive', 'Exide', 'Maintenance-free car battery, 12V 75Ah capacity, suitable for most Nigerian cars', 85000.00, 67, 18.5, '35 x 17 x 19'),
('Dunlop Tires 205/55R16', 'Automotive', 'Dunlop', 'All-season tires with excellent grip, suitable for Nigerian road conditions', 165000.00, 89, 12.5, '65 x 65 x 25'),
('Brake Pads (Front Set)', 'Automotive', 'Bosch', 'Premium brake pads for front wheels, ceramic compound, low dust formula', 35000.00, 234, 2.5, '25 x 15 x 8'),
('Car Air Freshener (Pack of 5)', 'Automotive', 'Little Trees', 'Hanging car air fresheners, mixed scents, long-lasting fragrance', 3500.00, 456, 0.1, '12 x 8 x 2'),
('LED Car Headlight Bulbs H4', 'Automotive', 'Philips', 'LED replacement bulbs for car headlights, brighter and longer-lasting than halogen', 25000.00, 178, 0.3, '12 x 8 x 8'),
('Car Phone Holder Dashboard Mount', 'Automotive', 'iOttie', 'Adjustable phone mount for car dashboard, suitable for all phone sizes', 8500.00, 289, 0.4, '15 x 10 x 10'),
('Car Jump Starter Power Bank', 'Automotive', 'NOCO', 'Portable jump starter with USB charging ports, LED flashlight, 12000mAh capacity', 125000.00, 89, 1.8, '20 x 10 x 5');

-- BOOKS CATEGORY
INSERT INTO products (product_name, category, brand, description, price, stock_quantity, weight_kg, dimensions_cm) VALUES
('Things Fall Apart by Chinua Achebe', 'Books', 'Penguin Classics', 'Classic Nigerian novel, cornerstone of African literature, paperback edition', 4500.00, 234, 0.25, '20 x 13 x 2'),
('Purple Hibiscus by Chimamanda Ngozi Adichie', 'Books', 'Fourth Estate', 'Award-winning novel by renowned Nigerian author, coming-of-age story', 5500.00, 189, 0.3, '20 x 13 x 2'),
('Lagos Wife by Vanessa Walters', 'Books', 'Cassava Republic', 'Contemporary Nigerian fiction, exploring modern Lagos relationships', 6000.00, 156, 0.28, '20 x 13 x 2'),
('The Wealth of Nations by Adam Smith', 'Books', 'Modern Library', 'Economic classic, fundamental text for business and economics students', 12000.00, 89, 0.8, '23 x 15 x 4'),
('Rich Dad Poor Dad by Robert Kiyosaki', 'Books', 'Plata Publishing', 'Personal finance bestseller, financial education and investment guide', 8500.00, 167, 0.4, '21 x 14 x 2'),
('Medical Textbook: Gray\'s Anatomy', 'Books', 'Elsevier', 'Comprehensive anatomy textbook for medical students, 41st edition', 95000.00, 23, 3.2, '28 x 22 x 6'),
('JAMB Past Questions 2024', 'Books', 'Exam Focus', 'Comprehensive JAMB past questions and answers, all subjects covered', 3500.00, 456, 0.3, '25 x 18 x 2'),
('Children\'s Picture Book: Anansi Stories', 'Books', 'Cassava Republic', 'Beautiful illustrated book of traditional African Anansi stories for children', 7500.00, 134, 0.4, '25 x 20 x 1');

-- Update trigger function to include products table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to products table
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraint to ensure product category matches order categories
ALTER TABLE products ADD CONSTRAINT chk_product_category
    CHECK (category IN ('Electronics', 'Fashion', 'Beauty', 'Computing', 'Automotive', 'Books'));

COMMENT ON CONSTRAINT chk_product_category ON products IS 'Ensures product categories match the defined order categories';

-- Create view for products with stock status
CREATE VIEW products_inventory_view AS
SELECT
    product_id,
    product_name,
    category,
    brand,
    price,
    stock_quantity,
    CASE
        WHEN stock_quantity = 0 THEN 'Out of Stock'
        WHEN stock_quantity <= 10 THEN 'Low Stock'
        WHEN stock_quantity <= 50 THEN 'Medium Stock'
        ELSE 'High Stock'
    END as stock_status,
    in_stock,
    created_at
FROM products
ORDER BY category, product_name;

COMMENT ON VIEW products_inventory_view IS 'Product inventory overview with stock status indicators';

-- Create view for popular products by category
CREATE VIEW popular_products_by_category AS
SELECT
    p.category,
    p.product_name,
    p.brand,
    p.price,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as total_revenue
FROM products p
LEFT JOIN orders o ON p.product_id = o.product_id
GROUP BY p.product_id, p.category, p.product_name, p.brand, p.price
ORDER BY p.category, order_count DESC;

COMMENT ON VIEW popular_products_by_category IS 'Products ranked by popularity within each category';

-- Success message
SELECT 'Products table created successfully with ' || COUNT(*) || ' products' as status
FROM products;
