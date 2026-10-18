"""NIFTY Microcap 250 constituent list (NSE symbols), fetched from NSE's
official archive CSV (https://nsearchives.nseindia.com/content/indices/
ind_niftymicrocap250_list.csv) on 2026-10-18. Used by backtest103.py for
the "Microcap 250 Momentum 10" study.

The index name says 250; the CSV ships 254 rows of which 249 are Series=EQ
(the 5 BE-series names are excluded — trade-to-trade segment, excluded from
every universe build in this project by convention).

NIFTY Microcap 250 is a REAL NSE index (launched Dec 2024), but the top-10
momentum selection applied to it here is NOT — same non-official-variant
convention as every other reconstruction in this project.

DISCLOSURES this list carries (same class as every other reconstruction
here, but heavier because of the universe):
  - today's membership used retroactively (survivorship bias is severe in
    microcaps — delisted/failed names are gone from this list);
  - the index itself launched only in Dec 2024, so "Microcap 250" before
    then is a backfilled construct of today's constituents;
  - equal weighting instead of free-float-market-cap weighting.
"""

MICROCAP_250_SYMBOLS = [
    "AARTIPHARM", "ABFRL", "ABLBL", "ACI", "ADVENZYMES", "AEQUS", "AEROFLEX",
    "AKUMS", "ALKYLAMINE", "AMAGI", "APOLLO", "ARVIND", "ARVINDFASN", "ASHAPURMIN",
    "ASHOKA", "ASTRAMICRO", "ATLANTAELE", "AURIONPRO", "AVALON", "AVL", "AXISCADES",
    "BAJAJCON", "BALAMINES", "BALUFORGE", "BANCOINDIA", "BECTORFOOD", "BIRLACORPN", "BLACKBUCK",
    "BLUEJET", "BLUESTONE", "BORORENEW", "CAMPUS", "CAPILLARY", "CEIGALL", "CELLO",
    "CENTUM", "CERA", "CHALET", "CMRGREEN", "CMSINFO", "CRAMC", "CSBBANK",
    "DATAMATICS", "DBL", "DBREALTY", "DCBBANK", "DUMMYINGL1", "DUMMYINGL2", "DUMMYINXGN",
    "DYNAMATECH", "EBGNG", "EDELWEISS", "EIEL", "ELECTCAST", "ELLEN", "EMBDL",
    "EMIL", "ENTERO", "EPL", "EQUITASBNK", "ERIS", "FEDFINA", "FIEMIND",
    "FINPIPE", "GAEL", "GENUSPOWER", "GMRP&UI", "GNFC", "GODREJAGRO", "GOKEX",
    "GOKULAGRO", "GOLDIAM", "GPPL", "GREAVESCOT", "GRINDWELL", "GRWRHITECH", "GSFC",
    "GUJALKALI", "HAPPSTMNDS", "HAPPYFORGE", "HCC", "HCG", "HERITGFOOD", "HGINFRA",
    "ICIL", "IFBIND", "IIFLCAPS", "IMFA", "INDGN", "INDIAGLYCO", "INDIGOPNTS",
    "IONEXCHANG", "IXIGO", "JAIBALAJI", "JAMNAAUTO", "JAYNECOIND", "JKPAPER", "JSFB",
    "JSLL", "JUBLPHARMA", "JUSTDIAL", "JYOTHYLAB", "KANSAINER", "KIRLPNU", "KISSHT",
    "KITEX", "KMEW", "KNRCON", "KPIGREEN", "KRBL", "KRN", "KSCL",
    "KTKBANK", "KWIL", "LATENTVIEW", "LLOYDSENGG", "LLOYDSENT", "LUMAXIND", "LUMAXTECH",
    "LXCHEM", "MANORAMA", "MANYAVAR", "MAPMYINDIA", "MARKSANS", "MASTEK", "MBAPL",
    "MEDPLUS", "METROPOLIS", "MIDHANI", "MOIL", "MSTCLTD", "NAZARA", "NEOGEN",
    "NEPHROPLUS", "NETWORK18", "NEWGEN", "NFL", "NIVABUPA", "NORTHARC", "OMNI",
    "OSWALPUMPS", "PAISALO", "PARAS", "PARKHOSPS", "PCJEWELLER", "PDSL", "PFIZER",
    "PGHL", "PGIL", "PICCADIL", "PNCINFRA", "PNGJL", "POWERICA", "POWERMECH",
    "PRAJIND", "PRECWIRE", "PRICOLLTD", "PTC", "PURVA", "QPOWER", "QUESS",
    "RAIN", "RALLIS", "RATEGAIN", "RATNAMANI", "RAYMONDLSL", "RBA", "RCF",
    "REFEX", "RELAXO", "RELIGARE", "RENUKA", "RESPONIND", "ROUTE", "RTNPOWER",
    "SAFARI", "SAMHI", "SANDUMA", "SAPPHIRE", "SAREGAMA", "SBFC", "SEDEMAC",
    "SENCO", "SENORES", "SFL", "SGMART", "SHADOWFAX", "SHAILY", "SHAKTIPUMP",
    "SHARDACROP", "SHAREINDIA", "SHILCTECH", "SHILPAMED", "SHREEJISPG", "SJS", "SKIPPER",
    "SKYGOLD", "SMLMAH", "SONATSOFTW", "SOUTHBANK", "SPARC", "SPLPETRO", "STAR",
    "STYLAMIND", "SUBROS", "SUDARSCHEM", "SUDEEPPHRM", "SUNDRMFAST", "SUNFLAG", "SUNTECK",
    "SUPRIYA", "SURYAROSNI", "SUVEN", "SWSOLAR", "TANLA", "TARC", "TEXRAIL",
    "THELEELA", "THOMASCOOK", "THYROCARE", "TI", "TIMETECHNO", "TIMEX", "TIPSMUSIC",
    "TMB", "TRANSRAILL", "TTKPRESTIG", "TVSSCS", "UJJIVANSFB", "UNIMECH", "UTLSOLAR",
    "V2RETAIL", "VAIBHAVGBL", "VESUVIUS", "VGUARD", "VIKRAMSOLR", "VIPIND", "VIYASH",
    "VMART", "VOLTAMP", "WAAREERTL", "WABAG", "WAKEFIT", "WEBELSOLAR", "WELENT",
    "WESTLIFE", "WEWORK", "YATHARTH", "ZAGGLE"
]
