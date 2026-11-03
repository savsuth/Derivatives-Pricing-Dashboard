<h1 align="center">Derivatives Pricing Dashboard</h1>

<p align="center">
  Black–Scholes prices and Greeks for European options, with every Greek checked live on the page.
</p>

<p align="center">
  <a href="https://derivatives-pricing-dashboard.vercel.app"><strong>Open the live demo</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" /></a>
</p>

<p align="center">
  <img src="Img-1.png" alt="The dashboard: inputs on the left, pricing equations and a table of prices and Greeks on the right" width="85%" />
</p>

## Table of Contents

- [About](#about)
- [Features](#features)
- [Getting Started](#getting-started)
- [Running the Tests](#running-the-tests)
- [Usage](#usage)
- [Edge Cases](#edge-cases)
- [Project Layout](#project-layout)
- [Deployment](#deployment)
- [Limitations](#limitations)
- [Built Using](#built-using)
- [Author](#author)
- [License](#license)

## About

An option's price and its Greeks (how the price responds to changes in its inputs) can look plausible and still be wrong. Many Black–Scholes calculators also fail at the edges, returning `NaN` or a wrong number when volatility or time to maturity is zero.

This project treats correctness as the feature. All numbers come from one tested model, `BlackScholes.py`. The page shows its work: beside each Greek is the difference between the closed-form value and a fresh numerical estimate, recalculated whenever an input changes.

The page is static. A small Vercel Python function does the pricing and returns JSON, and the browser contains no pricing math.

## Features

- **Prices and Greeks:** call and put prices, delta, theta and rho, plus gamma, vega, vanna, volga and charm.
- **Live checks:** each Greek is compared with a bump-and-reprice of the same model, and the prices are checked with put–call parity.
- **Heatmaps:** call and put values across spot and volatility, with a marker at the current inputs.
- **Defined edge cases:** zero volatility, expiry and negative rates return defined values. See [Edge Cases](#edge-cases).
- **Implied volatility:** available from Python, with a guarded Newton solver that rejects prices outside the no-arbitrage bounds. It is not in the page yet.

<p align="center">
  <img src="Img-2.png" alt="Call and put heatmaps across spot and volatility, followed by notes on the model, units and checks" width="85%" />
</p>

## Getting Started

### Prerequisites

- Python 3.12 or newer, because the pinned NumPy version requires it
- pip

### Installing

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/savsuth/Derivatives-Pricing-Dashboard.git
cd Derivatives-Pricing-Dashboard
python3 -m venv .venv
source .venv/bin/activate
```

Install the runtime and test dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Start the local server:

```bash
python3 dev_server.py
```

Open <http://localhost:3000>. To use another port, pass it as an argument, for example `python3 dev_server.py 8000`.

`dev_server.py` serves the static files and sends `/api/quote` to the same handler that runs on Vercel.

## Running the Tests

```bash
python3 -m unittest discover -s tests
```

The suite has 50 tests and checks the model against independent references:

| File | What it checks |
| --- | --- |
| `tests/test_black_scholes.py` | Textbook values, finite differences, complex-step derivatives, edge-case limits, floating-point underflow and the implied volatility solver |
| `tests/test_oracle_and_properties.py` | QuantLib 1.44 on 2,000 random inputs, plus property-based tests of price bounds, put–call parity, strike monotonicity and convexity, and implied volatility repricing |
| `tests/test_quote_api.py` | The API's JSON output, input validation and HTTP status codes |

QuantLib 1.44's `BlackCalculator::volga` divides by `stdDev` instead of volatility, which makes its result too small by a factor of √T. The oracle test corrects for this, and a separate complex-step test checks volga independently.

## Usage

### In the browser

Change any value in the Inputs panel, and the equations, table and heatmaps update. The last column of Table 1 shows how closely each check agrees.

| Greek | Unit shown |
| --- | --- |
| Delta, gamma | Per 1.00 change in spot |
| Vega | Per volatility point |
| Rho | Per 1% change in the rate |
| Theta | Per calendar day |
| Vanna | Change in delta per volatility point |
| Volga | Change in vega per volatility point |
| Charm | Change in delta per calendar day |

### From the API

Send a `GET` request to `/api/quote`:

```bash
curl "https://derivatives-pricing-dashboard.vercel.app/api/quote?S=100&K=100&T=1&sigma=0.2&r=0.05"
```

| Parameter | Required | Meaning | Default |
| --- | --- | --- | --- |
| `S` | Yes | Spot price | |
| `K` | Yes | Strike price | |
| `T` | Yes | Time to maturity in years | |
| `sigma` | Yes | Volatility, where 0.2 means 20% | |
| `r` | Yes | Risk-free rate, where 0.05 means 5% | |
| `spot_min` | No | Lowest heatmap spot | `0.6 * S` |
| `spot_max` | No | Highest heatmap spot | `1.4 * S` |
| `vol_min` | No | Lowest heatmap volatility | `0.05` |
| `vol_max` | No | Highest heatmap volatility | `max(sigma, 0.6)` |

The response is JSON with the keys `inputs`, `degenerate`, `prices`, `greeks`, `checks` and `heatmap`. For the request above, the prices are:

```json
{ "call": 10.450583572185565, "put": 5.573526022256971 }
```

Invalid inputs return status 400 with an `error` message. JSON has no infinity value, so an infinite Greek is returned as the string `"inf"` or `"-inf"`. A check is `null` when no bump can be made because σ√T = 0.

### From Python

Run this from the repository root:

```python
from BlackScholes import BlackScholes

# Arguments: time to maturity, strike, spot, volatility, rate
model = BlackScholes(1, 100, 100, 0.2, 0.05)
call, put = model.run()
print(round(call, 4), round(put, 4))  # 10.4506 5.5735
print(round(model.call_delta, 4), round(model.vega, 4))  # 0.6368 0.3752

# Arguments: option price, time to maturity, strike, spot, rate
sigma = BlackScholes.implied_volatility(call, 1, 100, 100, 0.05)
print(round(sigma, 6))  # 0.2
```

Inputs can also be NumPy arrays, which broadcast. The heatmaps use this to price a whole grid in one call:

```python
import numpy as np
from BlackScholes import BlackScholes

spots = np.linspace(60, 140, 10)
vols = np.linspace(0.05, 0.6, 10)
calls, puts = BlackScholes(1, 100, spots[None, :], vols[:, None], 0.05).run()
print(calls.shape)  # (10, 10)
```

In one local measurement, this was 37 times faster than the original Python loop on a 10x10 grid and 513 times faster on a 100x100 grid.

## Edge Cases

| Input | Result |
| --- | --- |
| σ = 0, T > 0 | The payoff is certain, so the call is `max(S - K * exp(-r * T), 0)`. With S = K = 100, T = 1 and r = 0.05, that is 4.87705755. |
| T = 0 | Each option is worth its intrinsic value, so the call is `max(S - K, 0)`. |
| S exactly at the discounted strike, with σ = 0 or T = 0 | Call delta is 0.5, put delta is -0.5, and gamma is infinite. |
| r < 0 | Supported. |
| σ√T too small for floating point | Treated as σ = 0. |
| T < 0, σ < 0, S ≤ 0, K ≤ 0, or a non-finite value | Python raises `ValueError`, and the API returns status 400. |

When σ = 0 or T = 0, every Greek reports its limit as σ or T approaches zero. Limits that diverge are returned as positive or negative infinity.

## Project Layout

| Path | Purpose |
| --- | --- |
| `BlackScholes.py` | The pricing model, Greeks and implied volatility solver |
| `api/quote.py` | Vercel function that returns the model's results as JSON |
| `index.html`, `styles.css`, `app.js` | The page, with no build step |
| `dev_server.py` | Local server that stands in for Vercel |
| `tests/` | Unit, oracle, property and API tests |
| `vercel.json`, `.vercelignore`, `.python-version` | Deployment settings |
| `PRODUCT.md`, `DESIGN.md` | Product and visual design records |

## Deployment

The project deploys to Vercel as static files plus one Python function. Vercel installs the function's dependencies from `requirements.txt`, and `.vercelignore` limits the upload to the files the site needs.

Project names on Vercel must be lowercase, so create and link the project by name:

```bash
npx vercel login
npx vercel project add derivatives-pricing-dashboard
npx vercel link --yes --project derivatives-pricing-dashboard
npx vercel deploy --prod --yes
```

Vercel CLI 62.2.0 could not run this Python function with `vercel dev`, so use `python3 dev_server.py` for local work.

## Limitations

- It prices European options on assets that pay no dividends.
- Volatility and the interest rate are constant, as the Black–Scholes model assumes.
- You enter all inputs by hand. The project does not use market data.
- The first request after an idle period can take a few seconds while the function starts.
- It is for education and is not investment advice.

## Built Using

- [NumPy](https://numpy.org/) and [SciPy](https://scipy.org/) for the model
- [Vercel Python Functions](https://vercel.com/docs/functions/runtimes/python) for the API
- HTML, CSS and JavaScript for the page, with [KaTeX](https://katex.org/) for equations and [STIX Two Text](https://www.stixfonts.org/) for type
- [QuantLib](https://www.quantlib.org/) and [Hypothesis](https://hypothesis.readthedocs.io/) for testing

## Author

[Aasav Suthar](https://github.com/savsuth)

## License

This project is available under the [MIT License](LICENSE).
