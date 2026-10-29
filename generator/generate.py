"""
Generate a fictional multimodal freight dataset.

Two outputs from the same simulation:

  data/clean/  the TRUTH: a tidy star schema (what a perfect normalisation should produce)
  data/raw/    the same facts as real systems would export them: one file per mode
               with its own columns, units, date formats and currencies, plus an AP
               invoice register, a payments ledger and master data.

The raw files are what Power BI (Power Query) and SQL start from; the clean
files are the answer key used to test the normalisation.

    python generator/generate.py              # default seed 2026, 12,000 shipments
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from master_data import (AIR_LANES, CARRIERS, COUNTRY_SPELLINGS, ENTITIES, ENTITY_HUBS, EU_ISO3,
                         LOCATIONS, MODE_SHARE, OCEAN_LANES)

ROOT = Path(__file__).resolve().parents[1]
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"

AS_OF = date(2026, 10, 30)          # "today" for statuses, open items and ageing
FIRST_PICKUP = date(2025, 1, 1)
LAST_PICKUP = date(2026, 10, 20)

LOC = {l[0]: dict(code=l[0], name=l[1], type=l[2], iso2=l[3], iso3=l[4], country=l[5],
                  region=l[6], lat=l[7], lon=l[8]) for l in LOCATIONS}
CAR = {c[0]: dict(id=c[0], name=c[1], mode=c[2], iso3=c[3], terms=c[4], ontime=c[5], price=c[6],
                  exc=c[7], ccy=c[8], variants=c[9]) for c in CARRIERS}
ENT = {e[0]: dict(id=e[0], name=e[1], iso3=e[2], share=e[3], variants=e[4]) for e in ENTITIES}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def km(a: str, b: str) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (LOC[a]["lat"], LOC[a]["lon"], LOC[b]["lat"], LOC[b]["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def months_between(a: date, b: date) -> list[str]:
    out, y, m = [], a.year, a.month
    while (y, m) <= (b.year, b.month):
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def next_friday(d: date) -> date:
    return d + timedelta(days=(4 - d.weekday()) % 7)


def fx_table(rng: random.Random) -> dict[tuple[str, str], float]:
    """Illustrative monthly rates to EUR (not real market data)."""
    rates = {}
    usd, gbp = 0.925, 1.185
    for m in months_between(date(2024, 12, 1), date(2026, 12, 1)):
        usd = min(0.97, max(0.84, usd + rng.gauss(-0.0025, 0.008)))
        gbp = min(1.22, max(1.12, gbp + rng.gauss(0.0, 0.006)))
        rates[(m, "USD")] = round(usd, 4)
        rates[(m, "GBP")] = round(gbp, 4)
        rates[(m, "EUR")] = 1.0
    return rates


def pick_date(rng: random.Random) -> date:
    """Pickup date with growth over time and a Q4 peak."""
    span = (LAST_PICKUP - FIRST_PICKUP).days
    while True:
        d = FIRST_PICKUP + timedelta(days=rng.randrange(span + 1))
        weight = 0.75 + 0.25 * (d - FIRST_PICKUP).days / span + (0.25 if d.month in (10, 11) else 0)
        weight -= 0.35 if d.month == 8 else 0          # August slowdown in Europe
        weight -= 0.5 if d.weekday() >= 5 else 0        # few weekend pickups
        if rng.random() < weight / 1.25:
            return d


# ---------------------------------------------------------------------------
# simulation
# ---------------------------------------------------------------------------
def simulate(n: int, seed: int):
    rng = random.Random(seed)
    fx = fx_table(rng)
    by_mode = defaultdict(list)
    for c in CAR.values():
        by_mode[c["mode"]].append(c["id"])
    road_cities = [c for c, l in LOC.items() if l["type"] == "City"]

    shipments, invoices, payments = [], [], []
    seq = defaultdict(int)

    for i in range(n):
        mode = rng.choices(list(MODE_SHARE), weights=list(MODE_SHARE.values()))[0]
        ent = rng.choices(list(ENT), weights=[e["share"] for e in ENT.values()])[0]
        hubs = ENTITY_HUBS[ent][mode.lower()]
        pickup = pick_date(rng)

        # ---- lane
        if mode == "Road":
            hub = rng.choice(hubs)
            other = rng.choice([c for c in road_cities if c != hub])
            orig, dest = (hub, other) if rng.random() < 0.55 else (other, hub)
            dist = km(orig, dest) * 1.25                       # road factor over great circle
            planned_days = 1 + math.ceil(dist / 650)
        else:
            lanes = OCEAN_LANES if mode == "Ocean" else AIR_LANES
            mine = [l for l in lanes if l[1] in hubs or l[0] in hubs] or lanes
            orig, dest, base, planned_days = rng.choice(mine)
            dist = km(orig, dest)

        # ---- carrier (road carriers win more work in their home countries)
        cands = by_mode[mode]
        weights = []
        for cid in cands:
            w = 1.0
            if mode == "Road" and CAR[cid]["iso3"] in (LOC[orig]["iso3"], LOC[dest]["iso3"]):
                w *= 3.0
            weights.append(w)
        cid = rng.choices(cands, weights=weights)[0]
        car = CAR[cid]

        # ---- timing
        if mode == "Ocean":
            etd = pickup
            pickup = etd + timedelta(days=rng.choice([0, 0, 0, 1, 2]))     # actual departure
        planned = pickup + timedelta(days=planned_days)
        if rng.random() < car["ontime"]:
            actual = planned - timedelta(days=1 if rng.random() < 0.12 else 0)
        else:
            late = rng.choice([1, 1, 2, 2, 3, 4, 6]) if mode != "Ocean" else rng.choice([2, 3, 4, 6, 9, 12])
            actual = planned + timedelta(days=late)
        delivered = actual if actual <= AS_OF else None

        # ---- quantities and cost (base currency: EUR for road, USD for ocean/air)
        pallets = pieces = containers = None
        teu = None
        equipment = None
        if mode == "Road":
            pallets = rng.choice([1, 2, 3, 4, 6, 8, 10, 12, 16, 20, 26, 33])
            gross = round(pallets * rng.uniform(250, 700), 1)
            chargeable = gross
            freight_base = max(95.0, dist * (0.55 + 0.035 * pallets)) * car["price"]
            surcharge_base = freight_base * rng.uniform(0.11, 0.17)       # fuel
            base_ccy = "EUR"
        elif mode == "Ocean":
            equipment = rng.choices(["20GP", "40HC"], weights=[0.35, 0.65])[0]
            containers = rng.choice([1, 1, 1, 2, 2, 3, 4])
            teu = containers * (1 if equipment == "20GP" else 2)
            gross = round(teu * rng.uniform(6000, 12000), 0)
            chargeable = gross
            season = 1 + 0.18 * math.sin((pickup.month - 2) / 12 * 2 * math.pi)
            freight_base = teu * base * season * car["price"] * rng.uniform(0.93, 1.07)
            surcharge_base = teu * rng.uniform(150, 330) + containers * rng.uniform(180, 260)   # BAF + THC
            base_ccy = "USD"
        else:
            pieces = rng.randint(1, 40)
            gross = round(min(6000, rng.lognormvariate(5.6, 0.9)), 1)
            volume = round(gross / rng.uniform(110, 260), 2)
            chargeable = round(max(gross, volume * 167) * 2) / 2
            band = 1.0 if chargeable < 300 else 0.88 if chargeable < 1000 else 0.78
            freight_base = chargeable * base * band * car["price"] * rng.uniform(0.95, 1.05)
            surcharge_base = chargeable * rng.uniform(0.9, 1.4) + chargeable * 0.15     # fuel + security
            base_ccy = "USD"

        shipment_id = {"Road": f"RD{i + 100000}", "Ocean": f"BK{i + 500000}", "Air": f"999-{i + 10000000}"}[mode]
        ship = dict(shipment_id=shipment_id, mode=mode, carrier_id=cid, entity_id=ent,
                    origin_code=orig, destination_code=dest, distance_km=round(dist),
                    pickup_date=pickup, planned_delivery_date=planned, actual_delivery_date=delivered,
                    gross_weight_kg=gross, chargeable_weight_kg=chargeable, teu=teu,
                    containers=containers, equipment=equipment, pallets=pallets, pieces=pieces,
                    volume_m3=volume if mode == "Air" else None)
        if mode == "Ocean":
            ship["etd"] = etd
        shipments.append(ship)

        # ---- invoice (road and air invoiced after delivery, ocean after departure)
        trigger = pickup if mode == "Ocean" else actual
        inv_date = trigger + timedelta(days=rng.randint(2, 10) if mode == "Ocean" else rng.randint(1, 15))
        received = inv_date + timedelta(days=rng.randint(0, 6))
        if received > AS_OF:
            continue                                            # not invoiced yet: an accrual

        ccy = rng.choices(list(car["ccy"]), weights=list(car["ccy"].values()))[0]
        month = inv_date.strftime("%Y-%m")
        to_ccy = 1.0 if ccy == base_ccy else fx[(month, base_ccy)] / fx[(month, ccy)]
        freight = round(freight_base * to_ccy, 2)
        surcharge = round(surcharge_base * to_ccy, 2)
        total = round(freight + surcharge, 2)

        exception = rng.random() < car["exc"]
        rejected = exception and rng.random() < 0.35
        decision = received + timedelta(days=rng.randint(6, 25) if exception else rng.randint(1, 4))
        due = inv_date + timedelta(days=car["terms"])

        # weekly payment run on Fridays: the last run before the due date, or the first
        # run after approval when the audit finished too late
        paid_date = None
        if not rejected:
            friday_before_due = due - timedelta(days=(due.weekday() - 4) % 7)
            paid_date = max(next_friday(decision + timedelta(days=1)), friday_before_due)
            r = rng.random()
            if r < 0.04:                                         # payment hold, released later
                paid_date = next_friday(paid_date + timedelta(days=rng.randint(10, 45)))
            elif r < 0.08:                                       # disputed: blocked 1-5 months
                paid_date = next_friday(paid_date + timedelta(days=rng.randint(30, 150)))

        if decision > AS_OF:
            status = "IN AUDIT"
        elif rejected:
            status = "REJECTED"
        elif paid_date and paid_date <= AS_OF:
            status = "PAID"
        else:
            status = "APPROVED"

        rate = fx[(month, ccy)]
        inv = dict(invoice_key=None, invoice_number=None, shipment_id=shipment_id,
                   carrier_id=cid, entity_id=ent, mode=mode, invoice_date=inv_date, received_date=received,
                   approval_date=decision if (not rejected and decision <= AS_OF) else None,
                   rejection_date=decision if (rejected and decision <= AS_OF) else None,
                   due_date=due, payment_terms_days=car["terms"], status=status, currency=ccy,
                   freight_amount=freight, surcharge_amount=surcharge, total_amount=total,
                   fx_rate_to_eur=rate, total_amount_eur=round(total * rate, 2),
                   paid_date=paid_date if status == "PAID" else None)
        invoices.append(inv)

        if status == "PAID":
            payments.append(dict(payment_id=None, invoice=inv, carrier_id=cid, payment_date=paid_date,
                                 amount=total, currency=ccy,
                                 amount_eur=round(total * fx[(paid_date.strftime('%Y-%m'), ccy)], 2)))

    # invoice numbers follow invoice date within each carrier and year, in the carrier's own format
    for inv in sorted(invoices, key=lambda v: (v["carrier_id"], v["invoice_date"], v["shipment_id"])):
        cid, yy = inv["carrier_id"], inv["invoice_date"].year
        seq[(cid, yy)] += 1
        n = seq[(cid, yy)]
        style = int(cid[1:]) % 4
        inv["invoice_number"] = [f"INV-{yy}-{n:06d}", f"{n:06d}/{yy % 100:02d}", f"{cid}-{yy % 100:02d}{n:05d}",
                                 f"F{yy}{n:05d}"][style]
        inv["invoice_key"] = f"{cid}|{inv['invoice_number']}"
    # payment documents numbered in posting order
    payments.sort(key=lambda p: (p["payment_date"], p["carrier_id"], p["invoice"]["invoice_number"]))
    for k, p in enumerate(payments, start=1):
        p["payment_id"] = f"PAY{k:07d}"
        p["invoice_key"] = p.pop("invoice")["invoice_key"]

    return shipments, invoices, payments, fx


# ---------------------------------------------------------------------------
# writers
# ---------------------------------------------------------------------------
def write_csv(path: Path, header: list[str], rows: list[list], delimiter=",", encoding="utf-8"):
    with open(path, "w", newline="", encoding=encoding) as f:
        w = csv.writer(f, delimiter=delimiter)
        w.writerow(header)
        w.writerows(rows)


def iso(d):
    return d.isoformat() if d else ""


def write_clean(shipments, invoices, payments, fx):
    CLEAN.mkdir(parents=True, exist_ok=True)
    write_csv(CLEAN / "dim_carrier.csv", ["carrier_id", "carrier_name", "mode", "country_iso3", "payment_terms_days"],
              [[c["id"], c["name"], c["mode"], c["iso3"], c["terms"]] for c in CAR.values()])
    write_csv(CLEAN / "dim_entity.csv", ["entity_id", "entity_name", "country_iso3", "eu_member"],
              [[e["id"], e["name"], e["iso3"], "Y" if e["iso3"] in EU_ISO3 else "N"] for e in ENT.values()])
    write_csv(CLEAN / "dim_location.csv",
              ["location_code", "location_name", "location_type", "country_iso2", "country_iso3", "country",
               "region", "eu_member", "latitude", "longitude"],
              [[l["code"], l["name"], l["type"], l["iso2"], l["iso3"], l["country"], l["region"],
                "Y" if l["iso3"] in EU_ISO3 else "N", l["lat"], l["lon"]] for l in LOC.values()])
    write_csv(CLEAN / "fx_rates.csv", ["month", "currency", "rate_to_eur"],
              [[m, c, r] for (m, c), r in sorted(fx.items())])

    cols = ["shipment_id", "mode", "carrier_id", "entity_id", "origin_code", "destination_code", "distance_km",
            "pickup_date", "planned_delivery_date", "actual_delivery_date", "gross_weight_kg",
            "chargeable_weight_kg", "teu", "containers", "pallets", "pieces"]
    write_csv(CLEAN / "fact_shipments.csv", cols,
              [[iso(s[c]) if isinstance(s[c], date) else ("" if s[c] is None else s[c]) for c in cols]
               for s in shipments])
    cols = ["invoice_key", "invoice_number", "shipment_id", "carrier_id", "entity_id", "mode", "invoice_date",
            "received_date", "approval_date", "rejection_date", "due_date", "payment_terms_days", "status",
            "currency", "total_amount", "fx_rate_to_eur", "total_amount_eur", "paid_date"]
    write_csv(CLEAN / "fact_invoices.csv", cols,
              [[iso(v[c]) if isinstance(v[c], date) else ("" if v[c] is None else v[c]) for c in cols]
               for v in invoices])
    cols = ["payment_id", "invoice_key", "carrier_id", "payment_date", "amount", "currency", "amount_eur"]
    write_csv(CLEAN / "fact_payments.csv", cols,
              [[iso(p[c]) if isinstance(p[c], date) else p[c] for c in cols] for p in payments])


def messy_name(rng, variants):
    v = rng.choice(variants)
    r = rng.random()
    if r < 0.15:
        return v.upper()
    if r < 0.25:
        return v + " "
    if r < 0.30:
        return "  " + v.lower()
    return v


def es_number(x: float, decimals=2) -> str:
    """1234.5 -> '1.234,50' (Spanish Excel export)."""
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def write_raw(shipments, invoices, payments, fx, seed):
    rng = random.Random(seed + 1)
    RAW.mkdir(parents=True, exist_ok=True)
    inv_by_ship = {v["shipment_id"]: v for v in invoices}

    # ---- master data
    write_csv(RAW / "carriers_master.csv", ["Carrier ID", "Carrier Name", "Mode", "Country", "Payment Terms (days)"],
              [[c["id"], c["name"], c["mode"], c["iso3"], c["terms"]] for c in CAR.values()])
    alias_rows = []
    for c in CAR.values():
        for v in sorted({" ".join(x.split()).upper() for x in c["variants"] + [c["name"]]}):
            alias_rows.append([v, c["id"]])
    write_csv(RAW / "carrier_aliases.csv", ["Alias", "Carrier ID"], alias_rows)
    write_csv(RAW / "entities.csv", ["Entity ID", "Entity Name", "Country", "Aliases"],
              [[e["id"], e["name"], e["iso3"],
                "|".join(sorted({" ".join(v.replace(" ", " ").split()).upper() for v in e["variants"]}))]
               for e in ENT.values()])
    write_csv(RAW / "locations.csv",
              ["Code", "Name", "Type", "Country ISO2", "Country ISO3", "Country", "Region", "Latitude", "Longitude"],
              [[l["code"], l["name"], l["type"], l["iso2"], l["iso3"], l["country"], l["region"], l["lat"], l["lon"]]
               for l in LOC.values()])
    write_csv(RAW / "fx_rates.csv", ["Month", "Currency", "Rate to EUR"],
              [[m, c, r] for (m, c), r in sorted(fx.items()) if c != "EUR"])

    def ccy_noise(c):
        return rng.choice([c, c, c, c.lower(), c.title()])

    # ---- ocean export: dd/mm/yyyy, weight sometimes in tonnes, TEU sometimes blank
    rows = []
    for s in (s for s in shipments if s["mode"] == "Ocean"):
        v = inv_by_ship.get(s["shipment_id"])
        in_tonnes = rng.random() < 0.10
        weight = round(s["gross_weight_kg"] / 1000, 3) if in_tonnes else s["gross_weight_kg"]
        dm = lambda d: d.strftime("%d/%m/%Y") if d else ""
        rows.append([
            s["shipment_id"], messy_name(rng, CAR[s["carrier_id"]]["variants"]),
            messy_name(rng, ENT[s["entity_id"]]["variants"]), s["origin_code"], s["destination_code"],
            dm(s["etd"]), dm(s["pickup_date"]), dm(s["planned_delivery_date"]), dm(s["actual_delivery_date"]),
            s["equipment"], s["containers"], "" if rng.random() < 0.05 else s["teu"],
            weight, "T" if in_tonnes else "KG",
            v["invoice_number"] if v else "", dm(v["invoice_date"]) if v else "",
            f'{v["freight_amount"]:.2f}' if v else "",
            f'{v["surcharge_amount"] * 0.6:.2f}' if v else "",
            f'{v["surcharge_amount"] - round(v["surcharge_amount"] * 0.6, 2):.2f}' if v else "",
            f'{v["total_amount"]:.2f}' if v else "", ccy_noise(v["currency"]) if v else "",
        ])
    write_csv(RAW / "ocean_export.csv",
              ["Booking Ref", "Carrier", "Bill To", "POL", "POD", "ETD", "ATD", "ETA", "ATA", "Equipment",
               "Containers", "TEU", "Gross Weight", "Weight Unit", "Invoice No", "Invoice Date", "Ocean Freight",
               "BAF", "THC", "Invoice Total", "Currency"], rows)

    # ---- air export: ISO datetimes, chargeable weight sometimes blank, a few duplicate rows
    rows = []
    for s in (s for s in shipments if s["mode"] == "Air"):
        v = inv_by_ship.get(s["shipment_id"])
        t = lambda d, h: f"{d.isoformat()}T{h:02d}:{rng.choice([0, 15, 30, 45]):02d}:00" if d else ""
        row = [
            s["shipment_id"], messy_name(rng, CAR[s["carrier_id"]]["variants"]),
            messy_name(rng, ENT[s["entity_id"]]["variants"]), s["origin_code"], s["destination_code"],
            t(s["pickup_date"], rng.randint(6, 20)), t(s["planned_delivery_date"], 12),
            t(s["actual_delivery_date"], rng.randint(7, 19)), s["pieces"], s["gross_weight_kg"], s["volume_m3"],
            "" if rng.random() < 0.08 else s["chargeable_weight_kg"],
            v["invoice_number"] if v else "", v["invoice_date"].isoformat() if v else "",
            f'{v["freight_amount"]:.2f}' if v else "",
            f'{v["surcharge_amount"] * 0.85:.2f}' if v else "",
            f'{v["surcharge_amount"] - round(v["surcharge_amount"] * 0.85, 2):.2f}' if v else "",
            f'{v["total_amount"]:.2f}' if v else "", ccy_noise(v["currency"]) if v else "",
        ]
        rows.append(row)
        if rng.random() < 0.006:
            rows.append(list(row))                               # export glitch: exact duplicate
    write_csv(RAW / "air_export.csv",
              ["AWB", "Airline/Forwarder", "Customer", "Origin", "Destination", "Pickup", "Promised Delivery",
               "Delivered", "Pieces", "Actual Weight (kg)", "Volume (m3)", "Chargeable Weight (kg)", "Invoice",
               "Invoice Date", "Air Freight", "Fuel Surcharge", "Security", "Total", "Curr"], rows)

    # ---- road export: Spanish Excel CSV (;), d/m/yy dates, numbers as text with 1.234,56, TOTAL row
    rows, grand = [], 0.0
    for s in (s for s in shipments if s["mode"] == "Road"):
        v = inv_by_ship.get(s["shipment_id"])
        dmy = lambda d: f"{d.day}/{d.month}/{d.year % 100:02d}" if d else ""
        o, d = LOC[s["origin_code"]], LOC[s["destination_code"]]
        if v:
            grand += v["total_amount"] if v["currency"] == "EUR" else 0
        rows.append([
            s["shipment_id"], messy_name(rng, CAR[s["carrier_id"]]["variants"]),
            messy_name(rng, ENT[s["entity_id"]]["variants"]),
            o["name"], rng.choice(COUNTRY_SPELLINGS[o["iso3"]]), d["name"], rng.choice(COUNTRY_SPELLINGS[d["iso3"]]),
            dmy(s["pickup_date"]), dmy(s["planned_delivery_date"]), dmy(s["actual_delivery_date"]),
            s["pallets"], es_number(s["gross_weight_kg"], 1),
            v["invoice_number"] if v else "", dmy(v["invoice_date"]) if v else "",
            es_number(v["total_amount"]) if v else "", ccy_noise(v["currency"]) if v else "",
        ])
    rows.append(["TOTAL", "", "", "", "", "", "", "", "", "", "", "", "", "", es_number(grand), "EUR"])
    write_csv(RAW / "road_export.csv",
              ["Nº Envío", "Transportista", "Entidad", "Origen", "País Origen", "Destino", "País Destino",
               "Fecha Carga", "Entrega Prevista", "Entrega Real", "Palés", "Kg", "Nº Factura", "Fecha Factura",
               "Importe", "Moneda"], rows, delimiter=";", encoding="utf-8-sig")

    # ---- AP invoice register (ERP): status codes, NETxx terms
    code = {"PAID": "PD", "APPROVED": "AP", "REJECTED": "RJ", "IN AUDIT": "AU"}
    write_csv(RAW / "ap_invoice_register.csv",
              ["Vendor ID", "Vendor Invoice No", "Invoice Date", "Received", "Decision Date", "Status", "Terms",
               "Due Date", "Amount", "Currency"],
              [[v["carrier_id"], v["invoice_number"], v["invoice_date"].isoformat(), v["received_date"].isoformat(),
                iso(v["approval_date"] or v["rejection_date"]), code[v["status"]], f'NET{v["payment_terms_days"]}',
                v["due_date"].isoformat(), f'{v["total_amount"]:.2f}', v["currency"]] for v in invoices])

    # ---- payments ledger: reference stripped of symbols, yyyymmdd as number, negative amounts
    strip = lambda s: s.replace("-", "").replace("/", "").replace(" ", "")
    inv_no = {v["invoice_key"]: v["invoice_number"] for v in invoices}
    write_csv(RAW / "ap_payments_ledger.csv",
              ["Payment Doc", "Vendor", "Reference", "Posting Date", "Amount", "Curr"],
              [[p["payment_id"], p["carrier_id"], strip(inv_no[p["invoice_key"]]),
                p["payment_date"].strftime("%Y%m%d"), f'{-p["amount"]:.2f}', p["currency"]] for p in payments])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--shipments", type=int, default=12000)
    args = ap.parse_args()
    shipments, invoices, payments, fx = simulate(args.shipments, args.seed)
    write_clean(shipments, invoices, payments, fx)
    write_raw(shipments, invoices, payments, fx, args.seed)
    by = defaultdict(int)
    for v in invoices:
        by[v["status"]] += 1
    print(f"shipments {len(shipments):,} · invoices {len(invoices):,} · payments {len(payments):,}")
    print("invoice status:", dict(by))


if __name__ == "__main__":
    main()
