# Data dictionary

## Raw files (`data/raw/`): what you normalise

| File | One row per | Format | Problems planted on purpose |
|---|---|---|---|
| `ocean_export.csv` | Booking (shipment + its invoice) | `,` · dates `dd/mm/yyyy` | Carrier and entity names in several spellings, case and stray spaces · weight in **KG or T** (see `Weight Unit`) · `TEU` blank on some rows (= containers × 1 for 20GP, × 2 for 40HC) · currency written `USD`, `usd`, `Usd` · charges split in Ocean Freight + BAF + THC |
| `air_export.csv` | Air waybill | `,` · ISO datetimes `2026-07-09T18:30:00` | Exact **duplicate rows** (export glitch) · `Chargeable Weight` blank on some rows (= max(actual kg, m³ × 167), rounded to 0.5) · names and currency as above |
| `road_export.csv` | Road shipment | **`;`** · UTF-8 with BOM · dates `d/m/yy` · Spanish headers | Numbers as text with **`1.234,56`** · countries typed by hand (`Germany`, `Alemania`, `DE`, `Deutschland`…) · cities by name, not code · a **TOTAL** footer row |
| `ap_invoice_register.csv` | Invoice received in the ERP | ISO dates | Status as codes (`PD` paid, `AP` approved, `RJ` rejected, `AU` in audit) · terms as `NET30`, `NET60`… |
| `ap_payments_ledger.csv` | Payment posted | `Posting Date` as `yyyymmdd` | Invoice reference **without `-` `/`** (match after stripping them from the invoice number, per vendor) · amounts **negative** (outflows) |
| `carriers_master.csv` | Carrier | | Official names, mode, payment terms |
| `carrier_aliases.csv` | Known spelling of a carrier | Upper case, single spaces | Mapping table: clean the export's name (trim, collapse spaces, upper) and look it up |
| `entities.csv` | Billing entity | `Aliases` pipe-separated | Same idea for entity names; one name uses a non-breaking space |
| `locations.csv` | City, port (UN/LOCODE) or airport (IATA) | | Coordinates for map visuals; road cities have their own codes |
| `fx_rates.csv` | Month × currency | `Rate to EUR` | EUR is implicitly 1 |

`normalizer/mappings/country_aliases.csv` is the mapping an analyst builds for the hand-typed countries; it is part of the solution, not of the raw export.

## Clean model (`data/clean/`): the answer key

### fact_shipments: one row per shipment
| Column | Meaning |
|---|---|
| shipment_id | Booking ref (ocean), AWB (air) or shipment number (road) |
| mode | Road, Ocean, Air |
| carrier_id, entity_id | → dim_carrier, dim_entity |
| origin_code, destination_code | → dim_location |
| distance_km | Great circle between the two locations; × 1.25 for road |
| pickup_date | Collection (road, air) or actual departure, ATD (ocean) |
| planned_delivery_date | Promised delivery / ETA |
| actual_delivery_date | Delivered / ATA; empty if not delivered by 30 Oct 2026 |
| gross_weight_kg, chargeable_weight_kg | Chargeable = gross for road and ocean |
| teu, containers | Ocean only |
| pallets | Road only |
| pieces | Air only |

### fact_invoices: one row per carrier invoice received
| Column | Meaning |
|---|---|
| invoice_key | `carrier_id|invoice_number` (invoice numbers repeat across carriers) |
| shipment_id | → fact_shipments |
| invoice_date, received_date | Carrier's date and the date it reached AP |
| approval_date / rejection_date | Audit decision (only one is filled) |
| due_date, payment_terms_days | Invoice date + carrier's terms |
| status | PAID, APPROVED (open), IN AUDIT (open), REJECTED, as of 30 Oct 2026 |
| currency, total_amount | As invoiced (EUR, USD or GBP) |
| fx_rate_to_eur, total_amount_eur | Rate of the invoice month |
| paid_date | From the payments ledger |

### fact_payments: one row per payment
`payment_id`, `invoice_key`, `carrier_id`, `payment_date`, `amount` (positive), `currency`, `amount_eur` (rate of the payment month).

### Dimensions
`dim_carrier` (30 carriers: 16 road, 7 ocean, 7 air) · `dim_entity` (5 billing entities) · `dim_location` (44 cities, ports and airports, with EU flag, region and coordinates) · `fx_rates`.

## Definitions used across the reports

| Term | Definition |
|---|---|
| On time (delivery) | actual_delivery_date ≤ planned_delivery_date, delivered shipments only |
| Open invoice | status APPROVED or IN AUDIT |
| Overdue | Open and due_date before 30 Oct 2026 |
| Paid on time | paid_date ≤ due_date |
| Spend | total_amount_eur of invoices not rejected |
