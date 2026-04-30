# CHAT.md — 對話紀錄

> 本檔案記錄開發過程中與 AI 助理的完整對話，依時間順序排列。

---

## 對話 1 — 撰寫 CWA 天氣預報程式

**User:**
使用 CWA API 獲取台灣北部、中部、南部、東北部、東部及東南部地區一週的天氣預報資料（必須是 JSON 格式）。程式需滿足以下條件：使用 Requests 套件調用 CWA API，使用 json.dumps 觀察獲得的資料，良好的程式碼結構與可讀性。

**Assistant:**
檢查現有檔案後，撰寫 `cwa_forecast.py`，包含以下函式：
- `fetch_forecast()` — 用 `requests.get()` 呼叫 CWA API
- `preview_json()` — 用 `json.dumps` 觀察資料
- `print_summary()` — 印出各地區摘要
- `main()` — 串接流程

六大地區 Dataset ID：北部 F-D0047-069、東北部 F-D0047-071、中部 F-D0047-075、南部 F-D0047-079、東部 F-D0047-083、東南部 F-D0047-085。

---

## 對話 2 — 詢問如何執行程式

**User:**
請問我要如何運行程式？

**Assistant:**
步驟一：安裝依賴套件
```bash
pip install requests python-dotenv
```
步驟二：在 `.env` 填入 CWA API Key（至 https://opendata.cwa.gov.tw/userLogin 申請）。
步驟三：執行 `python cwa_forecast.py`

---

## 對話 3 — venv 路徑衝突錯誤

**User:**
Fatal error in launcher: Unable to create process using '"C:\Users\Dash\Desktop\AIoTPjt3\venv\Scripts\python.exe" "C:\Users\Dash\Desktop\AIoTHW2\venv\Scripts\pip.exe" install requests python-dotenv'

**Assistant:**
這是 venv 路徑衝突問題，pip launcher 混用了別的專案的 Python。建議方案：
- 直接指定：`c:/Users/Dash/Desktop/AIoTHW2/venv/Scripts/pip install requests python-dotenv`
- 或啟動正確 venv 後再安裝

---

## 對話 4 — 重建虛擬環境

**User:**
請幫我重新建立我的虛擬環境，並安裝相應的套件。

**Assistant:**
執行以下步驟重建 venv 並安裝套件：
```bash
rm -rf venv
python -m venv venv
venv/Scripts/pip install requests python-dotenv
```
安裝成功：requests 2.33.1、python-dotenv 1.2.2。

---

## 對話 5 — SSL 憑證錯誤

**User:**
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Missing Subject Key Identifier

**Assistant:**
CWA 政府網站的已知 SSL 憑證問題。修正 `cwa_forecast.py`：
```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
resp = requests.get(url, params=params, timeout=30, verify=False)
```

---

## 對話 6 — 輸出 CSV 與 JSON

**User:**
請將觀察到的資料轉換成可讀的 CSV 檔和 JSON 檔。

**Assistant:**
新增 `parse_region()`、`save_json()`、`save_csv()` 函式。CSV 欄位：region / township / date / weather / weatherCode / maxTemp / minTemp / pop。

---

## 對話 7 — CSV 空白問題

**User:**
我的 CSV 檔沒有任何資料。

**Assistant:**
偵錯發現 CWA API 回應的 JSON key 全為大寫開頭，與預期不符：

| 預期（錯誤） | 實際（正確） |
|---|---|
| `records.locations` | `records.Locations` |
| `location` | `Location` |
| `weatherElement` | `WeatherElement` |
| `time` | `Time` |
| `startTime` | `DataTime` 或 `StartTime` |

另發現降雨機率值有時為 `"-"`，加入 `try/except ValueError` 防止崩潰。修正後 CSV 共 833 筆資料。

---

## 對話 8 — 撰寫氣溫分析程式

**User:**
分析天氣預報資料的 JSON 格式，找出最高與最低氣溫的資料位置，並提取出來。使用 json.dumps 觀察提取的資料，良好的程式碼結構與可讀性。

**Assistant:**
撰寫 `analyze_temperature.py`，包含：
- `extract_temperatures()` — 提取 maxTemp / minTemp
- `analyze()` — 找全台最高/最低，計算各地區統計
- `preview()` — 用 `json.dumps` 觀察資料
- `main()` — 串接流程

輸出結果：全台最高 30°C（北部中和區 4/20），全台最低 16°C（北部烏來區 4/20）。

---

## 對話 9 — 儲存氣溫統計結果

**User:**
請幫我把氣溫統計最高和最低的結果另外存到 "temperature_highestnlowest.json" 中。

**Assistant:**
在 `main()` 新增輸出：
```python
highest_lowest = {
    "overall_max": result["overall_max"],
    "overall_min": result["overall_min"],
    "region_stats": region_summary,
}
```
儲存至 `temperature_highestnlowest.json`。

---

## 對話 10 — 補充 township 與 date 資訊

**User:**
幫我在 region_stats 那邊也加入 township 和 date 的資訊。

**Assistant:**
更新 `analyze()` 中 `region_stats` 的資料結構，記錄極值發生的 `township` 與 `date`：
```json
{
  "北部": {
    "maxTemp": 30, "maxTownship": "中和區", "maxDate": "2026-04-20",
    "minTemp": 16, "minTownship": "烏來區", "minDate": "2026-04-20"
  }
}
```

---

## 對話 11 — 匯出 DEVLOG_1.md

**User:**
請幫我把到目前為止的對話放到 DEVLOG_1.md 中。

**Assistant:**
建立 `DEVLOG_1.md`，涵蓋 cwa_forecast.py 撰寫、環境問題排除、SSL 修正、CSV/JSON 輸出、CSV 空白偵錯、analyze_temperature.py 撰寫、temperature_highestnlowest.json 輸出等所有紀錄。

---

## 對話 12 — 延續 DEVLOG_2 繼續開發

**User:**
請幫我延續 DEVLOG_2.md 繼續撰寫專案。

**Assistant:**
閱讀 DEVLOG_2 後確認待完成項目：安裝 Streamlit、執行 Web App、介面中文化。發現 venv 為 Linux 格式（`bin/`），無法安裝 Windows wheel，改用 PowerShell 以 Python 3.13 重建 venv 並安裝所有套件（streamlit 1.56.0）。同時將 `streamlit_app.py` 介面全面中文化，啟動 App 於 http://localhost:8501。

---

## 對話 13 — 啟動時自動抓取最新資料

**User:**
幫我在每次 Streamlit 啟動時都抓取一次資料，我剛剛看北部只有顯示到 4/22 的資料。

**Assistant:**
在 `streamlit_app.py` 新增 `refresh_data_on_startup()`，使用 `@st.cache_resource` 確保每次伺服器啟動執行一次。直接從 `cwa_forecast` 和 `analyze_temperature` 匯入函式，抓取完成後清除 `@st.cache_data` 快取。App 重啟後資料即更新至最新。

---

## 對話 14 — 作業評分標準檢核

**User:**
（貼上 HW2-1 到 HW2-4 的完整評分標準）請幫我檢查我的專案是否完成這些事情。

**Assistant:**
逐一對照評分標準：

| 題目 | 配分 | 狀態 |
|------|------|------|
| HW2-1 獲取天氣預報資料 | 20% | ✅ 完整 |
| HW2-2 提取最高與最低氣溫 | 20% | ✅ 完整 |
| HW2-3 儲存到 SQLite3 | 20% | ✅ 完整 |
| HW2-4 Streamlit Web App | 40% | ✅ 完整 |

四題需求全部完成，沒有缺漏項目。

---

## 對話 15 — 建立 DEVLOG_3 與完整 DEVLOG

**User:**
請幫我撰寫一個 DEVLOG_3.md（裡面要有自從 DEVLOG_2.md 後的開發紀錄）與 DEVLOG.md（裡面寫從一開始到現在的過程，就是 DEVLOG 1+2+3 的概念）。

**Assistant:**
建立 `DEVLOG_3.md`（venv 重建、中文化、啟動自動抓取、作業檢核）與 `DEVLOG.md`（完整三階段開發紀錄，含最終檔案清單）。

---

## 對話 16 — 推送至 GitHub

**User:**
Please post this project to https://github.com/XD45hOuO/AIoTHW2_WeatherForecast

**Assistant:**
1. 初始化 git repo，新增 remote
2. 建立 `.gitignore`（排除 venv、`.env`、`data.db`、輸出檔案）
3. Commit 9 個檔案（cwa_forecast.py、analyze_temperature.py、streamlit_app.py、requirements.txt、DEVLOG*.md、.gitignore）
4. Push 成功至 https://github.com/XD45hOuO/AIoTHW2_WeatherForecast

---

## 對話 17 — 撰寫 README.md 並推送

**User:**
Please write a README.md of how to run this program and post to https://github.com/XD45hOuO/AIoTHW2_WeatherForecast

**Assistant:**
撰寫 `README.md`，包含：Prerequisites、Setup（clone/venv/套件/API Key）、Usage（Option A: Streamlit App、Option B: 分步執行）、Regions Covered、Output Files、SQLite Schema、Notes（SSL 說明）。Commit 並 push 成功。

---

## 對話 18 — 匯出完整對話紀錄

**User:**
請幫我將對話紀錄匯入到 CHAT.md

**Assistant:**
建立本檔案（CHAT.md），記錄所有對話的完整摘要。
---

## 對話 19 — 部署至 Streamlit Cloud

**User:**
請幫我把這個 demo 推到 Streamlit app 上。

**Assistant:**
為支援 Streamlit Cloud 部署，進行以下修改並 push 至 GitHub：

1. **`requirements.txt`** — 補上缺少的依賴：
   ```
   streamlit>=1.44,<2
   requests>=2.28
   python-dotenv>=1.0
   urllib3>=1.26
   ```

2. **`cwa_forecast.py`** — 將模組層級的 `API_KEY = os.getenv(...)` 改為動態函式，避免匯入時就固定值：
   ```python
   def _api_key() -> str:
       return os.getenv("CWA_API_KEY", "")
   ```

3. **`streamlit_app.py`** — 在匯入 `cwa_forecast` 之前，將 `st.secrets` 注入環境變數，相容本機 `.env` 與雲端 `st.secrets`：
   ```python
   if "CWA_API_KEY" in st.secrets:
       os.environ.setdefault("CWA_API_KEY", st.secrets["CWA_API_KEY"])
   ```

Push 成功後，提供 Streamlit Cloud 部署步驟：
- 前往 https://share.streamlit.io，以 GitHub 帳號登入
- New app → Repository: `XD45hOuO/AIoTHW2_WeatherForecast`，Branch: `master`，Main file: `streamlit_app.py`
- Advanced settings → Secrets 填入：`CWA_API_KEY = "你的CWA金鑰"`
- 點選 Deploy

---

## 對話 20 — 更新 CHAT.md

**User:**
請幫我把新增的聊天紀錄記錄到 CHAT.md。

**Assistant:**
在 CHAT.md 末尾新增對話 19（Streamlit Cloud 部署）與對話 20（本筆記錄），並 push 至 GitHub。

---

## 對話 21 — 執行 Streamlit Cloud 部署流程

**User:**
請依照以下步驟完成 Streamlit 部署：
1. 前往 https://share.streamlit.io 並登入（用 GitHub 帳號）
2. 點選 "New app" → 填入 Repository / Branch / Main file path
3. 點選 "Advanced settings" → Secrets，貼入 CWA_API_KEY
4. 點選 "Deploy"，等待部署完成。

**Assistant:**
自動讀取 `.env` 取得 CWA API 金鑰（`CWA-0AE80805-0D93-4073-A33D-103AD4734FE3`），透過瀏覽器自動化操作完成部署流程：

- Repository：`XD45hOuO/AIoTHW2_WeatherForecast`
- Branch：`master`
- Main file：`streamlit_app.py`
- Secrets：`CWA_API_KEY = "CWA-0AE80805-0D93-4073-A33D-103AD4734FE3"`

部署成功，App 已上線：  
🔗 https://aiothw2w-5ahxvovf5p9rfxrgcaywyf.streamlit.app/

截圖確認 App 正常顯示「台灣一週氣溫預報」，地區選擇中部，7 天預報，最低均溫 20.3°C、最高均溫 28.4°C，折線圖正常呈現。

---

## 對話 22 — 更新 CHAT.md

**User:**
請幫我把這段對話放到 CHAT.md 中。

**Assistant:**
在 CHAT.md 末尾新增對話 21（Streamlit Cloud 正式部署）與對話 22（本筆記錄），完成紀錄更新。
