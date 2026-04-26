import json
import sqlite3
from pathlib import Path

INPUT_FILE = "taiwan_weekly_forecast.json"
EXTRACT_OUTPUT_FILE = "temperature_extract.json"
SUMMARY_OUTPUT_FILE = "temperature_highestnlowest.json"
DATABASE_FILE = "data.db"
TABLE_NAME = "TemperatureForecasts"
CENTRAL_REGION_ALIASES = ("中部地區", "中部")


def load_data(filepath: str) -> dict:
    """Load the grouped forecast JSON file."""
    with open(filepath, encoding="utf-8") as file:
        return json.load(file)


def extract_temperatures(data: dict) -> list[dict]:
    """Flatten grouped JSON data into temperature records."""
    records: list[dict] = []

    for region_name, forecasts in data.items():
        for entry in forecasts:
            max_temp = entry.get("maxTemp")
            min_temp = entry.get("minTemp")

            if max_temp is None or min_temp is None:
                continue

            records.append(
                {
                    "regionName": region_name,
                    "township": entry.get("township", ""),
                    "dataDate": entry["date"],
                    "maxt": max_temp,
                    "mint": min_temp,
                }
            )

    return records


def analyze(records: list[dict]) -> dict:
    """Build max/min summaries for the full dataset and each region."""
    overall_max = max(records, key=lambda record: record["maxt"])
    overall_min = min(records, key=lambda record: record["mint"])

    region_stats: dict[str, dict] = {}
    for record in records:
        region_name = record["regionName"]
        stats = region_stats.setdefault(
            region_name,
            {
                "maxTemp": None,
                "maxTownship": None,
                "maxDate": None,
                "minTemp": None,
                "minTownship": None,
                "minDate": None,
            },
        )

        if stats["maxTemp"] is None or record["maxt"] > stats["maxTemp"]:
            stats["maxTemp"] = record["maxt"]
            stats["maxTownship"] = record["township"]
            stats["maxDate"] = record["dataDate"]

        if stats["minTemp"] is None or record["mint"] < stats["minTemp"]:
            stats["minTemp"] = record["mint"]
            stats["minTownship"] = record["township"]
            stats["minDate"] = record["dataDate"]

    return {
        "overall_max": overall_max,
        "overall_min": overall_min,
        "region_stats": region_stats,
    }


def preview(label: str, obj: object, indent: int = 2) -> None:
    """Pretty-print a JSON-serializable object."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(json.dumps(obj, ensure_ascii=False, indent=indent))


def save_json(filepath: str, data: object) -> None:
    """Write JSON output with UTF-8 encoding."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def initialize_database(database_path: str) -> None:
    """Create the SQLite database and temperature table."""
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regionName TEXT NOT NULL,
                dataDate TEXT NOT NULL,
                mint INTEGER NOT NULL,
                maxt INTEGER NOT NULL
            )
            """
        )
        connection.execute(f"DELETE FROM {TABLE_NAME}")
        connection.commit()


def save_records_to_database(database_path: str, records: list[dict]) -> None:
    """Insert all temperature records into SQLite."""
    rows = [
        (
            record["regionName"],
            record["dataDate"],
            record["mint"],
            record["maxt"],
        )
        for record in records
    ]

    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            f"""
            INSERT INTO {TABLE_NAME} (
                regionName,
                dataDate,
                mint,
                maxt
            ) VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()


def query_all_region_names(database_path: str) -> list[str]:
    """Return all distinct region names stored in the database."""
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            f"""
            SELECT DISTINCT regionName
            FROM {TABLE_NAME}
            ORDER BY regionName
            """
        )
        return [row[0] for row in cursor.fetchall()]


def query_region_temperatures(database_path: str, region_name: str) -> list[dict]:
    """Return all temperature rows for a single region."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            f"""
            SELECT id, regionName, dataDate, mint, maxt
            FROM {TABLE_NAME}
            WHERE regionName = ?
            ORDER BY dataDate, id
            """,
            (region_name,),
        )
        return [dict(row) for row in cursor.fetchall()]


def resolve_region_name(region_names: list[str], candidates: tuple[str, ...]) -> str:
    """Pick the first matching region name from a list of aliases."""
    for candidate in candidates:
        if candidate in region_names:
            return candidate
    raise ValueError(f"Could not find any matching region name in {candidates!r}")


def ensure_input_file_exists(filepath: str) -> None:
    """Fail fast with a clear message when the input file is missing."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")


def main() -> None:
    ensure_input_file_exists(INPUT_FILE)

    data = load_data(INPUT_FILE)
    region_count = len(data)
    forecast_count = sum(len(items) for items in data.values())
    print(f"Loaded {forecast_count} forecast rows from {region_count} regions.")

    records = extract_temperatures(data)
    print(f"Extracted {len(records)} temperature records.")
    preview("First 5 extracted temperature records", records[:5])

    result = analyze(records)
    preview("Overall highest temperature", result["overall_max"])
    preview("Overall lowest temperature", result["overall_min"])
    preview("Per-region summary", result["region_stats"])

    save_json(EXTRACT_OUTPUT_FILE, records)
    save_json(
        SUMMARY_OUTPUT_FILE,
        {
            "overall_max": result["overall_max"],
            "overall_min": result["overall_min"],
            "region_stats": result["region_stats"],
        },
    )
    print(f"\nSaved extracted records to {EXTRACT_OUTPUT_FILE}")
    print(f"Saved temperature summary to {SUMMARY_OUTPUT_FILE}")

    initialize_database(DATABASE_FILE)
    save_records_to_database(DATABASE_FILE, records)
    print(f"Saved temperature data to SQLite database {DATABASE_FILE}")

    all_regions = query_all_region_names(DATABASE_FILE)
    central_region_name = resolve_region_name(all_regions, CENTRAL_REGION_ALIASES)
    central_region_records = query_region_temperatures(DATABASE_FILE, central_region_name)

    preview("All region names in SQLite", all_regions)
    preview(f"{central_region_name} temperature records", central_region_records)


if __name__ == "__main__":
    main()
