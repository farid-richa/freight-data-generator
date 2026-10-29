# Freight Data Generator

A fictional but realistic **multimodal freight dataset** (road, ocean, air) for practising and showing data work: **12,000 shipments, 11,872 carrier invoices and 10,716 payments** from January 2025 to October 2026, across 30 carriers and 5 billing entities.

It comes in two versions of the same facts:

- **`data/raw/`: as real systems export it.** One file per mode, each with its own columns, units, date formats and currencies, plus an AP invoice register, a payments ledger and master data. This is where Power BI (Power Query) and SQL start.
- **`data/clean/`: the answer key.** The same data as a tidy star schema. A correct normalisation must reproduce it exactly.

> **All data is fictional.** The group "Valoria", its entities, the carriers, rates and volumes are invented. Cities, ports and airports are real places, so map visuals work.

It feeds the next projects in this portfolio: a set of **Power BI reports** (carriers and lanes, accounts payable, spend by entity, invoice quality) and a **SQL** version of the same KPIs.

## Why the raw data is messy

Because real data is. Every problem below comes from the kind of exports a freight audit team receives, and fixing them is most of the work:

| Problem | Where | Count in this dataset |
|---|---|---|
| One carrier, several spellings (`Levante Express S.L.`, `LEVANTE EXPRESS SL `…) | all exports | 30 carriers, 85 known spellings, plus case and spacing noise |
| Entity name with a non-breaking space | all exports | 1 entity |
| Weight in tonnes instead of kg | ocean | 124 rows |
| TEU missing (derive from equipment × containers) | ocean | 49 rows |
| Exact duplicate rows | air | 18 rows |
| Chargeable weight missing (max of actual kg and m³ × 167) | air | 177 rows |
| Numbers as text `1.234,56`, `;` separator, `d/m/yy` dates | road | whole file |
| Countries typed by hand: 13 countries written 54 ways | road | whole file |
| A TOTAL footer row | road | 1 row |
| Status codes and `NET60` terms | AP register | whole file |
| Invoice reference without `-` and `/`, negative amounts | payments ledger | whole file |

Full detail in [`docs/data_dictionary.md`](docs/data_dictionary.md).

## The data model

```
                dim_date (built in Power BI)
                         │
dim_carrier ─┐           │           ┌─ dim_location (origin / destination)
dim_entity ──┼── fact_shipments ── fact_invoices ── fact_payments
             └───────────────────────┘
```

## What's in it

- Carriers differ on purpose: cheaper ones tend to be less punctual, so "best carrier" is a real trade-off.
- Volumes grow over time, peak in October–November and dip in August.
- Ocean rates follow a seasonal cycle; air rates fall with weight bands.
- Payments run every Friday: the last run before the due date, or the first after approval when the audit took too long. Some invoices are held or disputed, so there are late payments and overdue items across all ageing buckets.
- Statuses and open items are **as of 30 October 2026**.

## Control totals

[`docs/control_totals.md`](docs/control_totals.md) lists what a correct model shows: spend by mode and entity, invoice status, open and overdue amounts with ageing, paid on time, on-time delivery, top lanes and carriers. Highlights:

| | |
|---|---|
| Spend (excl. rejected) | 22,488,699 € |
| On-time delivery | 88.4 % (ocean 79.3 %) |
| Paid on time | 92.3 % |
| Overdue | 65 invoices · 157,579 € |

## Reference normalisation and tests

`normalizer/normalize.py` turns `data/raw` into the star schema, one function per source, in the same order as the Power Query steps. It prints a data-quality log:

```
ocean: 124 weights converted from tonnes
ocean: 49 blank TEU filled from equipment x containers
air: 18 exact duplicate rows removed
air: 177 blank chargeable weights computed as max(actual, m3 x 167)
road: 1 footer TOTAL row removed
road: 13 countries written 54 ways; 0 origin country mismatches
payments: 10716 ledger lines, 0 not matched to an invoice
```

`tests/test_normalize.py` compares every table, column by column, with the answer key. To check that the tests would catch mistakes, I broke four steps on purpose (tonnes not converted, duplicates kept, ledger sign not flipped, dates read month-first): each one made the tests fail.

## Run it

```bash
pip install -r requirements.txt
python generator/generate.py          # writes data/raw and data/clean (seed 2026)
python generator/control_totals.py    # writes docs/control_totals.md
python normalizer/normalize.py        # writes output/ and prints the quality log
pytest -q                             # output/ must equal data/clean
```

## Files

```
generator/master_data.py     entities, carriers, locations, lanes
generator/generate.py        simulation → data/clean (truth) and data/raw (exports)
generator/control_totals.py  expected KPIs for checking the reports
normalizer/normalize.py      reference normalisation (Python version of the Power Query steps)
normalizer/mappings/         country spellings → ISO3
tests/                       output must equal the answer key
docs/                        data dictionary and control totals
```

Built with AI assistance (Claude).
