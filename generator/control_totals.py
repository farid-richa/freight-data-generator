"""
Write docs/control_totals.md: the numbers a correct Power BI model must show.

Computed from the truth in data/clean, as of 2026-10-30. When the report is
built, every card and table can be checked against this file.

    python generator/control_totals.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
AS_OF = pd.Timestamp("2026-10-30")


def eur(x):
    return f"{x:,.0f} €".replace(",", ".")


def pct(x):
    return f"{x * 100:.1f} %".replace(".", ",")


def table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def main():
    s = pd.read_csv(CLEAN / "fact_shipments.csv", parse_dates=["pickup_date", "planned_delivery_date",
                                                                "actual_delivery_date"])
    v = pd.read_csv(CLEAN / "fact_invoices.csv", parse_dates=["invoice_date", "received_date", "due_date",
                                                               "paid_date"])
    c = pd.read_csv(CLEAN / "dim_carrier.csv")
    e = pd.read_csv(CLEAN / "dim_entity.csv")

    out = ["# Control totals", "",
           "What a correct model shows **as of 30 Oct 2026**, computed from the truth in `data/clean`. "
           "Amounts in EUR at the invoice month's rate. Use it to check every card and table in Power BI.", ""]

    # ---- overview
    delivered = s.dropna(subset=["actual_delivery_date"])
    ontime = (delivered["actual_delivery_date"] <= delivered["planned_delivery_date"])
    out += ["## Overview", "", table(pd.DataFrame([
        {"Measure": "Shipments", "Value": f"{len(s):,}".replace(",", ".")},
        {"Measure": "Shipments delivered", "Value": f"{len(delivered):,}".replace(",", ".")},
        {"Measure": "Invoices", "Value": f"{len(v):,}".replace(",", ".")},
        {"Measure": "Spend (all invoices)", "Value": eur(v["total_amount_eur"].sum())},
        {"Measure": "Spend excl. rejected", "Value": eur(v.loc[v.status != "REJECTED", "total_amount_eur"].sum())},
        {"Measure": "On-time delivery", "Value": pct(ontime.mean())},
    ])), ""]

    # ---- by mode
    m = s.groupby("mode").agg(Shipments=("shipment_id", "size"), TEU=("teu", "sum"),
                              **{"Chargeable kg": ("chargeable_weight_kg", "sum")})
    m["Spend"] = v[v.status != "REJECTED"].groupby("mode")["total_amount_eur"].sum()
    m["On-time"] = delivered.assign(ok=ontime).groupby("mode")["ok"].mean()
    m["Cost per kg"] = m["Spend"] / m["Chargeable kg"]
    m = m.reset_index().rename(columns={"mode": "Mode"})
    m["TEU"] = m["TEU"].map(lambda x: f"{x:,.0f}".replace(",", ".") if x else "")
    m["Chargeable kg"] = m["Chargeable kg"].map(lambda x: f"{x:,.0f}".replace(",", "."))
    m["Spend"] = m["Spend"].map(eur)
    m["On-time"] = m["On-time"].map(pct)
    m["Cost per kg"] = m["Cost per kg"].map(lambda x: f"{x:.2f} €".replace(".", ","))
    out += ["## By mode", "", "Spend excludes rejected invoices.", "", table(m), ""]

    # ---- invoice status
    st = v.groupby("status").agg(Invoices=("invoice_key", "size"), Amount=("total_amount_eur", "sum")).reset_index()
    st["Amount"] = st["Amount"].map(eur)
    out += ["## Invoices by status", "", table(st.rename(columns={"status": "Status"})), ""]

    # ---- payables
    open_ = v[v.status.isin(["APPROVED", "IN AUDIT"])]
    overdue = open_[open_.due_date < AS_OF]
    paid = v[v.status == "PAID"]
    days_over = (AS_OF - overdue.due_date).dt.days
    buckets = pd.cut(days_over, [0, 30, 60, 90, 100000], labels=["1–30", "31–60", "61–90", "90+"])
    ag = overdue.assign(Bucket=buckets).groupby("Bucket", observed=False).agg(
        Invoices=("invoice_key", "size"), Amount=("total_amount_eur", "sum")).reset_index()
    ag["Amount"] = ag["Amount"].map(eur)
    next30 = open_[(open_.due_date >= AS_OF) & (open_.due_date <= AS_OF + pd.Timedelta(days=30))]
    cycle = (paid.paid_date - paid.received_date).dt.days
    out += ["## Accounts payable", "", table(pd.DataFrame([
        {"Measure": "Open (approved or in audit)", "Value": f"{len(open_)} invoices · {eur(open_.total_amount_eur.sum())}"},
        {"Measure": "Overdue", "Value": f"{len(overdue)} invoices · {eur(overdue.total_amount_eur.sum())}"},
        {"Measure": "Due in the next 30 days", "Value": f"{len(next30)} invoices · {eur(next30.total_amount_eur.sum())}"},
        {"Measure": "Paid on time", "Value": pct((paid.paid_date <= paid.due_date).mean())},
        {"Measure": "Median days received → paid", "Value": f"{cycle.median():.0f}"},
    ])), "", "Overdue by days past due:", "", table(ag), ""]

    # ---- top lanes and carriers
    lanes = (s.groupby(["mode", "origin_code", "destination_code"]).size().rename("Shipments")
             .reset_index().sort_values("Shipments", ascending=False).head(10))
    lanes["Lane"] = lanes["origin_code"] + " → " + lanes["destination_code"]
    out += ["## Top 10 lanes by shipments", "", table(lanes[["mode", "Lane", "Shipments"]].rename(
        columns={"mode": "Mode"})), ""]

    car = s.merge(c[["carrier_id", "carrier_name"]], on="carrier_id").groupby(["mode", "carrier_name"]).size()
    car = car.rename("Shipments").reset_index().sort_values(["mode", "Shipments"], ascending=[True, False])
    top = car.groupby("mode").head(3).rename(columns={"mode": "Mode", "carrier_name": "Carrier"})
    out += ["## Top 3 carriers per mode by shipments", "", table(top), ""]

    ent = v[v.status != "REJECTED"].merge(e, on="entity_id").groupby("entity_name")["total_amount_eur"].sum()
    ent = ent.sort_values(ascending=False).map(eur).rename("Spend").reset_index().rename(
        columns={"entity_name": "Entity"})
    out += ["## Spend by entity", "", "Excludes rejected invoices.", "", table(ent), ""]

    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "control_totals.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
