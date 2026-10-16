"""MomentumScore's "fit" — a 0-100 percentile standing of a stock's
signal against the rest of the eligible universe, best fit = 100, plus
the delta vs the previous review (their "Fit in → out" trade-log columns
and the ranks table's "Δ vs last review").

Pure functions over plain dicts {ticker: score} — used by the report-93
review engine and by anything else that wants percentile standings.
"""
from __future__ import annotations


def fit_percentiles(scores):
    """scores: {ticker: raw_score}. Returns {ticker: fit_0_100}.

    Fit is the share of the universe a stock's score stands at or above,
    scaled 0-100 (best = 100, worst = 0). Ties share the better fit."""
    if not scores:
        return {}
    items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    n = len(items)
    out = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and items[j + 1][1] == items[i][1]:
            j += 1
        # positions i..j tie: everyone in the tie gets the best position's fit
        fit = round((1.0 - i / (n - 1)) * 100) if n > 1 else 100
        for k in range(i, j + 1):
            out[items[k][0]] = fit
        i = j + 1
    return out


def ranked_rows(scores, prev_scores=None, held=None):
    """One row per ticker: rank, fit, and (if prev_scores given) the
    previous rank/fit and the two deltas — the exact columns
    MomentumScore shows as "Rank in → out" and "Fit in → out".

    prev_scores: {ticker: prev_score} (previous review's raw scores;
    a NEW entry has no previous row and gets prev_rank=None).
    held: optional iterable of currently held tickers.
    """
    if not scores:
        return []
    fit_now = fit_percentiles(scores)
    order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    rank_now = {tk: i + 1 for i, (tk, _) in enumerate(order)}
    fit_prev = fit_percentiles(prev_scores) if prev_scores else {}
    rank_prev = None
    if prev_scores:
        prev_order = sorted(prev_scores.items(), key=lambda kv: kv[1], reverse=True)
        rank_prev = {tk: i + 1 for i, (tk, _) in enumerate(prev_order)}

    held_set = set(held or [])
    rows = []
    for tk, score in order:
        r = {
            "ticker": tk,
            "score": score,
            "rank": rank_now[tk],
            "fit": fit_now[tk],
            "held": tk in held_set,
        }
        if rank_prev is not None:
            r["prev_rank"] = rank_prev.get(tk)
            r["prev_fit"] = fit_prev.get(tk)
            r["rank_delta"] = (r["prev_rank"] - rank_now[tk]) if r["prev_rank"] is not None else None
            r["fit_delta"] = (r["fit"] - r["prev_fit"]) if r["prev_fit"] is not None else None
        rows.append(r)
    return rows
