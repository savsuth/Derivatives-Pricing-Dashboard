import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from numpy import log, sqrt, exp
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------- Page setup --------------------
st.set_page_config(
    page_title="Derivatives Pricing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.metric-container{display:flex;justify-content:center;align-items:center;padding:8px;margin:0 auto;border-radius:12px}
.metric-call{background:#90ee90;color:#000}
.metric-put{background:#ffcccb;color:#000}
.metric-value{font-size:1.6rem;font-weight:700;margin:0}
.metric-label{font-size:0.95rem;margin-bottom:4px}
</style>
""", unsafe_allow_html=True)

# -------------------- Model --------------------
class BlackScholes:
    def __init__(self, time_to_maturity: float, strike: float, current_price: float,
                 volatility: float, interest_rate: float):
        self.time_to_maturity = float(time_to_maturity)
        self.strike = float(strike)
        self.current_price = float(current_price)
        self.volatility = float(volatility)
        self.interest_rate = float(interest_rate)
        self.call_price = 0.0
        self.put_price = 0.0
        self.call_delta = 0.0
        self.put_delta = 0.0
        self.call_gamma = 0.0
        self.put_gamma = 0.0

    def calculate_prices(self):
        T = self.time_to_maturity
        K = self.strike
        S = self.current_price
        sigma = self.volatility
        r = self.interest_rate

        # Guard rails to avoid nan/inf
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            self.call_price = max(S - K, 0.0)
            self.put_price = max(K - S, 0.0)
            self.call_delta = 1.0 if S > K else 0.0
            self.put_delta = 1.0 if K > S else 0.0
            self.call_gamma = 0.0
            self.put_gamma = 0.0
            return self.call_price, self.put_price

        d1 = (log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)

        self.call_price = S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
        self.put_price = K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        self.call_delta = norm.cdf(d1)
        self.put_delta = self.call_delta - 1.0
        self.call_gamma = norm.pdf(d1) / (S * sigma * sqrt(T))
        self.put_gamma = self.call_gamma
        return self.call_price, self.put_price

# -------------------- Sidebar inputs --------------------
with st.sidebar:
    st.title("Inputs")
    current_price = st.number_input("Spot Price (S)", min_value=0.01, value=100.0, step=0.5)
    strike = st.number_input("Strike Price (K)", min_value=0.01, value=100.0, step=0.5)
    maturity = st.number_input("Time to Maturity (years)", min_value=0.0, value=1.0, step=0.05)
    volatility = st.number_input("Volatility (σ)", min_value=0.0, value=0.20, step=0.01, format="%.2f")
    interest_rate = st.number_input("Risk-free Rate (r)", min_value=-0.50, value=0.05, step=0.01, format="%.2f")

    st.markdown("---")
    st.subheader("Heatmap Ranges")
    spot_min = st.number_input("Min Spot", min_value=0.01, value=max(0.01, current_price * 0.6), step=0.5)
    spot_max = st.number_input("Max Spot", min_value=spot_min + 0.01, value=current_price * 1.4, step=0.5)
    vol_min = st.slider("Min σ", min_value=0.01, max_value=1.00, value=max(0.01, min(volatility, 0.05)), step=0.01)
    vol_max = st.slider("Max σ", min_value=0.05, max_value=1.50, value=max(volatility, 0.60), step=0.01)

# canonical variable name used below
time_to_maturity = maturity

spot_range = np.linspace(spot_min, spot_max, 10)
vol_range = np.linspace(vol_min, vol_max, 10)

# -------------------- Heatmap helper --------------------
def plot_heatmap(bs_model: BlackScholes, spot_range, vol_range, strike_val):
    call_prices = np.zeros((len(vol_range), len(spot_range)))
    put_prices = np.zeros_like(call_prices)

    for i, vol in enumerate(vol_range):
        for j, spot in enumerate(spot_range):
            bs_temp = BlackScholes(
                time_to_maturity=bs_model.time_to_maturity,
                strike=strike_val,
                current_price=spot,
                volatility=vol,
                interest_rate=bs_model.interest_rate,
            )
            bs_temp.calculate_prices()
            call_prices[i, j] = bs_temp.call_price
            put_prices[i, j] = bs_temp.put_price

    fig_call, ax_call = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        call_prices,
        xticklabels=np.round(spot_range, 2),
        yticklabels=np.round(vol_range, 2),
        annot=True,
        fmt=".2f",
        cmap="viridis",
        ax=ax_call,
        cbar_kws={"label": "Call Price"},
    )
    ax_call.set_title("Call Price Heatmap")
    ax_call.set_xlabel("Spot (S)")
    ax_call.set_ylabel("Volatility (σ)")

    fig_put, ax_put = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        put_prices,
        xticklabels=np.round(spot_range, 2),
        yticklabels=np.round(vol_range, 2),
        annot=True,
        fmt=".2f",
        cmap="magma",
        ax=ax_put,
        cbar_kws={"label": "Put Price"},
    )
    ax_put.set_title("Put Price Heatmap")
    ax_put.set_xlabel("Spot (S)")
    ax_put.set_ylabel("Volatility (σ)")

    return fig_call, fig_put

# -------------------- Main layout --------------------
st.title("Derivatives Pricing Dashboard")

tab_prices, tab_heatmaps = st.tabs(["📊 Prices", "📈 Heatmaps"])

with tab_prices:
    bs_model = BlackScholes(time_to_maturity, strike, current_price, volatility, interest_rate)
    call_price, put_price = bs_model.calculate_prices()

    input_df = pd.DataFrame({
        "Spot (S)": [current_price],
        "Strike (K)": [strike],
        "Time to Maturity (T)": [time_to_maturity],
        "Volatility (σ)": [volatility],
        "Risk-free Rate (r)": [interest_rate],
    })
    st.subheader("Inputs")
    st.table(input_df)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="metric-container metric-call">'
            f'<div><div class="metric-label">CALL</div>'
            f'<div class="metric-value">${call_price:.2f}</div></div></div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div class="metric-container metric-put">'
            f'<div><div class="metric-label">PUT</div>'
            f'<div class="metric-value">${put_price:.2f}</div></div></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.caption("Note: European options, no dividends; Black–Scholes assumptions apply.")

with tab_heatmaps:
    st.info("Heatmaps show option prices as Spot and Volatility vary.")
    h1, h2 = st.columns(2, gap="large")
    fig_call, fig_put = plot_heatmap(
        BlackScholes(time_to_maturity, strike, current_price, volatility, interest_rate),
        spot_range, vol_range, strike
    )
    with h1:
        st.pyplot(fig_call, clear_figure=True)
    with h2:
        st.pyplot(fig_put, clear_figure=True)

st.markdown("---")
st.caption("Created by Aasav Suthar • For educational use only")
