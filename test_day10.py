
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "coffee_inventory.db"

REQUIRED_TABLES = {
    "stores",
    "products",
    "inventory",
    "reorder_recommendations",
    "stock_movements",
}

REQUIRED_COLUMNS = {
    "inventory": {
        "store_id",
        "product_id",
        "current_stock",
        "avg_daily_sales",
        "safety_stock",
        "lead_time_days",
        "reorder_point",
        "days_until_stockout",
        "risk_level",
    },
    "stock_movements": {
        "movement_id",
        "store_id",
        "product_id",
        "movement_type",
        "quantity",
        "stock_before",
        "stock_after",
        "created_at",
    },
    "reorder_recommendations": {
        "store_id",
        "product_id",
        "target_stock",
        "recommended_order_qty",
        "final_order_qty",
        "order_status",
    },
}

errors = []


def check(condition, description):
    if condition:
        print(f"[PASS] {description}")
    else:
        print(f"[FAIL] {description}")
        errors.append(description)


def main():
    print("=" * 50)
    print("DAY 10 - SMART INVENTORY SYSTEM TEST")
    print("=" * 50)

    check(DB_PATH.is_file(), "SQLite database exists")

    if not DB_PATH.is_file():
        return 1

    db_uri = DB_PATH.as_uri() + "?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)

    try:
        integrity = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        check(
            integrity == "ok",
            "SQLite integrity check"
        )

        existing_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table'"
            )
        }

        for table in sorted(REQUIRED_TABLES):
            check(
                table in existing_tables,
                f"Table exists: {table}"
            )

        for table, required in REQUIRED_COLUMNS.items():
            if table not in existing_tables:
                continue

            columns = {
                row[1]
                for row in conn.execute(
                    f"PRAGMA table_info({table})"
                )
            }

            for column in sorted(required):
                check(
                    column in columns,
                    f"{table}.{column}"
                )

        for table in sorted(REQUIRED_TABLES):
            if table in existing_tables:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

                print(f"[INFO] {table}: {count} rows")

        if "inventory" in existing_tables:
            negative_stock = conn.execute(
                """
                SELECT COUNT(*)
                FROM inventory
                WHERE current_stock < 0
                """
            ).fetchone()[0]

            check(
                negative_stock == 0,
                "No negative inventory"
            )

        if "stock_movements" in existing_tables:
            invalid_movements = conn.execute(
                """
                SELECT COUNT(*)
                FROM stock_movements
                WHERE quantity <= 0
                   OR movement_type NOT IN ('입고', '출고')
                   OR (
                       movement_type = '입고'
                       AND stock_after != stock_before + quantity
                   )
                   OR (
                       movement_type = '출고'
                       AND stock_after != stock_before - quantity
                   )
                """
            ).fetchone()[0]

            check(
                invalid_movements == 0,
                "Stock movement calculations"
            )

        fk_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        check(
            len(fk_errors) == 0,
            "Foreign key consistency"
        )

    except sqlite3.Error as error:
        print(f"[ERROR] {error}")
        errors.append(str(error))

    finally:
        conn.close()

    print("=" * 50)

    if errors:
        print(f"RESULT: {len(errors)} CHECK(S) FAILED")
        return 1

    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
