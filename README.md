# AIoT HW2 — Taiwan Weekly Weather Forecast

A Python project that fetches Taiwan's weekly weather forecast from the CWA (Central Weather Administration) Open Data API, stores the data in SQLite, and visualises it with a Streamlit web app.

## Project Structure

```
AIoTHW2/
├── cwa_forecast.py          # Fetch & parse CWA API data → JSON / CSV
├── analyze_temperature.py   # Extract max/min temps → SQLite
├── streamlit_app.py         # Streamlit web app
├── requirements.txt
└── .env                     # CWA API key (create this yourself)
```

## Prerequisites

- Python 3.11 or later
- A CWA Open Data API key — register at https://opendata.cwa.gov.tw/userLogin

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/XD45hOuO/AIoTHW2_WeatherForecast.git
cd AIoTHW2_WeatherForecast
```

**2. Create a virtual environment and install dependencies**

```bash
python -m venv venv

# Windows
venv\Scripts\pip install -r requirements.txt
venv\Scripts\pip install requests python-dotenv

# macOS / Linux
venv/bin/pip install -r requirements.txt
venv/bin/pip install requests python-dotenv
```

**3. Set your CWA API key**

Create a `.env` file in the project root:

```
CWA_API_KEY=your_api_key_here
```

## Usage

### Option A — Run the Streamlit web app (recommended)

The app automatically fetches the latest forecast data from CWA every time it starts.

```bash
# Windows
venv\Scripts\streamlit run streamlit_app.py

# macOS / Linux
venv/bin/streamlit run streamlit_app.py
```

Open http://localhost:8501 in your browser. Use the dropdown to select a region and view the weekly temperature chart and table.

### Option B — Run scripts individually

**Step 1: Fetch forecast data**

Calls the CWA API for all 6 regions and saves `taiwan_weekly_forecast.json` and `taiwan_weekly_forecast.csv`.

```bash
# Windows
venv\Scripts\python cwa_forecast.py

# macOS / Linux
venv/bin/python cwa_forecast.py
```

**Step 2: Analyse temperatures and populate the database**

Extracts max/min temperatures, writes to `data.db`, and prints a validation query.

```bash
# Windows
venv\Scripts\python analyze_temperature.py

# macOS / Linux
venv/bin/python analyze_temperature.py
```

## Regions Covered

| Region | CWA Dataset ID |
|--------|----------------|
| 北部 (North) | F-D0047-069 |
| 東北部 (Northeast) | F-D0047-071 |
| 中部 (Central) | F-D0047-075 |
| 南部 (South) | F-D0047-079 |
| 東部 (East) | F-D0047-083 |
| 東南部 (Southeast) | F-D0047-085 |

## Output Files

| File | Description |
|------|-------------|
| `taiwan_weekly_forecast.json` | Parsed forecast grouped by region |
| `taiwan_weekly_forecast.csv` | Same data in CSV format (UTF-8 BOM, Excel-compatible) |
| `temperature_extract.json` | Flattened temperature records |
| `temperature_highestnlowest.json` | Overall and per-region max/min summary |
| `data.db` | SQLite database (`TemperatureForecasts` table) |

## SQLite Schema

```sql
CREATE TABLE TemperatureForecasts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT    NOT NULL,
    dataDate   TEXT    NOT NULL,
    mint       INTEGER NOT NULL,
    maxt       INTEGER NOT NULL
);
```

## Notes

- The CWA government server uses an SSL certificate that is missing the Subject Key Identifier extension. The code disables SSL verification (`verify=False`) for CWA requests only.
- `.env` and `data.db` are excluded from version control. Both are regenerated automatically on each run.
