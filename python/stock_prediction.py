from pathlib import Path
import pandas as pd
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "inventory.csv"
OUTPUT_PATH = BASE_DIR / "data" / "stock_prediction.csv"

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        "inventory.csv 파일이 없습니다. "
        "먼저 4일차 코드를 실행하세요."
    )

df = pd.read_csv(INPUT_PATH)

print("=== 5일차: 품절 위험 예측 ===")
print("전체 재고 항목:", len(df))

required_columns = [
    "store_location",
    "product_detail",
    "current_stock",
    "avg_daily_sales",
    "lead_time_days",
    "reorder_point"
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"inventory.csv에 필요한 컬럼이 없습니다: {missing}"
    )

df["days_until_stockout"] = np.where(
    df["avg_daily_sales"] > 0,
    df["current_stock"] /
    df["avg_daily_sales"].replace(0, np.nan),
    np.inf
)

df["days_until_stockout"] = (
    df["days_until_stockout"].round(2)
)

def classify_risk(row):

    stock = row["current_stock"]
    days = row["days_until_stockout"]
    lead = row["lead_time_days"]
    reorder = row["reorder_point"]

    if stock <= 0:
        return "품절"

    elif days <= lead:
        return "위험"

    elif stock <= reorder:
        return "주의"

    else:
        return "정상"


df["risk_level"] = df.apply(
    classify_risk,
    axis=1
)

risk_order = {
    "품절": 0,
    "위험": 1,
    "주의": 2,
    "정상": 3
}

df["risk_order"] = df["risk_level"].map(risk_order)

print("정렬 전 컬럼:", df.columns.tolist())

df = df.sort_values(
    by=["risk_order", "days_until_stockout"],
    ascending=[True, True]
).reset_index(drop=True)

df = df.drop(columns=["risk_order"])

df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("\n위험 등급별 상품 수")
print(df["risk_level"].value_counts())

print("\n품절 위험 상품 TOP 10")

risk_df = df[
    df["risk_level"].isin(
        ["품절", "위험", "주의"]
    )
]

if risk_df.empty:
    print("현재 품절 위험 상품이 없습니다.")
else:
    print(
        risk_df[
            [
                "store_location",
                "product_detail",
                "current_stock",
                "avg_daily_sales",
                "days_until_stockout",
                "risk_level"
            ]
        ].head(10).to_string(index=False)
    )

print("\n저장 위치:", OUTPUT_PATH)
print("5일차 완료!")
