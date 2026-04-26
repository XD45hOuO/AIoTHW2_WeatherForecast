import csv
import json
import os

import requests
import urllib3
from dotenv import load_dotenv

# CWA 政府憑證缺少 Subject Key Identifier，停用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── 環境設定 ──────────────────────────────────────────────────────────────────
load_dotenv()

API_KEY  = os.getenv("CWA_API_KEY")
BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

# CWA 各地區「一週天氣預報」資料集 ID
REGIONS: dict[str, str] = {
    "北部":  "F-D0047-069",
    "東北部": "F-D0047-071",
    "中部":  "F-D0047-075",
    "南部":  "F-D0047-079",
    "東部":  "F-D0047-083",
    "東南部": "F-D0047-085",
}

PREVIEW_CHARS = 600
OUTPUT_JSON   = "taiwan_weekly_forecast.json"
OUTPUT_CSV    = "taiwan_weekly_forecast.csv"


# ── API 呼叫 ──────────────────────────────────────────────────────────────────
def fetch_forecast(region: str, dataset_id: str) -> dict:
    """呼叫 CWA API 取得指定地區一週天氣預報的原始 JSON。"""
    url    = f"{BASE_URL}/{dataset_id}"
    params = {"Authorization": API_KEY, "format": "JSON"}

    print(f"\n{'─' * 60}")
    print(f"[{region}] 正在請求 → {url}")

    try:
        resp = requests.get(url, params=params, timeout=30, verify=False)
        resp.raise_for_status()
        print(f"  狀態碼: {resp.status_code} OK")
        return resp.json()

    except requests.exceptions.HTTPError as e:
        print(f"  HTTP 錯誤: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"  連線錯誤: {e}")
    except requests.exceptions.Timeout:
        print("  請求逾時")
    except requests.exceptions.RequestException as e:
        print(f"  請求失敗: {e}")

    return {"error": "request failed", "region": region}


# ── 資料觀察 ──────────────────────────────────────────────────────────────────
def preview_json(label: str, data: dict, chars: int = PREVIEW_CHARS) -> None:
    """使用 json.dumps 將資料序列化後，印出前 chars 個字元以供觀察。"""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    print(f"\n【{label} — JSON 預覽（前 {chars} 字元）】")
    print(json_str[:chars])
    if len(json_str) > chars:
        print("  ... (已截斷，完整內容見輸出檔案)")


# ── 資料解析 ──────────────────────────────────────────────────────────────────
def parse_region(region_name: str, raw: dict) -> list[dict]:
    """
    從 F-D0047 原始 API 資料中，解析各鄉鎮每日天氣預報。

    回傳 list of dict，每筆包含：
        region, township, date, weather, weatherCode, maxTemp, minTemp, pop
    """
    if "error" in raw:
        return []

    try:
        locations = raw["records"]["Locations"][0]["Location"]
    except (KeyError, IndexError):
        return []

    rows: list[dict] = []

    for loc in locations:
        township = loc.get("LocationName", "")
        daily: dict[str, dict] = {}

        for el in loc.get("WeatherElement", []):
            times = el.get("Time", [])

            for t in times:
                # DataTime 用於溫度等逐時要素；StartTime 用於天氣現象與降雨機率
                raw_time = t.get("DataTime") or t.get("StartTime", "")
                date = raw_time[:10]
                if not date:
                    continue

                daily.setdefault(date, {
                    "region": region_name, "township": township, "date": date,
                    "weather": "", "weatherCode": "",
                    "maxTemp": None, "minTemp": None, "pop": None,
                })
                vals = t.get("ElementValue", [{}])
                v = vals[0] if vals else {}

                # 溫度（逐時）→ 累積後取 max/min
                if "Temperature" in v:
                    try:
                        temp = int(v["Temperature"])
                        d = daily[date]
                        d["maxTemp"] = temp if d["maxTemp"] is None else max(d["maxTemp"], temp)
                        d["minTemp"] = temp if d["minTemp"] is None else min(d["minTemp"], temp)
                    except ValueError:
                        pass

                # 天氣現象（取 12:00 白天時段）
                if "Weather" in v and "T12:00" in raw_time:
                    daily[date]["weather"]     = v.get("Weather", "")
                    daily[date]["weatherCode"] = v.get("WeatherCode", "")

                # 3小時降雨機率 → 取當日最大值
                if "ProbabilityOfPrecipitation" in v:
                    try:
                        pop = int(v["ProbabilityOfPrecipitation"])
                        d = daily[date]
                        d["pop"] = pop if d["pop"] is None else max(d["pop"], pop)
                    except ValueError:
                        pass

        rows.extend(sorted(daily.values(), key=lambda x: x["date"]))

    return rows


# ── 輸出 ──────────────────────────────────────────────────────────────────────
def save_json(all_rows: list[dict]) -> None:
    """將解析後的所有資料儲存為可讀 JSON。"""
    # 以地區分組
    grouped: dict[str, list] = {}
    for row in all_rows:
        grouped.setdefault(row["region"], []).append(row)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)

    print(f"\n  JSON 已儲存至：{OUTPUT_JSON}")


def save_csv(all_rows: list[dict]) -> None:
    """將解析後的所有資料儲存為 CSV。"""
    fieldnames = ["region", "township", "date", "weather", "weatherCode",
                  "maxTemp", "minTemp", "pop"]

    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"  CSV 已儲存至：{OUTPUT_CSV}")


# ── 摘要報告 ──────────────────────────────────────────────────────────────────
def print_summary(all_rows: list[dict]) -> None:
    print(f"\n{'═' * 60}")
    print("【各地區資料摘要】")
    print(f"{'═' * 60}")
    summary: dict[str, int] = {}
    for row in all_rows:
        summary[row["region"]] = summary.get(row["region"], 0) + 1
    for region, count in summary.items():
        print(f"  {region:6s}  OK {count} 筆（鄉鎮 x 日期）")


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main() -> None:
    all_rows: list[dict] = []

    for region, dataset_id in REGIONS.items():
        # 1. 呼叫 CWA API
        raw = fetch_forecast(region, dataset_id)

        # 2. 使用 json.dumps 觀察原始 JSON 結構
        preview_json(region, raw)

        # 3. 解析成可讀格式
        rows = parse_region(region, raw)
        all_rows.extend(rows)

    # 4. 儲存 JSON 與 CSV
    print(f"\n{'─' * 60}")
    print("【儲存輸出檔案】")
    save_json(all_rows)
    save_csv(all_rows)

    # 5. 印出摘要
    print_summary(all_rows)


if __name__ == "__main__":
    main()
