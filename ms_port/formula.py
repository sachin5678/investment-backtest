"""MomentumScore's ranking formula mini-language.

MomentumScore lets a strategy rank stocks by a free-form formula over
price series, e.g. its own worked example `ret(6m) / vol(6m)` — return
over the last 6 months divided by the trailing-6-month volatility. This
module compiles such formulas into callables over a plain list of close
prices, so any engine in this repo can offer "rank by formula" without
hand-writing a variant per idea.

Grammar:
    expr   := term (('+' | '-') term)*
    term   := factor (('*' | '/') factor)*
    factor := number | func | '(' expr ')' | '-' factor
    func   := NAME '(' NUMBER unit ')'
    unit   : m (months, 21 trading days) | w (weeks, 5) | y (years, 252) | d (days, 1)

Functions:
    ret(Nm)    — N-unit price return (fraction)
    vol(Nm)    — std dev of daily returns over the window (fraction/day)
    cagr(Ny)   — annualised CAGR over the window (fraction)
    maxdd(Nm)  — max drawdown over the window (fraction, <= 0)

Returned callable: fn(closes, idx) -> float, raising FormulaError on any
window that runs off the start of the series.
"""
from __future__ import annotations

import math

DAYS_PER = {"d": 1, "w": 5, "m": 21, "y": 252}


class FormulaError(ValueError):
    pass


def _tokenize(src):
    toks = []
    i = 0
    while i < len(src):
        c = src[i]
        if c.isspace():
            i += 1
        elif c in "+-*/(),":
            toks.append((c, None))
            i += 1
        elif c.isdigit() or c == ".":
            j = i
            while j < len(src) and (src[j].isdigit() or src[j] == "."):
                j += 1
            toks.append(("num", float(src[i:j])))
            i = j
        elif c.isalpha():
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            toks.append(("name", src[i:j]))
            i = j
        else:
            raise FormulaError(f"unexpected character {c!r} at position {i}")
    return toks


FUNCS = {"ret", "vol", "cagr", "maxdd"}


def _parse(toks):
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else (None, None)

    def eat(kind):
        t = peek()
        if t[0] != kind:
            raise FormulaError(f"expected {kind!r}, found {t[0]!r}")
        pos[0] += 1
        return t

    def expr():
        node = term()
        while peek()[0] in ("+", "-"):
            op = eat(peek()[0])[0]
            node = (op, node, term())
        return node

    def term():
        node = factor()
        while peek()[0] in ("*", "/"):
            op = eat(peek()[0])[0]
            node = (op, node, factor())
        return node

    def factor():
        kind, val = peek()
        if kind == "-":
            eat("-")
            return ("neg", factor())
        if kind == "(":
            eat("(")
            node = expr()
            eat(")")
            return node
        if kind == "num":
            eat("num")
            return ("const", val)
        if kind == "name":
            name = val
            eat("name")
            if name not in FUNCS:
                raise FormulaError(f"unknown function {name!r} (expected one of {sorted(FUNCS)})")
            eat("(")
            _, num = eat("num")
            _, unit = eat("name")
            if unit not in DAYS_PER:
                raise FormulaError(f"unknown unit {unit!r} (expected d/w/m/y)")
            eat(")")
            return ("call", name, int(round(num)), unit)
        raise FormulaError(f"unexpected token {peek()}")

    node = expr()
    if pos[0] != len(toks):
        raise FormulaError(f"unexpected trailing tokens from {toks[pos[0]]}")
    return node


def _lookback(node):
    """Maximum window (in trading days) the formula needs."""
    if node[0] == "call":
        return node[2] * DAYS_PER[node[3]]
    if node[0] == "const":
        return 0
    if node[0] == "neg":
        return _lookback(node[1])
    return max(_lookback(node[1]), _lookback(node[2]))


def _eval(node, closes, idx):
    if node[0] == "const":
        return node[1]
    if node[0] == "neg":
        return -_eval(node[1], closes, idx)
    if node[0] == "+":
        return _eval(node[1], closes, idx) + _eval(node[2], closes, idx)
    if node[0] == "-":
        return _eval(node[1], closes, idx) - _eval(node[2], closes, idx)
    if node[0] == "*":
        return _eval(node[1], closes, idx) * _eval(node[2], closes, idx)
    if node[0] == "/":
        denom = _eval(node[2], closes, idx)
        if denom == 0:
            return float("nan")
        return _eval(node[1], closes, idx) / denom
    # call
    _, name, n, unit = node
    win = n * DAYS_PER[unit]
    if idx - win < 0:
        raise FormulaError("window runs off the start of the series")
    window = closes[idx - win: idx + 1]
    if name == "ret":
        return window[-1] / window[0] - 1.0 if window[0] else float("nan")
    if name == "vol":
        rets = [window[i] / window[i - 1] - 1.0 for i in range(1, len(window)) if window[i - 1]]
        if len(rets) < 2:
            return float("nan")
        m = sum(rets) / len(rets)
        return math.sqrt(sum((r - m) ** 2 for r in rets) / len(rets))
    if name == "cagr":
        years = win / 252.0
        return (window[-1] / window[0]) ** (1.0 / years) - 1.0 if window[0] and years > 0 else float("nan")
    if name == "maxdd":
        peak = window[0]
        mdd = 0.0
        for v in window:
            peak = max(peak, v)
            if peak:
                mdd = min(mdd, v / peak - 1.0)
        return mdd
    raise FormulaError(f"unhandled function {name!r}")


def compile_formula(src):
    """Compile a formula string into fn(closes_list, idx) -> float."""
    node = _parse(_tokenize(src))

    def fn(closes, idx):
        return _eval(node, closes, idx)

    fn.lookback_days = _lookback(node)
    fn.source = src
    return fn
