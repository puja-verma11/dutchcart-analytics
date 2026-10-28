"""
Export the 6 mart tables to CSV files for Tableau.

Reads the local DuckDB database (built with:  dbt build --target duckdb)
and writes one CSV per mart into the exports/ folder.

Run (from the project root, with the DuckDB UI closed):
    uv run python scripts/export_marts.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / "dutchcart.duckdb"
OUT = ROOT / "exports"
MARTS = ["fct_orders", "fct_order_items", "fct_marketing_daily",
         "dim_customers", "dim_products", "dim_date"]


def main():
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB_FILE), read_only=True)
    print(f"{'table':<22}{'rows':>10}")
    for table in MARTS:
        path = OUT / f"{table}.csv"
        con.execute(f"copy (select * from marts.{table}) to '{path}' (header, delimiter ',')")
        rows = con.execute(f"select count(*) from marts.{table}").fetchone()[0]
        print(f"{table:<22}{rows:>10,}")
    con.close()
    print(f"\nDone -> {OUT}")


if __name__ == "__main__":
    main()
