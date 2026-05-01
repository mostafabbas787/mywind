# TEST_REPORT.md — Northwind MySQL Database Test Report

This report documents the automated tests defined in `tests/test_db.py` and executed by the GitHub Actions workflow in `.github/workflows/db-test.yml`.

---

## Test Summary

| # | Test Case | Steps | Expected Result | Actual Result | Pass/Fail |
|---|-----------|-------|----------------|---------------|-----------|
| 1 | **All expected tables exist** | 1. Import `northwind.sql` into a fresh MySQL 8.0 instance.<br>2. Run `SHOW TABLES`.<br>3. Assert all 20 tables are present (`customers`, `employees`, `privileges`, `employee_privileges`, `inventory_transaction_types`, `shippers`, `orders_tax_status`, `orders_status`, `orders`, `products`, `purchase_order_status`, `suppliers`, `purchase_orders`, `inventory_transactions`, `invoices`, `order_details_status`, `order_details`, `purchase_order_details`, `sales_reports`, `strings`). | All 20 tables are listed. | Functioning as designed — all 20 tables found. | ✅ Pass |
| 2 | **Core data loaded successfully** | 1. Import `northwind-data.sql`.<br>2. Execute `SELECT COUNT(*) FROM <table>` for `products`, `customers`, `employees`, `orders`, and `suppliers`.<br>3. Assert each count is greater than 0. | Each checked table contains at least one row of seed data. | Functioning as designed — all core tables are non-empty. | ✅ Pass |
| 3 | **FK constraint: orders → customers** | 1. Attempt `INSERT INTO orders (customer_id) VALUES (9999999)`.<br>2. Verify a `mysql.connector.errors.IntegrityError` is raised (foreign key constraint `fk_orders_customers`).<br>3. Roll back the transaction. | MySQL rejects the insert and raises an `IntegrityError`. | Functioning as designed — insert rejected with FK violation. | ✅ Pass |
| 4 | **FK constraint: order_details → orders** | 1. Attempt `INSERT INTO order_details (order_id, quantity) VALUES (9999999, 1)`.<br>2. Verify an `IntegrityError` is raised (constraint `fk_order_details_orders1`).<br>3. Roll back. | MySQL rejects the insert. | Functioning as designed — insert rejected with FK violation. | ✅ Pass |
| 5 | **FK constraint: order_details → products** | 1. Fetch a valid `order_id` from `orders`.<br>2. Attempt `INSERT INTO order_details (order_id, product_id, quantity) VALUES (<valid>, 9999999, 1)`.<br>3. Verify an `IntegrityError` is raised (constraint `fk_order_details_products1`).<br>4. Roll back. | MySQL rejects the insert due to invalid `product_id`. | Functioning as designed — insert rejected with FK violation. | ✅ Pass |
| 6 | **FK constraint: employee_privileges → employees** | 1. Fetch a valid `privilege_id` from `privileges`.<br>2. Attempt `INSERT INTO employee_privileges (employee_id, privilege_id) VALUES (9999999, <valid>)`.<br>3. Verify an `IntegrityError` is raised (constraint `fk_employee_privileges_employees1`).<br>4. Roll back. | MySQL rejects the insert. | Functioning as designed — insert rejected with FK violation. | ✅ Pass |
| 7 | **FK constraint: purchase_orders → suppliers** | 1. Attempt `INSERT INTO purchase_orders (supplier_id) VALUES (9999999)`.<br>2. Verify an `IntegrityError` is raised (constraint `fk_purchase_orders_suppliers1`).<br>3. Roll back. | MySQL rejects the insert. | Functioning as designed — insert rejected with FK violation. | ✅ Pass |
| 8 | **FK constraint: inventory_transactions → inventory_transaction_types** | 1. Fetch a valid `product_id` from `products`.<br>2. Attempt `INSERT INTO inventory_transactions (transaction_type, product_id, quantity) VALUES (99, <valid>, 5)` where `99` is not a valid type id.<br>3. Verify an `IntegrityError` is raised (constraint `fk_inventory_transactions_inventory_transaction_types1`).<br>4. Roll back. | MySQL rejects the insert. | Functioning as designed — insert rejected with FK violation. | ✅ Pass |
| 9 | **Unique / PK constraint: duplicate primary key rejected** | 1. Fetch an existing `id` from `customers`.<br>2. Attempt `INSERT INTO customers (id, last_name, first_name) VALUES (<existing_id>, 'Duplicate', 'Test')`.<br>3. Verify an `IntegrityError` is raised (error code 1062 — Duplicate entry). | MySQL rejects the duplicate primary key insert. | Functioning as designed — duplicate insert rejected. | ✅ Pass |

---

## Environment

| Item | Value |
|------|-------|
| Database | MySQL 8.0 |
| Schema file | `northwind.sql` |
| Data file | `northwind-data.sql` |
| Test framework | pytest |
| DB driver | mysql-connector-python |
| CI platform | GitHub Actions (ubuntu-latest) |

---

## How to Run Locally

```bash
# 1. Start a local MySQL 8.0 instance and import the schema/data
MYSQL_PWD=root mysql -h 127.0.0.1 -u root < northwind.sql
MYSQL_PWD=root mysql -h 127.0.0.1 -u root < northwind-data.sql

# 2. Install Python dependencies
pip install pytest mysql-connector-python

# 3. Run the tests
DB_HOST=127.0.0.1 DB_USER=root DB_PASS=root DB_NAME=northwind pytest tests/ -v
```
