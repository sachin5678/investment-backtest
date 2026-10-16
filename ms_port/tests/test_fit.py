import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ms_port import fit


def test_percentiles_spread_and_order():
    scores = {"A": 30.0, "B": 20.0, "C": 10.0}
    f = fit.fit_percentiles(scores)
    assert f["A"] == 100 and f["B"] == 50 and f["C"] == 0


def test_ties_share_best_fit():
    scores = {"A": 30.0, "B": 30.0, "C": 10.0}
    f = fit.fit_percentiles(scores)
    assert f["A"] == 100 and f["B"] == 100 and f["C"] == 0


def test_single_ticker():
    assert fit.fit_percentiles({"A": 1.0}) == {"A": 100}


def test_ranked_rows_with_previous():
    prev = {"A": 10.0, "B": 20.0, "C": 30.0}   # prev: C rank1, B rank2, A rank3
    now = {"A": 10.0, "B": 40.0, "C": 5.0}     # now: B rank1, A rank2, C rank3
    rows = fit.ranked_rows(now, prev_scores=prev, held=["A"])
    by = {r["ticker"]: r for r in rows}
    assert by["B"]["rank"] == 1 and by["A"]["rank"] == 2 and by["C"]["rank"] == 3
    assert by["B"]["prev_rank"] == 2
    assert by["B"]["rank_delta"] == 1           # improved one place
    assert by["A"]["prev_rank"] == 3
    assert by["A"]["rank_delta"] == 1
    assert by["B"]["fit_delta"] == 100 - 50     # 50 -> 100
    assert by["C"]["fit_delta"] == 0 - 100
    assert by["A"]["held"] is True


def test_new_entry_has_no_prev():
    rows = fit.ranked_rows({"NEW": 5.0, "OLD": 1.0}, prev_scores={"OLD": 1.0})
    by = {r["ticker"]: r for r in rows}
    assert by["NEW"]["prev_rank"] is None
    assert by["NEW"]["rank_delta"] is None
