import os
import pytest
import mysql.connector
from mysql.connector import errors as mysql_errors


@pytest.fixture(scope="module")
def db_connection():
    """Establish a connection to the test MySQL database."""
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "root"),
        database=os.getenv("DB_NAME", "northwind"),
    )
    yield connection
    connection.close()


# ---------------------------------------------------------------------------
# 1. Schema: all expected tables must exist
# ---------------------------------------------------------------------------

def test_all_tables_exist(db_connection):
    """Verify that all 20 expected Northwind tables were created."""
    cursor = db_connection.cursor()
    cursor.execute("SHOW TABLES;")
    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "customers",
        "employees",
        "privileges",
        "employee_privileges",
        "inventory_transaction_types",
        "shippers",
        "orders_tax_status",
        "orders_status",
        "orders",
        "products",
        "purchase_order_status",
        "suppliers",
        "purchase_orders",
        "inventory_transactions",
        "invoices",
        "order_details_status",
        "order_details",
        "purchase_order_details",
        "sales_reports",
        "strings",
    }

    missing = expected_tables - tables
    assert not missing, f"Missing tables: {missing}"


# ---------------------------------------------------------------------------
# 2. Data: core tables must not be empty after import
# ---------------------------------------------------------------------------

def test_core_data_loaded(db_connection):
    """Verify that core tables contain seed data after import."""
    cursor = db_connection.cursor()
    # Queries are written out explicitly to avoid dynamic table-name construction.
    checks = {
        "products": "SELECT COUNT(*) FROM `products`;",
        "customers": "SELECT COUNT(*) FROM `customers`;",
        "employees": "SELECT COUNT(*) FROM `employees`;",
        "orders": "SELECT COUNT(*) FROM `orders`;",
        "suppliers": "SELECT COUNT(*) FROM `suppliers`;",
    }
    for table, query in checks.items():
        cursor.execute(query)
        count = cursor.fetchone()[0]
        assert count > 0, f"Table '{table}' is empty — seed data was not loaded."


# ---------------------------------------------------------------------------
# 3. Foreign key constraints
# ---------------------------------------------------------------------------

def test_fk_orders_invalid_customer(db_connection):
    """orders.customer_id must reference a valid customers.id."""
    cursor = db_connection.cursor()
    with pytest.raises(mysql_errors.IntegrityError):
        cursor.execute(
            "INSERT INTO `orders` (`customer_id`) VALUES (%s);",
            (9999999,),
        )
        db_connection.commit()
    db_connection.rollback()


def test_fk_order_details_invalid_order(db_connection):
    """order_details.order_id must reference a valid orders.id."""
    cursor = db_connection.cursor()
    with pytest.raises(mysql_errors.IntegrityError):
        cursor.execute(
            "INSERT INTO `order_details` (`order_id`, `quantity`) VALUES (%s, %s);",
            (9999999, 1),
        )
        db_connection.commit()
    db_connection.rollback()


def test_fk_order_details_invalid_product(db_connection):
    """order_details.product_id must reference a valid products.id."""
    cursor = db_connection.cursor()
    # Fetch a real order id to isolate only the product FK violation
    cursor.execute("SELECT id FROM `orders` LIMIT 1;")
    row = cursor.fetchone()
    assert row is not None, "No orders found to use in FK test."
    valid_order_id = row[0]

    with pytest.raises(mysql_errors.IntegrityError):
        cursor.execute(
            "INSERT INTO `order_details` (`order_id`, `product_id`, `quantity`) VALUES (%s, %s, %s);",
            (valid_order_id, 9999999, 1),
        )
        db_connection.commit()
    db_connection.rollback()


def test_fk_employee_privileges_invalid_employee(db_connection):
    """employee_privileges.employee_id must reference a valid employees.id."""
    cursor = db_connection.cursor()
    # Fetch a real privilege id
    cursor.execute("SELECT id FROM `privileges` LIMIT 1;")
    row = cursor.fetchone()
    assert row is not None, "No privileges found to use in FK test."
    valid_privilege_id = row[0]

    with pytest.raises(mysql_errors.IntegrityError):
        cursor.execute(
            "INSERT INTO `employee_privileges` (`employee_id`, `privilege_id`) VALUES (%s, %s);",
            (9999999, valid_privilege_id),
        )
        db_connection.commit()
    db_connection.rollback()


def test_fk_purchase_orders_invalid_supplier(db_connection):
    """purchase_orders.supplier_id must reference a valid suppliers.id."""
    cursor = db_connection.cursor()
    with pytest.raises(mysql_errors.IntegrityError):
        cursor.execute(
            "INSERT INTO `purchase_orders` (`supplier_id`) VALUES (%s);",
            (9999999,),
        )
        db_connection.commit()
    db_connection.rollback()


def test_fk_inventory_transactions_invalid_type(db_connection):
    """inventory_transactions.transaction_type must reference a valid type id."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM `products` LIMIT 1;")
    row = cursor.fetchone()
    assert row is not None, "No products found to use in FK test."
    valid_product_id = row[0]

    with pytest.raises(mysql_errors.IntegrityError):
        cursor.execute(
            "INSERT INTO `inventory_transactions` (`transaction_type`, `product_id`, `quantity`) VALUES (%s, %s, %s);",
            (99, valid_product_id, 5),
        )
        db_connection.commit()
    db_connection.rollback()


# ---------------------------------------------------------------------------
# 4. Unique / primary-key constraints
# ---------------------------------------------------------------------------

def test_duplicate_primary_key_rejected(db_connection):
    """Inserting a duplicate primary key must be rejected."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM `customers` LIMIT 1;")
    row = cursor.fetchone()
    assert row is not None, "No customers found to use in PK uniqueness test."
    existing_id = row[0]

    with pytest.raises(mysql_errors.IntegrityError):
        cursor.execute(
            "INSERT INTO `customers` (`id`, `last_name`, `first_name`) VALUES (%s, %s, %s);",
            (existing_id, "Duplicate", "Test"),
        )
        db_connection.commit()
    db_connection.rollback()
