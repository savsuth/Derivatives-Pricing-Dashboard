"""GET /api/quote: Black-Scholes prices, Greeks, live checks and heatmap grids as JSON.

Every number comes from the BlackScholes class; this module only parses inputs,
reprices with small bumps to check the closed-form Greeks, and serializes.
"""
import json
import math
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from BlackScholes import BlackScholes

GRID_SIZE = 10


def _number(params, name, default=None):
    raw = params.get(name, default)
    if raw is None:
        raise ValueError(f"missing parameter {name}")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _json_safe(value):
    if isinstance(value, float) and math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value


def build_quote(params):
    S, K, T = _number(params, "S"), _number(params, "K"), _number(params, "T")
    sigma, r = _number(params, "sigma"), _number(params, "r")
    spot_min = _number(params, "spot_min", 0.6 * S)
    spot_max = _number(params, "spot_max", 1.4 * S)
    vol_min = _number(params, "vol_min", 0.05)
    vol_max = _number(params, "vol_max", max(sigma, 0.6))

    def priced(**bumps):
        inputs = dict(time_to_maturity=T, strike=K, current_price=S, volatility=sigma, interest_rate=r)
        inputs.update(bumps)
        model = BlackScholes(**inputs)
        model.run()
        return model

    model = priced()  # raises ValueError for invalid model inputs
    if not 0 < spot_min < spot_max:
        raise ValueError("heatmap spots need 0 < spot_min < spot_max")
    if not 0 < vol_min < vol_max:
        raise ValueError("heatmap volatilities need 0 < vol_min < vol_max")
    degenerate = sigma * math.sqrt(T) == 0

    # Live check: reprice with small input bumps and compare with the closed-form Greeks.
    checks = dict.fromkeys(("delta", "theta", "rho", "gamma", "vega", "vanna", "volga", "charm"))
    checks["price"] = abs(model.call_price - model.put_price - (S - K * math.exp(-r * T)))
    if not degenerate:
        h = 1e-3 * S
        up, down = priced(current_price=S + h), priced(current_price=S - h)
        checks["delta"] = max(abs(model.call_delta - (up.call_price - down.call_price) / (2 * h)),
                              abs(model.put_delta - (up.put_price - down.put_price) / (2 * h)))
        checks["gamma"] = abs(model.gamma - (up.call_price - 2 * model.call_price + down.call_price) / h ** 2)
        h = min(1e-4, sigma / 2)
        up, down = priced(volatility=sigma + h), priced(volatility=sigma - h)
        checks["vega"] = abs(model.vega - (up.call_price - down.call_price) / (2 * h) / 100)
        checks["vanna"] = abs(model.vanna - (up.call_delta - down.call_delta) / (2 * h) / 100)
        checks["volga"] = abs(model.volga - (up.vega - down.vega) / (2 * h) / 100)
        h = min(1e-4, T / 2)
        up, down = priced(time_to_maturity=T + h), priced(time_to_maturity=T - h)
        checks["theta"] = max(abs(model.call_theta + (up.call_price - down.call_price) / (2 * h) / 365),
                              abs(model.put_theta + (up.put_price - down.put_price) / (2 * h) / 365))
        checks["charm"] = abs(model.charm + (up.call_delta - down.call_delta) / (2 * h) / 365)
        h = 1e-5
        up, down = priced(interest_rate=r + h), priced(interest_rate=r - h)
        checks["rho"] = max(abs(model.call_rho - (up.call_price - down.call_price) / (2 * h) / 100),
                            abs(model.put_rho - (up.put_price - down.put_price) / (2 * h) / 100))

    # One broadcast call: rows are volatilities, columns are spots.
    spots = np.linspace(spot_min, spot_max, GRID_SIZE)
    vols = np.linspace(vol_min, vol_max, GRID_SIZE)
    call_grid, put_grid = BlackScholes(T, K, spots[None, :], vols[:, None], r).calculate_prices()

    greek_names = ("call_delta", "put_delta", "call_theta", "put_theta", "call_rho", "put_rho",
                   "gamma", "vega", "vanna", "volga", "charm")
    return {
        "inputs": {"S": S, "K": K, "T": T, "sigma": sigma, "r": r},
        "degenerate": degenerate,
        "prices": {"call": model.call_price, "put": model.put_price},
        "greeks": {name: _json_safe(getattr(model, name)) for name in greek_names},
        "checks": checks,
        "heatmap": {"spots": spots.tolist(), "vols": vols.tolist(),
                    "call": call_grid.tolist(), "put": put_grid.tolist()},
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        try:
            status, body = 200, build_quote(params)
        except ValueError as error:
            status, body = 400, {"error": str(error)}
        payload = json.dumps(body, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass  # keep test and function logs quiet
