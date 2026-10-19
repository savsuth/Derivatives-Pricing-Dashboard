import math
import re
import sys
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from scipy.special import erfc

from BlackScholes import BlackScholes


def complex_price(T, K, S, sigma, r, kind):
    """Black-Scholes price written independently with complex-safe functions."""
    N = lambda x: 0.5 * erfc(-x / np.sqrt(2))
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if kind == "call":
        return S * N(d1) - K * np.exp(-r * T) * N(d2)
    return K * np.exp(-r * T) * N(-d2) - S * N(-d1)


def complex_step(param, c, kind, h=1e-20):
    """d(price)/d(param) to machine precision via the complex-step method."""
    args = dict(c)
    args[param] = args[param] + 1j * h
    return complex_price(kind=kind, **args).imag / h


def priced(T, K, S, sigma, r):
    bs = BlackScholes(T, K, S, sigma, r)
    bs.run()
    return bs


class ZeroVolatility(unittest.TestCase):
    def test_deterministic_future_payoff(self):
        bs = priced(T=1, K=100, S=100, sigma=0.0, r=0.05)
        self.assertAlmostEqual(bs.call_price, 100 - 100 * math.exp(-0.05), places=8)
        self.assertAlmostEqual(bs.call_price, 4.87705755, places=8)
        self.assertEqual(bs.put_price, 0.0)
        self.assertEqual(bs.call_delta, 1.0)
        self.assertEqual(bs.put_delta, 0.0)
        self.assertEqual(bs.call_gamma, 0.0)

    def test_matches_small_volatility_limit(self):
        limit = priced(T=1, K=100, S=100, sigma=1e-6, r=0.05)
        zero = priced(T=1, K=100, S=100, sigma=0.0, r=0.05)
        self.assertAlmostEqual(limit.call_price, zero.call_price, places=5)
        self.assertAlmostEqual(limit.call_delta, zero.call_delta, places=5)

    def test_negative_rate_put_in_the_money(self):
        bs = priced(T=1, K=100, S=100, sigma=0.0, r=-0.02)
        self.assertAlmostEqual(bs.put_price, 100 * math.exp(0.02) - 100, places=10)
        self.assertEqual(bs.call_price, 0.0)
        self.assertEqual(bs.put_delta, -1.0)

    def test_kink_is_discounted_strike(self):
        K, r, T = 100.0, 0.05, 1.0
        bs = priced(T=T, K=K, S=K * math.exp(-r * T), sigma=0.0, r=r)
        self.assertEqual(bs.call_price, 0.0)
        self.assertEqual(bs.put_price, 0.0)
        self.assertEqual(bs.call_delta, 0.5)
        self.assertEqual(bs.put_delta, -0.5)
        self.assertTrue(math.isinf(bs.call_gamma))


class Expiry(unittest.TestCase):
    def test_itm_call(self):
        bs = priced(T=0, K=90, S=100, sigma=0.2, r=0.05)
        self.assertEqual((bs.call_price, bs.put_price), (10.0, 0.0))
        self.assertEqual((bs.call_delta, bs.put_delta), (1.0, 0.0))
        self.assertEqual(bs.call_gamma, 0.0)

    def test_itm_put(self):
        bs = priced(T=0, K=110, S=100, sigma=0.2, r=0.05)
        self.assertEqual((bs.call_price, bs.put_price), (0.0, 10.0))
        self.assertEqual((bs.call_delta, bs.put_delta), (0.0, -1.0))

    def test_at_the_money_kink(self):
        bs = priced(T=0, K=100, S=100, sigma=0.2, r=0.05)
        self.assertEqual((bs.call_price, bs.put_price), (0.0, 0.0))
        self.assertEqual((bs.call_delta, bs.put_delta), (0.5, -0.5))
        self.assertTrue(math.isinf(bs.call_gamma))


class InvalidInputs(unittest.TestCase):
    def test_rejected(self):
        bad = [
            dict(T=-1, K=100, S=100, sigma=0.2, r=0.05),
            dict(T=1, K=100, S=100, sigma=-0.2, r=0.05),
            dict(T=1, K=0, S=100, sigma=0.2, r=0.05),
            dict(T=1, K=100, S=0, sigma=0.2, r=0.05),
            dict(T=1, K=-5, S=100, sigma=0.2, r=0.05),
            dict(T=float("nan"), K=100, S=100, sigma=0.2, r=0.05),
            dict(T=1, K=100, S=100, sigma=0.2, r=float("inf")),
        ]
        for kwargs in bad:
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                priced(**kwargs)

    def test_negative_rate_supported(self):
        bs = priced(T=1, K=100, S=100, sigma=0.2, r=-0.01)
        self.assertTrue(math.isfinite(bs.call_price))


class PositiveVolatility(unittest.TestCase):
    CASES = [
        dict(T=2, K=90, S=100, sigma=0.2, r=0.05),
        dict(T=1, K=100, S=100, sigma=0.2, r=0.05),
        dict(T=0.5, K=120, S=100, sigma=0.35, r=-0.01),
    ]

    def test_reference_price(self):
        # Hull-style textbook value: S=K=100, T=1, sigma=0.2, r=0.05
        bs = priced(T=1, K=100, S=100, sigma=0.2, r=0.05)
        self.assertAlmostEqual(bs.call_price, 10.4506, places=4)
        self.assertAlmostEqual(bs.put_price, 5.5735, places=4)

    def test_put_call_parity(self):
        for c in self.CASES:
            with self.subTest(**c):
                bs = priced(**c)
                parity = c["S"] - c["K"] * math.exp(-c["r"] * c["T"])
                self.assertAlmostEqual(bs.call_price - bs.put_price, parity, places=10)

    def test_deltas_match_finite_difference(self):
        for c in self.CASES:
            with self.subTest(**c):
                h = 1e-3
                up = priced(**{**c, "S": c["S"] + h})
                dn = priced(**{**c, "S": c["S"] - h})
                bs = priced(**c)
                self.assertAlmostEqual(bs.call_delta, (up.call_price - dn.call_price) / (2 * h), places=6)
                self.assertAlmostEqual(bs.put_delta, (up.put_price - dn.put_price) / (2 * h), places=6)
                self.assertLess(bs.put_delta, 0.0)
                self.assertAlmostEqual(bs.call_delta - bs.put_delta, 1.0, places=12)

    def test_gamma_matches_finite_difference(self):
        for c in self.CASES:
            with self.subTest(**c):
                h = 0.05
                up = priced(**{**c, "S": c["S"] + h})
                dn = priced(**{**c, "S": c["S"] - h})
                bs = priced(**c)
                fd_call = (up.call_price - 2 * bs.call_price + dn.call_price) / h ** 2
                fd_put = (up.put_price - 2 * bs.put_price + dn.put_price) / h ** 2
                self.assertAlmostEqual(bs.call_gamma, fd_call, places=5)
                self.assertAlmostEqual(bs.put_gamma, fd_put, places=5)

    def test_gamma_uses_spot_not_strike(self):
        bs = priced(T=1, K=50, S=100, sigma=0.2, r=0.05)
        d1 = (math.log(2) + (0.05 + 0.02)) / 0.2
        expected = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) / (100 * 0.2)
        self.assertAlmostEqual(bs.call_gamma, expected, places=12)


class FirstOrderGreeks(unittest.TestCase):
    # Trader units: vega and rho per 1 percentage point, theta per calendar day.
    CASES = PositiveVolatility.CASES

    def test_against_complex_step(self):
        for c in self.CASES:
            bs = priced(**c)
            for kind in ("call", "put"):
                with self.subTest(kind=kind, **c):
                    self.assertAlmostEqual(bs.vega, complex_step("sigma", c, kind) / 100, places=10)
                    self.assertAlmostEqual(getattr(bs, f"{kind}_rho"), complex_step("r", c, kind) / 100, places=10)
                    self.assertAlmostEqual(getattr(bs, f"{kind}_theta"), -complex_step("T", c, kind) / 365, places=10)

    def test_textbook_values(self):
        bs = priced(T=1, K=100, S=100, sigma=0.2, r=0.05)
        self.assertAlmostEqual(bs.vega, 0.3752, places=4)
        self.assertAlmostEqual(bs.call_theta * 365, -6.414, places=3)
        self.assertAlmostEqual(bs.call_rho, 0.5323, places=4)


class SecondOrderGreeks(unittest.TestCase):
    # Trader units: vanna per vol point, volga per vol point squared, charm per day.
    CASES = PositiveVolatility.CASES

    def central(self, outer, inner, c, h=1e-5):
        up = complex_step(inner, {**c, outer: c[outer] + h}, "call")
        dn = complex_step(inner, {**c, outer: c[outer] - h}, "call")
        return (up - dn) / (2 * h)

    def test_against_differenced_complex_step(self):
        for c in self.CASES:
            with self.subTest(**c):
                bs = priced(**c)
                self.assertAlmostEqual(bs.vanna, self.central("sigma", "S", c) / 100, places=8)
                self.assertAlmostEqual(bs.volga, self.central("sigma", "sigma", c) / 100 ** 2, places=8)
                self.assertAlmostEqual(bs.charm, -self.central("T", "S", c) / 365, places=8)

    def test_textbook_values(self):
        bs = priced(T=1, K=100, S=100, sigma=0.2, r=0.05)
        self.assertAlmostEqual(bs.vanna * 100, -0.28143, places=5)
        self.assertAlmostEqual(bs.volga * 100 ** 2, 9.85006, places=5)


class DegenerateGreekLimits(unittest.TestCase):
    """sigma == 0 or T == 0 must report the limit of the regular formulas."""

    FIELDS = ("call_price", "put_price", "call_delta", "put_delta", "gamma", "vega",
              "call_theta", "put_theta", "call_rho", "put_rho", "vanna", "volga", "charm")

    def assertLimit(self, exact, near, fields=FIELDS):
        for f in fields:
            e, n = getattr(exact, f), getattr(near, f)
            with self.subTest(field=f):
                if math.isinf(e):
                    self.assertEqual(math.copysign(1, e), math.copysign(1, n))
                    self.assertGreater(abs(n), 1e3)
                else:
                    self.assertAlmostEqual(e, n, places=5)

    def test_zero_vol(self):
        K, T = 100.0, 1.0
        for r in (0.05, -0.02, 0.0):
            for S in (90.0, 110.0, K * math.exp(-r * T)):
                with self.subTest(r=r, S=S):
                    exact = priced(T=T, K=K, S=S, sigma=0.0, r=r)
                    others = tuple(f for f in self.FIELDS if f != "vanna")
                    self.assertLimit(exact, priced(T=T, K=K, S=S, sigma=1e-9, r=r), others)
                    # Vanna divides rounding error in log(S/K) + rT by sigma^2, so
                    # take its reference at a better-conditioned sigma.
                    self.assertLimit(exact, priced(T=T, K=K, S=S, sigma=1e-6, r=r), ("vanna",))

    def test_expiry(self):
        for sigma in (0.0, 0.3):
            for S in (90.0, 110.0, 100.0):
                if sigma == 0.0 and S == 100.0:
                    continue  # double limit; covered by test_expiry_and_zero_vol_kink
                with self.subTest(sigma=sigma, S=S):
                    near = priced(T=1e-14, K=100, S=S, sigma=sigma or 1e-9, r=0.05)
                    self.assertLimit(priced(T=0, K=100, S=S, sigma=sigma, r=0.05), near)

    def test_expiry_and_zero_vol_kink(self):
        # T -> 0 of the sigma == 0 limit: half the deterministic theta, no vol sensitivity.
        bs = priced(T=0, K=100, S=100, sigma=0.0, r=0.05)
        self.assertAlmostEqual(bs.call_theta, -0.05 * 100 / 2 / 365, places=12)
        self.assertAlmostEqual(bs.put_theta, 0.05 * 100 / 2 / 365, places=12)
        self.assertEqual((bs.vega, bs.vanna, bs.volga, bs.call_rho), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(bs.charm, -math.inf)


class ImpliedVolatility(unittest.TestCase):
    iv = staticmethod(BlackScholes.implied_volatility)

    def test_textbook_price(self):
        self.assertAlmostEqual(self.iv(10.450583572185568, 1, 100, 100, 0.05), 0.2, places=10)

    def test_round_trip(self):
        cases = PositiveVolatility.CASES + [
            dict(T=0.25, K=300, S=100, sigma=0.9, r=0.03),   # deep out of the money call
            dict(T=0.5, K=95, S=100, sigma=0.05, r=0.02),    # in the money, low vol
            dict(T=5, K=100, S=100, sigma=3.0, r=0.0),       # very high vol
        ]
        for c in cases:
            bs = priced(**c)
            for kind in ("call", "put"):
                with self.subTest(kind=kind, **c):
                    target = getattr(bs, f"{kind}_price")
                    sigma = self.iv(target, c["T"], c["K"], c["S"], c["r"], option=kind)
                    self.assertAlmostEqual(sigma, c["sigma"], places=8)

    def test_deep_in_the_money_rounding_below_intrinsic(self):
        # The model's own price can land a rounding error under intrinsic value.
        bs = priced(T=0.01, K=0.2, S=1.0, sigma=2.0, r=0.0)
        self.assertEqual(self.iv(bs.call_price, 0.01, 0.2, 1.0, 0.0), 0.0)

    def test_deep_out_of_the_money_converges(self):
        bs = priced(T=2.0, K=2.0, S=1.0, sigma=0.015625, r=0.0)
        sigma = self.iv(bs.call_price, 2.0, 2.0, 1.0, 0.0)
        self.assertAlmostEqual(priced(T=2.0, K=2.0, S=1.0, sigma=sigma, r=0.0).call_price,
                               bs.call_price, delta=1e-12)

    def test_price_at_lower_bound_is_zero_vol(self):
        intrinsic = 100 - 90 * math.exp(-0.05)
        self.assertEqual(self.iv(intrinsic, 1, 90, 100, 0.05), 0.0)
        self.assertEqual(self.iv(0.0, 1, 90, 100, 0.05, option="put"), 0.0)

    def test_arbitrage_violations_rejected(self):
        bad = [
            dict(price=4.0, T=1, K=90, S=100, r=0.05),                  # below intrinsic
            dict(price=100.0, T=1, K=90, S=100, r=0.05),                # call at spot
            dict(price=-1.0, T=1, K=90, S=100, r=0.05, option="put"),
            dict(price=90.0, T=1, K=90, S=100, r=0.05, option="put"),   # above discounted strike
            dict(price=5.0, T=0, K=90, S=100, r=0.05),                  # no vol information at expiry
            dict(price=5.0, T=1, K=90, S=100, r=0.05, option="straddle"),
            dict(price=float("nan"), T=1, K=90, S=100, r=0.05),
        ]
        for b in bad:
            with self.subTest(**b), self.assertRaises(ValueError):
                self.iv(b["price"], b["T"], b["K"], b["S"], b["r"], option=b.get("option", "call"))


class Underflow(unittest.TestCase):
    def test_tiny_vol_sqrt_t_is_the_zero_vol_limit(self):
        # sigma * sqrt(T) underflows to 0, log(S/K) / (sigma * sqrt(T)) overflows,
        # or T * sigma * sqrt(T) (the charm denominator) underflows.
        cases = ((1e-300, 1e-200, 100.0), (1e-300, 1e-160, 110.0), (1e-300, 1e-160, 90.0),
                 (1e-250, 1.0, 110.0))
        for T, sigma, S in cases:
            with self.subTest(T=T, sigma=sigma, S=S):
                tiny = priced(T=T, K=100, S=S, sigma=sigma, r=0.05)
                zero = priced(T=T, K=100, S=S, sigma=0.0, r=0.05)
                for f in DegenerateGreekLimits.FIELDS:
                    self.assertEqual(getattr(tiny, f), getattr(zero, f), f)


class NoRuntimeWarnings(unittest.TestCase):
    def test_huge_d1_is_silent(self):
        # |d1| ~ 1e205: the normal density underflows to exactly 0, which is the right limit.
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            bs = priced(T=1.0, K=0.5, S=1.0, sigma=1.36e-220, r=0.0)
        self.assertEqual((bs.call_price, bs.gamma, bs.volga), (0.5, 0.0, 0.0))


class ArrayInputs(unittest.TestCase):
    def test_grid_matches_pointwise(self):
        spots = np.linspace(60, 140, 7)
        vols = np.linspace(0.0, 0.8, 5)
        grid = BlackScholes(1.0, 100.0, spots[None, :], vols[:, None], 0.05)
        grid.run()
        self.assertEqual(grid.call_price.shape, (5, 7))
        for i, v in enumerate(vols):
            for j, s in enumerate(spots):
                point = priced(T=1.0, K=100.0, S=s, sigma=v, r=0.05)
                self.assertAlmostEqual(grid.call_price[i, j], point.call_price, places=12)
                self.assertAlmostEqual(grid.put_delta[i, j], point.put_delta, places=12)
                self.assertAlmostEqual(grid.vega[i, j], point.vega, places=12)

    def test_scalar_inputs_give_floats(self):
        bs = priced(T=1, K=100, S=100, sigma=0.2, r=0.05)
        self.assertIsInstance(bs.call_price, float)
        self.assertIsInstance(bs.vega, float)

    def test_one_bad_cell_rejects_the_grid(self):
        with self.assertRaises(ValueError):
            BlackScholes(1.0, 100.0, np.array([100.0, -1.0]), 0.2, 0.05).run()


class SingleImplementation(unittest.TestCase):
    def test_calculate_prices_wrapper(self):
        bs = BlackScholes(1, 100, 100, 0.0, 0.05)
        call, put = bs.calculate_prices()
        self.assertAlmostEqual(call, 4.87705755, places=8)
        self.assertEqual(put, 0.0)

    def test_api_uses_module_not_its_own_copy(self):
        src = (ROOT / "api" / "quote.py").read_text()
        self.assertRegex(src, r"(?m)^from BlackScholes import BlackScholes")
        self.assertIsNone(re.search(r"(?m)^class BlackScholes|norm\.cdf", src))


if __name__ == "__main__":
    unittest.main()
