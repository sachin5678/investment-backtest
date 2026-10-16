import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ms_port import formula


def _series_daily(rate, n=300):
    return [100.0 * (1 + rate) ** i for i in range(n)]


def test_ret_simple():
    closes = [100.0 + i for i in range(300)]
    fn = formula.compile_formula("ret(1m)")
    v = fn(closes, 21)
    assert math.isclose(v, 121.0 / 100.0 - 1.0)


def test_ret_over_vol_compiles_and_runs():
    closes = _series_daily(0.001)
    fn = formula.compile_formula("ret(6m) / vol(6m)")
    v = fn(closes, 260)
    assert v > 0
    assert fn.lookback_days == 126


def test_arithmetic_precedence_and_parens():
    closes = _series_daily(0.0)
    fn = formula.compile_formula("2 + 3 * 4")
    assert fn(closes, 0) == 14.0
    fn2 = formula.compile_formula("(2 + 3) * 4")
    assert fn2(closes, 0) == 20.0
    fn3 = formula.compile_formula("-ret(1w) + 1")
    assert math.isclose(fn3(closes, 10), 1.0)


def test_cagr_and_maxdd():
    closes = [100.0] * 252 + [50.0]  # wait - need increasing then flat; use direct window
    closes = [100.0 * (1.1) ** (i / 252.0) for i in range(253)]
    fn = formula.compile_formula("cagr(1y)")
    assert math.isclose(fn(closes, 252), 0.1, abs_tol=1e-9)
    closes2 = [100.0, 120.0, 60.0, 90.0, 95.0, 99.0]
    fn2 = formula.compile_formula("maxdd(1w)")
    assert math.isclose(fn2(closes2, 5), 60.0 / 120.0 - 1.0)


def test_errors():
    with pytest.raises(formula.FormulaError):
        formula.compile_formula("ret(6x)")
    with pytest.raises(formula.FormulaError):
        formula.compile_formula("foo(6m)")
    with pytest.raises(formula.FormulaError):
        formula.compile_formula("ret(6m")
    fn = formula.compile_formula("ret(6m)")
    with pytest.raises(formula.FormulaError):
        fn([100.0] * 100, 50)  # window runs off the start


def test_division_by_zero_is_nan():
    closes = _series_daily(0.0, 300)
    fn = formula.compile_formula("ret(1m) / vol(1m)")
    v = fn(closes, 100)
    assert math.isnan(v)
