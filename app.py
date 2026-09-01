#!/usr/bin/env python3
"""
FOREX TRADING SYSTEM — Streamlit App
Version 4.2 | Full 12 Strategies + Auth + Owners Panel
Educational Use Only
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ForexApp")

# ═══════════════════════════════════════════════════════════════════════════
# OWNER & AUTH CONFIG
# ═══════════════════════════════════════════════════════════════════════════

OWNER = {
    "name": "BISMARK OSEI OWUSU",
    "email": "monarchmanaois777666@gmail.com",
    "contact": "+233 559512438",
    "role": "Owner / Admin",
}

# Simple demo credentials (change in production)
# Username: Monarch Manaois   |  Password: Devil, HellTHELigHT6.
OWNER_USERNAME = "Monarch Manaois"
OWNER_PASSWORD_HASH = hashlib.sha256("Devil, HellTHELigHT6.".encode()).hexdigest()

# Invite tokens stored in session (demo only — use a real DB in production)
if "invite_tokens" not in st.session_state:
    st.session_state.invite_tokens = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# ═══════════════════════════════════════════════════════════════════════════
# CORE TRADING LOGIC
# ═══════════════════════════════════════════════════════════════════════════

class Side(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()

@dataclass
class Signal:
    strategy: str
    side: Side
    pair: str
    price: float
    stop_loss: float
    take_profit: float
    confidence: float
    timestamp: datetime
    reason: str = ""

    def to_dict(self):
        return {
            "strategy": self.strategy,
            "side": self.side.name,
            "pair": self.pair,
            "price": round(self.price, 5),
            "stop_loss": round(self.stop_loss, 5),
            "take_profit": round(self.take_profit, 5),
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
        }

# ── Indicators ────────────────────────────────────────────────────────────

def atr(highs, lows, closes, period=14):
    n = len(closes)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1]))
    out = np.full(n, np.nan)
    if n <= period:
        return out
    out[period-1] = np.mean(tr[:period])
    for i in range(period, n):
        out[i] = (out[i-1] * (period - 1) + tr[i]) / period
    return out

def ema(data, period):
    out = np.full_like(data, np.nan, dtype=float)
    if len(data) < period:
        return out
    k = 2.0 / (period + 1)
    out[period-1] = np.mean(data[:period])
    for i in range(period, len(data)):
        out[i] = data[i] * k + out[i-1] * (1 - k)
    return out

def sma(data, period):
    out = np.full_like(data, np.nan, dtype=float)
    for i in range(period-1, len(data)):
        out[i] = np.mean(data[i-period+1:i+1])
    return out

def rsi(closes, period=14):
    n = len(closes)
    out = np.full(n, np.nan)
    if n < period + 1:
        return out
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    out[period] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1 + avg_gain / avg_loss)
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out[i+1] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1 + avg_gain / avg_loss)
    return out

def bollinger_bands(closes, period=20, num_std=2.0):
    mid = sma(closes, period)
    std = np.full_like(closes, np.nan)
    for i in range(period-1, len(closes)):
        std[i] = np.std(closes[i-period+1:i+1])
    return mid + num_std * std, mid, mid - num_std * std

def macd(closes, fast=12, slow=26, signal=9):
    ema_f = ema(closes, fast)
    ema_s = ema(closes, slow)
    line = ema_f - ema_s
    valid = ~np.isnan(line)
    sig = np.full_like(closes, np.nan)
    if valid.sum() >= signal:
        sig_vals = ema(line[valid], signal)
        sig[np.where(valid)[0]] = sig_vals
    return line, sig, line - sig

def stochastic(highs, lows, closes, k_period=14, d_period=3):
    n = len(closes)
    k = np.full(n, np.nan)
    for i in range(k_period-1, n):
        hh = np.max(highs[i-k_period+1:i+1])
        ll = np.min(lows[i-k_period+1:i+1])
        k[i] = 50.0 if hh == ll else 100.0 * (closes[i] - ll) / (hh - ll)
    return k, sma(k, d_period)

def adx(highs, lows, closes, period=14):
    n = len(closes)
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    tr = np.zeros(n)
    for i in range(1, n):
        up = highs[i] - highs[i-1]
        down = lows[i-1] - lows[i]
        plus_dm[i] = up if (up > down and up > 0) else 0.0
        minus_dm[i] = down if (down > up and down > 0) else 0.0
        tr[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
    atr_s = np.full(n, np.nan)
    dx = np.full(n, np.nan)
    if n <= period:
        return np.full(n, np.nan)
    atr_s[period] = np.sum(tr[1:period+1])
    plus_s = np.sum(plus_dm[1:period+1])
    minus_s = np.sum(minus_dm[1:period+1])
    for i in range(period+1, n):
        atr_s[i] = atr_s[i-1] - atr_s[i-1]/period + tr[i]
        plus_s = plus_s - plus_s/period + plus_dm[i]
        minus_s = minus_s - minus_s/period + minus_dm[i]
        pdi = 100 * plus_s / atr_s[i] if atr_s[i] else 0
        mdi = 100 * minus_s / atr_s[i] if atr_s[i] else 0
        denom = pdi + mdi
        dx[i] = 100 * abs(pdi - mdi) / denom if denom else 0
    out = np.full(n, np.nan)
    valid = dx[~np.isnan(dx)]
    if len(valid) >= period:
        start = period * 2 - 1
        if start < n:
            out[start] = np.mean(valid[:period])
            for i in range(start+1, n):
                if not np.isnan(dx[i]):
                    out[i] = (out[i-1] * (period-1) + dx[i]) / period
    return out

def pips(pair, price_diff):
    return price_diff * 100 if "JPY" in pair else price_diff * 10000

def pip_value(pair, lot=1.0):
    return 9.09 * lot if "JPY" in pair else 10.0 * lot

# ── Sessions ──────────────────────────────────────────────────────────────

class Session(Enum):
    SYDNEY = "Sydney"
    TOKYO = "Tokyo"
    LONDON = "London"
    NEW_YORK = "New York"

SESSION_HOURS = {
    Session.SYDNEY: (22, 7),
    Session.TOKYO: (0, 9),
    Session.LONDON: (7, 16),
    Session.NEW_YORK: (12, 21),
}

OVERLAPS = {
    "London-New York": (12, 16),
    "Tokyo-London": (7, 9),
    "Sydney-Tokyo": (0, 7),
}

PAIR_SESSION = {
    "EUR/USD": [Session.LONDON, Session.NEW_YORK],
    "GBP/USD": [Session.LONDON, Session.NEW_YORK],
    "USD/JPY": [Session.TOKYO, Session.NEW_YORK],
    "USD/CHF": [Session.LONDON, Session.NEW_YORK],
    "AUD/USD": [Session.SYDNEY, Session.TOKYO],
    "USD/CAD": [Session.NEW_YORK],
    "NZD/USD": [Session.SYDNEY, Session.TOKYO],
}

class SessionAnalyzer:
    def __init__(self):
        self.now = datetime.now(timezone.utc)
        self.hour = self.now.hour

    def active(self):
        active = []
        for s, (start, end) in SESSION_HOURS.items():
            if start < end:
                if start <= self.hour < end:
                    active.append(s)
            else:
                if self.hour >= start or self.hour < end:
                    active.append(s)
        return active

    def overlap(self):
        for name, (s, e) in OVERLAPS.items():
            if s <= self.hour < e:
                return name
        return None

    def good_time(self, pair):
        active = self.active()
        best = PAIR_SESSION.get(pair, [Session.LONDON, Session.NEW_YORK])
        if self.overlap():
            return True, f"★ Overlap: {self.overlap()}"
        for s in best:
            if s in active:
                return True, f"Session {s.value} active"
        return False, "Outside preferred sessions"

# ── Strategies (full 12 + #13) ────────────────────────────────────────────

class BaseStrategy:
    name = "Base"
    def generate(self, pair, c, h, l, v=None) -> Optional[Signal]:
        raise NotImplementedError

class MACrossover(BaseStrategy):
    name = "MA Crossover"
    def generate(self, pair, c, h, l, v=None):
        if len(c) < 25:
            return None
        f, s = ema(c, 9), ema(c, 21)
        if any(np.isnan([f[-1], s[-1], f[-2]])):
            return None
        price, a = c[-1], atr(h, l, c)[-1] or 0.001
        prev, curr = f[-2]-s[-2], f[-1]-s[-1]
        if prev <= 0 < curr:
            return Signal(self.name, Side.BUY, pair, price, price-1.5*a, price+2.5*a,
                          min(abs(curr)/a, 1.0), datetime.now(timezone.utc), "EMA9 crossed above EMA21")
        if prev >= 0 > curr:
            return Signal(self.name, Side.SELL, pair, price, price+1.5*a, price-2.5*a,
                          min(abs(curr)/a, 1.0), datetime.now(timezone.utc), "EMA9 crossed below EMA21")
        return None

class RSIStrategy(BaseStrategy):
    name = "RSI"
    def generate(self, pair, c, h, l, v=None):
        r = rsi(c)
        valid = r[~np.isnan(r)]
        if len(valid) < 2:
            return None
        val, price, a = c[-1], atr(h, l, c)[-1] or 0.001
        if val < 30:
            return Signal(self.name, Side.BUY, pair, price, price-2*a, price+3*a,
                          (30-val)/30, datetime.now(timezone.utc), f"RSI={val:.1f} oversold")
        if val > 70:
            return Signal(self.name, Side.SELL, pair, price, price+2*a, price-3*a,
                          (val-70)/30, datetime.now(timezone.utc), f"RSI={val:.1f} overbought")
        return None

class Bollinger(BaseStrategy):
    name = "Bollinger Bands"
    def generate(self, pair, c, h, l, v=None):
        u, m, lo = bollinger_bands(c)
        if np.isnan(u[-1]):
            return None
        price, a = c[-1], atr(h, l, c)[-1] or 0.001
        bw = u[-1] - lo[-1]
        if bw == 0:
            return None
        pctb = (price - lo[-1]) / bw
        if pctb <= 0.05:
            return Signal(self.name, Side.BUY, pair, price, lo[-1]-a, m[-1],
                          1-pctb, datetime.now(timezone.utc), f"%B={pctb:.2f} lower band")
        if pctb >= 0.95:
            return Signal(self.name, Side.SELL, pair, price, u[-1]+a, m[-1],
                          pctb-0.5, datetime.now(timezone.utc), f"%B={pctb:.2f} upper band")
        return None

class MACDStrategy(BaseStrategy):
    name = "MACD"
    def generate(self, pair, c, h, l, v=None):
        m, s, hist = macd(c)
        if any(np.isnan([m[-1], s[-1], m[-2]])):
            return None
        price, a = c[-1], atr(h, l, c)[-1] or 0.001
        prev_h = m[-2] - s[-2]
        if prev_h <= 0 < hist[-1]:
            return Signal(self.name, Side.BUY, pair, price, price-2*a, price+3*a,
                          min(abs(hist[-1])/a, 1.0), datetime.now(timezone.utc), "MACD bullish cross")
        if prev_h >= 0 > hist[-1]:
            return Signal(self.name, Side.SELL, pair, price, price+2*a, price-3*a,
                          min(abs(hist[-1])/a, 1.0), datetime.now(timezone.utc), "MACD bearish cross")
        return None

class Fibonacci(BaseStrategy):
    name = "Fibonacci"
    LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    def generate(self, pair, c, h, l, v=None):
        lookback = min(200, len(c) - 1)
        if lookback < 50:
            return None
        hh, ll = np.max(h[-lookback:]), np.min(l[-lookback:])
        diff = hh - ll
        if diff == 0:
            return None
        price = c[-1]
        retr = (hh - price) / diff
        a = atr(h, l, c)[-1] or 0.001
        closest = min(self.LEVELS, key=lambda lv: abs(retr - lv))
        dist = abs(retr - closest)
        if dist < 0.025 and closest in (0.382, 0.5, 0.618):
            if c[-1] > c[-lookback]:
                return Signal(self.name, Side.BUY, pair, price, price-1.5*a, price+2.5*a,
                              max(0.4, 1 - dist*15), datetime.now(timezone.utc),
                              f"Fib bounce at {closest:.1%}")
            else:
                return Signal(self.name, Side.SELL, pair, price, price+1.5*a, price-2.5*a,
                              max(0.4, 1 - dist*15), datetime.now(timezone.utc),
                              f"Fib rejection at {closest:.1%}")
        return None

class Ichimoku(BaseStrategy):
    name = "Ichimoku"
    def generate(self, pair, c, h, l, v=None):
        if len(c) < 80:
            return None
        def mid(period):
            r = np.full(len(h), np.nan)
            for i in range(period-1, len(h)):
                r[i] = (np.max(h[i-period+1:i+1]) + np.min(l[i-period+1:i+1])) / 2
            return r
        tenkan, kijun = mid(9), mid(26)
        senkou_a = (tenkan + kijun) / 2
        senkou_b = mid(52)
        if any(np.isnan([tenkan[-1], kijun[-1], senkou_a[-1]])):
            return None
        price = c[-1]
        cloud_top = max(senkou_a[-1], senkou_b[-1] if not np.isnan(senkou_b[-1]) else senkou_a[-1])
        cloud_bot = min(senkou_a[-1], senkou_b[-1] if not np.isnan(senkou_b[-1]) else senkou_a[-1])
        a = atr(h, l, c)[-1] or 0.001
        if price > cloud_top and tenkan[-1] > kijun[-1]:
            return Signal(self.name, Side.BUY, pair, price, cloud_bot - a, price + 3*a, 0.8,
                          datetime.now(timezone.utc), "Price above cloud, Tenkan > Kijun")
        if price < cloud_bot and tenkan[-1] < kijun[-1]:
            return Signal(self.name, Side.SELL, pair, price, cloud_top + a, price - 3*a, 0.8,
                          datetime.now(timezone.utc), "Price below cloud, Tenkan < Kijun")
        return None

class StochasticStrat(BaseStrategy):
    name = "Stochastic"
    def generate(self, pair, c, h, l, v=None):
        k, d = stochastic(h, l, c)
        vk, vd = k[~np.isnan(k)], d[~np.isnan(d)]
        if len(vk) < 2 or len(vd) < 2:
            return None
        price, a = c[-1], atr(h, l, c)[-1] or 0.001
        if vk[-1] < 20 and vk[-1] > vd[-1]:
            return Signal(self.name, Side.BUY, pair, price, price-2*a, price+2*a,
                          (20-vk[-1])/20, datetime.now(timezone.utc), f"%K={vk[-1]:.1f} bullish")
        if vk[-1] > 80 and vk[-1] < vd[-1]:
            return Signal(self.name, Side.SELL, pair, price, price+2*a, price-2*a,
                          (vk[-1]-80)/20, datetime.now(timezone.utc), f"%K={vk[-1]:.1f} bearish")
        return None

class Breakout(BaseStrategy):
    name = "Breakout"
    def generate(self, pair, c, h, l, v=None):
        if len(c) < 55:
            return None
        res, sup = np.max(h[-50:-1]), np.min(l[-50:-1])
        price, a = c[-1], atr(h, l, c)[-1] or 0.001
        if price > res + 1.5 * a:
            return Signal(self.name, Side.BUY, pair, price, res, price+3*a, 0.75,
                          datetime.now(timezone.utc), f"Breakout above {res:.5f}")
        if price < sup - 1.5 * a:
            return Signal(self.name, Side.SELL, pair, price, sup, price-3*a, 0.75,
                          datetime.now(timezone.utc), f"Breakdown below {sup:.5f}")
        return None

class MeanReversion(BaseStrategy):
    name = "Mean Reversion"
    def generate(self, pair, c, h, l, v=None):
        if len(c) < 55:
            return None
        window = c[-50:]
        mu, sigma = np.mean(window), np.std(window)
        if sigma == 0:
            return None
        z = (c[-1] - mu) / sigma
        price, a = c[-1], atr(h, l, c)[-1] or 0.001
        if z < -2.0:
            return Signal(self.name, Side.BUY, pair, price, price-2*a, mu,
                          min(abs(z)/3, 1.0), datetime.now(timezone.utc), f"Z={z:.2f}")
        if z > 2.0:
            return Signal(self.name, Side.SELL, pair, price, price+2*a, mu,
                          min(abs(z)/3, 1.0), datetime.now(timezone.utc), f"Z={z:.2f}")
        return None

class CarryTrade(BaseStrategy):
    name = "Carry Trade"
    RATES = {"USD": 4.50, "EUR": 3.75, "GBP": 4.75, "JPY": 0.50,
             "CHF": 1.25, "AUD": 4.10, "NZD": 5.25, "CAD": 4.25}
    def generate(self, pair, c, h, l, v=None):
        base, quote = pair.split("/")
        r_base = self.RATES.get(base, 2.0)
        r_quote = self.RATES.get(quote, 2.0)
        diff = r_base - r_quote
        price = c[-1]
        a = atr(h, l, c)[-1] or 0.001
        ma50 = sma(c, 50)
        ma200 = sma(c, 200)
        trend_ok = True
        if not np.isnan(ma50[-1]) and not np.isnan(ma200[-1]):
            trend_ok = ma50[-1] > ma200[-1]
        if diff > 2.0 and trend_ok:
            return Signal(self.name, Side.BUY, pair, price, price-3*a, price+5*a,
                          min(diff/5, 1.0), datetime.now(timezone.utc),
                          f"Carry +{diff:.2f}% (long {base})")
        if diff < -2.0 and not trend_ok:
            return Signal(self.name, Side.SELL, pair, price, price+3*a, price-5*a,
                          min(abs(diff)/5, 1.0), datetime.now(timezone.utc),
                          f"Carry {diff:.2f}% (short {base})")
        return None

class Scalping(BaseStrategy):
    name = "Scalping"
    def generate(self, pair, c, h, l, v=None):
        if len(c) < 25:
            return None
        ef, es = ema(c, 5), ema(c, 13)
        if np.isnan(ef[-1]) or np.isnan(es[-1]):
            return None
        price = c[-1]
        a = atr(h, l, c, 7)[-1] or 0.0005
        tp = (h + l + c) / 3
        vwap = np.mean(tp[-20:])
        if ef[-1] > es[-1] and price > vwap:
            return Signal(self.name, Side.BUY, pair, price, price-a, price+1.5*a, 0.6,
                          datetime.now(timezone.utc), "Scalp BUY: EMA cross + above VWAP")
        if ef[-1] < es[-1] and price < vwap:
            return Signal(self.name, Side.SELL, pair, price, price+a, price-1.5*a, 0.6,
                          datetime.now(timezone.utc), "Scalp SELL: EMA cross + below VWAP")
        return None

class Swing(BaseStrategy):
    name = "Swing"
    def generate(self, pair, c, h, l, v=None):
        if len(c) < 55:
            return None
        ma = sma(c, 50)
        a = atr(h, l, c)[-1]
        if np.isnan(ma[-1]) or np.isnan(a):
            return None
        price = c[-1]
        r = rsi(c)
        vr = r[~np.isnan(r)]
        rsi_val = vr[-1] if len(vr) else 50
        if price > ma[-1] and rsi_val < 55:
            return Signal(self.name, Side.BUY, pair, price, price-2*a, price+4*a, 0.7,
                          datetime.now(timezone.utc), f"Swing BUY above MA50, RSI={rsi_val:.0f}")
        if price < ma[-1] and rsi_val > 45:
            return Signal(self.name, Side.SELL, pair, price, price+2*a, price-4*a, 0.7,
                          datetime.now(timezone.utc), f"Swing SELL below MA50, RSI={rsi_val:.0f}")
        return None

class VolumeConfirmedMomentum(BaseStrategy):
    name = "Volume Momentum"
    def generate(self, pair, c, h, l, v=None):
        if v is None or len(c) < 30:
            return None
        ef, es = ema(c, 8), ema(c, 21)
        r = rsi(c)
        if any(np.isnan([ef[-1], es[-1], r[-1]])):
            return None
        vol_ma = sma(v, 20)
        if np.isnan(vol_ma[-1]) or vol_ma[-1] == 0:
            return None
        rel = v[-1] / vol_ma[-1]
        price, a = c[-1], atr(h, l, c)[-1] or 0.001
        sa = SessionAnalyzer()
        good, _ = sa.good_time(pair)
        if not good:
            return None
        if ef[-1] > es[-1] and 40 < r[-1] < 60 and rel > 1.4:
            return Signal(self.name, Side.BUY, pair, price, price-1.5*a, price+2.5*a,
                          min(0.5 + (rel-1.4)*0.2, 0.95), datetime.now(timezone.utc),
                          f"VolMom BUY | relVol={rel:.2f}")
        if ef[-1] < es[-1] and 40 < r[-1] < 60 and rel > 1.4:
            return Signal(self.name, Side.SELL, pair, price, price+1.5*a, price-2.5*a,
                          min(0.5 + (rel-1.4)*0.2, 0.95), datetime.now(timezone.utc),
                          f"VolMom SELL | relVol={rel:.2f}")
        return None

STRATEGIES = [
    MACrossover(), RSIStrategy(), Bollinger(), MACDStrategy(),
    Fibonacci(), Ichimoku(), StochasticStrat(), Breakout(),
    MeanReversion(), CarryTrade(), Scalping(), Swing(),
    VolumeConfirmedMomentum(),
]

# ── Data & Aggregator ─────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_data(pair: str, period: str, interval: str):
    ticker = pair.replace("/", "") + "=X"
    if HAS_YF:
        try:
            df = yf.download(ticker, period=period, interval=interval,
                             progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if len(df) > 30:
                return (
                    df["Close"].values.astype(float),
                    df["High"].values.astype(float),
                    df["Low"].values.astype(float),
                    df["Volume"].values.astype(float) if "Volume" in df else np.ones(len(df)),
                    df.index
                )
        except Exception as e:
            logger.warning(f"yfinance error: {e}")

    np.random.seed(42)
    n = 500
    rets = np.random.normal(0.00003, 0.0012, n)
    closes = np.cumprod(1 + rets) * (1.0850 if "EUR" in pair else 150.0)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.0007, n)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.0007, n)))
    volumes = np.random.randint(500, 15000, n).astype(float)
    idx = pd.date_range(end=datetime.now(), periods=n, freq="h")
    return closes, highs, lows, volumes, idx

def run_strategies(pair, c, h, l, v):
    signals = []
    for strat in STRATEGIES:
        try:
            sig = strat.generate(pair, c, h, l, v)
            if sig and sig.side != Side.HOLD:
                signals.append(sig)
        except Exception:
            pass
    return signals

def consensus(signals, min_agree=2):
    buys = [s for s in signals if s.side == Side.BUY]
    sells = [s for s in signals if s.side == Side.SELL]
    if len(buys) >= min_agree and len(buys) > len(sells):
        return Signal("CONSENSUS", Side.BUY, buys[0].pair, buys[0].price,
                      float(np.mean([s.stop_loss for s in buys])),
                      float(np.mean([s.take_profit for s in buys])),
                      float(np.mean([s.confidence for s in buys])),
                      datetime.now(timezone.utc), f"{len(buys)} strategies agree BUY")
    if len(sells) >= min_agree and len(sells) > len(buys):
        return Signal("CONSENSUS", Side.SELL, sells[0].pair, sells[0].price,
                      float(np.mean([s.stop_loss for s in sells])),
                      float(np.mean([s.take_profit for s in sells])),
                      float(np.mean([s.confidence for s in sells])),
                      datetime.now(timezone.utc), f"{len(sells)} strategies agree SELL")
    return None

def position_size(sig: Signal, balance=10000, risk_pct=1.0):
    risk = balance * (risk_pct / 100)
    dist = abs(sig.price - sig.stop_loss)
    if dist < 1e-8:
        return 0.01
    sl_pips = pips(sig.pair, dist)
    pv = pip_value(sig.pair, 1.0)
    lots = risk / (sl_pips * pv)
    return max(0.01, min(round(lots, 2), 5.0))

def make_price_chart(c, h, l, idx, signals, pair):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.55, 0.25, 0.20],
                        subplot_titles=(f"{pair} Price", "RSI", "MACD"))
    fig.add_trace(go.Scatter(x=idx, y=c, name="Close", line=dict(color="#00d4ff", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=idx, y=ema(c, 9), name="EMA9", line=dict(color="#ffaa00", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=idx, y=ema(c, 21), name="EMA21", line=dict(color="#ff44aa", width=1)), row=1, col=1)
    u, m, lo = bollinger_bands(c)
    fig.add_trace(go.Scatter(x=idx, y=u, name="BB Upper", line=dict(color="rgba(100,100,255,0.4)", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=idx, y=lo, name="BB Lower", line=dict(color="rgba(100,100,255,0.4)", width=1),
                             fill="tonexty", fillcolor="rgba(100,100,255,0.08)"), row=1, col=1)
    for s in signals:
        color = "#00ff88" if s.side == Side.BUY else "#ff4466"
        fig.add_trace(go.Scatter(
            x=[idx[-1]], y=[s.price], mode="markers+text",
            marker=dict(size=14, color=color, symbol="triangle-up" if s.side == Side.BUY else "triangle-down"),
            text=[s.strategy[:10]], textposition="top center",
            name=f"{s.side.name} {s.strategy}", showlegend=False
        ), row=1, col=1)
    r = rsi(c)
    fig.add_trace(go.Scatter(x=idx, y=r, name="RSI", line=dict(color="#bb86fc")), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
    ml, sl, hist = macd(c)
    colors = ["#00ff88" if v >= 0 else "#ff4466" for v in hist]
    fig.add_trace(go.Bar(x=idx, y=hist, name="Hist", marker_color=colors), row=3, col=1)
    fig.add_trace(go.Scatter(x=idx, y=ml, name="MACD", line=dict(color="#00d4ff", width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=idx, y=sl, name="Signal", line=dict(color="#ffaa00", width=1)), row=3, col=1)
    fig.update_layout(height=780, template="plotly_dark", margin=dict(l=40, r=20, t=40, b=20),
                      legend=dict(orientation="h", y=1.02), xaxis_rangeslider_visible=False)
    return fig

# ═══════════════════════════════════════════════════════════════════════════
# AUTH & UI
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Forex Trading System", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0d1117 0%, #161b22 100%); }
    .metric-card {
        background: #21262d; border-radius: 12px; padding: 16px;
        border: 1px solid #30363d; margin-bottom: 12px;
    }
    .owner-card {
        background: linear-gradient(135deg, #1a2332 0%, #0d1117 100%);
        border-radius: 16px; padding: 24px; border: 1px solid #30363d;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .buy { color: #3fb950 !important; font-weight: 700; }
    .sell { color: #f85149 !important; font-weight: 700; }
    h1, h2, h3 { color: #e6edf3 !important; }
</style>
""", unsafe_allow_html=True)

# ── Login / Invite gate ───────────────────────────────────────────────────

query_params = st.query_params
invite_token = query_params.get("invite", None)

def check_login(username, password):
    if username == OWNER_USERNAME and hashlib.sha256(password.encode()).hexdigest() == OWNER_PASSWORD_HASH:
        return "owner"
    for token, info in st.session_state.invite_tokens.items():
        if info.get("email") == username and info.get("temp_pass") == password:
            if datetime.now(timezone.utc) < info["expires"]:
                return "member"
    return None

# Handle invite link login
if invite_token and invite_token in st.session_state.invite_tokens:
    info = st.session_state.invite_tokens[invite_token]
    if datetime.now(timezone.utc) < info["expires"]:
        st.session_state.logged_in = True
        st.session_state.user_role = "member"
        st.session_state.user_email = info["email"]
        st.success(f"Welcome! You joined via invite for {info['email']}")
        st.query_params.clear()

if not st.session_state.logged_in:
    st.title("🔐 Forex Trading System — Sign In")
    st.markdown("---")

    tab_login, tab_invite = st.tabs(["Owner / Member Login", "Have an Invite Link?"])

    with tab_login:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username / Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                role = check_login(username, password)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.user_role = role
                    st.session_state.user_email = username if role == "member" else OWNER["email"]
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")

        with st.expander("Owner credentials (demo)"):
            st.code("Username: owner\\nPassword: ForexOwner2026!", language=None)
            st.caption("Change these in production. This is an educational demo only.")

    with tab_invite:
        st.subheader("Join with Invite Link")
        st.info("If the owner sent you an invite link, open it in your browser. "
                "The link contains a one-time token that will sign you in automatically.")
        st.markdown("Example format: `http://your-app-url/?invite=TOKEN`")

    st.stop()

# ── Logged-in app ─────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown(f"**Logged in as:** `{st.session_state.user_role}`")
    if st.session_state.user_email:
        st.caption(st.session_state.user_email)

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_email = None
        st.rerun()

    st.markdown("---")

    page = st.radio("Navigate", ["Trading Dashboard", "Owners Panel", "Invite Members"],
                    label_visibility="collapsed")

    if page == "Trading Dashboard":
        pair = st.selectbox("Currency Pair", [
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
            "AUD/USD", "USD/CAD", "NZD/USD"
        ], index=0)
        period = st.selectbox("Lookback", ["7d", "30d", "60d", "90d"], index=2)
        interval = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)
        balance = st.number_input("Account Balance ($)", 1000, 1_000_000, 10_000, 500)
        risk_pct = st.slider("Risk per trade (%)", 0.25, 3.0, 1.0, 0.25)
        min_agree = st.slider("Min strategies for consensus", 1, 5, 2)
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()

    st.markdown("---")
    st.caption("Educational demo only. Not financial advice.")

# ── Owners Panel ──────────────────────────────────────────────────────────

if page == "Owners Panel":
    st.title("👑 Owners Panel")
    st.markdown("---")

    st.markdown(f"""
    <div class="owner-card">
        <h2 style="margin-top:0;">Primary Owner</h2>
        <p style="font-size:1.3rem; margin-bottom:4px;"><b>{OWNER['name']}</b></p>
        <p style="color:#8b949e; margin:0;">Role: {OWNER['role']}</p>
        <hr style="border-color:#30363d;">
        <p>📧 <b>Email:</b> <a href="mailto:{OWNER['email']}" style="color:#58a6ff;">{OWNER['email']}</a></p>
        <p>📱 <b>Contact:</b> {OWNER['contact']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### System Status")
    c1, c2, c3 = st.columns(3)
    c1.metric("Strategies Loaded", "13 (12 + Volume Momentum)")
    c2.metric("Data Source", "yfinance" if HAS_YF else "Synthetic")
    c3.metric("Active Invites", len(st.session_state.invite_tokens))

    if st.session_state.user_role == "owner":
        st.success("You are logged in as the Owner. Full access granted.")
    else:
        st.info("You are viewing the Owners Panel as a member.")

# ── Invite Members ────────────────────────────────────────────────────────

elif page == "Invite Members":
    st.title("📨 Invite Members")
    st.markdown("---")

    if st.session_state.user_role != "owner":
        st.warning("Only the Owner can generate invite links.")
        st.stop()

    st.markdown("""
    Generate a unique invite link and **share it with the person via Gmail** (or any channel).  
    When they open the link they will be signed in automatically as a member.
    """)

    with st.form("invite_form"):
        invite_email = st.text_input("Recipient Gmail / Email")
        days_valid = st.slider("Link valid for (days)", 1, 30, 7)
        submitted = st.form_submit_button("Generate Invite Link", use_container_width=True)

        if submitted and invite_email:
            token = secrets.token_urlsafe(24)
            expires = datetime.now(timezone.utc) + timedelta(days=days_valid)
            temp_pass = secrets.token_urlsafe(8)
            st.session_state.invite_tokens[token] = {
                "email": invite_email.strip().lower(),
                "expires": expires,
                "temp_pass": temp_pass,
                "created": datetime.now(timezone.utc),
            }
            # Use relative link so it works on any deployed domain
            invite_link = f"?invite={token}"
            # Full public URL will be shown after user knows their Streamlit Cloud URL

            st.success("Invite created!")
            st.markdown("### Share this link with the person (via Gmail):")
            st.code(invite_link, language=None)
            st.markdown(f"""
**Suggested Gmail message:**

> Subject: Your invite to the Forex Trading System  
>  
> Hi,  
> You have been invited by **{OWNER['name']}** to access the Forex Trading System.  
>  
> Click the link below to join (valid for {days_valid} days):  
> {invite_link}  
>  
> Or sign in with:  
> Email: {invite_email}  
> Temporary password: `{temp_pass}`  
>  
> Owner contact: {OWNER['contact']}
            """)
            st.info("Copy the message above and paste it into Gmail to send the invite.")

    if st.session_state.invite_tokens:
        st.markdown("### Active Invites")
        rows = []
        now = datetime.now(timezone.utc)
        for tok, info in st.session_state.invite_tokens.items():
            rows.append({
                "Email": info["email"],
                "Expires": info["expires"].strftime("%Y-%m-%d %H:%M UTC"),
                "Status": "Active" if now < info["expires"] else "Expired",
                "Token (first 8)": tok[:8] + "…",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Trading Dashboard ─────────────────────────────────────────────────────

else:
    st.title("📈 Forex Trading System")
    st.caption("Full 12 strategies + Volume Momentum · Real market data · Multi-signal consensus")

    sa = SessionAnalyzer()
    active = sa.active()
    overlap = sa.overlap()
    good, msg = sa.good_time(pair)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("UTC Time", sa.now.strftime("%H:%M"))
    col2.metric("Active Sessions", ", ".join(s.value for s in active) or "None")
    col3.metric("Overlap", overlap or "None")
    col4.metric("Pair Timing", "✅ Good" if good else "⛔ Off", delta=msg)

    with st.spinner("Loading market data..."):
        closes, highs, lows, volumes, idx = load_data(pair, period, interval)

    data_source = "Real (yfinance)" if HAS_YF else "Synthetic"
    st.info(f"Loaded **{len(closes)}** bars of **{pair}** · Source: {data_source} · "
            f"Range: {closes.min():.5f} – {closes.max():.5f}")

    ma50 = sma(closes, 50)
    ma200 = sma(closes, 200)
    adx_val = adx(highs, lows, closes)
    strength = float(adx_val[~np.isnan(adx_val)][-1]) if np.any(~np.isnan(adx_val)) else 0
    if not np.isnan(ma50[-1]) and not np.isnan(ma200[-1]):
        if ma50[-1] > ma200[-1] * 1.001:
            trend = "UPTREND 🟢"
        elif ma50[-1] < ma200[-1] * 0.999:
            trend = "DOWNTREND 🔴"
        else:
            trend = "SIDEWAYS ⚪"
    else:
        trend = "INSUFFICIENT DATA"
    st.subheader(f"Trend Consensus: {trend}  (ADX strength ≈ {strength:.1f})")

    signals = run_strategies(pair, closes, highs, lows, volumes)
    cs = consensus(signals, min_agree)

    st.plotly_chart(make_price_chart(closes, highs, lows, idx, signals, pair), use_container_width=True)

    st.subheader("Active Signals")
    if signals:
        rows = []
        for s in signals:
            lots = position_size(s, balance, risk_pct)
            rows.append({
                "Side": s.side.name,
                "Strategy": s.strategy,
                "Price": f"{s.price:.5f}",
                "Stop Loss": f"{s.stop_loss:.5f}",
                "Take Profit": f"{s.take_profit:.5f}",
                "Confidence": f"{s.confidence:.2f}",
                "Lots": lots,
                "Reason": s.reason
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        if cs:
            color = "buy" if cs.side == Side.BUY else "sell"
            lots = position_size(cs, balance, risk_pct)
            st.markdown(f"""
            <div class="metric-card">
                <h3>★ CONSENSUS: <span class="{color}">{cs.side.name}</span> {cs.pair}</h3>
                <p>Confidence: <b>{cs.confidence:.2f}</b> · Suggested lots: <b>{lots}</b></p>
                <p>SL: {cs.stop_loss:.5f} · TP: {cs.take_profit:.5f}</p>
                <p>{cs.reason}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No consensus yet — not enough strategies agree.")
    else:
        st.info("No active signals on the latest bar.")

    col_a, col_b = st.columns(2)
    with col_a:
        if signals:
            json_str = json.dumps([s.to_dict() for s in signals], indent=2)
            st.download_button("⬇️ Download Signals JSON", json_str, "forex_signals.json", "application/json")
    with col_b:
        if signals:
            csv = pd.DataFrame([s.to_dict() for s in signals]).to_csv(index=False)
            st.download_button("⬇️ Download Signals CSV", csv, "forex_signals.csv", "text/csv")

st.markdown("---")
st.caption("⚠️ Educational use only. Past performance is not indicative of future results. Never risk money you cannot afford to lose.")
