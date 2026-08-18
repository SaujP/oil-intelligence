"""
src/charts.py
=============
All chart functions for the Oil Intelligence project.
Each function returns a matplotlib Figure — works in notebooks and Streamlit.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec


# ── STYLE DEFAULTS ────────────────────────────────────────────────────────────
BLUE    = "#2563eb"
RED     = "#dc2626"
GREEN   = "#16a34a"
GREY    = "#aab4c8"
DARK    = "#1e3a5f"
AMBER   = "#f59e0b"

plt.rcParams.update({
    "font.family":   "sans-serif",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})


def _fmt_xaxis(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))


# ── CHART 1: Brent Price + Inventory Signal ───────────────────────────────────

def chart_inventory_signal(df: pd.DataFrame) -> plt.Figure:
    """
    Dual-axis chart: Brent price (line) + 4-week inventory change (bars).
    Bars coloured green (bullish draw) / red (bearish build).
    """
    df = df.dropna(subset=["brent_price", "inventory_ma4"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("US Crude Inventory Signal vs Brent Price\n"
                 "Inventory draws (green) → bullish for price | builds (red) → bearish",
                 fontsize=13, fontweight="bold")

    # Top: Brent price
    ax1.plot(df["period"], df["brent_price"], color=RED, linewidth=2, label="Brent ($/bbl)")
    if "brent_ma4" in df.columns:
        ax1.plot(df["period"], df["brent_ma4"], color=DARK, linewidth=1,
                 linestyle="--", alpha=0.7, label="4-week MA")
    ax1.set_ylabel("Brent Price ($/bbl)", fontsize=11)
    ax1.legend(fontsize=9)
    ax1.grid(True)

    # Latest annotation
    last = df.iloc[-1]
    ax1.annotate(f"  ${last['brent_price']:.1f}",
                 xy=(last["period"], last["brent_price"]),
                 fontsize=10, color=RED, fontweight="bold", va="center")

    # Bottom: Inventory 4-week MA as bars
    colors = [GREEN if v < 0 else RED for v in df["inventory_ma4"]]
    ax2.bar(df["period"], df["inventory_ma4"], color=colors, alpha=0.7, width=5)
    ax2.axhline(0, linestyle="-", color="black", linewidth=0.8)
    ax2.set_ylabel("4-Week Avg Inventory\nChange (kb)", fontsize=10)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.grid(True, axis="y")
    _fmt_xaxis(ax2)

    plt.tight_layout()
    return fig


# ── CHART 2: Crack Spread ─────────────────────────────────────────────────────

def chart_crack_spread(df: pd.DataFrame) -> plt.Figure:
    """
    3-2-1 crack spread vs WTI crude price.
    """
    df = df.dropna(subset=["crack_321", "wti"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("3-2-1 Crack Spread vs WTI Crude\n"
                 "Refinery margin: profit from turning crude into fuel",
                 fontsize=13, fontweight="bold")

    ax1.plot(df["period"], df["crack_321"], color=GREY, linewidth=0.8, alpha=0.6,
             label="Weekly crack spread")
    ax1.plot(df["period"], df["crack_ma4"], color=BLUE, linewidth=2,
             label="4-week moving average")
    ax1.axhline(0,  linestyle="--", color="grey",  linewidth=0.8)
    ax1.axhline(15, linestyle=":",  color=GREEN,   linewidth=1.2,
                label="$15/bbl — typical breakeven")
    ax1.fill_between(df["period"], df["crack_ma4"], 0,
                     where=df["crack_ma4"] > 0, alpha=0.15, color=GREEN)
    ax1.fill_between(df["period"], df["crack_ma4"], 0,
                     where=df["crack_ma4"] < 0, alpha=0.15, color=RED)

    last = df.dropna(subset=["crack_ma4"]).iloc[-1]
    ax1.annotate(f"  ${last['crack_ma4']:.1f}/bbl",
                 xy=(last["period"], last["crack_ma4"]),
                 fontsize=10, color=BLUE, fontweight="bold", va="center")

    ax1.set_ylabel("Crack Spread ($/bbl)", fontsize=11)
    ax1.legend(fontsize=9)
    ax1.grid(True)

    ax2.plot(df["period"], df["wti"], color=RED, linewidth=1.5, label="WTI ($/bbl)")
    ax2.set_ylabel("WTI ($/bbl)", fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(True)
    _fmt_xaxis(ax2)

    plt.tight_layout()
    return fig


# ── CHART 3: WTI-Brent Spread ─────────────────────────────────────────────────

def chart_wti_brent_spread(df: pd.DataFrame) -> plt.Figure:
    """
    Brent vs WTI prices + spread over time.
    The spread reflects geopolitical risk premium and US export dynamics.
    """
    df = df.dropna(subset=["brent_price", "wti"]).copy()
    df["spread"]    = df["brent_price"] - df["wti"]
    df["spread_ma4"] = df["spread"].rolling(4).mean()

    # Key events to annotate
    events = [
        ("2014-11-28", "OPEC no-cut\ndecision",   +3),
        ("2016-01-16", "Iran sanctions\nlifted",   -5),
        ("2020-03-09", "Saudi-Russia\nprice war",  +6),
        ("2022-02-24", "Russia invades\nUkraine",  +5),
    ]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("WTI vs Brent: Geopolitical Risk Premium & US Export Dynamics",
                 fontsize=13, fontweight="bold")

    ax1.plot(df["period"], df["brent_price"], color=DARK,  linewidth=1.8, label="Brent")
    ax1.plot(df["period"], df["wti"],         color=RED,   linewidth=1.5, label="WTI", alpha=0.85)
    ax1.set_ylabel("Price ($/bbl)", fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(True)

    for date_str, label, y_off in events:
        dt = pd.Timestamp(date_str)
        if dt < df["period"].min() or dt > df["period"].max():
            continue
        closest = df[df["period"] >= dt].iloc[0]
        ax1.axvline(dt, linestyle=":", color="grey", linewidth=0.9, alpha=0.7)
        ax1.annotate(label, xy=(dt, closest["brent_price"] + y_off),
                     fontsize=7.5, color="#374151", ha="center",
                     bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="grey", alpha=0.8))

    ax2.plot(df["period"], df["spread"],     color=GREY, linewidth=0.8, alpha=0.7)
    ax2.plot(df["period"], df["spread_ma4"], color=BLUE, linewidth=2, label="4-week MA")
    ax2.axhline(0, linestyle="--", color="black", linewidth=1)
    ax2.fill_between(df["period"], df["spread_ma4"], 0,
                     where=df["spread_ma4"] > 0, alpha=0.2, color=DARK,
                     label="Brent premium")
    ax2.fill_between(df["period"], df["spread_ma4"], 0,
                     where=df["spread_ma4"] < 0, alpha=0.2, color=RED,
                     label="WTI premium")
    ax2.set_ylabel("Brent − WTI ($/bbl)", fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(True)
    _fmt_xaxis(ax2)

    plt.tight_layout()
    return fig


# ── CHART 4: Signal Backtest ──────────────────────────────────────────────────

def chart_backtest(df: pd.DataFrame, backtest_results: dict) -> plt.Figure:
    """
    Two panels:
    Left  — forward return distribution by signal
    Right — cumulative PnL: signal strategy vs buy-and-hold Brent
    """
    bt   = backtest_results["df_backtest"].copy()
    hw   = backtest_results["horizon_weeks"]
    col  = f"fwd_{hw}w_return"

    bull = bt[bt["inventory_signal_num"] == 1][col]
    bear = bt[bt["inventory_signal_num"] == -1][col]

    # Cumulative PnL
    bt["weekly_ret"]   = bt["brent_price"].pct_change(1)
    bt["strat_ret"]    = bt["inventory_signal_num"].shift(1) * bt["weekly_ret"]
    bt["cum_strategy"] = (1 + bt["strat_ret"].fillna(0)).cumprod()
    bt["cum_brent"]    = (1 + bt["weekly_ret"].fillna(0)).cumprod()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(f"Inventory Signal Backtest — {hw}-Week Forward Return",
                 fontsize=13, fontweight="bold")

    # Left: Distribution
    ax1.hist(bear, bins=35, alpha=0.6, color=RED,  label=f"Bearish (n={len(bear)})")
    ax1.hist(bull, bins=35, alpha=0.6, color=BLUE, label=f"Bullish (n={len(bull)})")
    ax1.axvline(0,            linestyle="--", color="black", linewidth=1)
    ax1.axvline(bull.mean(),  linestyle="-",  color=BLUE,   linewidth=2,
                label=f"Bullish avg: {bull.mean():+.1f}%")
    ax1.axvline(bear.mean(),  linestyle="-",  color=RED,    linewidth=2,
                label=f"Bearish avg: {bear.mean():+.1f}%")
    ax1.set_xlabel(f"{hw}-Week Forward Return (%)", fontsize=10)
    ax1.set_ylabel("Frequency", fontsize=10)
    ax1.set_title("Return Distribution by Signal", fontweight="bold")
    ax1.legend(fontsize=8)
    ax1.grid(True)

    # Right: Cumulative PnL
    ax2.plot(bt["period"], bt["cum_strategy"], color=BLUE,  linewidth=2,
             label="Inventory Signal Strategy")
    ax2.plot(bt["period"], bt["cum_brent"],    color=RED,   linewidth=1.5,
             linestyle="--", label="Buy & Hold Brent")
    ax2.axhline(1, linestyle=":", color="grey", linewidth=0.8)
    ax2.fill_between(bt["period"], bt["cum_strategy"], bt["cum_brent"],
                     where=bt["cum_strategy"] >= bt["cum_brent"],
                     alpha=0.15, color=BLUE, label="Outperforming")
    ax2.fill_between(bt["period"], bt["cum_strategy"], bt["cum_brent"],
                     where=bt["cum_strategy"] < bt["cum_brent"],
                     alpha=0.15, color=RED)
    ax2.set_ylabel("Cumulative Return (1 = start)", fontsize=10)
    ax2.set_xlabel("Date", fontsize=10)
    ax2.set_title("Cumulative PnL: Strategy vs Buy & Hold", fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.grid(True)
    _fmt_xaxis(ax2)

    plt.tight_layout()
    return fig


# ── CHART 5: Refinery Inputs ──────────────────────────────────────────────────

def chart_refinery_inputs(df: pd.DataFrame) -> plt.Figure:
    """
    Refinery crude inputs (demand-side indicator) vs Brent price.
    High inputs = refineries are buying crude aggressively = bullish demand signal.
    """
    df = df.dropna(subset=["refinery_inputs", "brent_price"]).copy()
    df["ref_ma4"] = df["refinery_inputs"].rolling(4).mean()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True,
                                    gridspec_kw={"height_ratios": [1, 2]})
    fig.suptitle("US Refinery Crude Inputs vs Brent Price\n"
                 "Rising inputs = strong demand pull on crude stocks",
                 fontsize=13, fontweight="bold")

    ax1.plot(df["period"], df["refinery_inputs"], color=GREY, linewidth=0.8, alpha=0.6)
    ax1.plot(df["period"], df["ref_ma4"],         color=BLUE, linewidth=2,
             label="4-week MA")
    ax1.axhline(0, linestyle="--", color="grey", linewidth=0.8)
    ax1.set_ylabel("Refinery Inputs\n(kb change)", fontsize=10)
    ax1.legend(fontsize=9)
    ax1.grid(True)

    ax2.plot(df["period"], df["brent_price"], color=RED, linewidth=2, label="Brent ($/bbl)")
    ax2.set_ylabel("Brent Price ($/bbl)", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(True)
    _fmt_xaxis(ax2)

    plt.tight_layout()
    return fig


# ── CHART 6: Market Regime ────────────────────────────────────────────────────

def chart_market_regime(df: pd.DataFrame) -> plt.Figure:
    """
    Colour-coded timeline showing which market regime we are in each week.
    """
    df = df.dropna(subset=["market_regime", "brent_price"]).copy()

    regime_colors = {
        "Demand-driven bull": GREEN,
        "Tightening supply":  BLUE,
        "Supply shock":       AMBER,
        "Demand destruction": RED,
        "Cautious bull":      "#86efac",
        "Cautious bear":      "#fca5a5",
        "Balanced":           GREY,
    }

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8), sharex=True,
                                    gridspec_kw={"height_ratios": [1, 3]})
    fig.suptitle("Oil Market Regime Classification\n"
                 "Based on inventory signal + crack spread signal",
                 fontsize=13, fontweight="bold")

    # Top: regime colour strip
    for regime, color in regime_colors.items():
        mask = df["market_regime"] == regime
        ax1.fill_between(df["period"], 0, 1,
                         where=mask, color=color, alpha=0.8,
                         transform=ax1.get_xaxis_transform(), label=regime)
    ax1.set_yticks([])
    ax1.set_ylabel("Regime", fontsize=9)
    ax1.legend(fontsize=7.5, loc="upper left", ncol=4,
               bbox_to_anchor=(0, 1.3), framealpha=0.9)

    # Bottom: Brent price coloured by regime
    for regime, color in regime_colors.items():
        mask = df["market_regime"] == regime
        sub  = df[mask]
        ax2.scatter(sub["period"], sub["brent_price"],
                    color=color, s=6, alpha=0.7, zorder=3)

    ax2.plot(df["period"], df["brent_price"],
             color="black", linewidth=0.6, alpha=0.3, zorder=2)
    ax2.set_ylabel("Brent Price ($/bbl)", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.grid(True)
    _fmt_xaxis(ax2)

    plt.tight_layout()
    return fig
