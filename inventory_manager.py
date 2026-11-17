
import sqlite3
import math
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "coffee_inventory.db"

TARGET_STOCK_DAYS = 7

def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"DB 파일을 찾을 수 없습니다: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                stock_before INTEGER NOT NULL,
                stock_after INTEGER NOT NULL,
                memo TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (store_id)
                    REFERENCES stores(store_id),
                FOREIGN KEY (product_id)
                    REFERENCES products(product_id)
            )
        """)

def get_stores():
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT store_id, store_location
            FROM stores
            ORDER BY store_location
            """,
            conn
        )

def get_products(store_id):
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                i.product_id,
                p.product_detail,
                i.current_stock,
                i.avg_daily_sales,
                i.risk_level
            FROM inventory AS i
            JOIN products AS p
                ON i.product_id = p.product_id
            WHERE i.store_id = ?
            ORDER BY p.product_detail, i.product_id
            """,
            conn,
            params=(int(store_id),)
        )

def calculate_risk(
    current_stock,
    avg_daily_sales,
    lead_time_days,
    reorder_point
):
    if current_stock <= 0:
        return "품절", 0.0

    if avg_daily_sales <= 0:
        days_until_stockout = None
    else:
        days_until_stockout = round(
            current_stock / avg_daily_sales, 2
        )

    if (
        days_until_stockout is not None
        and days_until_stockout <= lead_time_days
    ):
        risk_level = "위험"

    elif current_stock <= reorder_point:
        risk_level = "주의"

    else:
        risk_level = "정상"

    return risk_level, days_until_stockout

def calculate_reorder(
    current_stock,
    avg_daily_sales,
    lead_time_days,
    safety_stock,
    reorder_point
):
    target_stock = math.ceil(
        avg_daily_sales *
        (lead_time_days + TARGET_STOCK_DAYS)
        + safety_stock
    )

    recommended_qty = max(
        0, target_stock - current_stock
    )

    order_required = (
        current_stock <= reorder_point
        and recommended_qty > 0
    )

    final_order_qty = (
        recommended_qty if order_required else 0
    )

    order_status = (
        "발주 필요" if order_required
        else "발주 불필요"
    )

    return (
        target_stock,
        recommended_qty,
        final_order_qty,
        order_status
    )

def process_stock_movement(
    store_id,
    product_id,
    movement_type,
    quantity,
    memo=""
):
    if movement_type not in ("입고", "출고"):
        raise ValueError("입고 또는 출고를 선택하세요.")

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity <= 0
    ):
        raise ValueError("수량은 1 이상의 정수여야 합니다.")

    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            """
            SELECT
                current_stock,
                avg_daily_sales,
                safety_stock,
                lead_time_days,
                reorder_point
            FROM inventory
            WHERE store_id = ?
              AND product_id = ?
            """,
            (int(store_id), int(product_id))
        ).fetchone()

        if row is None:
            raise ValueError("상품 재고를 찾을 수 없습니다.")

        (
            stock_before,
            daily_sales,
            safety_stock,
            lead_time,
            reorder_point
        ) = row

        stock_before = int(stock_before)

        if movement_type == "입고":
            stock_after = stock_before + quantity

        else:
            if quantity > stock_before:
                raise ValueError(
                    f"재고 부족! 현재 재고는 "
                    f"{stock_before}개입니다."
                )

            stock_after = stock_before - quantity

        risk_level, days = calculate_risk(
            stock_after,
            daily_sales,
            lead_time,
            reorder_point
        )

        (
            target_stock,
            recommended_qty,
            final_order_qty,
            order_status
        ) = calculate_reorder(
            stock_after,
            daily_sales,
            lead_time,
            safety_stock,
            reorder_point
        )

        conn.execute(
            """
            UPDATE inventory
            SET current_stock = ?,
                days_until_stockout = ?,
                risk_level = ?
            WHERE store_id = ?
              AND product_id = ?
            """,
            (
                stock_after,
                days,
                risk_level,
                int(store_id),
                int(product_id)
            )
        )

        cursor = conn.execute(
            """
            UPDATE reorder_recommendations
            SET target_stock = ?,
                recommended_order_qty = ?,
                final_order_qty = ?,
                order_status = ?
            WHERE store_id = ?
              AND product_id = ?
            """,
            (
                target_stock,
                recommended_qty,
                final_order_qty,
                order_status,
                int(store_id),
                int(product_id)
            )
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "발주 추천 데이터를 찾을 수 없습니다."
            )

        created_at = (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        )

        conn.execute(
            """
            INSERT INTO stock_movements (
                store_id,
                product_id,
                movement_type,
                quantity,
                stock_before,
                stock_after,
                memo,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(store_id),
                int(product_id),
                movement_type,
                quantity,
                stock_before,
                stock_after,
                str(memo).strip(),
                created_at
            )
        )

        conn.commit()

        return {
            "stock_before": stock_before,
            "stock_after": stock_after,
            "risk_level": risk_level,
            "final_order_qty": final_order_qty
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_stock_movements(store_id=None):
    query = """
        SELECT
            m.movement_id,
            m.created_at,
            s.store_location,
            p.product_detail,
            m.product_id,
            m.movement_type,
            m.quantity,
            m.stock_before,
            m.stock_after,
            m.memo
        FROM stock_movements AS m
        JOIN stores AS s
            ON m.store_id = s.store_id
        JOIN products AS p
            ON m.product_id = p.product_id
    """

    params = []

    if store_id is not None:
        query += " WHERE m.store_id = ?"
        params.append(int(store_id))

    query += """
        ORDER BY m.movement_id DESC
        LIMIT 500
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query, conn, params=params
        )


if __name__ == "__main__":
    initialize_database()
    print("9일차 재고 관리 모듈 준비 완료")
