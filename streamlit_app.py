import json
import sqlite3
from pathlib import Path

import streamlit as st

# 從現有模組匯入抓取、解析、資料庫函式
from cwa_forecast import fetch_forecast, parse_region, REGIONS
from analyze_temperature import (
    extract_temperatures,
    initialize_database,
    save_records_to_database,
)

DATABASE_FILE = "data.db"
FORECAST_FILE = "taiwan_weekly_forecast.json"
TABLE_NAME    = "TemperatureForecasts"


# ── 啟動時自動抓取（每次伺服器啟動執行一次） ──────────────────────────────────
@st.cache_resource
def refresh_data_on_startup() -> None:
    """
    Streamlit 伺服器啟動時執行一次：
    1. 向 CWA API 抓取六大地區最新一週預報
    2. 解析並儲存為 JSON
    3. 更新 SQLite 資料庫
    """
    all_rows: list[dict] = []

    for region, dataset_id in REGIONS.items():
        raw  = fetch_forecast(region, dataset_id)
        rows = parse_region(region, raw)
        all_rows.extend(rows)

    # 儲存 JSON（供其他程式使用）
    grouped: dict[str, list] = {}
    for row in all_rows:
        grouped.setdefault(row["region"], []).append(row)
    with open(FORECAST_FILE, "w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)

    # 更新資料庫
    records = extract_temperatures(grouped)
    initialize_database(DATABASE_FILE)
    save_records_to_database(DATABASE_FILE, records)


# ── 資料庫查詢 ────────────────────────────────────────────────────────────────
def ensure_database_exists(database_path: str) -> None:
    """資料庫檔案不存在時提早停止 App。"""
    if not Path(database_path).exists():
        st.error(f"找不到資料庫檔案：{database_path}")
        st.stop()


@st.cache_data
def fetch_region_names(database_path: str) -> list[str]:
    """從資料庫載入所有地區名稱。"""
    with sqlite3.connect(database_path) as conn:
        cursor = conn.execute(
            f"SELECT DISTINCT regionName FROM {TABLE_NAME} ORDER BY regionName"
        )
        return [row[0] for row in cursor.fetchall()]


@st.cache_data
def fetch_weekly_temperature_summary(database_path: str, region_name: str) -> list[dict]:
    """從 SQLite 查詢指定地區一週的每日平均氣溫。"""
    with sqlite3.connect(database_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            f"""
            SELECT
                dataDate,
                ROUND(AVG(mint), 1) AS avgMint,
                ROUND(AVG(maxt), 1) AS avgMaxt,
                COUNT(*) AS sourceCount
            FROM {TABLE_NAME}
            WHERE regionName = ?
            GROUP BY dataDate
            ORDER BY dataDate
            """,
            (region_name,),
        )
        return [dict(row) for row in cursor.fetchall()]


# ── 圖表 ──────────────────────────────────────────────────────────────────────
def build_chart_rows(weekly_rows: list[dict]) -> list[dict]:
    """將週資料轉為折線圖所需的 long format。"""
    chart_rows: list[dict] = []
    for row in weekly_rows:
        chart_rows.append({"日期": row["dataDate"], "系列": "平均最低氣溫", "氣溫": row["avgMint"]})
        chart_rows.append({"日期": row["dataDate"], "系列": "平均最高氣溫", "氣溫": row["avgMaxt"]})
    return chart_rows


def render_chart(chart_rows: list[dict]) -> None:
    """使用 Vega-Lite 渲染氣溫折線圖。"""
    st.vega_lite_chart(
        {
            "data": {"values": chart_rows},
            "mark": {"type": "line", "point": True, "strokeWidth": 3},
            "encoding": {
                "x": {
                    "field": "日期",
                    "type": "temporal",
                    "title": "日期",
                    "axis": {"format": "%m/%d"},
                },
                "y": {
                    "field": "氣溫",
                    "type": "quantitative",
                    "title": "氣溫（°C）",
                },
                "color": {
                    "field": "系列",
                    "type": "nominal",
                    "title": "系列",
                    "scale": {
                        "domain": ["平均最低氣溫", "平均最高氣溫"],
                        "range": ["#2C7FB8", "#D95F0E"],
                    },
                },
                "tooltip": [
                    {"field": "日期",  "type": "temporal",    "title": "日期"},
                    {"field": "系列",  "type": "nominal",     "title": "系列"},
                    {"field": "氣溫",  "type": "quantitative","title": "氣溫（°C）"},
                ],
            },
        },
        use_container_width=True,
    )


# ── UI 元件 ───────────────────────────────────────────────────────────────────
def render_summary_metrics(weekly_rows: list[dict]) -> None:
    """顯示所選地區的摘要數值。"""
    col1, col2, col3 = st.columns(3)
    col1.metric("預報天數",     f"{len(weekly_rows)} 天")
    col2.metric("最低平均低溫", f"{min(r['avgMint'] for r in weekly_rows):.1f} °C")
    col3.metric("最高平均高溫", f"{max(r['avgMaxt'] for r in weekly_rows):.1f} °C")


def render_weekly_table(weekly_rows: list[dict]) -> None:
    """顯示一週氣溫摘要表格。"""
    st.dataframe(
        weekly_rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "dataDate":    st.column_config.TextColumn("日期"),
            "avgMint":     st.column_config.NumberColumn("平均最低氣溫（°C）", format="%.1f"),
            "avgMaxt":     st.column_config.NumberColumn("平均最高氣溫（°C）", format="%.1f"),
            "sourceCount": st.column_config.NumberColumn("來源鄉鎮數"),
        },
    )


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="台灣一週氣溫預報",
        page_icon="🌤",
        layout="wide",
    )

    st.title("🌤 台灣一週氣溫預報")
    st.caption("資料來源：中央氣象署 CWA Open Data，由 SQLite 資料庫提供查詢。")

    # 啟動時抓取最新資料（顯示 spinner 提示使用者等待）
    with st.spinner("正在從 CWA API 抓取最新天氣預報..."):
        refresh_data_on_startup()

    # 清除快取以確保查詢到最新資料
    fetch_region_names.clear()
    fetch_weekly_temperature_summary.clear()

    ensure_database_exists(DATABASE_FILE)

    region_names = fetch_region_names(DATABASE_FILE)
    if not region_names:
        st.warning("資料庫中沒有找到任何氣溫資料。")
        st.stop()

    selected_region = st.selectbox("選擇地區", region_names)
    weekly_rows = fetch_weekly_temperature_summary(DATABASE_FILE, selected_region)

    if not weekly_rows:
        st.warning("所選地區目前沒有預報資料。")
        st.stop()

    render_summary_metrics(weekly_rows)
    st.divider()

    left_col, right_col = st.columns([2, 1])
    with left_col:
        st.subheader("一週氣溫趨勢圖")
        render_chart(build_chart_rows(weekly_rows))
    with right_col:
        st.subheader("查詢資訊")
        st.write(f"**地區：** {selected_region}")
        st.write(f"**回傳天數：** {len(weekly_rows)} 天")
        st.info("折線圖與表格以每日平均最低／最高氣溫彙整，資料來源為各鄉鎮預報紀錄。")

    st.divider()
    st.subheader("每日氣溫明細表")
    render_weekly_table(weekly_rows)


if __name__ == "__main__":
    main()
