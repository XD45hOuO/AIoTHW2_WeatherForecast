# DEVLOG 2

---

## 本次工作目標

本次延續前一份開發紀錄，主要完成兩個方向：

1. 將氣溫資料整理並存入 SQLite3 資料庫，方便後續查詢。
2. 使用 Streamlit 製作氣溫預報 Web App，將資料視覺化。

---

## 1. SQLite3 資料庫整合

### 完成內容

- 建立 SQLite3 資料庫檔案：`data.db`
- 建立資料表：`TemperatureForecasts`
- 由 `analyze_temperature.py` 將氣溫資料寫入資料庫
- 欄位包含：
  - `id`
  - `regionName`
  - `dataDate`
  - `mint`
  - `maxt`

### `analyze_temperature.py` 新增/整理的功能

- `initialize_database()`
  - 建立 `TemperatureForecasts` 資料表
- `save_records_to_database()`
  - 將抽出的氣溫資料批次寫入 SQLite
- `query_all_region_names()`
  - 查詢資料庫內所有地區名稱
- `query_region_temperatures()`
  - 查詢指定地區的氣溫資料
- `resolve_region_name()`
  - 嘗試用候選名稱找到實際存在的地區

### 資料驗證結果

已實際驗證資料有成功寫入資料庫。

- 總筆數：`833`
- 地區數量：`6`
- 地區名稱：
  - `中部`
  - `北部`
  - `南部`
  - `東北部`
  - `東南部`
  - `東部`

此外，也已查詢 `中部` 的氣溫資料，確認有正常回傳資料。

---

## 2. 氣溫分析程式整理

### 檔案

- `analyze_temperature.py`

### 目前程式職責

- 讀取 `taiwan_weekly_forecast.json`
- 抽出氣溫欄位，整理成扁平化資料
- 分析：
  - 全部資料中的最高溫
  - 全部資料中的最低溫
  - 各地區最高溫/最低溫摘要
- 輸出：
  - `temperature_extract.json`
  - `temperature_highestnlowest.json`
- 寫入 SQLite3 資料庫
- 查詢資料庫內容作為驗證

### 結構上的調整

目前已將流程分成多個職責明確的函式，整體邏輯比原本更清楚：

- 載入資料
- 抽取資料
- 分析資料
- 輸出 JSON
- 初始化資料庫
- 寫入資料庫
- 查詢驗證

---

## 3. Streamlit Web App 製作

### 新增檔案

- `streamlit_app.py`
- `requirements.txt`

### Web App 功能

`streamlit_app.py` 目前已完成以下功能：

- 從 SQLite3 資料庫 `data.db` 查詢資料
- 提供下拉選單讓使用者選擇地區
- 依照所選地區查詢一週氣溫資料
- 使用折線圖顯示：
  - 平均最低氣溫
  - 平均最高氣溫
- 使用表格顯示每一天的整理結果
- 顯示簡單摘要資訊：
  - 天數
  - 最低平均低溫
  - 最高平均高溫

### `streamlit_app.py` 的主要結構

- `ensure_database_exists()`
  - 檢查資料庫檔案是否存在
- `fetch_region_names()`
  - 查詢所有地區名稱
- `fetch_weekly_temperature_summary()`
  - 依地區查詢一週資料並做每日平均
- `build_chart_rows()`
  - 將資料轉為折線圖需要的格式
- `render_chart()`
  - 使用 Vega-Lite 顯示折線圖
- `render_summary_metrics()`
  - 顯示摘要數值
- `render_weekly_table()`
  - 顯示表格
- `main()`
  - 組合整個 Streamlit 頁面流程

### 設計上的選擇

- 圖表沒有依賴 `pandas`
- 直接使用 `streamlit` 與 `vega_lite_chart`
- 資料查詢固定來自 SQLite，而不是直接讀 JSON

---

## 4. 套件與執行環境狀態

### `requirements.txt`

目前內容為：

```txt
streamlit>=1.44,<2
```

### Python / venv 狀態

在嘗試執行 Web App 的過程中，發現原本的 `venv` 已損壞，無法正常啟動：

- 舊的 `venv\\Scripts\\python.exe` 無法執行
- 因此先將舊環境備份為：
  - `venv_backup_20260423_193947`
- 再重建新的 `venv`

### 新 `venv` 的狀態

目前新的虛擬環境已建立成功，但結構如下：

- `venv/bin/python.exe`
- `venv/bin/pip.exe`

也就是說，這個虛擬環境使用的是 `bin` 目錄，而不是一般 Windows 常見的 `Scripts` 目錄。

### Streamlit 安裝狀態

- `pip` 已成功安裝到新的 `venv`
- 但 `streamlit` 尚未確認安裝完成
- 原因是安裝流程在下載期間被中斷

因此目前狀態是：

- Web App 程式碼已完成
- 語法檢查已通過
- 但尚未在本機完成最終啟動驗證

---

## 5. 已完成的驗證

### 已完成

- `analyze_temperature.py` 可成功執行
- `data.db` 已建立
- `TemperatureForecasts` 已有資料
- `streamlit_app.py` 已通過 `py_compile` 語法檢查

### 尚未完成

- 在新的 `venv` 中完成 `streamlit` 安裝
- 用 `streamlit run streamlit_app.py` 實際啟動並檢查畫面

---

## 6. 目前專案中的關鍵檔案

| 檔案 | 說明 |
|------|------|
| `analyze_temperature.py` | 氣溫資料抽取、分析、寫入 SQLite、查詢驗證 |
| `data.db` | SQLite3 資料庫 |
| `streamlit_app.py` | Streamlit Web App 主程式 |
| `requirements.txt` | Web App 需要的套件 |
| `temperature_extract.json` | 扁平化後的氣溫資料 |
| `temperature_highestnlowest.json` | 最高溫 / 最低溫 / 各區摘要結果 |
| `venv_backup_20260423_193947` | 舊的損壞虛擬環境備份 |

---

## 下一步建議

1. 在新的 `venv` 中完成 `streamlit` 安裝。
2. 實際執行：
   - `venv/bin/python.exe -m streamlit run streamlit_app.py`
3. 將 Web App 介面文字改成中文版。
4. 視需求加入更多查詢條件，例如日期篩選或多地區比較。
