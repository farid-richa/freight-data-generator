"""
Master data for the fictional "Valoria" group and its carriers.

Everything here is invented. Locations are real places with approximate
coordinates (so Power BI map visuals work); companies, carriers, rates and
volumes are fictional.
"""

# ---------------------------------------------------------------------------
# Billing entities of the fictional Valoria group
# ---------------------------------------------------------------------------
ENTITIES = [
    # id, official name, country iso3, share of volume, spelling variants seen in exports
    ("E01", "Valoria Consumer Care AG", "CHE", 0.18,
     ["VALORIA CONSUMER CARE AG", "Valoria Consumer Care AG ", "Valoria Consumer Care"]),
    ("E02", "Valoria Health AG", "DEU", 0.25,
     ["VALORIA HEALTH AG", "Valoria Health Aktiengesellschaft", "Valoria Health AG"]),
    ("E03", "Valoria Oy", "FIN", 0.12,
     ["VALORIA OY", "Valoria Oy", "Valoria OY "]),
    ("E04", "Valoria Steinfeld GmbH", "DEU", 0.15,
     ["VALORIA STEINFELD GMBH", "Valoria Steinfeld GmbH", "Valoria Steinfeld"]),
    ("E05", "Valoria Iberica SL", "ESP", 0.30,
     ["VALORIA IBERICA SL", "Valoria Iberica S.L.", "Valoria Iberica SL"]),
]

# Where each entity ships to / from, by mode
ENTITY_HUBS = {
    "E01": {"road": ["BSL"], "ocean": ["NLRTM", "ITGOA"], "air": ["ZRH"]},
    "E02": {"road": ["FRA-C", "HAM-C", "MUC"], "ocean": ["DEHAM"], "air": ["FRA"]},
    "E03": {"road": ["HEL-C"], "ocean": ["DEHAM"], "air": ["HEL"]},
    "E04": {"road": ["DUI", "MUC"], "ocean": ["NLRTM", "BEANR"], "air": ["FRA", "AMS"]},
    "E05": {"road": ["VLC", "MAD-C", "BCN-C"], "ocean": ["ESVLC"], "air": ["MAD", "BCN"]},
}

# ---------------------------------------------------------------------------
# Locations: code, name, type, iso2, iso3, country (EN), region, lat, lon
# Road locations use internal city codes; ports use UN/LOCODE; airports IATA.
# ---------------------------------------------------------------------------
LOCATIONS = [
    # road cities
    ("VLC", "Valencia", "City", "ES", "ESP", "Spain", "Europe", 39.47, -0.38),
    ("MAD-C", "Madrid", "City", "ES", "ESP", "Spain", "Europe", 40.42, -3.70),
    ("BCN-C", "Barcelona", "City", "ES", "ESP", "Spain", "Europe", 41.39, 2.17),
    ("ZAZ", "Zaragoza", "City", "ES", "ESP", "Spain", "Europe", 41.65, -0.89),
    ("LIS", "Lisbon", "City", "PT", "PRT", "Portugal", "Europe", 38.72, -9.14),
    ("LYS", "Lyon", "City", "FR", "FRA", "France", "Europe", 45.76, 4.84),
    ("PAR", "Paris", "City", "FR", "FRA", "France", "Europe", 48.86, 2.35),
    ("MIL", "Milan", "City", "IT", "ITA", "Italy", "Europe", 45.46, 9.19),
    ("MUC", "Munich", "City", "DE", "DEU", "Germany", "Europe", 48.14, 11.58),
    ("FRA-C", "Frankfurt", "City", "DE", "DEU", "Germany", "Europe", 50.11, 8.68),
    ("HAM-C", "Hamburg", "City", "DE", "DEU", "Germany", "Europe", 53.55, 9.99),
    ("DUI", "Duisburg", "City", "DE", "DEU", "Germany", "Europe", 51.43, 6.76),
    ("RTM-C", "Rotterdam", "City", "NL", "NLD", "Netherlands", "Europe", 51.92, 4.48),
    ("ANR-C", "Antwerp", "City", "BE", "BEL", "Belgium", "Europe", 51.22, 4.40),
    ("WAW", "Warsaw", "City", "PL", "POL", "Poland", "Europe", 52.23, 21.01),
    ("BSL", "Basel", "City", "CH", "CHE", "Switzerland", "Europe", 47.56, 7.59),
    ("VIE", "Vienna", "City", "AT", "AUT", "Austria", "Europe", 48.21, 16.37),
    ("HEL-C", "Helsinki", "City", "FI", "FIN", "Finland", "Europe", 60.17, 24.94),
    ("STO", "Stockholm", "City", "SE", "SWE", "Sweden", "Europe", 59.33, 18.07),
    ("BHX", "Birmingham", "City", "GB", "GBR", "United Kingdom", "Europe", 52.49, -1.89),
    # ports (UN/LOCODE)
    ("CNSHA", "Shanghai", "Port", "CN", "CHN", "China", "Asia", 31.23, 121.47),
    ("CNNGB", "Ningbo", "Port", "CN", "CHN", "China", "Asia", 29.87, 121.54),
    ("SGSIN", "Singapore", "Port", "SG", "SGP", "Singapore", "Asia", 1.29, 103.85),
    ("INNSA", "Nhava Sheva", "Port", "IN", "IND", "India", "Asia", 18.95, 72.95),
    ("USNYC", "New York", "Port", "US", "USA", "United States", "North America", 40.68, -74.04),
    ("BRSSZ", "Santos", "Port", "BR", "BRA", "Brazil", "South America", -23.96, -46.33),
    ("ESVLC", "Valencia", "Port", "ES", "ESP", "Spain", "Europe", 39.45, -0.32),
    ("NLRTM", "Rotterdam", "Port", "NL", "NLD", "Netherlands", "Europe", 51.95, 4.14),
    ("DEHAM", "Hamburg", "Port", "DE", "DEU", "Germany", "Europe", 53.54, 9.97),
    ("BEANR", "Antwerp", "Port", "BE", "BEL", "Belgium", "Europe", 51.26, 4.40),
    ("ITGOA", "Genoa", "Port", "IT", "ITA", "Italy", "Europe", 44.41, 8.93),
    # airports (IATA)
    ("PVG", "Shanghai Pudong", "Airport", "CN", "CHN", "China", "Asia", 31.14, 121.81),
    ("HKG", "Hong Kong", "Airport", "HK", "HKG", "Hong Kong", "Asia", 22.31, 113.92),
    ("BOM", "Mumbai", "Airport", "IN", "IND", "India", "Asia", 19.09, 72.87),
    ("NRT", "Tokyo Narita", "Airport", "JP", "JPN", "Japan", "Asia", 35.77, 140.39),
    ("ORD", "Chicago O'Hare", "Airport", "US", "USA", "United States", "North America", 41.97, -87.91),
    ("JFK", "New York JFK", "Airport", "US", "USA", "United States", "North America", 40.64, -73.78),
    ("GRU", "Sao Paulo Guarulhos", "Airport", "BR", "BRA", "Brazil", "South America", -23.43, -46.47),
    ("MAD", "Madrid Barajas", "Airport", "ES", "ESP", "Spain", "Europe", 40.49, -3.57),
    ("BCN", "Barcelona El Prat", "Airport", "ES", "ESP", "Spain", "Europe", 41.30, 2.08),
    ("FRA", "Frankfurt", "Airport", "DE", "DEU", "Germany", "Europe", 50.04, 8.56),
    ("AMS", "Amsterdam Schiphol", "Airport", "NL", "NLD", "Netherlands", "Europe", 52.31, 4.76),
    ("HEL", "Helsinki Vantaa", "Airport", "FI", "FIN", "Finland", "Europe", 60.32, 24.96),
    ("ZRH", "Zurich", "Airport", "CH", "CHE", "Switzerland", "Europe", 47.46, 8.55),
]

EU_ISO3 = {"AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN",
           "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"}

# How the road export spells countries (people type them by hand)
COUNTRY_SPELLINGS = {
    "ESP": ["Spain", "España", "ES", "ESP", "SPAIN"],
    "PRT": ["Portugal", "PT", "PRT"],
    "FRA": ["France", "Francia", "FR", "FRA"],
    "ITA": ["Italy", "Italia", "IT", "ITA"],
    "DEU": ["Germany", "Alemania", "DE", "DEU", "Deutschland"],
    "NLD": ["Netherlands", "Holanda", "NL", "NLD", "Países Bajos"],
    "BEL": ["Belgium", "Bélgica", "BE", "BEL"],
    "POL": ["Poland", "Polonia", "PL", "POL"],
    "CHE": ["Switzerland", "Suiza", "CH", "CHE"],
    "AUT": ["Austria", "AT", "AUT"],
    "FIN": ["Finland", "Finlandia", "FI", "FIN"],
    "SWE": ["Sweden", "Suecia", "SE", "SWE"],
    "GBR": ["United Kingdom", "Reino Unido", "UK", "GB", "GBR"],
}

# ---------------------------------------------------------------------------
# Carriers: id, official name, mode, country iso3, payment terms (days),
# on-time probability, price factor, invoice exception rate, invoice currency mix,
# spelling variants used in exports.
# Cheaper carriers tend to be less punctual, so "best carrier" is a trade-off.
# ---------------------------------------------------------------------------
CARRIERS = [
    # ---- road
    ("R01", "Levante Express SL", "Road", "ESP", 30, 0.94, 1.05, 0.03, {"EUR": 1},
     ["LEVANTE EXPRESS SL", "Levante Express S.L.", "Levante Express"]),
    ("R02", "Meseta Haulage SA", "Road", "ESP", 60, 0.86, 0.92, 0.08, {"EUR": 1},
     ["MESETA HAULAGE SA", "Meseta Haulage S.A.", "Meseta Haulage"]),
    ("R03", "Norte Cargo GmbH", "Road", "DEU", 45, 0.91, 1.00, 0.05, {"EUR": 1},
     ["NORTE CARGO GMBH", "Norte Cargo GmbH", "Norte Cargo"]),
    ("R04", "Costa Freight BV", "Road", "NLD", 30, 0.89, 0.97, 0.06, {"EUR": 1},
     ["COSTA FREIGHT BV", "Costa Freight B.V.", "Costa Freight"]),
    ("R05", "Rio Transportes Lda", "Road", "PRT", 45, 0.84, 0.88, 0.11, {"EUR": 1},
     ["RIO TRANSPORTES LDA", "Rio Transportes, Lda.", "Rio Transportes"]),
    ("R06", "Alpine Road AG", "Road", "CHE", 60, 0.95, 1.15, 0.02, {"EUR": 1},
     ["ALPINE ROAD AG", "Alpine Road AG", "Alpine Road"]),
    ("R07", "Vistula Trans Sp. z o.o.", "Road", "POL", 30, 0.82, 0.84, 0.13, {"EUR": 1},
     ["VISTULA TRANS SP. Z O.O.", "Vistula Trans", "VISTULA TRANS SP Z OO"]),
    ("R08", "Rhone Routiers SAS", "Road", "FRA", 45, 0.90, 1.02, 0.05, {"EUR": 1},
     ["RHONE ROUTIERS SAS", "Rhône Routiers SAS", "Rhone Routiers"]),
    ("R09", "Po Valley Trasporti Srl", "Road", "ITA", 60, 0.87, 0.95, 0.07, {"EUR": 1},
     ["PO VALLEY TRASPORTI SRL", "Po Valley Trasporti S.r.l.", "Po Valley Trasporti"]),
    ("R10", "Hanse Road GmbH", "Road", "DEU", 30, 0.93, 1.08, 0.04, {"EUR": 1},
     ["HANSE ROAD GMBH", "Hanse Road GmbH", "Hanse Road"]),
    ("R11", "Polder Transport BV", "Road", "NLD", 45, 0.88, 0.99, 0.06, {"EUR": 1},
     ["POLDER TRANSPORT BV", "Polder Transport B.V.", "Polder Transport"]),
    ("R12", "Nordic Linehaul AB", "Road", "SWE", 30, 0.92, 1.10, 0.04, {"EUR": 1},
     ["NORDIC LINEHAUL AB", "Nordic Linehaul AB", "Nordic Linehaul"]),
    ("R13", "Atlas Iberia Transportes SL", "Road", "ESP", 75, 0.85, 0.90, 0.09, {"EUR": 1},
     ["ATLAS IBERIA TRANSPORTES SL", "Atlas Iberia Transportes S.L.", "Atlas Iberia"]),
    ("R14", "Northstar Freight GmbH", "Road", "DEU", 60, 0.93, 1.00, 0.03, {"EUR": 1},
     ["NORTHSTAR FREIGHT GMBH", "Northstar Freight GmbH", "Northstar Freight"]),
    ("R15", "Celtic Haulage Ltd", "Road", "GBR", 30, 0.86, 1.04, 0.07, {"EUR": 0.6, "GBP": 0.4},
     ["CELTIC HAULAGE LTD", "Celtic Haulage Limited", "Celtic Haulage"]),
    ("R16", "Tajo Logistica SL", "Road", "ESP", 45, 0.90, 0.96, 0.05, {"EUR": 1},
     ["TAJO LOGISTICA SL", "Tajo Logística S.L.", "Tajo Logistica"]),
    # ---- ocean
    ("O01", "Bluewave Container Line", "Ocean", "SGP", 30, 0.78, 1.00, 0.06, {"USD": 1},
     ["BLUEWAVE CONTAINER LINE", "Bluewave Container Line Ltd", "Bluewave CL"]),
    ("O02", "Meridian Ocean Shipping", "Ocean", "CHN", 45, 0.72, 0.90, 0.09, {"USD": 1},
     ["MERIDIAN OCEAN SHIPPING", "Meridian Ocean Shipping Co.", "Meridian Ocean"]),
    ("O03", "Pacific Crest Lines", "Ocean", "CHN", 30, 0.80, 1.06, 0.05, {"USD": 1},
     ["PACIFIC CREST LINES", "Pacific Crest Lines Inc.", "Pacific Crest"]),
    ("O04", "Atlantica Maritime", "Ocean", "ESP", 60, 0.83, 1.10, 0.04, {"USD": 0.5, "EUR": 0.5},
     ["ATLANTICA MARITIME", "Atlántica Maritime S.A.", "Atlantica Maritime SA"]),
    ("O05", "Coral Sea Carriers", "Ocean", "SGP", 45, 0.70, 0.86, 0.12, {"USD": 1},
     ["CORAL SEA CARRIERS", "Coral Sea Carriers Pte Ltd", "Coral Sea"]),
    ("O06", "Northstar Ocean Forwarding", "Ocean", "DEU", 60, 0.81, 1.04, 0.03, {"EUR": 0.7, "USD": 0.3},
     ["NORTHSTAR OCEAN FORWARDING", "Northstar Ocean Fwd", "Northstar Ocean"]),
    ("O07", "Harbor Bridge Shipping", "Ocean", "USA", 30, 0.79, 0.98, 0.06, {"USD": 1},
     ["HARBOR BRIDGE SHIPPING", "Harbor Bridge Shipping LLC", "Harbor Bridge"]),
    # ---- air
    ("A01", "Skyline Air Cargo", "Air", "USA", 30, 0.91, 1.05, 0.05, {"USD": 1},
     ["SKYLINE AIR CARGO", "Skyline Air Cargo Inc.", "Skyline Air"]),
    ("A02", "Aerolink Freight", "Air", "NLD", 45, 0.88, 0.95, 0.07, {"EUR": 0.6, "USD": 0.4},
     ["AEROLINK FREIGHT", "Aerolink Freight B.V.", "Aerolink"]),
    ("A03", "Polaris Air Logistics", "Air", "FIN", 30, 0.93, 1.12, 0.03, {"EUR": 1},
     ["POLARIS AIR LOGISTICS", "Polaris Air Logistics Oy", "Polaris Air"]),
    ("A04", "Swift Wings Cargo", "Air", "HKG", 45, 0.84, 0.88, 0.10, {"USD": 1},
     ["SWIFT WINGS CARGO", "Swift Wings Cargo Ltd", "Swift Wings"]),
    ("A05", "Northstar Air Express", "Air", "DEU", 60, 0.92, 1.03, 0.03, {"EUR": 1},
     ["NORTHSTAR AIR EXPRESS", "Northstar Air Express GmbH", "Northstar Air"]),
    ("A06", "Cirrus Air Freight", "Air", "GBR", 30, 0.87, 0.97, 0.06, {"GBP": 0.7, "USD": 0.3},
     ["CIRRUS AIR FREIGHT", "Cirrus Air Freight Ltd", "Cirrus Air"]),
    ("A07", "Altitude Cargo Partners", "Air", "USA", 45, 0.86, 0.93, 0.08, {"USD": 1},
     ["ALTITUDE CARGO PARTNERS", "Altitude Cargo Partners LLC", "Altitude Cargo"]),
]

# Market share inside each mode (same order as CARRIERS for that mode)
MODE_SHARE = {"Road": 0.70, "Air": 0.20, "Ocean": 0.10}

# Ocean lanes: origin, destination, base USD per TEU, planned transit days
OCEAN_LANES = [
    ("CNSHA", "NLRTM", 1900, 32), ("CNSHA", "DEHAM", 1950, 34), ("CNSHA", "ESVLC", 1850, 29),
    ("CNNGB", "NLRTM", 1880, 33), ("CNNGB", "ITGOA", 1800, 28), ("SGSIN", "BEANR", 1600, 26),
    ("SGSIN", "ESVLC", 1550, 23), ("INNSA", "ESVLC", 1300, 20), ("INNSA", "DEHAM", 1450, 24),
    ("USNYC", "NLRTM", 1250, 12), ("USNYC", "ESVLC", 1350, 14),
    ("ESVLC", "USNYC", 1150, 14), ("NLRTM", "USNYC", 1100, 12), ("ESVLC", "BRSSZ", 1500, 21),
]

# Air lanes: origin, destination, base USD per chargeable kg, planned transit days
AIR_LANES = [
    ("PVG", "FRA", 3.9, 3), ("PVG", "AMS", 3.8, 3), ("PVG", "MAD", 4.1, 3), ("HKG", "FRA", 3.7, 2),
    ("HKG", "ZRH", 4.0, 3), ("HKG", "HEL", 4.2, 3), ("BOM", "FRA", 3.2, 2), ("BOM", "MAD", 3.4, 3),
    ("NRT", "AMS", 4.4, 2), ("ORD", "FRA", 2.9, 2), ("JFK", "MAD", 3.0, 2), ("JFK", "ZRH", 3.1, 2),
    ("MAD", "GRU", 3.6, 3), ("FRA", "ORD", 2.8, 2), ("AMS", "JFK", 2.7, 2), ("BCN", "JFK", 3.0, 2),
]
