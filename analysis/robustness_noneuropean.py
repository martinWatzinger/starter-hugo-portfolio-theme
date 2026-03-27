"""
Robustness Check: Non-European Donor Pool
==========================================
Repeats the Germany gas-shock synthetic control analysis using only
geographically distant, non-European OECD economies as donors:
  USA, Canada, Japan, South Korea, Australia, New Zealand.

These countries were NOT directly exposed to the European energy crisis,
so they are clean counterfactuals. The main analysis uses the full 28-country
OECD pool, which includes countries partially contaminated by the gas shock
(Austria, Finland, Sweden, …), biasing the counterfactual *downward* and
therefore *understating* the true German loss.

Outputs
-------
static/germany-gas-shock/robustness_comparison.png   — baseline vs robustness
static/germany-gas-shock/robustness_gap.png          — robustness gap only
static/germany-gas-shock/main_with_ci.png            — main result + placebo CI
analysis/summary_robustness.json
"""

import json, sys, os
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
from germany_gas_shock_synthetic_control import (
    fit_synth, gap as baseline_gap, synth as baseline_synth,
    y_treated, years, pre_mask, post_mask, post_years, post_gaps,
    pre_rmspe as baseline_pre_rmspe, placebo_gaps,
)

# ---------------------------------------------------------------------------
# 0. Settings
# ---------------------------------------------------------------------------
BLUE   = "#1f4e79"
RED    = "#c0392b"
GREEN  = "#1a7a4a"
GREY   = "#b0b0b0"
DARK   = "#1a1a1a"
ORANGE = "#d35400"

TREATMENT_YEAR = 2022
BASE_DIR  = os.path.join(os.path.dirname(__file__), "..")
out_dir   = os.path.join(BASE_DIR, "static", "germany-gas-shock")
os.makedirs(out_dir, exist_ok=True)

plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "figure.dpi":        150,
})

# ---------------------------------------------------------------------------
# 1. Robustness: non-European donor pool
# ---------------------------------------------------------------------------
NON_EU_DONORS = ["USA", "CAN", "JPN", "KOR", "AUS", "NZL"]

wide = build_index_series()
rob_donors = [c for c in NON_EU_DONORS if c in wide.columns]
print(f"Non-European donor pool ({len(rob_donors)}): {rob_donors}")

X_rob_pre = wide[rob_donors].values[pre_mask]
X_rob_all = wide[rob_donors].values
y_pre_arr  = y_treated[pre_mask]

print("Fitting robustness synthetic control…")
w_rob  = fit_synth(y_pre_arr, X_rob_pre, n_starts=60)
synth_rob = X_rob_all @ w_rob
gap_rob   = y_treated - synth_rob

pre_rmspe_rob  = float(np.sqrt(np.mean((y_pre_arr - X_rob_pre @ w_rob) ** 2)))
post_rmspe_rob = float(np.sqrt(np.mean(gap_rob[post_mask] ** 2)))
ratio_rob      = post_rmspe_rob / pre_rmspe_rob

w_series_rob = pd.Series(w_rob, index=rob_donors).sort_values(ascending=False)
print("\nRobustness weights:")
print(w_series_rob.round(3).to_string())
print(f"\nPre-treatment RMSPE  : {pre_rmspe_rob:.4f}")
print(f"Post-treatment RMSPE : {post_rmspe_rob:.4f}")
print(f"Post/Pre ratio       : {ratio_rob:.2f}")
for yr, g in zip(post_years, gap_rob[post_mask]):
    print(f"  {yr}: gap = {g:+.2f} pp  ({g:.1f}% of 2019 level)")

# Placebo inference for robustness (each non-EU donor as pseudo-treated)
rob_placebo_gaps  = {}
rob_placebo_rmspe = {}
for donor in rob_donors:
    others = [c for c in rob_donors if c != donor]
    if len(others) < 2:
        continue
    y_pb   = wide[donor].values[pre_mask]
    X_pb_p = wide[others].values[pre_mask]
    X_pb_a = wide[others].values
    w_pb   = fit_synth(y_pb, X_pb_p, n_starts=10)
    g_pb   = wide[donor].values - (X_pb_a @ w_pb)
    rob_placebo_gaps[donor]  = g_pb
    rob_placebo_rmspe[donor] = float(np.sqrt(np.mean(g_pb[pre_mask] ** 2)))

def post_pre_ratio(g):
    r = float(np.sqrt(np.mean(g[pre_mask] ** 2)))
    return float(np.sqrt(np.mean(g[post_mask] ** 2))) / r if r > 0 else np.nan

ratios_rob = {"DEU": ratio_rob}
for d, g in rob_placebo_gaps.items():
    ratios_rob[d] = post_pre_ratio(g)
ratio_series_rob = pd.Series(ratios_rob).dropna().sort_values(ascending=False)
p_val_rob = (ratio_series_rob >= ratio_rob).mean()
print(f"\nRobustness permutation p-value: {p_val_rob:.3f} "
      f"({int((ratio_series_rob >= ratio_rob).sum())} / {len(ratio_series_rob)} ≥ Germany)")

# ---------------------------------------------------------------------------
# 2. Confidence envelope from the full-pool placebo distribution
# ---------------------------------------------------------------------------
# At each year, compute the 5th–95th percentile of placebo gaps
placebo_matrix = np.column_stack([placebo_gaps[d] for d in placebo_gaps])
ci_lo = np.percentile(placebo_matrix, 5,  axis=1)
ci_hi = np.percentile(placebo_matrix, 95, axis=1)

# ---------------------------------------------------------------------------
# 3. Figures
# ---------------------------------------------------------------------------

# --- Figure A: Main result with 90% placebo confidence envelope -------------
fig_ci, ax_ci = plt.subplots(figsize=(9, 5))

ax_ci.fill_between(years, ci_lo, ci_hi, color=GREY, alpha=0.35,
                   label="90% placebo interval")
ax_ci.axhline(0, color=DARK, lw=0.9, ls="--")
ax_ci.plot(years, baseline_gap, color=BLUE, lw=2.5, label="Germany", zorder=5)
ax_ci.axvline(TREATMENT_YEAR - 0.5, color=DARK, lw=1.2, ls=":")

for yr, g in zip(post_years, post_gaps):
    ax_ci.annotate(f"{g:.1f}",
                   xy=(yr, g), xytext=(yr + 0.1, g - 0.6),
                   fontsize=9, color=RED)

ax_ci.set_xlabel("Year", fontsize=11)
ax_ci.set_ylabel("Gap (index points)", fontsize=11)
ax_ci.set_title(
    "Germany–Synthetic Germany Gap with 90% Placebo Interval\n"
    "(shaded band = 5th–95th percentile of donor-country placebo gaps)",
    fontsize=11.5, fontweight="bold", pad=14,
)
ax_ci.legend(frameon=False, fontsize=10)
ax_ci.set_xlim(2000, 2023)
fig_ci.tight_layout()
p_ci = os.path.join(out_dir, "main_with_ci.png")
fig_ci.savefig(p_ci, bbox_inches="tight")
print(f"\nSaved: {p_ci}")

# --- Figure B: Baseline vs Robustness (actual vs both synthetics) -----------
fig_cmp, ax_cmp = plt.subplots(figsize=(9, 5))

ax_cmp.plot(years, y_treated,     color=BLUE,   lw=2.4,
            label="Germany (actual)", zorder=5)
ax_cmp.plot(years, baseline_synth, color=RED,    lw=2.0, ls="--",
            label="Synthetic Germany — full OECD pool (baseline)", zorder=4)
ax_cmp.plot(years, synth_rob,      color=GREEN,  lw=2.0, ls="-.",
            label="Synthetic Germany — non-European pool (robustness)", zorder=4)
ax_cmp.axvline(TREATMENT_YEAR - 0.5, color=DARK, lw=1.2, ls=":", zorder=3)

# shade the robustness gap (larger)
ax_cmp.fill_between(years[post_mask],
                    y_treated[post_mask], synth_rob[post_mask],
                    color=GREEN, alpha=0.10, label="Robustness gap")

ax_cmp.set_xlabel("Year", fontsize=11)
ax_cmp.set_ylabel("Real GDP per capita (index, 2019 = 100)", fontsize=11)
ax_cmp.set_title(
    "Robustness Check: Baseline vs Non-European Donor Pool",
    fontsize=12.5, fontweight="bold", pad=14,
)
ax_cmp.legend(frameon=False, fontsize=9.5, loc="upper left")
ax_cmp.set_xlim(2000, 2023)
fig_cmp.tight_layout()
p_cmp = os.path.join(out_dir, "robustness_comparison.png")
fig_cmp.savefig(p_cmp, bbox_inches="tight")
print(f"Saved: {p_cmp}")

# --- Figure C: Robustness gap only ------------------------------------------
fig_rg, ax_rg = plt.subplots(figsize=(9, 4))

ax_rg.axhline(0, color=DARK, lw=0.9, ls="--")
ax_rg.plot(years, gap_rob, color=GREEN, lw=2.4, label="Gap (non-European pool)")
ax_rg.fill_between(years, gap_rob, 0,
                   where=(gap_rob < 0), color=GREEN, alpha=0.18)
ax_rg.axvline(TREATMENT_YEAR - 0.5, color=DARK, lw=1.2, ls=":")

for yr, g in zip(post_years, gap_rob[post_mask]):
    ax_rg.annotate(f"{g:.1f}",
                   xy=(yr, g), xytext=(yr + 0.1, g - 0.6),
                   fontsize=9, color=GREEN)

ax_rg.set_xlabel("Year", fontsize=11)
ax_rg.set_ylabel("Gap (index points)", fontsize=11)
ax_rg.set_title(
    "Robustness Gap: Germany vs Synthetic Germany (Non-European Donors)",
    fontsize=12, fontweight="bold", pad=14,
)
ax_rg.legend(frameon=False, fontsize=10)
ax_rg.set_xlim(2000, 2023)
fig_rg.tight_layout()
p_rg = os.path.join(out_dir, "robustness_gap.png")
fig_rg.savefig(p_rg, bbox_inches="tight")
print(f"Saved: {p_rg}")

# ---------------------------------------------------------------------------
# 4. Save summary
# ---------------------------------------------------------------------------
summary_rob = {
    "donor_pool":         rob_donors,
    "pre_rmspe":          round(pre_rmspe_rob, 4),
    "post_rmspe":         round(post_rmspe_rob, 4),
    "ratio":              round(ratio_rob, 2),
    "p_value":            round(float(p_val_rob), 3),
    "n_placebos":         len(ratio_series_rob) - 1,
    "avg_gap_post":       round(float(gap_rob[post_mask].mean()), 2),
    "gaps": {
        int(yr): round(float(g), 2)
        for yr, g in zip(post_years, gap_rob[post_mask])
    },
    "weights": {
        iso: round(float(w), 4)
        for iso, w in w_series_rob[w_series_rob > 0.005].items()
    },
}
stats_path = os.path.join(os.path.dirname(__file__), "summary_robustness.json")
with open(stats_path, "w") as f:
    json.dump(summary_rob, f, indent=2)

print(f"\nRobustness summary:\n{json.dumps(summary_rob, indent=2)}")
print("\nDone.")
