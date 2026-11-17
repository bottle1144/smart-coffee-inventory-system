from pathlib import Path
import math
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "stock_prediction.csv"
OUTPUT_PATH = BASE_DIR / "data" / "reorder_recommendations.csv"

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        "stock_prediction.csv 파일이 없습니다.\n"
        "먼저 5일차 stock_prediction.py를 실행하세요."
    )

df = pd.read_csv(INPUT_PATH)

print("=== 6일차: 자동 발주량 계산 ===")
print("전체 재고 항목:", len(df))

required_columns = [
    "store_location",
    "product_id",
    "product_detail",
    "avg_daily_sales",
    "current_stock",
    "safety_stock",
    "lead_time_days",
    "reorder_point",
    "risk_level"
]

missing = [col for col in required_columns if col not in df.columns]
if missing: raise ValueError(f"필요한 컬럼이 없습니다: {missing}")

TARGET_STOCK_DAYS = 7 

def calculate_target_stock(row):
    daily_sales = row["avg_daily_sales"]
    lead_time = row["lead_time_days"]
    safety_stock = row["safety_stock"]

    target = (
        daily_sales * (lead_time + TARGET_STOCK_DAYS) + safety_stock
    )

    return math.ceil(target)

df["target_stock"] = df.apply(calculate_target_stock, axis=1)

df["recommended_order_qty"] = (df["target_stock"] - df["current_stock"]).clip(lower=0).astype(int)
df["order_required"] = (
    (df["current_stock"] <= df["reorder_point"]) & 
    (df["recommended_order_qty"] > 0)
)
df["final_order_qty"] = df.apply(
    lambda row: (
        row["recommended_order_qty"]
        if row["order_required"]
        else 0
    ), axis=1
)
df["order_status"] = df["order_required"].map(
    {
        True: "발주 필요",
        False: "발주 불필요"
    }
)
df = df.sort_values(
    by="final_order_qty",ascending=False
).reset_index(drop=True)

df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

orders = df[df["order_required"]]
print("\n발주 필요 상품 수:", len(orders))
print("총 추천 발주 수량:", int(orders["final_order_qty"].sum()))
print("\n발주 추천 TOP 10")

if orders.empty:
    print("현재 발주가 필요한 상품이 없습니다.")
else:
    print(
        orders[
            [
                "store_location",
                "product_detail",
                "current_stock",
                "reorder_point",
                "target_stock",
                "final_order_qty",
                "order_status"
            ]
        ].head(10).to_string(index=False)
    )

print("\n저장 위치:", OUTPUT_PATH)
print("6일차 완료!")
