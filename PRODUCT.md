# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Hiring reviewers: recruiters, quant and fintech interviewers, and engineers who open the live demo from Aasav Suthar's resume or GitHub. They have a few minutes to judge two things: whether the pricing is correct, and whether the work is serious engineering rather than a tutorial copy.

## Product Purpose

An interactive European option pricer. It shows Black-Scholes call and put prices, the full set of Greeks, and price heatmaps across spot and volatility. Success means a reviewer leaves convinced that the numbers are right and that the author understands where the model breaks down.

## Positioning

Verified numerics. Every price and Greek is cross-checked against QuantLib, complex-step differentiation and no-arbitrage property tests. Degenerate inputs (sigma = 0, T = 0, negative rates, extreme underflow) return defined limits, never NaN. A generic Black-Scholes calculator cannot claim this.

## Operating Context

- Reached from a resume link or the GitHub README, often on a laptop and sometimes on a phone.
- The live demo is a static page on Vercel; prices come from a Vercel Python function, `api/quote.py`.
- It also runs locally with `python3 dev_server.py`.

## Capabilities and Constraints

- The pricing model is `BlackScholes` in `BlackScholes.py`. It is the single tested implementation; the UI must consume it, not reimplement it.
- It accepts scalar or NumPy-array inputs and returns:
  - call and put price and delta;
  - gamma, vega and call/put theta and rho;
  - vanna, volga and charm.
- Greeks are in trader units:
  - vega and rho per 1 percentage point;
  - theta and charm per calendar day;
  - vanna per vol point;
  - volga per vol point squared.
- `BlackScholes.implied_volatility` exists. The user did not ask for it to appear in the UI in this round.
- Heatmaps are drawn in the page as HTML cell grids from the API's broadcast prices. Plotly was declined.
- Stack, by user decision: no Streamlit. Static `index.html`, `styles.css` and `app.js` with no build step, plus one Vercel Python function (`api/quote.py`) that imports `BlackScholes.py`. No pricing math in JavaScript.

## Brand Commitments

- Dark UI ("keep ui black"), pinned by the user.
- Title: "Derivatives Pricing Dashboard".
- Credit footer: "Created by Aasav Suthar", with "For educational use only".

## Evidence on Hand

- Test suite in `tests/`: 50 unittest tests (including the API function and its HTTP handler), including a QuantLib 1.44 oracle on 2,000 random inputs and hypothesis no-arbitrage properties.
- A documented finding: QuantLib 1.44 `BlackCalculator::volga` is low by a factor of 1/sqrt(T).
- Measured heatmap speedup from broadcasting: 37x at 10x10 and 513x at 100x100, compared with the original loop.
- Live demo: https://derivatives-pricing-dashboard.vercel.app
- `Img-1.png` and `Img-2.png` are screenshots of the current UI.
- There are no testimonials, users or usage statistics; do not invent any.

## Product Principles

1. Correctness is the product. Show numbers with their units and with their edge-case behavior, never hide it.
2. Respect a short visit. The key result and the evidence for it should be readable without scrolling or prior explanation.
3. One source of truth. Every figure on screen comes from the tested model.
4. No overclaiming. State only what the tests and measurements support.
