from pathlib import Path
import math
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "demand_analysis.csv"
OUTPUT_PATH = BASE_DIR / "data" / "inventory.csv"

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        "demand_analysis.csv 파일이 없습니다. "
        "먼저 3일차 코드를 실행하세요."
    )

df = pd.read_csv(INPUT_PATH)

print("=== 4일차: 초기 재고 생성 ===")
print("전체 매장·상품 조합 수:", len(df))

INITIAL_STOCK_DAYS = 7 
SAFETY_STOCK_DAYS = 2
LEAD_TIME_DAYS = 3
MIN_INITIAL_STOCK = 5

df["current_stock"] = df["avg_daily_sales"].apply(
    lambda x: max(
        MIN_INITIAL_STOCK,
        math.ceil(x * INITIAL_STOCK_DAYS)
    )
)
df["safety_stock"] = df["avg_daily_sales"].apply(
    lambda x: math.ceil(x * SAFETY_STOCK_DAYS)
)
df["lead_time_days"] = LEAD_TIME_DAYS
df["reorder_point"] = df.apply(
    lambda row: math.ceil(
        row["avg_daily_sales"] *
        row["lead_time_days"] +
        row["safety_stock"]
    ), axis=1
)

def check_stock_status(row):
    if row["current_stock"] <= 0:
        return "품절"
    elif row["current_stock"] <= row["reorder_point"]:
        return "발주 필요"
    else:
        return "정상"

df["stock_status"] = df.apply(
    check_stock_status, axis=1
)
df["data_type"] = "simulation"
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print("\n초기 재고 데이터 TOP 10")
print(df[["store_location", "product_detail", "avg_daily_sales", "current_stock", "safety_stock", "reorder_point", "stock_status"]].head(10).to_string(index=False))
print("\n재고 상태별 상품 수 ")
print(df["stock_status"].value_counts())
print("\n저장 위치:", OUTPUT_PATH)
print("\n4일차 완료!")