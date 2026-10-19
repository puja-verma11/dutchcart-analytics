"""
DutchCart data generator
------------------------
Pretends to be the backend of a Dutch online shop and writes raw JSON-lines
files into data/landing/<table>/ (this folder plays the role of a cloud bucket).

Two modes:
  history  - creates the past N days in one go (run once, at the start)
             python generator/live_feed.py history --days 180
  live     - adds new data "right now", on demand
             python generator/live_feed.py live --batches 10 --interval 5

Tables produced (raw, like real source systems):
  products, customers, inventory_snapshots,
  web_events, orders, order_items, payments, shipments, returns, reviews,
  marketing_spend

Dirty data is added ON PURPOSE (duplicates, nulls, "€19,99" text prices,
orders dated next year, shipments without delivery date) so the cleaning
step in dbt has real problems to solve.

The shop "remembers" its customers and open orders in data/state.json,
so live data continues where the history stopped.
"""
import argparse
import json
import random
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "data" / "landing"
STATE_FILE = ROOT / "data" / "state.json"
fake = Faker("nl_NL")

# ---------------- fixed catalogue (same every run: seed 42) ----------------
CATEGORIES = {
    #  category      price range   return rate  margin
    "Fashion":      ((15, 120),     0.35,        0.55),
    "Shoes":        ((40, 160),     0.30,        0.50),
    "Electronics":  ((25, 900),     0.06,        0.15),
    "Home":         ((10, 250),     0.08,        0.40),
    "Beauty":       ((5, 60),       0.03,        0.60),
    "Sports":       ((12, 200),     0.10,        0.45),
}
_rng = random.Random(42)
PRODUCTS = []
for cat, ((lo, hi), _, margin) in CATEGORIES.items():
    for i in range(1, 11):
        price = round(_rng.uniform(lo, hi), 2)
        PRODUCTS.append({"product_id": f"{cat[:3].upper()}-{i:03d}", "product_name": f"{cat} item {i}",
                         "category": cat, "price": price, "cost": round(price * (1 - margin), 2),
                         "stock": _rng.randint(20, 80)})
PRODUCT_BY_ID = {p["product_id"]: p for p in PRODUCTS}

CHANNELS = {"organic": 0.30, "google_ads": 0.25, "instagram": 0.15,
            "email": 0.12, "affiliate": 0.10, "tiktok": 0.08}
PROMOS = [None] * 7 + ["WELCOME10", "SUMMER15", "FREESHIP"]
PAY_METHODS = {"ideal": (0.55, 0.02), "klarna": (0.20, 0.08),      # (share, fail rate)
               "card": (0.15, 0.06), "paypal": (0.10, 0.03)}
CARRIERS = {"PostNL": (2, 0.12), "DHL": (2, 0.08), "DPD": (3, 0.15)}  # (promised days, late rate)
RETURN_REASONS = ["size_too_small", "size_too_big", "not_as_pictured",
                  "damaged", "changed_mind", "late_delivery"]
DEVICES = ["mobile"] * 6 + ["desktop"] * 3 + ["tablet"]
TABLES = ["products", "customers", "inventory_snapshots", "web_events", "orders",
          "order_items", "payments", "shipments", "returns", "reviews", "marketing_spend"]
# cost per visit for paid online channels (EUR); TV/radio are offline campaigns
COST_PER_VISIT = {"google_ads": 0.45, "instagram": 0.35, "tiktok": 0.25, "affiliate": 0.30, "email": 0.02}

# ---------------- shop memory ----------------
CUSTOMERS, PENDING = [], []      # PENDING = paid orders waiting for shipment/return/review
SIM_NOW = None                   # in history mode we move this clock day by day


def now():
    return SIM_NOW or datetime.now(timezone.utc)


def load_state():
    if STATE_FILE.exists():
        s = json.loads(STATE_FILE.read_text())
        CUSTOMERS.extend(s["customers"])
        for o in s["pending"]:
            o["order_ts"] = datetime.fromisoformat(o["order_ts"])
            PENDING.append(o)
        for pid, stock in s["stock"].items():
            PRODUCT_BY_ID[pid]["stock"] = stock
        return True
    return False


def save_state():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({
        "customers": CUSTOMERS,
        "pending": [{**o, "order_ts": o["order_ts"].isoformat()} for o in PENDING],
        "stock": {p["product_id"]: p["stock"] for p in PRODUCTS}}))


def pick(weighted):
    return random.choices(list(weighted), weights=[v if isinstance(v, (int, float)) else v[0]
                                                   for v in weighted.values()])[0]


# ---------------- one website visit ----------------
def new_customer(out, ts):
    """A visitor becomes a customer only when they place their first order."""
    c = {"customer_id": str(uuid.uuid4())[:8],
         "email": fake.email() if random.random() > 0.01 else None,     # dirty: missing email
         "city": fake.city(), "postcode": fake.postcode(), "signup_ts": ts.isoformat()}
    CUSTOMERS.append(c)
    out["customers"].append(c)
    return c


def one_session(ts, out, promo_boost=1.0):
    # ~20% of visits are logged-in existing customers, the rest anonymous visitors
    cust = random.choice(CUSTOMERS) if CUSTOMERS and random.random() < 0.20 else None
    session_id = str(uuid.uuid4())[:12]
    channel = "email" if cust and random.random() < 0.3 else pick(CHANNELS)
    device = random.choice(DEVICES)
    base = {"session_id": session_id, "customer_id": cust["customer_id"] if cust else None,
            "channel": channel, "device": device}

    def event(name, product_id=None, secs=0):
        e = {**base, "event_id": str(uuid.uuid4()), "event_name": name, "product_id": product_id,
             "event_ts": (ts + timedelta(seconds=secs)).isoformat()}
        out["web_events"].append(e)
        if random.random() < 0.01:                            # dirty: duplicate event
            out["web_events"].append(dict(e))

    viewed = random.sample(PRODUCTS, k=random.randint(1, 5))
    for i, p in enumerate(viewed):
        event("page_view", p["product_id"], secs=i * 20)

    # funnel: real shops convert ~2-3% of visits; mobile worse than desktop
    cart_rate = (0.12 if device == "desktop" else 0.07) * promo_boost
    if cust:
        cart_rate *= 1.8                                      # returning customers buy more easily
    in_stock = [p for p in viewed if p["stock"] > 0]         # out of stock -> lost sale
    if not in_stock or random.random() > cart_rate:
        return
    basket = random.sample(in_stock, k=random.randint(1, min(3, len(in_stock))))
    for p in basket:
        event("add_to_cart", p["product_id"], secs=120)
    if random.random() > 0.40:                                # ~60% cart abandonment
        return
    event("begin_checkout", secs=180)
    if cust is None:
        cust = new_customer(out, ts)                          # first order -> new customer

    order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
    promo = random.choice(PROMOS)
    items = []
    for p in basket:
        qty = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
        price_out = f"€{p['price']:.2f}".replace(".", ",") if random.random() < 0.01 else p["price"]  # dirty
        items.append({"order_id": order_id, "product_id": p["product_id"],
                      "quantity": qty, "unit_price": price_out})
    subtotal = sum(p["price"] * i["quantity"] for p, i in zip(basket, items))
    discount = {"WELCOME10": 0.10, "SUMMER15": 0.15}.get(promo, 0) * subtotal
    shipping = 0 if (subtotal >= 50 or promo == "FREESHIP") else 4.95

    method = pick(PAY_METHODS)
    failed = random.random() < PAY_METHODS[method][1]
    order_ts = ts + timedelta(seconds=200)
    order_ts_out = order_ts + timedelta(days=365) if random.random() < 0.003 else order_ts  # dirty: clock bug

    out["orders"].append({
        "order_id": order_id, "customer_id": cust["customer_id"], "session_id": session_id,
        "order_ts": order_ts_out.isoformat(), "status": "payment_failed" if failed else "paid",
        "channel": channel, "device": device, "promo_code": promo,
        "subtotal": round(subtotal, 2), "discount": round(discount, 2), "shipping_fee": shipping,
        "city": cust["city"], "postcode": cust["postcode"] if random.random() > 0.01 else None})
    out["order_items"].extend(items)
    out["payments"].append({
        "payment_id": str(uuid.uuid4())[:10], "order_id": order_id, "method": method,
        "amount": round(subtotal - discount + shipping, 2),
        "status": "failed" if failed else "success", "payment_ts": order_ts.isoformat()})
    if not failed:
        event("purchase", secs=200)
        for p, i in zip(basket, items):
            p["stock"] = max(0, p["stock"] - i["quantity"])
        PENDING.append({"order_id": order_id, "order_ts": order_ts, "stage": "paid",
                        "product_ids": [p["product_id"] for p in basket]})


# ---------------- things that happen AFTER the order (late-arriving data) ----------------
def progress_orders(out):
    keep = []
    for o in PENDING:
        age_days = (now() - o["order_ts"]).total_seconds() / 86400
        if o["stage"] == "paid" and (age_days >= 1 or random.random() < 0.5):
            carrier = random.choice(list(CARRIERS))
            promised_days, late_rate = CARRIERS[carrier]
            late = random.random() < late_rate
            actual = promised_days + (random.randint(1, 4) if late else random.choice([-1, 0, 0]))
            delivered = o["order_ts"] + timedelta(days=max(1, actual))
            out["shipments"].append({
                "shipment_id": str(uuid.uuid4())[:10], "order_id": o["order_id"], "carrier": carrier,
                "shipped_ts": o["order_ts"].isoformat(),
                "promised_date": (o["order_ts"] + timedelta(days=promised_days)).date().isoformat(),
                "delivered_date": delivered.date().isoformat() if random.random() > 0.02 else None})
            o.update(stage="shipped", late=late, delivered=delivered.isoformat())
            keep.append(o)
        elif o["stage"] == "shipped" and now() >= datetime.fromisoformat(o["delivered"]):
            after = datetime.fromisoformat(o["delivered"])
            for pid in o["product_ids"]:
                cat = PRODUCT_BY_ID[pid]["category"]
                if random.random() < CATEGORIES[cat][1] + (0.05 if o["late"] else 0):
                    if o["late"] and random.random() < 0.3:
                        reason = "late_delivery"
                    elif cat in ("Fashion", "Shoes"):
                        reason = random.choice(RETURN_REASONS[:4])
                    else:
                        reason = random.choice(RETURN_REASONS[2:5])
                    out["returns"].append({
                        "return_id": str(uuid.uuid4())[:10], "order_id": o["order_id"], "product_id": pid,
                        "reason": reason,
                        "return_ts": (after + timedelta(days=random.randint(1, 14))).isoformat()})
            if random.random() < 0.4:
                stars = random.choices([1, 2, 3, 4, 5],
                                       weights=[30, 25, 20, 15, 10] if o["late"] else [3, 4, 13, 35, 45])[0]
                out["reviews"].append({"review_id": str(uuid.uuid4())[:10], "order_id": o["order_id"],
                                       "stars": stars,
                                       "review_ts": (after + timedelta(days=random.randint(1, 7))).isoformat()})
        else:
            keep.append(o)
    PENDING[:] = keep


def marketing_spend(out, day: date):
    """Daily ad spend per channel: online = visits x cost per visit, offline = TV/radio flights."""
    sessions = {}
    for e in out["web_events"]:
        if e["event_name"] == "page_view":
            sessions.setdefault(e["channel"], set()).add(e["session_id"])
    for ch, cpv in COST_PER_VISIT.items():
        visits = len(sessions.get(ch, ()))
        out["marketing_spend"].append({"spend_date": day.isoformat(), "channel": ch,
                                       "spend_eur": round(visits * cpv * random.uniform(0.8, 1.2), 2),
                                       "clicks": visits, "impressions": int(visits * random.uniform(30, 60))})
    if day.weekday() in (3, 4, 5):                     # TV + radio run Thu-Sat
        out["marketing_spend"].append({"spend_date": day.isoformat(), "channel": "tv",
                                       "spend_eur": round(random.uniform(2500, 6000), 2),
                                       "clicks": None, "impressions": random.randint(300000, 700000)})
        out["marketing_spend"].append({"spend_date": day.isoformat(), "channel": "radio",
                                       "spend_eur": round(random.uniform(600, 1500), 2),
                                       "clicks": None, "impressions": random.randint(100000, 250000)})


def restock_and_snapshot(out, day: date):
    """Warehouse restocks low products (sometimes too late -> stock-outs) + daily snapshot."""
    for p in PRODUCTS:
        if p["stock"] < 5 and random.random() < 0.35:
            p["stock"] += random.randint(30, 80)
        out["inventory_snapshots"].append({"snapshot_date": day.isoformat(),
                                           "product_id": p["product_id"], "stock": p["stock"]})


# ---------------- writing files ----------------
def empty():
    return {t: [] for t in TABLES}


def write(out, tag):
    counts = {}
    for table, rows in out.items():
        if rows:
            folder = LANDING / table
            folder.mkdir(parents=True, exist_ok=True)
            with open(folder / f"{table}_{tag}.jsonl", "w") as f:
                f.writelines(json.dumps(r) + "\n" for r in rows)
            counts[table] = len(rows)
    return counts


def write_products():
    out = empty()
    out["products"] = [{k: v for k, v in p.items() if k != "stock"} for p in PRODUCTS]
    write(out, "catalogue")


# ---------------- modes ----------------
def run_history(days, visits_per_day):
    global SIM_NOW
    if STATE_FILE.exists():
        raise SystemExit("History already exists (data/state.json). Delete the data/ folder to start over.")
    random.seed(7)
    write_products()
    start = (datetime.now(timezone.utc) - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    total_orders = 0
    for d in range(days):
        day_start = start + timedelta(days=d)
        growth = 1 + 0.6 * d / days                             # shop grows ~60% over the period
        weekend = 1.25 if day_start.weekday() >= 5 else 1.0     # busier weekends
        summer_sale = 1.5 if day_start.month == 7 and day_start.day <= 14 else 1.0
        n = int(visits_per_day * growth * weekend * random.uniform(0.85, 1.15))
        out = empty()
        for _ in range(n):
            # more visits in the evening (18-22h), like real webshops
            hour = random.choices(range(24), weights=[1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 6, 6, 7,
                                                      6, 6, 6, 7, 8, 10, 11, 11, 9, 6, 3])[0]
            ts = day_start + timedelta(hours=hour, seconds=random.randint(0, 3599))
            one_session(ts, out, promo_boost=summer_sale)
        SIM_NOW = day_start + timedelta(days=1)
        progress_orders(out)
        restock_and_snapshot(out, day_start.date())
        marketing_spend(out, day_start.date())
        write(out, day_start.strftime("%Y%m%d"))
        total_orders += len(out["orders"])
        if d % 30 == 0 or d == days - 1:
            print(f"  {day_start:%Y-%m-%d}  visits={n:>5}  orders={len(out['orders']):>4}  "
                  f"customers so far={len(CUSTOMERS)}")
    SIM_NOW = None
    save_state()
    print(f"\nDone: {days} days, {total_orders} orders, {len(CUSTOMERS)} customers -> {LANDING}")


def run_live(batches, interval, visits):
    if not load_state():
        raise SystemExit("Run history first:  python generator/live_feed.py history")
    for n in range(1, batches + 1):
        out = empty()
        ts = now()
        for _ in range(random.randint(int(visits * 0.7), int(visits * 1.3))):
            one_session(ts + timedelta(seconds=random.randint(0, 25)), out)
        progress_orders(out)
        counts = write(out, ts.strftime("%Y%m%d_%H%M%S_%f"))
        print(f"[{ts:%H:%M:%S}] batch {n}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
        save_state()
        if n < batches:
            time.sleep(interval)


def main():
    ap = argparse.ArgumentParser(description="DutchCart data generator")
    sub = ap.add_subparsers(dest="mode", required=True)
    h = sub.add_parser("history", help="create past data once")
    h.add_argument("--days", type=int, default=180)
    h.add_argument("--visits", type=int, default=800, help="website visits per day at the start")
    lv = sub.add_parser("live", help="add new data now, on demand")
    lv.add_argument("--batches", type=int, default=10)
    lv.add_argument("--interval", type=float, default=5, help="seconds between batches")
    lv.add_argument("--visits", type=int, default=150, help="visits per batch")
    a = ap.parse_args()
    if a.mode == "history":
        run_history(a.days, a.visits)
    else:
        run_live(a.batches, a.interval, a.visits)


if __name__ == "__main__":
    main()