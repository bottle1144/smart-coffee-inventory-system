from pathlib import Path
import pandas as pd
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "Coffee_Shop_Sales.csv"

if not CSV_PATH.exists():
    raise FileNotFoundError(f"파일을 찾을 수 없습니다: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)

print("=== 커피 판매 데이터 확인 ===")
print("전체 거래 수:", len(df))
print("매장 수:", df["store_location"].nunique())
print("상품 수:", df["product_id"].nunique())
print("\n데이터 미리보기")
print(df.head())
print("\n1일차 완료!")