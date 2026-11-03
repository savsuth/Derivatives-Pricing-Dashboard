"""The Vercel function in api/quote.py: a JSON view of the BlackScholes model."""
import importlib.util
import json
import math
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from BlackScholes import BlackScholes

spec = importlib.util.spec_from_file_location("quote", ROOT / "api" / "quote.py")
quote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quote)

DEFAULT = dict(S="100", K="100", T="1", sigma="0.2", r="0.05")


class BuildQuote(unittest.TestCase):
    def test_prices_and_greeks_come_from_the_model(self):
        q = quote.build_quote(DEFAULT)
        bs = BlackScholes(1.0, 100.0, 100.0, 0.2, 0.05)
        bs.run()
        self.assertEqual(q["prices"], {"call": bs.call_price, "put": bs.put_price})
        self.assertEqual(q["greeks"]["call_delta"], bs.call_delta)
        self.assertEqual(q["greeks"]["volga"], bs.volga)
        self.assertAlmostEqual(q["prices"]["call"], 10.4506, places=4)

    def test_live_checks_agree(self):
        checks = quote.build_quote(DEFAULT)["checks"]
        self.assertEqual(set(checks), {"price", "delta", "theta", "rho", "gamma", "vega", "vanna", "volga", "charm"})
        for name, value in checks.items():
            with self.subTest(name=name):
                self.assertLess(value, 1e-5)

    def test_default_checks_keep_their_published_size(self):
        # The README's Table 1 quotes these values.
        published = dict(delta=8.6e-7, theta=1.3e-11, rho=9.4e-11, gamma=2.3e-8,
                         vega=3.0e-9, vanna=1.1e-9, volga=5.6e-10, charm=2.4e-13)
        checks = quote.build_quote(DEFAULT)["checks"]
        for name, value in published.items():
            with self.subTest(name=name):
                self.assertEqual(f"{checks[name]:.1e}", f"{value:.1e}")

    def test_checks_resolve_near_expiry_and_at_low_volatility(self):
        cases = (dict(T="0.0001", sigma="0.01"), dict(T="0.0001"), dict(T="0.001"),
                 dict(T=str(1 / 365)), dict(sigma="0.01"), dict(T="0.0001", sigma="0.01", S="100.5"))
        for inputs in cases:
            q = quote.build_quote({**DEFAULT, **inputs})
            g = q["greeks"]
            scale = dict(delta=1.0, theta=abs(g["call_theta"]), rho=abs(g["call_rho"]), gamma=g["gamma"],
                         vega=g["vega"], vanna=abs(g["vanna"]), volga=abs(g["volga"]), charm=abs(g["charm"]))
            for name, size in scale.items():
                with self.subTest(inputs=inputs, name=name):
                    self.assertLess(q["checks"][name], max(1e-2 * size, 1e-6))

    def test_extreme_inputs_give_valid_json_or_a_clear_error(self):
        values = dict(S=("1e-308", "1e-200", "1e200", "1e308"), K=("1e-308", "1e308"),
                      T=("5e-324", "1e-300", "1e-250", "1e-8", "1000", "1e308"),
                      sigma=("5e-324", "1e-300", "1e-8", "50", "1e308"),
                      r=("-1e308", "-1000", "-700", "1000", "1e308"))
        for name, options in values.items():
            for value in options:
                with self.subTest(name=name, value=value):
                    try:
                        q = quote.build_quote({**DEFAULT, name: value})
                    except ValueError:
                        continue
                    json.loads(json.dumps(q, allow_nan=False))

    def test_checks_that_cannot_be_computed_are_null(self):
        q = quote.build_quote({**DEFAULT, "S": "1e200"})  # the squared bump leaves float range
        self.assertIsNone(q["checks"]["gamma"])
        self.assertFalse(q["degenerate"])
        q = quote.build_quote({**DEFAULT, "T": "1e-300"})
        for name, value in q["checks"].items():
            with self.subTest(name=name):
                self.assertTrue(value is None or math.isfinite(value))

    def test_no_bump_when_float_arithmetic_cannot_resolve_it(self):
        for inputs in (dict(T="1e-20", sigma="0.1"), dict(T="1e-12", sigma="0.1"), dict(T="1e-10", sigma="0.01")):
            q = quote.build_quote({**DEFAULT, **inputs})
            self.assertFalse(q["degenerate"])
            for name, value in q["checks"].items():
                with self.subTest(inputs=inputs, name=name):
                    self.assertEqual(value is None, name != "price")

    def test_overflowing_discounted_strike_is_a_clear_error(self):
        for bad in ({**DEFAULT, "r": "-1000"}, {**DEFAULT, "T": "1500", "r": "-0.5"}, {**DEFAULT, "K": "1e308", "r": "-1"}):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "discounted strike"):
                quote.build_quote(bad)

    def test_zero_vol_reports_limits_without_bump_checks(self):
        q = quote.build_quote({**DEFAULT, "sigma": "0"})
        self.assertTrue(q["degenerate"])
        self.assertAlmostEqual(q["prices"]["call"], 4.87705755, places=8)
        self.assertIsNotNone(q["checks"]["price"])
        self.assertIsNone(q["checks"]["delta"])

    def test_infinities_are_json_safe(self):
        kink = str(100 * math.exp(-0.05))
        q = quote.build_quote({**DEFAULT, "S": kink, "sigma": "0"})
        self.assertEqual(q["greeks"]["gamma"], "inf")
        json.loads(json.dumps(q, allow_nan=False))

    def test_invalid_inputs_name_the_api_parameters(self):
        for bad in ("S", "K", "T", "sigma"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, r"^T and sigma must be >= 0, and S and K must be > 0$"):
                quote.build_quote({**DEFAULT, bad: "-1"})

    def test_heatmap_grid(self):
        q = quote.build_quote({**DEFAULT, "spot_min": "60", "spot_max": "140", "vol_min": "0.05", "vol_max": "0.6"})
        grid = q["heatmap"]
        self.assertEqual((len(grid["vols"]), len(grid["spots"])), (10, 10))
        self.assertEqual((len(grid["call"]), len(grid["call"][0])), (10, 10))
        bs = BlackScholes(1.0, 100.0, grid["spots"][3], grid["vols"][7], 0.05)
        bs.run()
        self.assertAlmostEqual(grid["call"][7][3], bs.call_price, places=12)
        self.assertAlmostEqual(grid["put"][7][3], bs.put_price, places=12)

    def test_heatmap_defaults_follow_spot(self):
        grid = quote.build_quote({**DEFAULT, "S": "50"})["heatmap"]
        self.assertAlmostEqual(grid["spots"][0], 30.0)
        self.assertAlmostEqual(grid["spots"][-1], 70.0)

    def test_invalid_inputs_raise(self):
        for bad in ({**DEFAULT, "S": "-1"}, {**DEFAULT, "T": "abc"}, {**DEFAULT, "sigma": "nan"},
                    {k: v for k, v in DEFAULT.items() if k != "K"},
                    {**DEFAULT, "spot_min": "120", "spot_max": "80"}, {**DEFAULT, "vol_min": "0"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                quote.build_quote(bad)


class Handler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), quote.handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/api/quote"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_ok(self):
        with urllib.request.urlopen(f"{self.base}?S=100&K=100&T=1&sigma=0.2&r=0.05") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Content-Type"], "application/json")
            body = json.load(response)
        self.assertAlmostEqual(body["prices"]["call"], 10.4506, places=4)

    def test_bad_request(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(f"{self.base}?S=-5&K=100&T=1&sigma=0.2&r=0.05")
        self.assertEqual(caught.exception.code, 400)
        self.assertIn("error", json.load(caught.exception))

    def test_head_matches_get_without_a_body(self):
        url = f"{self.base}?S=100&K=100&T=1&sigma=0.2&r=0.05"
        with urllib.request.urlopen(url) as response:
            length = response.headers["Content-Length"]
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Content-Type"], "application/json")
            self.assertEqual(response.headers["Content-Length"], length)
            self.assertEqual(response.read(), b"")

    def test_head_reports_bad_requests(self):
        request = urllib.request.Request(f"{self.base}?S=-5&K=100&T=1&sigma=0.2&r=0.05", method="HEAD")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 400)

    def test_extreme_inputs_are_not_server_errors(self):
        for query in ("S=1e308&K=100&T=1&sigma=0.2&r=0.05", "S=1e-308&K=100&T=1&sigma=0.2&r=0.05",
                      "S=100&K=100&T=1e-300&sigma=0.2&r=0.05", "S=100&K=100&T=1&sigma=0.2&r=-1000",
                      "S=100&K=100&T=1&sigma=0.2&r=-700"):
            with self.subTest(query=query):
                try:
                    with urllib.request.urlopen(f"{self.base}?{query}") as response:
                        status, body = response.status, json.load(response)
                except urllib.error.HTTPError as error:
                    status, body = error.code, json.load(error)
                self.assertIn(status, (200, 400))
                self.assertTrue("prices" in body or "error" in body)


if __name__ == "__main__":
    unittest.main()
