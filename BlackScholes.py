import numpy as np
from numpy import exp, sqrt, log
from scipy.stats import norm

INV_SQRT_2PI = 1.0 / sqrt(2.0 * np.pi)


class BlackScholes:
    """European Black-Scholes prices and Greeks, no dividends.

    Inputs may be scalars or NumPy arrays; arrays broadcast and every output
    then has the broadcast shape. Scalar inputs give float outputs.

    Greeks are in trader units: vega and rho per 1 percentage point of sigma
    or r, theta and charm (d delta / dt) per calendar day, vanna (d delta /
    d sigma) per vol point, volga (d vega / d sigma) per vol point squared.

    Degenerate cases (T == 0 or sigma == 0) are a deterministic payoff against
    the discounted strike K * exp(-r * T). Every Greek there is its limit as
    sigma -> 0 (or T -> 0); exactly at the kink delta is 0.5 / -0.5 and gamma is
    +inf. Negative rates are valid. Invalid inputs (T < 0, sigma < 0, S <= 0,
    K <= 0, non-finite) raise ValueError.
    """

    def __init__(
        self,
        time_to_maturity,
        strike,
        current_price,
        volatility,
        interest_rate,
    ):
        self.time_to_maturity = time_to_maturity
        self.strike = strike
        self.current_price = current_price
        self.volatility = volatility
        self.interest_rate = interest_rate

    def run(
        self,
    ):
        T, K, S, sigma, r = np.broadcast_arrays(
            *(np.asarray(x, dtype=float) for x in (
                self.time_to_maturity, self.strike, self.current_price,
                self.volatility, self.interest_rate,
            ))
        )
        scalar = T.ndim == 0

        if not np.all(np.isfinite([T, K, S, sigma, r])):
            raise ValueError("inputs must be finite")
        if np.any(T < 0) or np.any(sigma < 0) or np.any(S <= 0) or np.any(K <= 0):
            raise ValueError(
                "require time_to_maturity >= 0, volatility >= 0, strike > 0, current_price > 0"
            )

        discounted_strike = K * exp(-r * T)

        # Regular Black-Scholes wherever T * sigma * sqrt(T) (the smallest denominator, in
        # charm) is representable and d1 is finite; other cells are numerically the
        # sigma -> 0 limit below.
        raw_vol_sqrt_t = sigma * sqrt(T)
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            raw_d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / raw_vol_sqrt_t
        regular = (T * raw_vol_sqrt_t > 0) & np.isfinite(raw_d1)
        vol_sqrt_t = np.where(regular, raw_vol_sqrt_t, 1.0)
        safe_t = np.where(regular, T, 1.0)
        safe_sigma = np.where(regular, sigma, 1.0)
        d1 = np.where(regular, raw_d1, 0.0)
        d2 = d1 - vol_sqrt_t
        # Overflow is expected near the sigma -> 0 limit: d1 ** 2 overflows where the
        # density is 0 anyway, and Greeks that exceed float range become +/-inf,
        # matching the degenerate-case convention.
        with np.errstate(over="ignore"):
            pdf_d1 = norm.pdf(d1)
            decay = -S * pdf_d1 * sigma / (2.0 * sqrt(safe_t))
            reg = dict(
                call_price=S * norm.cdf(d1) - discounted_strike * norm.cdf(d2),
                put_price=discounted_strike * norm.cdf(-d2) - S * norm.cdf(-d1),
                call_delta=norm.cdf(d1),
                gamma=pdf_d1 / (S * vol_sqrt_t),
                vega=S * pdf_d1 * sqrt(T),
                call_theta=decay - r * discounted_strike * norm.cdf(d2),
                put_theta=decay + r * discounted_strike * norm.cdf(-d2),
                call_rho=T * discounted_strike * norm.cdf(d2),
                put_rho=-T * discounted_strike * norm.cdf(-d2),
                vanna=-pdf_d1 * d2 / safe_sigma,
                volga=S * pdf_d1 * sqrt(T) * d1 * d2 / safe_sigma,
                charm=-pdf_d1 * (2.0 * r * T - d2 * vol_sqrt_t) / (2.0 * safe_t * vol_sqrt_t),
            )

        # Deterministic payoff: sign of S against the discounted strike, kink at equality.
        moneyness = S - discounted_strike
        kink = moneyness == 0
        deg_call_delta = np.where(moneyness > 0, 1.0, np.where(kink, 0.5, 0.0))
        deg_put_delta = deg_call_delta - 1.0
        # At the kink the threshold drifts at rate r + sigma^2 / 2, so charm diverges unless that is 0.
        drift = r + 0.5 * sigma ** 2
        expiry_kink = kink & (T == 0) & (sigma > 0)  # time value ~ sigma * sqrt(T) decays infinitely fast
        kink_charm = np.where(drift > 0, -np.inf, np.where(drift < 0, np.inf, 0.0))
        deg = dict(
            call_price=np.maximum(moneyness, 0.0),
            put_price=np.maximum(-moneyness, 0.0),
            call_delta=deg_call_delta,
            gamma=np.where(kink, np.inf, 0.0),
            vega=np.where(kink, S * sqrt(T) * INV_SQRT_2PI, 0.0),
            call_theta=np.where(expiry_kink, -np.inf, -r * discounted_strike * deg_call_delta),
            put_theta=np.where(expiry_kink, -np.inf, -r * discounted_strike * deg_put_delta),
            call_rho=T * discounted_strike * deg_call_delta,
            put_rho=T * discounted_strike * deg_put_delta,
            vanna=np.where(kink, sqrt(T) * INV_SQRT_2PI / 2.0, 0.0),
            volga=np.zeros_like(S),
            charm=np.where(kink, kink_charm, 0.0),
        )

        out = {k: np.where(regular, reg[k], deg[k]) for k in reg}
        out["put_delta"] = out["call_delta"] - 1.0
        out["vega"] = out["vega"] / 100.0
        out["call_rho"] = out["call_rho"] / 100.0
        out["put_rho"] = out["put_rho"] / 100.0
        out["call_theta"] = out["call_theta"] / 365.0
        out["put_theta"] = out["put_theta"] / 365.0
        out["vanna"] = out["vanna"] / 100.0
        out["volga"] = out["volga"] / 100.0 ** 2
        out["charm"] = out["charm"] / 365.0
        for name, value in out.items():
            setattr(self, name, float(value) if scalar else value)
        self.call_gamma = self.put_gamma = self.gamma
        return self.call_price, self.put_price

    calculate_prices = run

    @classmethod
    def implied_volatility(
        cls,
        price,
        time_to_maturity,
        strike,
        current_price,
        interest_rate,
        option="call",
        tol=1e-12,
        max_iter=200,
    ):
        """Volatility at which the model reproduces a market price (scalar inputs).

        Puts are converted to calls by put-call parity. Newton steps start from
        the Manaster-Koehler seed and stay inside a bisection bracket, so a step
        that overshoots (vega near zero far from the money) falls back to
        bisection. A price at the no-arbitrage lower bound returns 0.0; a price
        outside [lower bound, upper bound) or T == 0 raises ValueError.
        """
        if option not in ("call", "put"):
            raise ValueError("option must be 'call' or 'put'")
        T, K, S, r, price = (float(x) for x in (
            time_to_maturity, strike, current_price, interest_rate, price))
        if not np.isfinite(price):
            raise ValueError("price must be finite")
        if T <= 0:
            raise ValueError("implied volatility needs time_to_maturity > 0")
        cls(T, K, S, 0.0, r).run()  # validates the remaining inputs

        discounted_strike = K * exp(-r * T)
        call = price if option == "call" else price + S - discounted_strike
        lower = max(S - discounted_strike, 0.0)
        rounding = 1e-12 * max(S, discounted_strike)
        if call < lower - rounding or call >= S:
            raise ValueError(f"{option} price is outside the no-arbitrage bounds")
        if call <= lower + rounding:
            return 0.0  # no time value left to attribute to volatility

        def error_and_vega(sigma):
            model = cls(T, K, S, sigma, r)
            model.run()
            return model.call_price - call, model.vega * 100.0

        lo, hi = 0.0, 1.0
        while error_and_vega(hi)[0] < 0:
            lo, hi = hi, 2.0 * hi
        sigma = sqrt(2.0 * abs(log(S / K) + r * T) / T)
        if not lo < sigma < hi:
            sigma = 0.5 * (lo + hi)
        step = previous_step = hi - lo
        for _ in range(max_iter):
            error, vega = error_and_vega(sigma)
            if error == 0:
                return sigma
            if error > 0:
                hi = sigma
            else:
                lo = sigma
            # Bisect when Newton would leave the bracket or is not halving the step
            # (rtsafe, Numerical Recipes 9.4); otherwise take the Newton step.
            newton = sigma - error / vega if vega > 0 else lo
            previous_step = step
            if not lo < newton < hi or abs(2.0 * error) > abs(previous_step * vega):
                step = 0.5 * (hi - lo)
                sigma = lo + step
            else:
                step = sigma - newton
                sigma = newton
            if abs(step) < tol:
                return sigma
        raise RuntimeError("implied volatility did not converge")


if __name__ == "__main__":
    time_to_maturity = 2
    strike = 90
    current_price = 100
    volatility = 0.2
    interest_rate = 0.05

    # Black Scholes
    BS = BlackScholes(
        time_to_maturity=time_to_maturity,
        strike=strike,
        current_price=current_price,
        volatility=volatility,
        interest_rate=interest_rate)
    BS.run()