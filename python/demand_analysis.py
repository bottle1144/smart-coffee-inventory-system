from pathlib import Path 
import pandas as pd
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "Coffee_Shop_Sales.csv"
OUTPUT_PATH = BASE_DIR / "data" / "demand_analysis.csv"

if not INPUT_PATH.exists():
    raise FileNotFoundError("clean_sales.csv 파일이 없습니다." "먼저 2일차 코드를 실행하세요.")
df = pd.read_csv(INPUT_PATH, parse_dates=["transaction_date"])

print("=== 3일차: 상품별 수요 분석 ===")
print("전체 거래 행 수:", len(df))

last_date = df["transaction_date"].max()
start_date = last_date - pd.Timedelta(days=29)
recent_df = df[
    (df["transaction_date"] >= start_date) &
    (df["transaction_date"] <= last_date)
].copy()

print("분석 시작일:", start_date.date())
print("분석 종료일:", last_date.date())

product_list = (
    df[
        [
            "store_location","product_id", "product_category", "product_detail"
        ]
    ]
    .drop_duplicates(subset=["store_location", "product_id"]).copy()
)

sales_summary = (
    recent_df.groupby(
        ["store_location", "product_id"], as_index=False
    )["transaction_qty"].sum()
)
sales_summary = sales_summary.rename(columns={"transaction_qty": "sales_30days"})

demand = product_list.merge(
    sales_summary, on=["store_location", "product_id"], how="left"
)
demand["sales_30days"] = (demand["sales_30days"].fillna(0))
demand["avg_daily_sales"] = (demand["sales_30days"] / 30).round(2)
demand = demand.sort_values(
    "avg_daily_sales", ascending=False
).reset_index(drop=True)
demand.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print("\n분석된 매장·상품 조합 수:", len(demand))
print("\n일평균 판매량 TOP 10")
print(demand[["store_location", "product_detail", "sales_30days", "avg_daily_sales"]].head(10).to_string(index=False))
print("\n저장 위치:",OUTPUT_PATH)
print("\n3일차 완료!")