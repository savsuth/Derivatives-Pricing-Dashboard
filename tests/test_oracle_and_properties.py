"""Cross-checks against QuantLib and no-arbitrage properties (requirements-dev.txt)."""
import math
import unittest

import numpy as np
import QuantLib as ql
from hypothesis import assume, given, settings
from hypothesis import strategies as st

import test_black_scholes as base
from BlackScholes import BlackScholes


def random_inputs(n, seed=7):
    rng = np.random.default_rng(seed)
    S = rng.uniform(20, 200, n)
    return dict(
        S=S,
        K=S * rng.uniform(0.5, 2.0, n),
        T=rng.uniform(0.01, 5.0, n),
        sigma=rng.uniform(0.05, 1.5, n),
        r=rng.uniform(-0.03, 0.10, n),
    )


class QuantLibOracle(unittest.TestCase):
    """QuantLib's BlackCalculator reports theta per year and vega, rho, vanna, volga per unit."""

    N = 2000
    UNITS = dict(price=1.0, delta=1.0, gamma=1.0, vega=100.0, theta=365.0, rho=100.0,
                 vanna=100.0, volga=100.0 ** 2)

    def test_prices_and_greeks(self):
        x = random_inputs(self.N)
        bs = BlackScholes(x["T"], x["K"], x["S"], x["sigma"], x["r"])
        bs.run()
        worst = {}
        for i in range(self.N):
            S, K, T, sigma, r = (float(x[k][i]) for k in ("S", "K", "T", "sigma", "r"))
            discount = math.exp(-r * T)
            for kind, ql_type in (("call", ql.Option.Call), ("put", ql.Option.Put)):
                ref = ql.BlackCalculator(ql.PlainVanillaPayoff(ql_type, K), S / discount,
                                         sigma * math.sqrt(T), discount)
                expected = dict(price=ref.value(), delta=ref.delta(S), gamma=ref.gamma(S),
                                vega=ref.vega(T), theta=ref.theta(S, T), rho=ref.rho(T),
                                vanna=ref.vanna(S, T),
                                # QuantLib 1.44 divides vega * d1 * d2 by stdDev (sigma * sqrt(T))
                                # instead of sigma, so its volga is d2V/dsigma2 / sqrt(T); see
                                # ql/pricingengines/blackcalculator.cpp. Complex-step tests in
                                # test_black_scholes.py check volga independently.
                                volga=ref.volga(T) * math.sqrt(T))
                ours = dict(price=bs.call_price if kind == "call" else bs.put_price,
                            delta=getattr(bs, f"{kind}_delta"), gamma=bs.gamma, vega=bs.vega,
                            theta=getattr(bs, f"{kind}_theta"), rho=getattr(bs, f"{kind}_rho"),
                            vanna=bs.vanna, volga=bs.volga)
                for name, ref_value in expected.items():
                    value = ours[name][i] * self.UNITS[name]
                    rel = abs(value - ref_value) / max(1.0, abs(ref_value))
                    worst[(kind, name)] = max(worst.get((kind, name), 0.0), rel)
        for key, err in worst.items():
            with self.subTest(greek=key):
                self.assertLess(err, 1e-9, f"max relative error {err:.2e}")

    def test_implied_volatility(self):
        x = random_inputs(300, seed=11)
        checked = 0
        for i in range(300):
            S, K, T, sigma, r = (float(x[k][i]) for k in ("S", "K", "T", "sigma", "r"))
            bs = base.priced(T=T, K=K, S=S, sigma=sigma, r=r)
            if bs.vega * 100 < 1e-3 * S:
                continue  # price barely moves with sigma: not identifiable by either solver
            discount = math.exp(-r * T)
            ref = ql.blackFormulaImpliedStdDev(ql.Option.Call, K, S / discount, bs.call_price,
                                               discount, 0.0, sigma * math.sqrt(T), 1e-14, 1000)
            ours = BlackScholes.implied_volatility(bs.call_price, T, K, S, r)
            self.assertAlmostEqual(ours, ref / math.sqrt(T), places=8)
            checked += 1
        self.assertGreater(checked, 250)


spot = st.floats(1.0, 1000.0)
moneyness = st.floats(0.2, 5.0)
maturity = st.floats(0.0, 10.0)
vol = st.floats(0.0, 3.0)
rate = st.floats(-0.05, 0.15)


class NoArbitrageProperties(unittest.TestCase):
    @settings(max_examples=300, deadline=None)
    @given(spot, moneyness, maturity, vol, rate)
    def test_price_bounds_and_parity(self, S, m, T, sigma, r):
        K = S * m
        bs = base.priced(T=T, K=K, S=S, sigma=sigma, r=r)
        D = K * math.exp(-r * T)
        tol = 1e-9 * max(S, D)
        self.assertGreaterEqual(bs.call_price, max(S - D, 0.0) - tol)
        self.assertLessEqual(bs.call_price, S + tol)
        self.assertGreaterEqual(bs.put_price, max(D - S, 0.0) - tol)
        self.assertLessEqual(bs.put_price, D + tol)
        self.assertAlmostEqual(bs.call_price - bs.put_price, S - D, delta=tol)
        for field in base.DegenerateGreekLimits.FIELDS:
            self.assertFalse(math.isnan(getattr(bs, field)), field)

    @settings(max_examples=300, deadline=None)
    @given(spot, moneyness, maturity, vol, rate, st.floats(0.001, 0.2))
    def test_call_decreasing_and_convex_in_strike(self, S, m, T, sigma, r, width):
        K = S * m
        h = K * width
        lo, mid, hi = (base.priced(T=T, K=k, S=S, sigma=sigma, r=r).call_price for k in (K - h, K, K + h))
        tol = 1e-9 * S
        self.assertGreaterEqual(lo, mid - tol)
        self.assertGreaterEqual(mid, hi - tol)
        self.assertGreaterEqual(lo - 2 * mid + hi, -tol)  # butterfly spread is never negative

    @settings(max_examples=300, deadline=None)
    @given(spot, moneyness, maturity, vol, rate, st.floats(0.0, 1.0))
    def test_prices_nondecreasing_in_vol(self, S, m, T, sigma, r, bump):
        K = S * m
        low = base.priced(T=T, K=K, S=S, sigma=sigma, r=r)
        high = base.priced(T=T, K=K, S=S, sigma=sigma + bump, r=r)
        tol = 1e-9 * S
        self.assertGreaterEqual(high.call_price, low.call_price - tol)
        self.assertGreaterEqual(low.vega, 0.0)

    @settings(max_examples=300, deadline=None)
    @given(spot, moneyness, st.floats(0.01, 10.0), st.floats(0.01, 3.0), rate,
           st.sampled_from(["call", "put"]))
    def test_implied_vol_reprices(self, S, m, T, sigma, r, kind):
        K = S * m
        bs = base.priced(T=T, K=K, S=S, sigma=sigma, r=r)
        target = getattr(bs, f"{kind}_price")
        D = K * math.exp(-r * T)
        upper = S if kind == "call" else D
        assume(target < upper * (1 - 1e-12))  # strictly inside the bounds in floating point
        implied = BlackScholes.implied_volatility(target, T, K, S, r, option=kind)
        again = getattr(base.priced(T=T, K=K, S=S, sigma=implied, r=r), f"{kind}_price")
        self.assertAlmostEqual(again, target, delta=1e-9 * S)
        if bs.vega * 100 > 1e-3 * S:
            self.assertAlmostEqual(implied, sigma, places=6)


if __name__ == "__main__":
    unittest.main()
