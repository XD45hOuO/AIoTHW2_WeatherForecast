# DEVLOG 1 — CWA 天氣預報資料擷取與分析

---

## 任務目標

使用 CWA Open Data API 獲取台灣六大地區（北部、中部、南部、東北部、東部、東南部）一週天氣預報資料，並進行氣溫分析。

---

## 1. 撰寫 `cwa_forecast.py`

### 需求
- 使用 `requests` 套件呼叫 CWA API
- 使用 `json.dumps` 觀察回傳資料
- 獲取六大地區一週天氣預報（JSON 格式）
- 良好的程式碼結構與可讀性

### 各地區資料集 ID

| 地區 | Dataset ID |
|------|------------|
| 北部 | F-D0047-069 |
| 東北部 | F-D0047-071 |
| 中部 | F-D0047-075 |
| 南部 | F-D0047-079 |
| 東部 | F-D0047-083 |
| 東南部 | F-D0047-085 |

### 程式結構

| 函式 | 職責 |
|------|------|
| `fetch_forecast()` | 用 `requests.get()` 呼叫 CWA API，回傳 JSON dict |
| `preview_json()` | 用 `json.dumps` 序列化並印出前 600 字元供觀察 |
| `print_summary()` | 印出各地區抓取結果摘要 |
| `main()` | 串接流程：抓資料 → 觀察 → 儲存 → 摘要 |

---

## 2. 環境建置問題排除

### 問題：venv 路徑衝突
執行 `pip install` 時出現錯誤：
```
Fatal error in launcher: Unable to create process using
'"C:\Users\Dash\Desktop\AIoTPjt3\venv\Scripts\python.exe"
"C:\Users\Dash\Desktop\AIoTHW2\venv\Scripts\pip.exe"'
```

### 原因
pip launcher 混用了另一個專案（`AIoTPjt3`）的 Python 執行檔。

### 解法：重建虛擬環境
```bash
cd c:/Users/Dash/Desktop/AIoTHW2
rm -rf venv
python -m venv venv
venv/Scripts/pip install requests python-dotenv
```

---

## 3. SSL 憑證錯誤

### 問題
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
Missing Subject Key Identifier (_ssl.c:1032)
```

### 原因
CWA 政府網站 SSL 憑證缺少 Subject Key Identifier extension。

### 解法
在 `requests.get()` 加入 `verify=False`，並用 `urllib3` 停用警告：
```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
resp = requests.get(url, params=params, timeout=30, verify=False)
```

---

## 4. 輸出 CSV 與 JSON

### 需求
將觀察到的資料轉換為可讀的 CSV 和 JSON 檔案。

### 新增函式

| 函式 | 職責 |
|------|------|
| `parse_region()` | 解析原始 API 資料，提取每鄉鎮每日天氣 |
| `save_json()` | 以地區分組儲存為 JSON |
| `save_csv()` | 儲存為 CSV（含 BOM，支援 Excel 開啟） |

### CSV 欄位
`region` / `township` / `date` / `weather` / `weatherCode` / `maxTemp` / `minTemp` / `pop`

---

## 5. CSV 空白問題排除

### 問題
執行後 CSV 檔案沒有任何資料。

### 偵錯過程
透過直接呼叫 API 並印出結構，發現 JSON key 命名與預期不符：

| 預期（錯誤） | 實際（正確） |
|-------------|-------------|
| `records.locations` | `records.Locations` |
| `location` | `Location` |
| `weatherElement` | `WeatherElement` |
| `elementName` | `ElementName` |
| `time` | `Time` |
| `startTime` | `DataTime`（逐時）或 `StartTime`（區間） |

### API 回應結構（實際）
```
records.Locations[0].Location[]
  └── LocationName
  └── WeatherElement[]
        └── ElementName
        └── Time[]
              └── DataTime        ← 溫度、風速等逐時要素
              └── StartTime/EndTime ← 天氣現象、降雨機率（3小時區間）
              └── ElementValue[]
                    └── Temperature / Weather / WeatherCode /
                        ProbabilityOfPrecipitation / ...
```

### 其他修正
- 降雨機率值有時為 `"-"`（無資料），加入 `try/except ValueError` 防止崩潰
- Windows 終端機（CP950）不支援 `⋮`、`✓` 等字元，改為 ASCII 替代

### 最終輸出
- `taiwan_weekly_forecast.json`：以地區分組的可讀 JSON
- `taiwan_weekly_forecast.csv`：833 筆資料，可直接用 Excel 開啟

---

## 6. 撰寫 `analyze_temperature.py`

### 需求
分析 JSON 中的氣溫資料，找出最高與最低氣溫，用 `json.dumps` 觀察結果。

### 程式結構

| 函式 | 職責 |
|------|------|
| `load_data()` | 讀取 JSON 檔案 |
| `extract_temperatures()` | 提取 `maxTemp` / `minTemp` 欄位（精簡版） |
| `analyze()` | 找全台最高/最低記錄，計算各地區統計 |
| `preview()` | 用 `json.dumps` 觀察任意資料 |
| `main()` | 串接流程，依序觀察各階段結果 |

### 輸出結果

| 項目 | 數值 | 地點 | 日期 |
|------|------|------|------|
| 全台最高氣溫 | 30°C | 北部 中和區 | 2026-04-20 |
| 全台最低氣溫 | 16°C | 北部 烏來區 | 2026-04-20 |

---

## 7. 儲存氣溫統計結果

### 新增輸出：`temperature_highestnlowest.json`

結構：
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

`region_stats` 初版只有 `maxTemp` / `minTemp`，後來補上 `township` 與 `date` 資訊，完整記錄各地區極值的發生地點與日期。

---

## 最終產出檔案

| 檔案 | 說明 |
|------|------|
| `cwa_forecast.py` | CWA API 擷取程式，輸出 JSON 與 CSV |
| `analyze_temperature.py` | 氣溫分析程式 |
| `taiwan_weekly_forecast.json` | 六地區一週天氣預報（833 筆） |
| `taiwan_weekly_forecast.csv` | 同上，CSV 格式 |
| `temperature_extract.json` | 僅含氣溫欄位的精簡資料 |
| `temperature_highestnlowest.json` | 全台及各地區最高/最低氣溫統計 |
