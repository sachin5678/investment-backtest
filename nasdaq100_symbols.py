"""Current Nasdaq-100 constituent list (US tickers, no exchange suffix
needed for yfinance), fetched from slickcharts.com/nasdaq100 on 2026-08-24.
102 symbols (100 companies; GOOGL/GOOG dual-class shares both included, as
Nasdaq itself lists them). Used by fetch_nasdaq100.py / backtest20.py for
the NASDAQ100 Momentum 10 reconstruction — see that file's docstring.
"""

NASDAQ_100_SYMBOLS = [
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "SPCX", "AVGO", "TSLA", "META",
    "MU", "WMT", "AMD", "ASML", "INTC", "CSCO", "PLTR", "COST", "LRCX", "AMAT",
    "NFLX", "PANW", "ARM", "TXN", "KLAC", "AMGN", "SNDK", "LIN", "MRVL", "TMUS",
    "PEP", "CRWD", "STX", "SHOP", "ADI", "GILD", "QCOM", "WDC", "BKNG", "VRTX",
    "ISRG", "PDD", "SBUX", "FTNT", "ABNB", "ADP", "ADBE", "APP", "INTU", "MELI",
    "DASH", "CEG", "CSX", "CMCSA", "MNST", "MAR", "CDNS", "REGN", "DDOG", "MDLZ",
    "CTAS", "LITE", "ROST", "SNPS", "ORLY", "WBD", "PCAR", "HON", "AEP", "MPWR",
    "BKR", "NBIS", "FANG", "FAST", "TER", "NXPI", "ADSK", "PYPL", "HONA", "AXON",
    "ALAB", "WDAY", "CRWV", "CCEP", "XEL", "MSTR", "RKLB", "TRI", "FER", "EXC",
    "TTWO", "PAYX", "IDXX", "KDP", "ODFL", "MCHP", "ROP", "DXCM", "GEHC", "ALNY",
    "CPRT", "KHC",
]
