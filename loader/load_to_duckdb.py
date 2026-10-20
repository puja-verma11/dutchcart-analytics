"""
Loader: JSON-lines files -> DuckDB RAW tables (free, local, no account needed).

Same idea as load_to_snowflake.py, but the "warehouse" is one file: dutchcart.duckdb
Each RAW table gets the same 3 columns as in Snowflake:
    RECORD     the whole JSON line
    FILE_NAME  which file the row came from
    LOADED_AT  when we loaded it

It reads every file in data/archive/ (already loaded to Snowflake) AND data/landing/
(new, not loaded yet) and rebuilds the RAW tables from scratch, so it is safe to run
again and again. It does not move any files, so the Snowflake loader keeps working.

Run (from the project root):
    uv run python loader/load_to_duckdb.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / "dutchcart.duckdb"
FOLDERS = [ROOT / "data" / "archive", ROOT / "data" / "landing"]
TABLES = ["products", "customers", "inventory_snapshots", "web_events", "orders",
          "order_items", "payments", "shipments", "returns", "reviews", "marketing_spend"]


def main():
    con = duckdb.connect(str(DB_FILE))
    con.execute("create schema if not exists raw")
    print(f"{'table':<20}{'files':>7}{'rows':>10}")
    for table in TABLES:
        files = sorted(str(f) for folder in FOLDERS for f in (folder / table).glob("*.jsonl"))
        if not files:
            print(f"{table:<20}{0:>7}{'-':>10}")
            continue
        # read_json_objects = one JSON value per line, kept as JSON (like Snowflake VARIANT)
        con.execute(f"""
            create or replace table raw.{table} as
            select json                     as record,
                   filename                 as file_name,
                   current_timestamp        as loaded_at
            from read_json_objects(?, format = 'newline_delimited', filename = true)
        """, [files])
        rows = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        print(f"{table:<20}{len(files):>7}{rows:>10,}")
    con.close()
    print(f"\nDone -> {DB_FILE}")


if __name__ == "__main__":
    main()
