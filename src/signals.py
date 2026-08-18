""
src/signals.py
==============
All signal calculations for the Oil Intelligence project.
Import these functions in notebooks and the Streamlit app.
"""

import pandas as pd
import numpy as np


def add_inventory_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds inventory-based supply/demand signals to the master DataFrame

    Columns added:
      inventory_change    - week-on-week change in crude stocks (kb)
      inventory_ma4       - 4-week rolling average of that change
      inventory_signal    - 'Bullish' / 'Bearish' / 'Neutral'
      inventory_signal_num - +1 / -1 / 0 (for backtesting
      inventory_yoy       - year-on-year change (vs same week last year)
    """
    df = df.copy()
    df["inventory_change"] = df["inventory_kb"].diff()
    df["inventory_ma4"]    = df["inventory_change"].rolling(4).mean()
    df["inventory_yoy"]    = df["inventory_kb"] - df["inventory_kb"].shift(52)

    def classify(val):
        if pd.isna(val):
            return "Neutral"
        elif val < -1000:   # drawing > 1 million barrels/week = clearly bullish
            return "Bullish"
        elif val > 1000:    # building > 1 million barrels/week = clearly bearish
            return "Bearish"
        else:
            return "Neutral"

    df["inventory_signal"]     = df["inventory_ma4"].apply(classify)
    df["inventory_signal_num"] = df["inventory_signal"].map(
        {"Bullish": 1, "Neutral": 0, "Bearish": -1}
    )
    return df


def add_crack_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds crack spread signal - proxy for refinery demand strength.

    Columns added:
      crack_signal - 'High' / 'Normal' / 'Low'
    """
    df = df.copy()

    def classify(val):
        if pd.isna(val):
            return "Unknown"
        elif val > 25:
            return "High"
        elif val > 12:
            return "Normal"
        else:
            return "Low"

    df["crack_signal"] = df["crack_ma4"].apply(classify)
    return df


def add_price_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds price momentum signals.

    Columns added:
      brent_ma4       - 4-week Brent moving average
      brent_ma13      - 13-week (quarterly) moving average
      brent_momentum  - 'Uptrend' / 'Downtrend' / 'Flat'
      brent_yoy_pct   - year-on-year % change
      wti_brent_spread - Brent minus WTI ($/bbl)
    """
    df = df.copy()
    df["brent_ma4"]  = df["brent_price"].rolling(4).mean()
    df["brent_ma13"] = df["brent_price"].rolling(13).mean()
    df["brent_yoy_pct"] = (
        (df["brent_price"] - df["brent_price"].shift(52))
        / df["brent_price"].shift(52) * 100
    )

    def momentum(row):
        if pd.isna(row["brent_ma4"]) or pd.isna(row["brent_ma13"]):
            return "Unknown"
        diff = row["brent_ma4"] - row["brent_ma13"]
        if diff > 2:
            return "Uptrend"
        elif diff < -2:
            return "Downtrend"
        else:
            return "Flat"

    df["brent_momentum"] = df.apply(momentum, axis=1)

    if "wti" in df.columns:
        df["wti_brent_spread"] = df["brent_price"] - df["wti"]

    return df


def add_market_regime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classifies the current market regime based on inventory signal + crack spread.

    Regime logic:
      Bullish inventory + High crack   → 'Demand-driven bull'
      Bullish inventory + Normal crack → 'Tightening supply'
      Bearish inventory + Low crack    → 'Demand destruction'
      Bearish inventory + High crack   → 'Supply shock'
      Otherwise                        → 'Balanced'

    Column added: market_regime
    """
    df = df.copy()

    def regime(row):
        inv   = row.get("inventory_signal", "Neutral")
        crack = row.get("crack_signal", "Normal")

        if inv == "Bullish" and crack == "High":
            return "Demand-driven bull"
        elif inv == "Bullish" and crack in ("Normal", "High"):
            return "Tightening supply"
        elif inv == "Bearish" and crack == "Low":
            return "Demand destruction"
        elif inv == "Bearish" and crack == "High":
            return "Supply shock"
        elif inv == "Bullish":
            return "Cautious bull"
        elif inv == "Bearish":
            return "Cautious bear"
        else:
            return "Balanced"

    df["market_regime"] = df.apply(regime, axis=1)
    return df


def backtest_inventory_signal(df: pd.DataFrame, horizon_weeks: int = 4) -> dict:
    """
    Tests whether the inventory signal predicts forward Brent price returns.

    Args:
        df             — master DataFrame with signals applied
        horizon_weeks  — how many weeks forward to measure return

    Returns dict with:
        hit_rate_bullish  — % of bullish signals followed by price rise
        hit_rate_bearish  — % of bearish signals followed by price fall
        avg_return_bullish — average forward return on bullish weeks
        avg_return_bearish — average forward return on bearish weeks
        df_backtest        — full backtest DataFrame
    """
    df = df.copy().dropna(subset=["brent_price", "inventory_signal_num"])

    col = f"fwd_{horizon_weeks}w_return"
    df[col] = df["brent_price"].pct_change(horizon_weeks).shift(-horizon_weeks) * 100

    df_bt = df.dropna(subset=[col])

    bull = df_bt[df_bt["inventory_signal_num"] == 1][col]
    bear = df_bt[df_bt["inventory_signal_num"] == -1][col]

    return {
        "horizon_weeks":      horizon_weeks,
        "hit_rate_bullish":   round((bull > 0).mean() * 100, 1),
        "hit_rate_bearish":   round((bear < 0).mean() * 100, 1),
        "avg_return_bullish": round(bull.mean(), 2),
        "avg_return_bearish": round(bear.mean(), 2),
        "n_bullish":          len(bull),
        "n_bearish":          len(bear),
        "df_backtest":        df_bt,
    }


def current_snapshot(df: pd.DataFrame) -> dict:
    """
    Returns a plain-English summary of the latest week's market state.
    Used in the Streamlit dashboard header.
    """
    latest = df.dropna(subset=["brent_price"]).iloc[-1]

    return {
        "date":            latest["period"].strftime("%d %b %Y"),
        "brent":           round(latest.get("brent_price", 0), 2),
        "wti":             round(latest.get("wti", 0), 2),
        "crack_spread":    round(latest.get("crack_ma4", 0), 2),
        "inventory_kb":    int(latest.get("inventory_kb", 0)),
        "inventory_signal": latest.get("inventory_signal", "Unknown"),
        "crack_signal":    latest.get("crack_signal", "Unknown"),
        "market_regime":   latest.get("market_regime", "Unknown"),
        "brent_momentum":  latest.get("brent_momentum", "Unknown"),
        "wti_brent_spread": round(latest.get("wti_brent_spread", 0), 2),
    }
