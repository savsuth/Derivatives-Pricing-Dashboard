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

    def test_invalid_spot_names_the_model_input(self):
        with self.assertRaisesRegex(ValueError, "current_price"):
            quote.build_quote({**DEFAULT, "S": "-1"})

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


if __name__ == "__main__":
    unittest.main()
