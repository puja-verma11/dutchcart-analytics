"""
Loader = ingestion: moves files from data/landing (on your Mac) into Snowflake RAW tables.
Run:  python loader/load_to_snowflake.py
"""
import os
import shutil
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "data" / "landing"     # new files wait here
ARCHIVE = ROOT / "data" / "archive"     # files move here after upload
TABLES = ["products", "customers", "inventory_snapshots", "web_events", "orders",
          "order_items", "payments", "shipments", "returns", "reviews", "marketing_spend"]


def main():
    # 1. log in to Snowflake (login details come from the .env file)
    load_dotenv(ROOT / ".env")
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse="DUTCHCART_WH", database="DUTCHCART", schema="RAW")
    cur = conn.cursor()
    print(f"{'table':<20}{'files':>7}{'rows loaded':>13}")

    for table in TABLES:
        folder = LANDING / table
        files = sorted(folder.glob("*.jsonl")) if folder.exists() else []
        if not files:
            continue

        # 2. PUT = upload the files into the Snowflake "mailbox" (stage)
        cur.execute(f"PUT 'file://{folder.as_posix()}/*.jsonl' @LANDING_STAGE/{table}/ "
                    f"AUTO_COMPRESS=TRUE PARALLEL=8")

        # 3. COPY INTO = move rows from the mailbox into the RAW table
        #    (Snowflake remembers loaded files, so nothing is loaded twice)
        cur.execute(f"""COPY INTO {table.upper()} (RECORD, FILE_NAME)
                        FROM (SELECT $1, METADATA$FILENAME FROM @LANDING_STAGE/{table}/)
                        ON_ERROR = 'CONTINUE'""")
        cols = [c[0].lower() for c in cur.description]
        rows = sum(dict(zip(cols, r)).get("rows_loaded") or 0 for r in cur.fetchall())

        # 4. move uploaded files to the archive, so we don't upload them again
        (ARCHIVE / table).mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.move(str(f), ARCHIVE / table / f.name)
        print(f"{table:<20}{len(files):>7}{rows:>13,}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()