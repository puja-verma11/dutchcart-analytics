# DutchCart Analytics

**An end-to-end e-commerce analytics project for a (simulated) Dutch online shop.**
Python → Snowflake → dbt → SQL analysis → Power BI

---

## The business problem

DutchCart is a fictional Dutch online shop selling Fashion, Shoes, Electronics, Home, Beauty and Sports, delivered by PostNL, DHL and DPD.

Sales are coming in, but management suspects **profit is leaking**:

- many **returns**, especially in Fashion and Shoes
- rising **ad spend** across Google, Instagram, TikTok, TV and radio, with no clear view of what pays off
- complaints about **late parcels**
- many website visitors **leave without buying**

The CEO's question:

> **"Where are we losing money, and where should we put next quarter's budget?"**

## Stakeholders and the questions this project answers

| Stakeholder | Question | KPI |
|---|---|---|
| CEO / Finance | Are we growing? Where does revenue come from? | Revenue, orders, average order value (AOV) |
| Marketing | Which channel is worth the money? | ROAS (revenue ÷ ad spend) per channel |
| Customer / CRM | Do customers come back? | Repeat customer rate, customer value segments |
| Operations | Which carrier is late, and what does it cost us? | Late delivery %, returns and bad reviews after late delivery |
| Category / Buying | Which categories lose money through returns? | Return rate and revenue lost per category |
| E-commerce / Web | Where do visitors drop off? | Funnel conversion: view → cart → checkout → purchase |

## Architecture

```
Python generator  →  landing files (JSON lines)  →  Snowflake RAW  →  dbt STAGING  →  dbt MARTS  →  analysis / Power BI
 (history + live)       data/landing/<table>/        PUT + COPY INTO    clean, typed,      facts and
                                                     (loader script)    tested views       dimensions
```

| Layer | Snowflake schema | What happens |
|---|---|---|
| **Raw** (bronze) | `RAW` | Files loaded as-is into a `VARIANT` column, with file name and load time |
| **Staging** (silver) | `STAGING` | One view per source: JSON unpacked, columns renamed and typed, bad data fixed or flagged |
| **Marts** (gold) | `MARTS` | Business-ready tables in a star schema: facts (events) and dimensions (who / what) |

## Data

The data is **simulated with realistic business patterns** by `generator/live_feed.py`: 11 source tables (orders, order items, products, customers, payments, shipments, returns, reviews, web events, inventory snapshots, marketing spend), 180 days of history, plus "live" batches on demand.

Data-quality problems are added **on purpose**, so the pipeline has real issues to solve:

| Problem | How it is handled |
|---|---|
| Prices stored as text (`"€19,99"`) | **Fixed** in staging: cleaned and cast to a number |
| Duplicate web events | **Removed** with `row_number()` + `qualify` |
| Orders dated in the future | **Flagged** in staging, **excluded** from marts |
| Missing email, postcode or delivery date | **Flagged** (`is_missing_...`), not deleted |

Rule used: *fix what is certain, flag what is not.*

## Data quality and testing

Every model is tested with dbt (all passing):

- `unique` / `not_null` on every key, which also guards against join fan-out in the marts
- `relationships`, e.g. every order item belongs to an existing order and product
- `accepted_values` for statuses, channels, carriers, payment methods and so on
- **Reconciliation test**: the sum of order-item revenue must match each order's subtotal (source-to-target check)

## dbt models

**Staging (11):** `stg_orders`, `stg_order_items`, `stg_products`, `stg_customers`, `stg_payments`, `stg_shipments`, `stg_returns`, `stg_reviews`, `stg_web_events`, `stg_inventory_snapshots`, `stg_marketing_spend`

**Marts:**

| Model | Grain (one row =) | Status |
|---|---|---|
| `fct_orders` | one order (with items, delivery, return and review info) | ✅ |
| `dim_customers` | one customer (lifetime orders, revenue, repeat flag, value segment) | ✅ |
| `fct_order_items` + `dim_products` | one product in an order / one product | planned |
| `fct_marketing_daily` | one channel per day (spend vs revenue) | planned |
| `fct_sessions` | one website visit (funnel) | planned |

## Project structure

```
dutchcart-analytics/
├── generator/live_feed.py         # simulates the shop (history + live batches)
├── loader/load_to_snowflake.py    # PUT + COPY INTO Snowflake RAW, then archives files
├── dutchcart/                     # dbt project
│   ├── models/staging/            # 11 staging models + sources + tests
│   ├── models/marts/              # facts and dimensions
│   ├── macros/                    # custom schema naming (STAGING / MARTS)
│   └── tests/                     # custom data tests (reconciliation)
├── snowflake/sql/                 # exploration queries
├── pyproject.toml / uv.lock       # Python dependencies (uv)
└── README.md
```

## How to run

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/), a Snowflake account.

```bash
# 1. install dependencies
uv sync

# 2. Snowflake login for the loader: create a .env file (never committed)
#    SNOWFLAKE_ACCOUNT=...  SNOWFLAKE_USER=...  SNOWFLAKE_PASSWORD=...
#    and a dbt profile in ~/.dbt/profiles.yml (profile name: dutchcart)

# 3. generate data
uv run python generator/live_feed.py history --days 180
uv run python generator/live_feed.py live --batches 10 --interval 5   # optional: new data

# 4. load into Snowflake RAW
uv run python loader/load_to_snowflake.py

# 5. build and test all models
cd dutchcart
uv run dbt build
```

## Roadmap

- [x] Data generator with realistic dirty data
- [x] Snowflake loader (internal stage, COPY INTO)
- [x] dbt staging layer with tests
- [x] First marts: `fct_orders`, `dim_customers`
- [ ] Remaining marts (products, marketing, funnel)
- [ ] SQL analysis per stakeholder question
- [ ] Power BI dashboard
- [ ] Insights memo: 3 findings and 3 recommendations
- [ ] CI with GitHub Actions (`dbt build` on every pull request)

## Key findings

*Coming after the analysis step.*

---

**Author:** Puja Verma · [LinkedIn](https://linkedin.com/in/puja-verma-19b668103) · [GitHub](https://github.com/puja-verma11)
