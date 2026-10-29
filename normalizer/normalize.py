"""
Reference normalisation: data/raw  ->  output/ (tidy star schema).

This is the Python version of the Power Query steps used in the Power BI
reports. Each function handles one source and its specific problems, in the
same order a Power Query would apply them. The result must match data/clean/
exactly; tests/test_normalize.py checks that.

    python normalizer/normalize.py               # writes output/*.csv and prints a quality log
"""
from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "output"
MAP = Path(__file__).resolve().parent / "mappings"
AS_OF = pd.Timestamp("2026-10-30")

STATUS = {"PD": "PAID", "AP": "APPROVED", "RJ": "REJECTED", "AU": "IN AUDIT"}
ROAD_FACTOR = 1.25          # road distance = great circle x 1.25
AIR_VOLUMETRIC = 167        # kg per m3 (IATA)

log: list[str] = []


def note(msg: str):
    log.append(msg)


# ---------------------------------------------------------------------------
# text helpers
# ---------------------------------------------------------------------------
def clean_text(s) -> str:
    """Trim, collapse spaces (incl. non-breaking), upper case: 'valoria oy ' -> 'VALORIA OY'."""
    if pd.isna(s):
        return ""
    return " ".join(str(s).replace(" ", " ").split()).upper()


def es_number(s) -> float:
    """'1.234,56' -> 1234.56"""
    if pd.isna(s) or str(s).strip() == "":
        return float("nan")
    return float(str(s).replace(".", "").replace(",", "."))


def strip_ref(s: str) -> str:
    return re.sub(r"[-/ ]", "", str(s)).upper()


# ---------------------------------------------------------------------------
# master data
# ---------------------------------------------------------------------------
def load_masters():
    aliases = pd.read_csv(RAW / "carrier_aliases.csv")
    carrier_of = dict(zip(aliases["Alias"].map(clean_text), aliases["Carrier ID"]))

    ent = pd.read_csv(RAW / "entities.csv")
    entity_of = {}
    for _, r in ent.iterrows():
        entity_of[clean_text(r["Entity Name"])] = r["Entity ID"]
        for a in str(r["Aliases"]).split("|"):
            entity_of[clean_text(a)] = r["Entity ID"]

    loc = pd.read_csv(RAW / "locations.csv", keep_default_na=False)
    city_code = {clean_text(r["Name"]): r["Code"] for _, r in loc.iterrows() if r["Type"] == "City"}

    carriers = pd.read_csv(RAW / "carriers_master.csv")
    fx = pd.read_csv(RAW / "fx_rates.csv")
    country_of = dict(pd.read_csv(MAP / "country_aliases.csv").values)
    return dict(carrier_of=carrier_of, entity_of=entity_of, loc=loc, city_code=city_code,
                carriers=carriers, fx=fx, country_of=country_of)


def map_or_flag(values: pd.Series, mapping: dict, what: str, source: str) -> pd.Series:
    keys = values.map(clean_text)
    out = keys.map(mapping)
    missing = sorted(set(keys[out.isna() & (keys != "")]))
    if missing:
        note(f"{source}: {len(missing)} unmapped {what}: {missing[:5]}")
    return out


# ---------------------------------------------------------------------------
# one function per source
# ---------------------------------------------------------------------------
def ocean(m) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(RAW / "ocean_export.csv", dtype=str)
    d = lambda c: pd.to_datetime(df[c], format="%d/%m/%Y", errors="coerce")
    weight = df["Gross Weight"].astype(float)
    in_t = df["Weight Unit"].str.upper().eq("T")
    note(f"ocean: {in_t.sum()} weights converted from tonnes")
    containers = df["Containers"].astype(int)
    teu_calc = containers * df["Equipment"].map({"20GP": 1, "40HC": 2})
    teu = pd.to_numeric(df["TEU"], errors="coerce")
    note(f"ocean: {teu.isna().sum()} blank TEU filled from equipment x containers")
    ship = pd.DataFrame({
        "shipment_id": df["Booking Ref"], "mode": "Ocean",
        "carrier_id": map_or_flag(df["Carrier"], m["carrier_of"], "carriers", "ocean"),
        "entity_id": map_or_flag(df["Bill To"], m["entity_of"], "entities", "ocean"),
        "origin_code": df["POL"], "destination_code": df["POD"],
        "pickup_date": d("ATD"), "planned_delivery_date": d("ETA"), "actual_delivery_date": d("ATA"),
        "gross_weight_kg": (weight.where(~in_t, weight * 1000)).round(1),
        "teu": teu.fillna(teu_calc).astype(int), "containers": containers,
    })
    ship["chargeable_weight_kg"] = ship["gross_weight_kg"]
    inv = pd.DataFrame({"shipment_id": df["Booking Ref"], "carrier_id": ship["carrier_id"],
                        "entity_id": ship["entity_id"], "mode": "Ocean", "invoice_number": df["Invoice No"]})
    return ship, inv.dropna(subset=["invoice_number"])


def air(m) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(RAW / "air_export.csv", dtype=str)
    dups = df.duplicated().sum()
    df = df.drop_duplicates()
    note(f"air: {dups} exact duplicate rows removed")
    d = lambda c: pd.to_datetime(df[c].str.slice(0, 10), format="%Y-%m-%d", errors="coerce")
    actual = df["Actual Weight (kg)"].astype(float)
    volume = df["Volume (m3)"].astype(float)
    given = pd.to_numeric(df["Chargeable Weight (kg)"], errors="coerce")
    calc = (pd.concat([actual, volume * AIR_VOLUMETRIC], axis=1).max(axis=1) * 2).round() / 2
    note(f"air: {given.isna().sum()} blank chargeable weights computed as max(actual, m3 x 167)")
    ship = pd.DataFrame({
        "shipment_id": df["AWB"], "mode": "Air",
        "carrier_id": map_or_flag(df["Airline/Forwarder"], m["carrier_of"], "carriers", "air"),
        "entity_id": map_or_flag(df["Customer"], m["entity_of"], "entities", "air"),
        "origin_code": df["Origin"], "destination_code": df["Destination"],
        "pickup_date": d("Pickup"), "planned_delivery_date": d("Promised Delivery"),
        "actual_delivery_date": d("Delivered"),
        "gross_weight_kg": actual, "chargeable_weight_kg": given.fillna(calc),
        "pieces": df["Pieces"].astype(int),
    })
    inv = pd.DataFrame({"shipment_id": df["AWB"], "carrier_id": ship["carrier_id"],
                        "entity_id": ship["entity_id"], "mode": "Air", "invoice_number": df["Invoice"]})
    return ship, inv.dropna(subset=["invoice_number"])


def road(m) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(RAW / "road_export.csv", sep=";", dtype=str, encoding="utf-8-sig")
    total_rows = df["Nº Envío"].str.upper().eq("TOTAL")
    df = df[~total_rows]
    note(f"road: {total_rows.sum()} footer TOTAL row removed")
    d = lambda c: pd.to_datetime(df[c], format="%d/%m/%y", errors="coerce")
    orig = map_or_flag(df["Origen"], m["city_code"], "cities", "road")
    dest = map_or_flag(df["Destino"], m["city_code"], "cities", "road")

    # the hand-typed country must agree with the city's country
    loc_iso3 = dict(zip(m["loc"]["Code"], m["loc"]["Country ISO3"]))
    stated = df["País Origen"].map(clean_text).map(m["country_of"])
    bad = (stated != orig.map(loc_iso3)).sum()
    note(f"road: {stated.nunique()} countries written {df['País Origen'].nunique()} ways; "
         f"{bad} origin country mismatches")

    ship = pd.DataFrame({
        "shipment_id": df["Nº Envío"], "mode": "Road",
        "carrier_id": map_or_flag(df["Transportista"], m["carrier_of"], "carriers", "road"),
        "entity_id": map_or_flag(df["Entidad"], m["entity_of"], "entities", "road"),
        "origin_code": orig, "destination_code": dest,
        "pickup_date": d("Fecha Carga"), "planned_delivery_date": d("Entrega Prevista"),
        "actual_delivery_date": d("Entrega Real"),
        "gross_weight_kg": df["Kg"].map(es_number), "pallets": df["Palés"].astype(int),
    })
    ship["chargeable_weight_kg"] = ship["gross_weight_kg"]
    inv = pd.DataFrame({"shipment_id": df["Nº Envío"], "carrier_id": ship["carrier_id"],
                        "entity_id": ship["entity_id"], "mode": "Road", "invoice_number": df["Nº Factura"]})
    return ship, inv.dropna(subset=["invoice_number"])


def distance_km(ship: pd.DataFrame, loc: pd.DataFrame) -> pd.Series:
    lat = dict(zip(loc["Code"], loc["Latitude"].astype(float)))
    lon = dict(zip(loc["Code"], loc["Longitude"].astype(float)))

    def gc(a, b):
        la1, lo1, la2, lo2 = map(math.radians, (lat[a], lon[a], lat[b], lon[b]))
        h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
        return 6371 * 2 * math.asin(math.sqrt(h))

    raw = [gc(a, b) for a, b in zip(ship["origin_code"], ship["destination_code"])]
    factor = ship["mode"].map({"Road": ROAD_FACTOR}).fillna(1.0)
    return (pd.Series(raw, index=ship.index) * factor).round().astype(int)


def fx_lookup(fx: pd.DataFrame):
    rate = {(r["Month"], r["Currency"]): r["Rate to EUR"] for _, r in fx.iterrows()}
    return lambda month, ccy: 1.0 if ccy == "EUR" else rate[(month, ccy)]


def invoices(m, export_inv: pd.DataFrame) -> pd.DataFrame:
    reg = pd.read_csv(RAW / "ap_invoice_register.csv", dtype=str)
    d = lambda c: pd.to_datetime(reg[c], format="%Y-%m-%d", errors="coerce")
    status = reg["Status"].map(STATUS)
    decision = d("Decision Date")
    inv = pd.DataFrame({
        "carrier_id": reg["Vendor ID"], "invoice_number": reg["Vendor Invoice No"],
        "invoice_date": d("Invoice Date"), "received_date": d("Received"),
        "approval_date": decision.where(status.isin(["PAID", "APPROVED"])),
        "rejection_date": decision.where(status.eq("REJECTED")),
        "due_date": d("Due Date"), "payment_terms_days": reg["Terms"].str.replace("NET", "").astype(int),
        "status": status, "currency": reg["Currency"].str.upper(), "total_amount": reg["Amount"].astype(float),
    })
    inv = inv.merge(export_inv, on=["carrier_id", "invoice_number"], how="left", validate="one_to_one")
    missing = inv["shipment_id"].isna().sum()
    if missing:
        note(f"invoices: {missing} register lines with no shipment in the exports")
    rate = fx_lookup(m["fx"])
    inv["fx_rate_to_eur"] = [rate(dt.strftime("%Y-%m"), c) for dt, c in zip(inv["invoice_date"], inv["currency"])]
    inv["total_amount_eur"] = (inv["total_amount"] * inv["fx_rate_to_eur"]).round(2)
    inv["invoice_key"] = inv["carrier_id"] + "|" + inv["invoice_number"]
    return inv


def payments(m, inv: pd.DataFrame) -> pd.DataFrame:
    led = pd.read_csv(RAW / "ap_payments_ledger.csv", dtype=str)
    key = inv.assign(ref=inv["invoice_number"].map(strip_ref))[["carrier_id", "ref", "invoice_key"]]
    pay = led.assign(ref=led["Reference"].map(strip_ref)).merge(
        key, left_on=["Vendor", "ref"], right_on=["carrier_id", "ref"], how="left", validate="many_to_one")
    unmatched = pay["invoice_key"].isna().sum()
    note(f"payments: {len(pay)} ledger lines, {unmatched} not matched to an invoice")
    rate = fx_lookup(m["fx"])
    pdate = pd.to_datetime(pay["Posting Date"], format="%Y%m%d")
    amount = -pay["Amount"].astype(float)                         # ledger posts outflows as negatives
    out = pd.DataFrame({"payment_id": pay["Payment Doc"], "invoice_key": pay["invoice_key"],
                        "carrier_id": pay["Vendor"], "payment_date": pdate, "amount": amount,
                        "currency": pay["Curr"].str.upper()})
    out["amount_eur"] = [round(a * rate(d.strftime("%Y-%m"), c), 2)
                         for a, d, c in zip(out["amount"], out["payment_date"], out["currency"])]
    return out


# ---------------------------------------------------------------------------
def run() -> dict[str, pd.DataFrame]:
    log.clear()
    m = load_masters()
    parts = [ocean(m), air(m), road(m)]
    ship = pd.concat([p[0] for p in parts], ignore_index=True)
    export_inv = pd.concat([p[1] for p in parts], ignore_index=True)
    ship["distance_km"] = distance_km(ship, m["loc"])

    inv = invoices(m, export_inv)
    pay = payments(m, inv)
    first_paid = pay.groupby("invoice_key")["payment_date"].max()
    inv["paid_date"] = inv["invoice_key"].map(first_paid)

    loc = m["loc"]
    eu = {"AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL",
          "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"}
    dims = {
        "dim_carrier": m["carriers"].rename(columns={"Carrier ID": "carrier_id", "Carrier Name": "carrier_name",
                                                     "Mode": "mode", "Country": "country_iso3",
                                                     "Payment Terms (days)": "payment_terms_days"}),
        "dim_entity": pd.read_csv(RAW / "entities.csv").rename(
            columns={"Entity ID": "entity_id", "Entity Name": "entity_name", "Country": "country_iso3"})
        [["entity_id", "entity_name", "country_iso3"]].assign(
            eu_member=lambda x: x["country_iso3"].map(lambda c: "Y" if c in eu else "N")),
        "dim_location": loc.rename(columns={"Code": "location_code", "Name": "location_name",
                                            "Type": "location_type", "Country ISO2": "country_iso2",
                                            "Country ISO3": "country_iso3", "Country": "country", "Region": "region",
                                            "Latitude": "latitude", "Longitude": "longitude"}).assign(
            eu_member=lambda x: x["country_iso3"].map(lambda c: "Y" if c in eu else "N")),
    }
    return {**dims, "fact_shipments": ship, "fact_invoices": inv, "fact_payments": pay}


def main():
    tables = run()
    OUT.mkdir(exist_ok=True)
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    print("Data quality log:")
    for line in log:
        print("  -", line)
    print("Rows:", {k: len(v) for k, v in tables.items()})


if __name__ == "__main__":
    main()
