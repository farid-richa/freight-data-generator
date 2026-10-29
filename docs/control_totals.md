# Control totals

What a correct model shows **as of 30 Oct 2026**, computed from the truth in `data/clean`. Amounts in EUR at the invoice month's rate. Use it to check every card and table in Power BI.

## Overview

| Measure | Value |
|---|---|
| Shipments | 12.000 |
| Shipments delivered | 11.954 |
| Invoices | 11.872 |
| Spend (all invoices) | 22.979.051 € |
| Spend excl. rejected | 22.488.699 € |
| On-time delivery | 88,4 % |

## By mode

Spend excludes rejected invoices.

| Mode | Shipments | TEU | Chargeable kg | Spend | On-time | Cost per kg |
|---|---|---|---|---|---|---|
| Air | 2384 |  | 1.052.599 | 3.930.662 € | 88,3 % | 3,73 € |
| Ocean | 1160 | 3.815 | 34.319.947 | 6.447.850 € | 79,3 % | 0,19 € |
| Road | 8456 |  | 47.024.317 | 12.110.187 € | 89,6 % | 0,26 € |

## Invoices by status

| Status | Invoices | Amount |
|---|---|---|
| APPROVED | 829 | 1.541.507 € |
| IN AUDIT | 76 | 114.883 € |
| PAID | 10716 | 20.832.309 € |
| REJECTED | 251 | 490.352 € |

## Accounts payable

| Measure | Value |
|---|---|
| Open (approved or in audit) | 905 invoices · 1.656.390 € |
| Overdue | 65 invoices · 157.579 € |
| Due in the next 30 days | 496 invoices · 905.976 € |
| Paid on time | 92,3 % |
| Median days received → paid | 39 |

Overdue by days past due:

| Bucket | Invoices | Amount |
|---|---|---|
| 1–30 | 25 | 55.782 € |
| 31–60 | 22 | 60.284 € |
| 61–90 | 10 | 15.736 € |
| 90+ | 8 | 25.778 € |

## Top 10 lanes by shipments

| Mode | Lane | Shipments |
|---|---|---|
| Air | HKG → HEL | 286 |
| Ocean | CNSHA → DEHAM | 228 |
| Air | HKG → ZRH | 217 |
| Air | JFK → ZRH | 210 |
| Ocean | INNSA → DEHAM | 205 |
| Air | ORD → FRA | 177 |
| Air | BOM → FRA | 176 |
| Air | PVG → FRA | 166 |
| Air | FRA → ORD | 165 |
| Air | HKG → FRA | 163 |

## Top 3 carriers per mode by shipments

| Mode | Carrier | Shipments |
|---|---|---|
| Air | Altitude Cargo Partners | 363 |
| Air | Skyline Air Cargo | 354 |
| Air | Polaris Air Logistics | 353 |
| Ocean | Harbor Bridge Shipping | 177 |
| Ocean | Coral Sea Carriers | 176 |
| Ocean | Atlantica Maritime | 175 |
| Road | Northstar Freight GmbH | 730 |
| Road | Norte Cargo GmbH | 691 |
| Road | Tajo Logistica SL | 680 |

## Spend by entity

Excludes rejected invoices.

| Entity | Spend |
|---|---|
| Valoria Iberica SL | 6.990.762 € |
| Valoria Health AG | 5.133.372 € |
| Valoria Oy | 3.847.828 € |
| Valoria Consumer Care AG | 3.605.996 € |
| Valoria Steinfeld GmbH | 2.910.741 € |
