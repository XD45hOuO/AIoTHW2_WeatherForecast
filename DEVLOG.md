# DEVLOG — AIoT HW2 完整開發紀錄

> 涵蓋從專案建立到最終完成的所有開發過程。

---

## 專案目標

使用 CWA Open Data API 獲取台灣六大地區（北部、中部、南部、東北部、東部、東南部）一週天氣預報資料，進行氣溫分析，並製作一個 Streamlit Web App 進行視覺化展示。

---

## 階段一：環境建置與資料擷取

### 1-1. 撰寫 `cwa_forecast.py`

使用 `requests` 呼叫 CWA API，取得六大地區一週預報。

**各地區資料集 ID：**

| 地區 | Dataset ID |
|------|------------|
| 北部 | F-D0047-069 |
| 東北部 | F-D0047-071 |
| 中部 | F-D0047-075 |
| 南部 | F-D0047-079 |
| 東部 | F-D0047-083 |
| 東南部 | F-D0047-085 |

**程式結構：**

| 函式 | 職責 |
|------|------|
| `fetch_forecast()` | 用 `requests.get()` 呼叫 CWA API，回傳 JSON dict |
| `preview_json()` | 用 `json.dumps` 序列化並印出前 600 字元供觀察 |
| `parse_region()` | 解析原始 API 資料，提取每鄉鎮每日天氣 |
| `save_json()` | 以地區分組儲存為 JSON |
| `save_csv()` | 儲存為 CSV（含 BOM，支援 Excel 開啟） |
| `print_summary()` | 印出各地區抓取結果摘要 |
| `main()` | 串接流程：抓資料 → 觀察 → 解析 → 儲存 → 摘要 |

---

### 1-2. 環境問題排除

**問題一：venv 路徑衝突**

```
Fatal error in launcher: Unable to create process using
'"C:\Users\Dash\Desktop\AIoTPjt3\venv\Scripts\python.exe" ...'
```

pip launcher 混用了另一個專案的 Python 執行檔。解法：重建 venv。

```bash
rm -rf venv
python -m venv venv
venv/Scripts/pip install requests python-dotenv
```

**問題二：SSL 憑證錯誤**

```
[SSL: CERTIFICATE_VERIFY_FAILED] Missing Subject Key Identifier
```

CWA 政府網站 SSL 憑證缺少 Subject Key Identifier。解法：加入 `verify=False` 並停用 urllib3 警告。

```python
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
resp = requests.get(url, params=params, timeout=30, verify=False)
```

---

### 1-3. CSV 空白問題排除

執行後 CSV 沒有任何資料，偵錯後發現 CWA API 回應的 JSON key 全為大寫開頭，與預期不符：

| 預期（錯誤） | 實際（正確） |
|-------------|-------------|
| `records.locations` | `records.Locations` |
| `location` | `Location` |
| `weatherElement` | `WeatherElement` |
| `time` | `Time` |
| `startTime` | `DataTime`（逐時）或 `StartTime`（區間） |

**實際 API 回應結構：**

```
records.Locations[0].Location[]
  └── LocationName
  └── WeatherElement[]
        └── ElementName
        └── Time[]
              └── DataTime        ← 溫度等逐時要素
              └── StartTime/EndTime ← 天氣現象、降雨機率（3小時區間）
              └── ElementValue[]
                    └── Temperature / Weather / WeatherCode /
                        ProbabilityOfPrecipitation / ...
```

其他修正：
- 降雨機率值有時回傳 `"-"`，加入 `try/except ValueError` 防止崩潰
- Windows CP950 終端機不支援 `⋮`、`✓`，改為 ASCII 字元

**最終輸出：**
- `taiwan_weekly_forecast.json`：以地區分組的可讀 JSON
- `taiwan_weekly_forecast.csv`：833 筆，可直接用 Excel 開啟

---

## 階段二：氣溫分析與資料庫

### 2-1. 撰寫 `analyze_temperature.py`

分析 JSON 中的氣溫資料，找出最高與最低氣溫。

**程式結構：**

| 函式 | 職責 |
|------|------|
| `load_data()` | 讀取 JSON 檔案 |
| `extract_temperatures()` | 提取 `maxTemp` / `minTemp` 欄位 |
| `analyze()` | 找全台最高/最低記錄，計算各地區統計 |
| `preview()` | 用 `json.dumps` 觀察任意資料 |
| `save_json()` | 寫出 JSON 檔案 |
| `initialize_database()` | 建立 SQLite `data.db` 與 `TemperatureForecasts` 資料表 |
| `save_records_to_database()` | 批次寫入氣溫資料 |
| `query_all_region_names()` | 查詢資料庫內所有地區名稱 |
| `query_region_temperatures()` | 查詢指定地區的氣溫資料 |
| `resolve_region_name()` | 以候選名稱找到實際存在的地區 |

**分析結果範例（2026-04-26 當日資料）：**

| 項目 | 數值 | 地點 |
|------|------|------|
| 全台最高氣溫 | 30°C | 北部 中和區 |
| 全台最低氣溫 | 16°C | 北部 烏來區 |

---

### 2-2. SQLite3 資料庫

**資料表定義：**

```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT    NOT NULL,
    dataDate   TEXT    NOT NULL,
    mint       INTEGER NOT NULL,
    maxt       INTEGER NOT NULL
)
```

**驗證查詢：**
- `query_all_region_names()`：列出所有地區（6 個）
- `query_region_temperatures("中部")`：列出中部所有氣溫記錄

**資料庫驗證結果：**
- 總筆數：833
- 地區數量：6（北部、中部、南部、東北部、東南部、東部）

---

### 2-3. 氣溫統計輸出

新增輸出 `temperature_highestnlowest.json`，結構如下：

```json
{
  "overall_max": { "region", "township", "date", "maxTemp", "minTemp" },
  "overall_min": { "region", "township", "date", "maxTemp", "minTemp" },
  "region_stats": {
    "地區名": {
      "maxTemp", "maxTownship", "maxDate",
      "minTemp", "minTownship", "minDate"
    }
  }
}
```

`region_stats` 初版只有 `maxTemp` / `minTemp`，後補上 `township` 與 `date`，完整記錄各地區極值的發生地點與日期。

---

## 階段三：Streamlit Web App 與最終完成

### 3-1. 撰寫 `streamlit_app.py`

**程式結構：**

| 函式 | 職責 |
|------|------|
| `refresh_data_on_startup()` | 啟動時呼叫 CWA API 並更新資料庫（`@st.cache_resource`） |
| `ensure_database_exists()` | 資料庫不存在時提早停止 |
| `fetch_region_names()` | 查詢所有地區名稱（`@st.cache_data`） |
| `fetch_weekly_temperature_summary()` | 查詢指定地區一週每日平均氣溫 |
| `build_chart_rows()` | 轉為折線圖 long format |
| `render_chart()` | Vega-Lite 折線圖 |
| `render_summary_metrics()` | 顯示預報天數、最低/最高平均氣溫 |
| `render_weekly_table()` | `st.dataframe` 表格 |
| `main()` | 組合整個頁面流程 |

---

### 3-2. 第二次 venv 重建

DEVLOG_2 重建的 venv 使用 `bin/` 目錄（Linux 格式），安裝 streamlit 時因缺少 Windows wheel 失敗：

```
error: metadata-generation-failed — numpy
ERROR: Could not find a version that satisfies the requirement numpy<2
```

解法：改用 PowerShell 以 Windows Python 3.13.13 重建：

```powershell
Remove-Item -Recurse -Force venv
python -m venv venv
venv\Scripts\pip install requests python-dotenv streamlit
```

安裝完成套件：streamlit 1.56.0、numpy 2.4.4、pandas 3.0.2 等。

---

### 3-3. 介面中文化

所有英文介面文字改為中文，包含頁面標題、下拉選單、折線圖軸標題、系列名稱、表格欄位、tooltip、摘要卡片。新增頁面 icon（`🌤`）。

---

### 3-4. 啟動時自動更新資料

**問題：** 北部資料只顯示到 4/22，因為資料庫存的是舊資料。

**解法：** 在 `main()` 最前面呼叫 `refresh_data_on_startup()`（`@st.cache_resource`，每次伺服器啟動執行一次）：

1. 呼叫六大地區 CWA API
2. 解析後覆寫 `taiwan_weekly_forecast.json`
3. 清空並重寫 SQLite 資料庫
4. 清除 `@st.cache_data` 快取確保查詢到最新資料

`streamlit_app.py` 直接從 `cwa_forecast` 與 `analyze_temperature` 匯入函式，避免重複程式碼。

---

### 3-5. 作業評分標準檢核結果

| 題目 | 配分 | 狀態 |
|------|------|------|
| HW2-1 獲取天氣預報資料 | 20% | ✅ 完整 |
| HW2-2 提取最高與最低氣溫 | 20% | ✅ 完整 |
| HW2-3 儲存到 SQLite3 | 20% | ✅ 完整 |
| HW2-4 Streamlit Web App | 40% | ✅ 完整 |

---

## 最終專案檔案清單

| 檔案 | 說明 |
|------|------|
| `cwa_forecast.py` | CWA API 擷取、解析，輸出 JSON 與 CSV |
| `analyze_temperature.py` | 氣溫提取、分析、寫入 SQLite、查詢驗證 |
| `streamlit_app.py` | Streamlit Web App，含啟動自動更新 |
| `requirements.txt` | `streamlit>=1.44,<2` |
| `data.db` | SQLite3 資料庫（TemperatureForecasts） |
| `taiwan_weekly_forecast.json` | 六地區一週天氣預報（以地區分組） |
| `taiwan_weekly_forecast.csv` | 同上，CSV 格式，含 BOM |
| `temperature_extract.json` | 精簡氣溫欄位資料 |
| `temperature_highestnlowest.json` | 全台及各地區最高/最低氣溫統計 |
| `.env` | CWA API Key（不納入版控） |
| `DEVLOG_1.md` | 階段一開發紀錄 |
| `DEVLOG_2.md` | 階段二開發紀錄 |
| `DEVLOG_3.md` | 階段三開發紀錄 |
| `DEVLOG.md` | 完整開發紀錄（本檔案） |
