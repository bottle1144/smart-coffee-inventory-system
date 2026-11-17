from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="스마트 재고 관리 시스템",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = (BASE_DIR / "database" / "coffee_inventory.db")

st.markdown(
    """

    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"]{
        background-color: #f4f7fb;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5eaf1;
    }

    [data-testid="stMetricLabel"] {color: #526174;}

    [data-testid="stMetricValue"]{color: #17365d;}

    h1, h2, h3 {color: #17365d;}
    
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data(ttl=60)
def load_data():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB 파일이 없습니다: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        inventory_query = """
        SELECT
            s.store_location,
            p.product_id,
            p.product_category,
            p.product_detail,
            i.avg_daily_sales,
            i.current_stock,
            i.safety_stock,
            i.lead_time_days,
            i.reorder_point,
            i.days_until_stockout,
            i.risk_level
        FROM inventory AS i 
        JOIN stores AS s 
            on i.store_id = s.store_id 
        JOIN products AS p
            on i.product_id = p.product_id
        """

        inventory_df = pd.read_sql_query(inventory_query, conn)

        reorder_query = """
        SELECT 
            s.store_location,
            p.product_id,
            p.product_detail,
            r.target_stock,
            r.recommended_order_qty,
            r.final_order_qty,
            r.order_status
        FROM reorder_recommendations AS r 
        JOIN stores AS s
            ON r.store_id = s.store_id
        JOIN products AS p 
            ON r.product_id = p.product_id
        """

        reorder_df = pd.read_sql_query(reorder_query, conn)

        return inventory_df, reorder_df

    finally: conn.close()

try:
    inventory_df, reorder_df = load_data()

except Exception as error:
    st.error("데이터베이스 연결 오류")
    st.exception(error)
    st.stop()

st.title("📦 스마트 재고 관리 시스템")

st.caption(
    "Coffee Inventory BI Dashboard | "
    "SQLite + Pandas + Streamlit"
    )

st.divider()

st.sidebar.header("🔎 데이터 필터")

store_list = sorted(
    inventory_df["store_location"]
    .dropna()
    .unique()
    .tolist()
)

selected_store = st.sidebar.selectbox("매장 선택", ["전체 매장"] + store_list)

risk_options = ["전체", "정상", "주의", "위험", "품절"]
selected_risk = st.sidebar.selectbox("위험 등급 선택", risk_options)
search_product = st.sidebar.text_input("상품명 검색", placeholder="예: Latte")
st.sidebar.divider()
st.sidebar.info("필터를 변경하면 재고 현황과" "차트가 자동으로 업데이트됩니다.")

filtered_inventory = inventory_df.copy()
filtered_reorder = reorder_df.copy()

if selected_store != "전체 매장":
    filtered_inventory = filtered_inventory[
        filtered_inventory["store_location"]
        == selected_store
    ]
    filtered_reorder = filtered_reorder[
        filtered_reorder["store_location"]
        == selected_store
    ]

if selected_risk != "전체":
    filtered_inventory = filtered_inventory[
        filtered_inventory["risk_level"]
        == selected_risk
    ]
    risk_keys = filtered_inventory[
        ["store_location", "product_id"]
    ].drop_duplicates()
    filtered_reorder = filtered_reorder.merge(
        risk_keys, on=["store_location", "product_id"], how="inner"
    )

if search_product.strip():
    filtered_inventory = filtered_inventory[
        filtered_inventory["product_detail"]
        .fillna("")
        .str.contains(
            search_product, case=False, regex=False
        )
    ]
    filtered_reorder = filtered_reorder[
        filtered_reorder["product_detail"]
        .fillna("")
        .str.contains(
            search_product, case=False, regex=False
        )
    ]

total_products = len(filtered_inventory)
total_stock = int(filtered_inventory["current_stock"].sum())

risk_count = int(
    filtered_inventory["risk_level"]
    .isin(["품절", "위험", "주의"]).sum()
    )

order_count = int(
    (filtered_reorder["final_order_qty"] > 0).sum()
)

total_order_qty = int(
    filtered_reorder["final_order_qty"].sum()
)

st.subheader("📊 재고 핵심 지표")
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("관리 재고 항목", f"{total_products:,}개")
with col2: st.metric("총 재고 수량",f"{total_stock:,}개")
with col3: st.metric("품절 위험 항목", f"{risk_count:,} 개")
with col4: st.metric("발주 필요 항목", f"{order_count:,}개")
with col5: st.metric("추천 발주 수량", f"{total_order_qty:,}개")

st.divider()

st.subheader("📈 재고 분석 차트")
chart_col1, chart_col2 = st.columns(2)
with chart_col1: 
    st.markdown("#### 위험 등급별 재고 현황")
    risk_counts = (
        filtered_inventory["risk_level"]
        .value_counts()
        .reindex(
            ["정상","주의","위험","품절"],
            fill_value=0
        )
        .reset_index()
    )
    risk_counts.columns = ["risk_level", "count"]
    fig_risk = px.bar(
        risk_counts,
        x="risk_level",
        y="count",
        color="risk_level",
        color_discrete_map={
            "정상": "#2E8B57",
            "주의": "#F4B400",
            "위험": "#F97316",
            "품절": "#DC2626"
        },
        labels={"risk_level": "위험 등급", "count": "재고 항목 수"}
    )
    fig_risk.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_risk, width="stretch")

with chart_col2:
    st.markdown("### 매장별 재고 수량")
    store_stock = (
        filtered_inventory
        .groupby(
            "store_location",
            as_index=False
        )["current_stock"].sum()
    )
    fig_store = px.bar(
        store_stock,
        x="store_location",
        y="current_stock",
        color="store_location",
        labels={"store_location": "매장", "current_stock": "재고 수량"}
    )
    fig_store.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_store, width="stretch")

st.divider()

st.subheader("⚠️ 품절 위험 상품")

risk_products = filtered_inventory[
     filtered_inventory["risk_level"]
    .isin(["품절", "위험", "주의"])
].copy()
risk_priority = {"품절": 0, "위험": 1, "주의": 2}
risk_products["risk_priority"] = (risk_products["risk_level"].map(risk_priority))
risk_products = risk_products.sort_values(
    by=[
        "risk_priority",
        "days_until_stockout"
        ], ascending=[True, True]
)
risk_columns = [
    "store_location",
    "product_detail",
    "current_stock",
    "avg_daily_sales",
    "reorder_point",
    "days_until_stockout",
    "risk_level"
]
if risk_products.empty:
    st.success("현재 선택한 조건에 품절 위험 상품이 없습니다.")
else:
    st.dataframe(
        risk_products[risk_columns],
        width="stretch",
        hide_index=True
    ) 

st.divider()

st.subheader("🛒 자동 발주 추천")

order_products = filtered_reorder[filtered_reorder["final_order_qty"] > 0].copy()
order_products = order_products.sort_values(
    by="final_order_qty",
    ascending=False
)
order_columns = [
    "store_location",
    "product_detail",
    "target_stock",
    "recommended_order_qty",
    "final_order_qty",
    "order_status"
]
if order_products.empty:
    st.info("현재 선택한 조건에 발주 필요 상품이 없습니다.")
else:
    st.dataframe(
        order_products[order_columns],
        width="stretch",
        hide_index=True
    )

st.divider()

st.subheader("📋 전체 재고 상세 현황")
st.dataframe(
    filtered_inventory,
    width="stretch",
    hide_index=True
)

st.divider()

st.subheader("⬇️데이터 다운로드")
download_col1, download_col2 = st.columns(2)
with download_col1: 
    inventory_csv = (
        filtered_inventory
        .to_csv(index=False)
        .encode("utf-8-sig")
    )
    st.download_button(
        label="재고 현황 CSV 다운로드",
        data=inventory_csv,
        file_name="inventory_dashboard.csv",
        mime="text/csv",
        width="stretch"
    )
with download_col2:
    order_csv = (
        order_products
        .to_csv(index=False)
        .encode("utf-8-sig")
    )
    st.download_button(
        label="발주 추천 CSV 다운로드",
        data=order_csv,
        file_name="reorder_dashboard.csv",
        mime="text/csv",
        width="stretch"
    )

st.divider()

st.caption("스마트 재고 관리 시스템 |" " 8일차 Streamlit Dashboard")
st.caption("※ 현재 재고와 발주량은 학습용" "시뮬레이션 데이터입니다.")