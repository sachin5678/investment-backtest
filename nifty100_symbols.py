"""Current NIFTY 100 constituent list (NSE symbols), fetched from NSE's
official archive CSV (https://archives.nseindia.com/content/indices/ind_nifty100list.csv)
on 2026-08-24. Used by backtest11.py for the "NIFTY100 Momentum 10" custom
reconstruction — see that file's docstring: no such official NSE index
exists, this applies the real published Momentum 30 formula to this smaller
universe with N=10 instead, as a clearly-labelled, non-official variant.
"""

NIFTY_100_SYMBOLS = [
    "ABB", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "AMBUJACEM", "APOLLOHOSP",
    "ASIANPAINT", "DMART", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BAJAJHLDNG", "BANKBARODA",
    "BEL", "BPCL", "BHARTIARTL", "BOSCHLTD", "BRITANNIA", "CGPOWER", "CANBK", "CHOLAFIN", "CIPLA",
    "COALINDIA", "CUMMINSIND", "DLF", "DIVISLAB", "DRREDDY", "EICHERMOT", "ETERNAL", "GAIL", "GODREJCP",
    "GRASIM", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HINDALCO", "HAL", "HINDUNILVR", "HINDZINC",
    "HYUNDAI", "ICICIBANK", "ITC", "INDHOTEL", "IOC", "IRFC", "INFY", "INDIGO", "JSWSTEEL", "JINDALSTEL",
    "JIOFIN", "KOTAKBANK", "LTM", "LT", "LODHA", "M&M", "MARUTI", "MAXHEALTH", "MAZDOCK", "MUTHOOTFIN",
    "NTPC", "NESTLEIND", "ONGC", "PIDILITIND", "PFC", "POWERGRID", "PNB", "RECLTD", "RELIANCE", "SBILIFE",
    "MOTHERSON", "SHREECEM", "SHRIRAMFIN", "ENRIN", "SIEMENS", "SOLARINDS", "SBIN", "SUNPHARMA", "TVSMOTOR",
    "TATACAP", "TCS", "TATACONSUM", "TMCV", "TMPV", "TATAPOWER", "TATASTEEL", "TECHM", "TITAN",
    "TORNTPHARM", "TRENT", "ULTRACEMCO", "UNIONBANK", "UNITDSPR", "VBL", "VEDL", "WIPRO", "ZYDUSLIFE",
]
