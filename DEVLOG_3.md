# DEVLOG 3 — Streamlit App 完成與作業檢核

---

## 本次工作目標

延續 DEVLOG_2，完成以下事項：

1. 修復 venv 環境（從 Linux 格式重建為 Windows 格式）
2. 安裝 Streamlit 並成功啟動 Web App
3. 將 App 介面全面中文化
4. 加入啟動時自動向 CWA API 抓取最新資料的功能
5. 修復資料只顯示到 4/22 的問題
6. 對照作業評分標準進行完整檢核

---

## 1. venv 環境修復

### 問題
DEVLOG_2 重建的 venv 使用 `bin/` 目錄（Linux 格式），而非 Windows 標準的 `Scripts/` 目錄。
執行 `pip install streamlit` 時出現：

```
error: metadata-generation-failed
numpy — could not find a version that satisfies the requirement
```

原因是 Linux 格式的 venv 無法找到 Windows 平台的預編譯 wheel。

### 解法：用 PowerShell 以系統 Python 重建 venv

```powershell
Remove-Item -Recurse -Force venv
python -m venv venv
venv\Scripts\pip install requests python-dotenv streamlit
```

系統 Python 版本：**3.13.13**
重建後 venv 結構恢復為標準 `Scripts/` 格式。

### 安裝結果

一次安裝成功，包含所有依賴：

| 套件 | 版本 |
|------|------|
| streamlit | 1.56.0 |
| numpy | 2.4.4 |
| pandas | 3.0.2 |
| requests | 2.33.1 |
| python-dotenv | 1.2.2 |

---

## 2. Streamlit App 介面中文化

`streamlit_app.py` 所有英文介面文字改為中文：

| 原文 | 中文 |
|------|------|
| `Temperature Forecast Dashboard` | `台灣一週氣溫預報` |
| `Choose a region` | `選擇地區` |
| `Days` | `預報天數` |
| `Lowest Avg Min` | `最低平均低溫` |
| `Highest Avg Max` | `最高平均高溫` |
| `Weekly Temperature Trend` | `一週氣溫趨勢圖` |
| `Average Min Temperature` | `平均最低氣溫` |
| `Average Max Temperature` | `平均最高氣溫` |
| `Date` / `Series` / `Temperature (deg C)` | `日期` / `系列` / `氣溫（°C）` |
| 表格欄位標題 | 全部改為中文 |

同時新增頁面 icon（`🌤`）與 `st.divider()` 分隔線，提升視覺層次。

---

## 3. 啟動時自動抓取最新資料

### 問題

使用者發現北部地區資料只顯示到 4/22，原因是資料庫存的是舊資料，App 沒有在啟動時重新抓取。

### 解法

在 `streamlit_app.py` 新增 `refresh_data_on_startup()`，使用 `@st.cache_resource` 裝飾，確保每次 Streamlit **伺服器啟動時執行一次**：

```python
@st.cache_resource
def refresh_data_on_startup() -> None:
    # 1. 逐一呼叫六大地區 CWA API
    # 2. 解析並儲存 taiwan_weekly_forecast.json
    # 3. 清空並重新寫入 SQLite 資料庫
```

### 執行流程整合

`streamlit_app.py` 直接從現有模組匯入函式，避免重複程式碼：

```python
from cwa_forecast import fetch_forecast, parse_region, REGIONS
from analyze_temperature import extract_temperatures, initialize_database, save_records_to_database
```

### UI 提示

抓取期間顯示 spinner：

```python
with st.spinner("正在從 CWA API 抓取最新天氣預報..."):
    refresh_data_on_startup()
```

抓取完成後清除 `@st.cache_data` 快取，確保查詢到最新資料：

```python
fetch_region_names.clear()
fetch_weekly_temperature_summary.clear()
```

---

## 4. 作業評分標準檢核

對照 HW2 全部四題需求逐項確認：

### HW2-1 獲取天氣預報資料（20%）

| 項目 | 狀態 | 說明 |
|------|------|------|
| 調用 CWA API 獲取六大地區資料（10%） | ✅ | `cwa_forecast.py` `fetch_forecast()` + `REGIONS` |
| 使用 `json.dumps` 觀察資料（5%） | ✅ | `preview_json()` 印出前 600 字元 |
| 程式碼結構與可讀性（5%） | ✅ | 各功能分為獨立函式，含 docstring 與區塊標題 |

### HW2-2 提取最高與最低氣溫（20%）

| 項目 | 狀態 | 說明 |
|------|------|------|
| 找出並提取最高/最低氣溫（10%） | ✅ | `analyze_temperature.py` `extract_temperatures()` + `analyze()` |
| 使用 `json.dumps` 觀察提取的資料（5%） | ✅ | `preview()` 觀察前5筆、全台極值、各區統計 |
| 程式碼結構與可讀性（5%） | ✅ | 載入、提取、分析、輸出各自獨立函式 |

### HW2-3 儲存到 SQLite3（20%）

| 項目 | 狀態 | 說明 |
|------|------|------|
| 建立 `data.db` + `TemperatureForecasts`（10%） | ✅ | `initialize_database()` |
| 欄位：id / regionName / dataDate / mint / maxt | ✅ | `CREATE TABLE` 定義 |
| 查詢所有地區名稱（5%） | ✅ | `query_all_region_names()` |
| 查詢中部地區氣溫資料（5%） | ✅ | `query_region_temperatures()` |
| 程式碼結構與可讀性（5%） | ✅ | |

### HW2-4 Streamlit Web App（40%）

| 項目 | 狀態 | 說明 |
|------|------|------|
| 下拉選單選擇地區（10%） | ✅ | `st.selectbox` |
| 折線圖（15%） | ✅ | Vega-Lite 折線圖，含最高/最低兩條線與 tooltip |
| 表格（15%） | ✅ | `st.dataframe` 含中文欄位標題 |
| 從 SQLite 查詢資料（10%） | ✅ | `fetch_weekly_temperature_summary()` |
| 程式碼結構與可讀性（5%） | ✅ | |

**結論：四題需求全部完成。**

---

## 5. 最終專案檔案清單

| 檔案 | 說明 |
|------|------|
| `cwa_forecast.py` | CWA API 擷取、解析，輸出 JSON 與 CSV |
| `analyze_temperature.py` | 氣溫提取、分析、寫入 SQLite、查詢驗證 |
| `streamlit_app.py` | Streamlit Web App，含啟動自動更新 |
| `requirements.txt` | `streamlit>=1.44,<2` |
| `data.db` | SQLite3 資料庫 |
| `taiwan_weekly_forecast.json` | 六地區一週天氣預報（以地區分組） |
| `taiwan_weekly_forecast.csv` | 同上，CSV 格式，含 BOM |
| `temperature_extract.json` | 精簡氣溫欄位資料 |
| `temperature_highestnlowest.json` | 全台及各地區最高/最低氣溫統計 |
| `.env` | CWA API Key（不納入版控） |
