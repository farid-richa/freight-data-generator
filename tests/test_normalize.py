"""
The normalised output must equal the truth in data/clean, table by table and column by column.

    pytest -q
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "normalizer"))
import normalize  # noqa: E402

KEYS = {
    "dim_carrier": "carrier_id", "dim_entity": "entity_id", "dim_location": "location_code",
    "fact_shipments": "shipment_id", "fact_invoices": "invoice_key", "fact_payments": "payment_id",
}


@pytest.fixture(scope="module")
def produced():
    return normalize.run()


def as_comparable(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime("%Y-%m-%d")
    return out


@pytest.mark.parametrize("table", list(KEYS))
def test_table_matches_truth(produced, table):
    truth = pd.read_csv(ROOT / "data" / "clean" / f"{table}.csv", keep_default_na=False, na_values=[""])
    got = as_comparable(produced[table])
    key = KEYS[table]
    assert len(got) == len(truth), f"{table}: {len(got)} rows vs {len(truth)} in truth"
    assert set(got[key]) == set(truth[key]), f"{table}: different {key} values"

    got = got.set_index(key).sort_index()
    truth = truth.set_index(key).sort_index()
    for col in truth.columns:
        assert col in got.columns, f"{table}: missing column {col}"
        a, b = got[col], truth[col]
        if pd.api.types.is_numeric_dtype(b):
            diff = (pd.to_numeric(a) - b).abs().fillna(0)
            both_nan = a.isna() & b.isna()
            assert ((diff < 0.011) | both_nan).all(), f"{table}.{col}: {(diff >= 0.011).sum()} values differ"
        else:
            a = a.fillna("").astype(str)
            b = b.fillna("").astype(str)
            bad = (a != b).sum()
            assert bad == 0, f"{table}.{col}: {bad} values differ, e.g. {a[a != b].head(3).to_dict()} vs {b[a != b].head(3).to_dict()}"


def test_no_unmapped_names(produced):
    assert not [l for l in normalize.log if "unmapped" in l]


def test_every_payment_matches_an_invoice(produced):
    assert produced["fact_payments"]["invoice_key"].notna().all()
