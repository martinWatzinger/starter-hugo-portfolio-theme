"""
Synthetic Control Study: Germany and the Gas Price Shock from the Russia-Ukraine War
======================================================================================
Replicating the approach of Born, Müller, Schularick & Sedlacek (2019),
"The Costs of Economic Nationalism: Evidence from the Brexit Experiment",
The Economic Journal, 129(623), 2722-2744.

Treatment event : Russia's invasion of Ukraine (Feb 24, 2022), triggering a
                  severe energy/gas price shock for Germany.
Outcome         : Real GDP per capita (index, 2019 = 100; based on World Bank
                  NY.GDP.PCAP.PP.KD, constant 2017 international $ PPP).
Donor pool      : 28 OECD countries (excluding Germany, Russia, Ukraine, and
                  Ireland whose GDP is distorted by multinational IP transfers).
Pre-treatment   : 2000–2021.
Post-treatment  : 2022–2023.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.optimize import minimize
import warnings
warnings.filterwarnings("ignore")

from gdp_data import build_index_series

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
wide = build_index_series()
print(f"Data: {len(wide)} years ({wide.index.min()}–{wide.index.max()}), "
      f"{wide.shape[1]} countries")

TREATED = "DEU"
TREATMENT_YEAR = 2022
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

donors_available = [c for c in wide.columns if c != TREATED]
years      = wide.index.values
pre_mask   = years < TREATMENT_YEAR
post_mask  = years >= TREATMENT_YEAR

y_treated  = wide[TREATED].values
X_donor    = wide[donors_available].values
X_pre      = X_donor[pre_mask]
y_pre      = y_treated[pre_mask]

print(f"Treated unit: {TREATED}")
print(f"Donor pool ({len(donors_available)}): {donors_available}")
print(f"Pre-treatment years: {years[pre_mask][0]}–{years[pre_mask][-1]}")
print(f"Post-treatment years: {years[post_mask][0]}–{years[post_mask][-1]}")

# ---------------------------------------------------------------------------
# 2. Synthetic Control  (Abadie-Diamond-Hainmueller, 2010)
#    min_w  || y_pre - X_pre @ w ||^2   s.t.  w >= 0, sum(w) = 1
# ---------------------------------------------------------------------------

def fit_synth(y_pre: np.ndarray, X_pre: np.ndarray,
              n_starts: int = 40) -> np.ndarray:
    """Return optimal non-negative donor weights that sum to 1."""
    J = X_pre.shape[1]

    def obj(w):
        r = y_pre - X_pre @ w
        return float(r @ r)

    def jac(w):
        return -2.0 * X_pre.T @ (y_pre - X_pre @ w)

    constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0,
                   "jac": lambda w: np.ones(J)}
    bounds = [(0.0, 1.0)] * J
    best_val, best_w = np.inf, np.ones(J) / J

    rng = np.random.default_rng(0)
    for _ in range(n_starts):
        w0 = rng.dirichlet(np.ones(J))
        res = minimize(obj, w0, jac=jac, method="SLSQP",
                       bounds=bounds, constraints=constraints,
                       options={"ftol": 1e-14, "maxiter": 5000})
        if res.fun < best_val:
            best_val, best_w = res.fun, res.x.copy()
    return best_w


print("\nFitting synthetic control…")
weights = fit_synth(y_pre, X_pre)

weight_series = pd.Series(weights, index=donors_available).sort_values(ascending=False)
print("\nWeights (> 0.5%):")
top_weights = weight_series[weight_series > 0.005]
print(top_weights.round(3).to_string())

synth     = X_donor @ weights
gap       = y_treated - synth
post_gaps = gap[post_mask]
post_years = years[post_mask]

pre_rmspe  = float(np.sqrt(np.mean((y_pre - X_pre @ weights) ** 2)))
post_rmspe = float(np.sqrt(np.mean(post_gaps ** 2)))
print(f"\nPre-treatment RMSPE : {pre_rmspe:.4f} index pts")
print(f"Post-treatment RMSPE: {post_rmspe:.4f} index pts")
print(f"Post/Pre ratio      : {post_rmspe/pre_rmspe:.2f}")
for yr, g in zip(post_years, post_gaps):
    print(f"  {yr}: gap = {g:+.2f} index pts  ({g:.1f}% of 2019 level)")

# ---------------------------------------------------------------------------
# 3. Placebo / permutation inference
# ---------------------------------------------------------------------------
print("\nRunning placebo tests…")

placebo_gaps  = {}
placebo_rmspe = {}

for donor in donors_available:
    other = [c for c in donors_available if c != donor]
    y_pb_pre = wide[donor].values[pre_mask]
    X_pb_pre = wide[other].values[pre_mask]
    X_pb_all = wide[other].values

    w_pb = fit_synth(y_pb_pre, X_pb_pre, n_starts=10)
    g_pb = wide[donor].values - (X_pb_all @ w_pb)
    placebo_gaps[donor]  = g_pb
    placebo_rmspe[donor] = float(np.sqrt(np.mean(g_pb[pre_mask] ** 2)))

# Post/pre RMSPE ratios
def ratio(pre_g, post_g):
    r = float(np.sqrt(np.mean(pre_g ** 2)))
    return float(np.sqrt(np.mean(post_g ** 2))) / r if r > 0 else np.nan

ratios = {"DEU": post_rmspe / pre_rmspe}
for donor in donors_available:
    g = placebo_gaps[donor]
    ratios[donor] = ratio(g[pre_mask], g[post_mask])

ratio_series = pd.Series(ratios).dropna().sort_values(ascending=False)
p_val = (ratio_series >= ratio_series["DEU"]).mean()
rank  = int((ratio_series >= ratio_series["DEU"]).sum())
print(f"\nPost/Pre RMSPE ratio – Germany: {ratios['DEU']:.2f}")
print(f"Permutation p-value: {p_val:.3f} ({rank} / {len(ratio_series)} units ≥ Germany)")

# ---------------------------------------------------------------------------
# 4. Figures
# ---------------------------------------------------------------------------
BLUE  = "#1f4e79"
RED   = "#c0392b"
GREY  = "#b0b0b0"
DARK  = "#1a1a1a"

plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "figure.dpi":         150,
})

out_dir = os.path.join(BASE_DIR, "static", "germany-gas-shock")
os.makedirs(out_dir, exist_ok=True)

# ------ Figure 1: Actual vs Synthetic Germany --------------------------------
fig1, ax1 = plt.subplots(figsize=(9, 5))

ax1.plot(years, y_treated, color=BLUE, lw=2.4, label="Germany (actual)", zorder=5)
ax1.plot(years, synth,     color=RED,  lw=2.4, linestyle="--",
         label="Synthetic Germany", zorder=5)
ax1.axvline(TREATMENT_YEAR - 0.5, color=DARK, lw=1.2, ls=":", zorder=4)
ax1.fill_between(years[post_mask], y_treated[post_mask], synth[post_mask],
                 color=RED, alpha=0.15, label="Estimated GDP loss")

ymin, ymax = ax1.get_ylim()
ax1.annotate(
    "Russia invades\nUkraine (Feb 2022)",
    xy=(TREATMENT_YEAR - 0.5, ymin + 4),
    xytext=(TREATMENT_YEAR - 5, ymin + 10),
    arrowprops=dict(arrowstyle="->", color=DARK, lw=1.0),
    fontsize=8.5, color=DARK,
)
ax1.set_xlabel("Year", fontsize=11)
ax1.set_ylabel("Real GDP per capita (index, 2019 = 100)", fontsize=11)
ax1.set_title(
    "Germany vs Synthetic Germany\n"
    "The Cost of the Gas Price Shock from the Russia–Ukraine War",
    fontsize=12.5, fontweight="bold", pad=14,
)
ax1.legend(frameon=False, fontsize=10)
ax1.set_xlim(2000, 2023)
fig1.tight_layout()
p1 = os.path.join(out_dir, "gdp_actual_vs_synthetic.png")
fig1.savefig(p1, bbox_inches="tight")
print(f"\nSaved: {p1}")

# ------ Figure 2: GDP gap ----------------------------------------------------
fig2, ax2 = plt.subplots(figsize=(9, 4))

ax2.axhline(0, color=DARK, lw=0.9, ls="--")
ax2.plot(years, gap, color=BLUE, lw=2.4)
ax2.fill_between(years, gap, 0, where=(gap < 0), color=RED,  alpha=0.22,
                 label="Below counterfactual")
ax2.fill_between(years, gap, 0, where=(gap >= 0), color=BLUE, alpha=0.10,
                 label="Above counterfactual")
ax2.axvline(TREATMENT_YEAR - 0.5, color=DARK, lw=1.2, ls=":")

for yr, g in zip(post_years, post_gaps):
    ax2.annotate(f"{g:.1f}",
                 xy=(yr, g),
                 xytext=(yr + 0.1, g - 0.5 if g < 0 else g + 0.4),
                 fontsize=9, color=RED if g < 0 else BLUE)

ax2.set_xlabel("Year", fontsize=11)
ax2.set_ylabel("Gap (index points)", fontsize=11)
ax2.set_title(
    "Germany – Synthetic Germany: GDP per Capita Gap",
    fontsize=12.5, fontweight="bold", pad=14,
)
ax2.legend(frameon=False, fontsize=10)
ax2.set_xlim(2000, 2023)
fig2.tight_layout()
p2 = os.path.join(out_dir, "gdp_gap.png")
fig2.savefig(p2, bbox_inches="tight")
print(f"Saved: {p2}")

# ------ Figure 3: Placebo tests ----------------------------------------------
threshold = 5.0 * pre_rmspe
fig3, ax3 = plt.subplots(figsize=(9, 5))

plotted = 0
for donor, g in placebo_gaps.items():
    if placebo_rmspe[donor] <= threshold:
        ax3.plot(years, g, color=GREY, lw=0.8, alpha=0.65, zorder=1)
        plotted += 1

ax3.plot(years, gap, color=BLUE, lw=2.8, label="Germany", zorder=5)
ax3.axhline(0, color=DARK, lw=0.9, ls="--")
ax3.axvline(TREATMENT_YEAR - 0.5, color=DARK, lw=1.2, ls=":")

de_patch = mpatches.Patch(color=BLUE, label="Germany")
pb_patch = mpatches.Patch(color=GREY, alpha=0.65,
                           label=f"Donor placebos (n={plotted}, pre-RMSPE ≤ 5× Germany's)")
ax3.legend(handles=[de_patch, pb_patch], frameon=False, fontsize=10)
ax3.set_xlabel("Year", fontsize=11)
ax3.set_ylabel("Gap (index points)", fontsize=11)
ax3.set_title(
    "Placebo Tests: Germany vs Donor Countries",
    fontsize=12.5, fontweight="bold", pad=14,
)
ax3.set_xlim(2000, 2023)
fig3.tight_layout()
p3 = os.path.join(out_dir, "placebo_tests.png")
fig3.savefig(p3, bbox_inches="tight")
print(f"Saved: {p3}")

# ------ Figure 4: Weights bar chart -----------------------------------------
fig4, ax4 = plt.subplots(figsize=(8, 5))
top_w = weight_series[weight_series > 0.005].sort_values()
colors = [BLUE if v > 0.10 else "#5b8db8" for v in top_w.values]
bars = ax4.barh(top_w.index, top_w.values * 100, color=colors, edgecolor="white")
ax4.set_xlabel("Weight (%)", fontsize=11)
ax4.set_title("Synthetic Germany: Donor Country Weights", fontsize=12.5,
              fontweight="bold", pad=14)
for bar, val in zip(bars, top_w.values):
    ax4.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
             f"{val*100:.1f}%", va="center", fontsize=9)
ax4.set_xlim(0, top_w.values.max() * 100 * 1.25)
fig4.tight_layout()
p4 = os.path.join(out_dir, "donor_weights.png")
fig4.savefig(p4, bbox_inches="tight")
print(f"Saved: {p4}")

# ---------------------------------------------------------------------------
# 5. Save summary statistics (for Hugo page)
# ---------------------------------------------------------------------------
summary = {
    "pre_rmspe":      round(pre_rmspe, 4),
    "post_rmspe":     round(post_rmspe, 4),
    "ratio":          round(post_rmspe / pre_rmspe, 2),
    "p_value":        round(float(p_val), 3),
    "n_placebos":     len(ratio_series) - 1,
    "rank":           rank,
    "avg_gap_post":   round(float(post_gaps.mean()), 2),
    "gaps": {
        int(yr): round(float(g), 2)
        for yr, g in zip(post_years, post_gaps)
    },
    "weights": {
        iso: round(float(w), 4)
        for iso, w in weight_series[weight_series > 0.005].items()
    },
}
stats_path = os.path.join(os.path.dirname(__file__), "summary_stats.json")
with open(stats_path, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary stats:\n{json.dumps(summary, indent=2)}")
print("\nDone.")
