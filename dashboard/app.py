"""
dashboard/app.py
================
Oil Market Intelligence Dashboard — Streamlit app.

Run with:
    streamlit run dashboard/app.py

Make sure you're in the OIL_INTELLIGENCE root folder when running.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.data_loader import load_all, load_crack_spread
from src.signals     import (add_inventory_signal, add_crack_signal,
                              add_price_signals, add_market_regime,
                              backtest_inventory_signal, current_snapshot)
from src.charts      import (chart_inventory_signal, chart_crack_spread,
                              chart_wti_brent_spread, chart_backtest,
                              chart_refinery_inputs, chart_market_regime)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Oil Market Intelligence",
    page_icon="🛢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("🛢 Oil Intelligence")
st.sidebar.markdown("*Monitoring supply, storage, demand & pricing*")
st.sidebar.divider()

start_date = st.sidebar.selectbox(
    "Data start year",
    options=["2010", "2014", "2016", "2018", "2020"],
    index=1
)

backtest_horizon = st.sidebar.selectbox(
    "Backtest horizon (weeks)",
    options=[1, 4, 8, 13],
    index=1
)

st.sidebar.divider()
st.sidebar.markdown("""
**Data sources**
- [EIA Weekly Petroleum](https://www.eia.gov/petroleum/)
- [EIA Spot Prices Excel](https://www.eia.gov/dnav/pet/xls/PET_PRI_SPT_S1_W.xls)

**Methodology**
- Inventory signal: 4-week rolling avg change
- Crack spread: 3-2-1 formula (2×RBOB + 1×HO − 3×WTI) / 3
- Market regime: inventory signal × crack signal matrix
""")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)   # cache for 1 hour — re-fetches fresh data each hour
def get_data(start: str) -> pd.DataFrame:
    df = load_all(start=start)
    df = add_inventory_signal(df)
    df = add_crack_signal(df)
    df = add_price_signals(df)
    df = add_market_regime(df)
    return df

with st.spinner("Loading market data from EIA..."):
    df = get_data(start=f"{start_date}-01-01")

snap = current_snapshot(df)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("🛢 Oil Market Intelligence Dashboard")
st.caption(f"Latest data: **{snap['date']}** | Source: US Energy Information Administration (EIA)")

# ── KPI METRICS ROW ───────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Brent Crude", f"${snap['brent']:.2f}", help="Latest weekly Brent spot price ($/bbl)")

with col2:
    st.metric("WTI Crude", f"${snap['wti']:.2f}", help="Latest weekly WTI spot price ($/bbl)")

with col3:
    spread_delta = f"Brent premium: ${snap['wti_brent_spread']:.1f}/bbl"
    st.metric("WTI-Brent Spread", f"${snap['wti_brent_spread']:.2f}", help=spread_delta)

with col4:
    st.metric("Crack Spread (4W MA)", f"${snap['crack_spread']:.1f}/bbl",
              help="3-2-1 crack spread — refinery profit margin")

with col5:
    signal_color = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}.get(snap["inventory_signal"], "⚪")
    st.metric("Inventory Signal", f"{signal_color} {snap['inventory_signal']}")

with col6:
    st.metric("Market Regime", snap["market_regime"])

st.divider()

# ── MARKET COMMENTARY ─────────────────────────────────────────────────────────
regime     = snap["market_regime"]
inv_signal = snap["inventory_signal"]
crack_sig  = snap["crack_signal"]
momentum   = snap["brent_momentum"]

commentary_map = {
    "Demand-driven bull":  f"Crude inventories are drawing and refinery margins are high — classic demand-driven bull market. Brent at ${snap['brent']:.0f}/bbl with {momentum.lower()} momentum.",
    "Tightening supply":   f"Inventory draws signal tightening supply. Crack spreads at {crack_sig.lower()} levels suggest refineries are actively pulling crude. Watch for further price upside.",
    "Supply shock":        f"Bearish inventory builds but high crack spreads point to a supply-side disruption — refineries want crude but supply is constrained. Geopolitical risk premium likely elevated.",
    "Demand destruction":  f"Inventory builds and weak refinery margins signal demand weakness. Downward pressure on Brent likely unless OPEC intervenes.",
    "Cautious bull":       f"Inventory signal is bullish but crack spreads are not confirming — mixed signals. Monitor refinery runs in coming weeks.",
    "Cautious bear":       f"Inventory builds with normal crack spreads — market building supply cushion. Neutral to bearish near-term outlook.",
    "Balanced":            f"Inventory and crack signals are neutral. Brent at ${snap['brent']:.0f}/bbl. Market awaiting a directional catalyst.",
}

commentary = commentary_map.get(regime, "Insufficient data for commentary.")
st.info(f"**Market Commentary ({snap['date']}):** {commentary}")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📦 Inventory Signal",
    "⚗️ Crack Spread",
    "🌍 WTI vs Brent",
    "📊 Backtest",
    "🏭 Refinery Inputs",
    "🎯 Market Regime",
])

with tab1:
    st.subheader("US Crude Inventory vs Brent Price")
    st.markdown("""
    Weekly US crude stocks (EIA) drive the core supply/demand signal.
    **Green bars** = inventory draw (bullish) | **Red bars** = inventory build (bearish).
    The 4-week average smooths seasonal noise.
    """)
    fig = chart_inventory_signal(df)
    st.pyplot(fig)
    plt.close()

    # Show raw numbers
    with st.expander("View latest inventory data"):
        st.dataframe(
            df[["period", "inventory_kb", "inventory_change", "inventory_ma4",
                "inventory_signal"]].tail(20).sort_values("period", ascending=False),
            use_container_width=True
        )

with tab2:
    st.subheader("3-2-1 Crack Spread — Refinery Profit Margin")
    st.markdown("""
    The crack spread measures refinery profitability.
    **Formula:** (2 × RBOB gasoline + 1 × Heating oil − 3 × WTI) ÷ 3.
    Above $15/bbl = refineries profitable and buying crude aggressively.
    """)
    crack_df = load_crack_spread(start=f"{start_date}-01-01")
    fig = chart_crack_spread(crack_df)
    st.pyplot(fig)
    plt.close()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Latest Crack Spread", f"${snap['crack_spread']:.1f}/bbl")
    with col_b:
        st.metric("Signal", snap["crack_signal"])
    with col_c:
        hist_avg = crack_df["crack_321"].mean()
        st.metric("Historical Average", f"${hist_avg:.1f}/bbl")

with tab3:
    st.subheader("WTI vs Brent — Geopolitical Risk Premium")
    st.markdown("""
    Brent typically trades above WTI as it reflects global geopolitical risk.
    A **widening spread** signals elevated risk premium or US storage constraints.
    A **narrowing or negative spread** often reflects US export pipeline constraints or a domestic glut.
    """)
    fig = chart_wti_brent_spread(df)
    st.pyplot(fig)
    plt.close()

with tab4:
    st.subheader("Signal Backtest")
    st.markdown(f"""
    Does the inventory signal predict Brent price moves over the next **{backtest_horizon} weeks**?
    Tests historical signal performance since {start_date}.
    """)
    results = backtest_inventory_signal(df, horizon_weeks=backtest_horizon)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bullish Hit Rate",   f"{results['hit_rate_bullish']}%",
              help="% of bullish signals followed by price rise")
    c2.metric("Bearish Hit Rate",   f"{results['hit_rate_bearish']}%",
              help="% of bearish signals followed by price fall")
    c3.metric("Avg Return (Bullish)", f"{results['avg_return_bullish']:+.1f}%")
    c4.metric("Avg Return (Bearish)", f"{results['avg_return_bearish']:+.1f}%")

    fig = chart_backtest(df, results)
    st.pyplot(fig)
    plt.close()

    st.caption(f"n={results['n_bullish']} bullish weeks, n={results['n_bearish']} bearish weeks. "
               "Past signal performance does not guarantee future results.")

with tab5:
    st.subheader("US Refinery Crude Inputs")
    st.markdown("""
    Refinery inputs measure actual crude demand from refineries — a leading indicator.
    Rising inputs mean refineries are pulling crude from storage to process,
    which tightens supply and supports prices.
    """)
    fig = chart_refinery_inputs(df)
    st.pyplot(fig)
    plt.close()

with tab6:
    st.subheader("Market Regime Classification")
    st.markdown("""
    Combines inventory signal and crack spread to classify the weekly market regime.
    Each dot on the Brent price chart is coloured by the regime active that week.
    """)

    # Regime explanation table
    regime_table = pd.DataFrame({
        "Regime":          ["Demand-driven bull", "Tightening supply", "Supply shock",
                            "Demand destruction", "Cautious bull", "Balanced"],
        "Inventory Signal": ["Bullish", "Bullish", "Bearish", "Bearish", "Bullish", "Neutral"],
        "Crack Signal":    ["High", "Normal", "High", "Low", "Low/Normal", "Normal"],
        "Implication":     [
            "Strong demand — price likely to rise",
            "Supply tightening — watch for price upside",
            "Disruption driving prices — demand may follow",
            "Weak demand — price likely to fall",
            "Mixed signals — wait for confirmation",
            "Balanced market — awaiting catalyst",
        ]
    })
    st.dataframe(regime_table, use_container_width=True, hide_index=True)

    fig = chart_market_regime(df)
    st.pyplot(fig)
    plt.close()

    # Regime frequency
    with st.expander("Regime frequency breakdown"):
        freq = df["market_regime"].value_counts().reset_index()
        freq.columns = ["Regime", "Weeks"]
        freq["% of time"] = (freq["Weeks"] / freq["Weeks"].sum() * 100).round(1)
        st.dataframe(freq, use_container_width=True, hide_index=True)
