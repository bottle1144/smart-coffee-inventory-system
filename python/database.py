from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "database"

DB_DIR.mkdir(parents=True, exist_ok=True)

INVENTORY_PATH = DATA_DIR / "inventory.csv"
PREDICTION_PATH = DATA_DIR / "stock_prediction.csv"
REORDER_PATH = DATA_DIR / "reorder_recommendations.csv"

DB_PATH = DB_DIR / "coffee_inventory.db"

print("=== 7일차: SQLite 데이터베이스 구축 ===")

files = [INVENTORY_PATH, PREDICTION_PATH, REORDER_PATH]
for file_path in files:
    if not file_path.exists():
        raise FileNotFoundError(f"필요한 파일이 없습니다: {file_path}")
print("CSV 파일 확인 완료!")

inventory_df = pd.read_csv(INVENTORY_PATH)
prediction_df = pd.read_csv(PREDICTION_PATH)
reorder_df = pd.read_csv(REORDER_PATH)

print("초기 재고 데이터:", len(inventory_df))
print("품절 예측 데이터:", len(prediction_df))
print("발주 추천 데이터:", len(reorder_df))

inventory_columns = [
    "store_location",
    "product_id",
    "product_category",
    "product_detail",
    "avg_daily_sales",
    "current_stock",
    "safety_stock",
    "lead_time_days",
    "reorder_point"
]

prediction_columns = [
    "store_location",
    "product_id",
    "risk_level",
    "days_until_stockout"
]

reorder_columns = [
    "store_location",
    "product_id",
    "target_stock",
    "recommended_order_qty",
    "final_order_qty",
    "order_status"
]

def check_columns(df, required, file_name):
    missing = [
        col for col in required 
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{file_name}에 없는 컬럼: {missing}"
        )

check_columns(
    inventory_df, inventory_columns, "inventory.csv"
)
check_columns(
    prediction_df, prediction_columns, "stock_prediction.csv"
)
check_columns(
    reorder_df, reorder_columns, "reorder_recommendations.csv"
)

stores_df = (
    inventory_df[["store_location"]]
    .drop_duplicates()
    .sort_values("store_location")
    .reset_index(drop=True)
)
stores_df.insert(0, "store_id", range(1, len(stores_df) + 1))

products_df = (
    inventory_df[
        [
            "product_id",
            "product_category",
            "product_detail"
        ]
    ]
    .drop_duplicates(subset=["product_id"])
    .copy()
)

keys = ["store_location", "product_id"]

risk_df = prediction_df[
    keys + ["risk_level", "days_until_stockout"].copy()
]

inventory_merged = inventory_df.merge(
    risk_df, on=keys, how="left", validate="one_to_one"
)
inventory_merged =  inventory_merged.merge(
    stores_df, on="store_location", how="left", validate="many_to_one"
)

inventory_table = inventory_merged[
    [
        "store_id",
        "product_id",
        "avg_daily_sales",
        "current_stock",
        "safety_stock",
        "lead_time_days",
        "reorder_point",
        "days_until_stockout",
        "risk_level"
    ]
].copy()

inventory_table["days_until_stockout"] = (
    inventory_table["days_until_stockout"]
    .replace([float("inf"), float("-inf")], None)
)

reorder_merged = reorder_df.merge(
    stores_df,
    on="store_location",
    how="left",
    validate="many_to_one"
)
reorder_table = reorder_merged[
    [
        "store_id",
        "product_id",
        "target_stock",
        "recommended_order_qty",
        "final_order_qty",
        "order_status"
    ]
].copy()

conn = sqlite3.connect(DB_PATH)

try:
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS stores (
        store_id INTEGER PRIMARY KEY,
        store_location TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        product_category TEXT,
        product_detail TEXT
    );
    CREATE TABLE IF NOT EXISTS inventory (
        store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        avg_daily_sales REAL NOT NULL,
        current_stock INTEGER NOT NULL,
        safety_stock INTEGER NOT NULL, 
        lead_time_days INTEGER NOT NULL, 
        reorder_point INTEGER NOT NULL,
        days_until_stockout REAL,
        risk_level TEXT,
        PRIMARY KEY (store_id, product_id),
        FOREIGN KEY (store_id) REFERENCES stores(store_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    CREATE TABLE IF NOT EXISTS reorder_recommendations (
        store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        target_stock INTEGER NOT NULL,
        recommended_order_qty INTEGER NOT NULL,
        final_order_qty INTEGER NOT NULL, 
        order_status TEXT,
        PRIMARY KEY (store_id, product_id),
        FOREIGN KEY (store_id) REFERENCES stores(store_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    conn.execute("DELETE FROM reorder_recommendations")
    conn.execute("DELETE FROM inventory")
    conn.execute("DELETE FROM products")
    conn.execute("DELETE FROM stores")

    stores_df.to_sql(
        "stores", conn, if_exists="append", index=False
    )
    products_df.to_sql(
        "products", conn, if_exists="append", index=False
    )
    inventory_table.to_sql(
        "inventory", conn, if_exists="append", index=False
    )
    reorder_table.to_sql(
        "reorder_recommendations", conn, if_exists="append", index=False)
    
    conn.commit()

    print("발주 추천 CSV 행 수:", len(reorder_df))
    print("DB 저장 대상 행 수", len(reorder_table))

    print("\n=== 데이터베이스 저장 결과 ===")

    for table in [ "stores", "products", "inventory", "reorder_recommendations"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}개")

    print("\n데이터베이스 저장 위치:", DB_PATH)
    print("7일차 데이터베이스 구축 완료!")

except Exception: 
    conn.rollback()
    raise

finally: conn.close()

