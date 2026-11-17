from pathlib import Path 
import pandas as pd
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "Coffee_Shop_Sales.csv"
OUTPUT_PATH = BASE_DIR / "data" / "clean_sales.csv"

df = pd.read_csv(INPUT_PATH)

print("전처리 전 데이터:", df.shape)

df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="%m/%d/%y", errors="coerce")
columns = [ "transaction_date", "store_location", "product_id", "product_category", "product_detail",
           "transaction_qty", "unit_price"]
df = df[columns].copy()
df["transaction_qty"] = pd.to_numeric(df["transaction_qty"], errors="coerce")
df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
df = df.dropna(subset=columns)
df = df[(df["transaction_qty"] > 0) & (df["unit_price"] >= 0)].copy()
df = df.sort_values("transaction_date")
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print("전처리 후 데이터:", df.shape)
print("저장 위치:", OUTPUT_PATH)
print("2일차 완료")