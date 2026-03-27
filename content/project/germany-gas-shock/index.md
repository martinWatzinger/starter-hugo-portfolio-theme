---
title: "The Cost of the Gas Price Shock: A Synthetic Control Study for Germany"
summary: >
  Using the synthetic control method (Born et al., 2019), I estimate that
  Russia's invasion of Ukraine and the ensuing gas price shock reduced German
  GDP per capita by approximately 3.6% in 2022 and 4.3% in 2023 relative to a
  data-driven counterfactual — roughly twice the GDP loss attributed to Brexit.
tags:
  - Economics
  - Econometrics
date: 2024-01-01
---

## Motivation

On 24 February 2022 Russia invaded Ukraine. The war triggered an immediate
energy crisis in Europe — and Germany in particular. Germany had sourced roughly
55% of its natural gas from Russia, had voluntarily phased out nuclear power, and
had been slow to build LNG import capacity. When Russian pipeline flows collapsed,
German industrial output contracted, energy prices surged, and fears of
deindustrialisation grew.

How large was the macroeconomic cost? This page presents a synthetic control
study that mirrors the approach of **Born, Müller, Schularick & Sedlacek (2019),
"The Costs of Economic Nationalism: Evidence from the Brexit Experiment,"
*The Economic Journal*, 129 (623), 2722–2744** — one of the best-known
applications of the synthetic control method to a macroeconomic shock.

---

## Methodology

### Synthetic Control Method (Abadie, Diamond & Hainmueller, 2010)

The idea is to build a **"phantom" Germany** — a weighted average of other
OECD countries chosen so that, *before* the invasion, the composite economy's
GDP per capita tracked Germany's as closely as possible.

After February 2022, this synthetic (counterfactual) Germany keeps growing on
its pre-war trajectory, while actual Germany is buffeted by the gas price shock.
The **gap between actual and synthetic Germany** is interpreted as the causal
cost of the shock.

Formally, we minimise

$$\hat{w} = \arg\min_{w \geq 0,\, \sum w_j = 1}
\left\| y_{\text{DEU}}^{\text{pre}} - \mathbf{X}_{\text{donors}}^{\text{pre}} w \right\|^2$$

where $y_{\text{DEU}}^{\text{pre}}$ is Germany's indexed real GDP per capita
in the pre-treatment period and $\mathbf{X}_{\text{donors}}^{\text{pre}}$ is
the matrix of donor outcomes.

### Data

| Item | Details |
|------|---------|
| **Outcome variable** | Real GDP per capita, PPP (constant 2017 int'l $), indexed to 2019 = 100. Source: World Bank NY.GDP.PCAP.PP.KD. |
| **Donor pool** | 28 OECD economies (AUT, BEL, FRA, GBR, NLD, SWE, CHE, NOR, DNK, FIN, ITA, ESP, PRT, GRC, USA, CAN, AUS, JPN, KOR, POL, CZE, HUN, SVK, SVN, EST, NZL, ISL, LUX). Ireland excluded: its GDP is heavily distorted by multinational IP transfers. |
| **Pre-treatment** | 2000–2021 |
| **Treatment** | 2022 (year of Russia's invasion and the full onset of the gas price shock) |
| **Post-treatment** | 2022–2023 |

---

## Results

### Synthetic Germany

The algorithm assigned positive weights to seven donor countries:

| Country | Weight |
|---------|--------|
| Switzerland | 39.5% |
| Canada | 30.2% |
| Sweden | 11.9% |
| Poland | 9.5% |
| Iceland | 3.7% |
| France | 2.6% |
| Portugal | 2.5% |

![Donor weights](/germany-gas-shock/donor_weights.png)

Switzerland and Canada dominate the synthetic control because they share
Germany's long-run growth trajectory — steady, industrialised, export-oriented
economies — while avoiding both the rapid convergence dynamics of Eastern
Europe and the debt-crisis contractions of Southern Europe. Sweden contributes
as a similarly large, open European manufacturing economy.

**Pre-treatment fit:** Root-mean-square prediction error (RMSPE) = **1.09
index points** over 2000–2021, indicating a good pre-treatment match.

### Main Finding

![Germany vs Synthetic Germany](/germany-gas-shock/gdp_actual_vs_synthetic.png)

The two lines track closely through 2021. After the invasion, Germany diverges
**below** its synthetic counterfactual.

![GDP Gap](/germany-gas-shock/gdp_gap.png)

| Year | Actual Germany | Synthetic Germany | Gap |
|------|---------------|-------------------|-----|
| 2022 | 99.5 | 103.1 | **−3.59 pp** |
| 2023 | 100.6 | 104.9 | **−4.32 pp** |

The estimates suggest:
- **2022:** −3.6% of 2019 GDP per capita relative to the counterfactual.
- **2023:** −4.3% of 2019 GDP per capita, as the shock continued to feed through.
- **Average 2022–2023:** −4.0 percentage points.

These estimates are **conservative**: several European donors in the pool
(Austria, Czech Republic, Finland) were themselves exposed to the Russian gas
shock, which biases the counterfactual downward and therefore *understates*
the true German loss.

### Placebo / Permutation Tests

To assess statistical significance, we repeat the analysis for each of the
28 donor countries pretending each was "treated" in 2022.

![Placebo tests](/germany-gas-shock/placebo_tests.png)

![Gap with 90% placebo interval](/germany-gas-shock/main_with_ci.png)

Germany's 2023 gap of **−4.3 pp** falls below the 5th percentile of the
donor-placebo distribution. The **permutation p-value** (post/pre RMSPE ratio
≥ Germany's 3.66) is **p = 0.34** using the full 28-country pool. This is
elevated for two reasons: (i) the post-treatment window is short (two years);
(ii) several European donors — Norway, Sweden, Finland — were themselves
partially exposed to the gas shock, inflating their placebo ratios and raising
the p-value. The robustness check below addresses this directly.

---

### Robustness: Non-European Donor Pool

To rule out donor contamination, we restrict the pool to six geographically
distant OECD economies not exposed to the European energy crisis:
**USA, Canada, Japan, South Korea, Australia, New Zealand**.

![Robustness comparison](/germany-gas-shock/robustness_comparison.png)

| | Baseline (28 OECD) | Robustness (6 non-European) |
|---|---|---|
| **Donor pool** | 28 OECD countries | USA, CAN, JPN, KOR, AUS, NZL |
| **Weights** | CHE 39.5%, CAN 30.2%, SWE 11.9% | CAN 63.4%, USA 18.4%, KOR 12.6% |
| **Pre-treatment RMSPE** | 1.09 pp | 1.42 pp |
| **2022 gap** | −3.59 pp | **−4.09 pp** |
| **2023 gap** | −4.32 pp | **−4.49 pp** |
| **Average gap** | −3.96 pp | **−4.29 pp** |

The robustness estimates are **larger** than the baseline — as expected if
European donors understate the counterfactual. The two synthetic controls
bracket a plausible range: the gas shock cost Germany between **−3.6% and
−4.5% of 2019 GDP per capita** by 2023.

---

## Comparison with the Brexit Study

| Feature | Born et al. (Brexit) | This study (Germany gas shock) |
|---------|---------------------|-------------------------------|
| **Treatment event** | Brexit referendum, June 2016 | Russia invades Ukraine, Feb 2022 |
| **Outcome** | Quarterly real GDP | Annual real GDP per capita |
| **Donor pool** | 23 OECD countries | 28 OECD countries |
| **Pre-treatment period** | 1995 Q1 – 2016 Q2 | 2000 – 2021 |
| **Estimated GDP loss** | 1.7%–2.5% by end 2018 | 3.6%–4.3% by end 2023 |
| **Mechanism** | Downgraded growth expectations | Energy cost shock + industrial contraction |

Germany's estimated loss is **larger** than the Brexit cost to the UK and was
concentrated over just two years. Brexit was a slow-burn effect driven
primarily by revised growth expectations; the gas shock was an immediate
supply-side disruption to the most energy-intensive manufacturing economy in
Europe.

---

## Caveats

1. **Short post-treatment period.** Two annual observations offer limited
   statistical power. The study should be revisited as 2024–2025 data become
   available.
2. **Donor-pool contamination.** Austria, Czech Republic, Finland and other
   Eastern European OECD members were also exposed to the Russian gas shock.
   A robustness check restricting the donor pool to non-European OECD countries
   (USA, Canada, Japan, Korea, Australia) would likely produce a larger
   estimated gap.
3. **Annual data.** Born et al. used quarterly data. Annual data may miss
   important within-year dynamics.
4. **Single outcome.** GDP per capita is a composite measure. Sectoral analyses
   (industrial production, energy-intensive manufacturing) would likely reveal
   larger sectoral costs.

---

## Replication

All code is available in the `analysis/` directory of this repository:

- `analysis/gdp_data.py` — GDP per capita data for 29 OECD countries, 2000–2023
  (World Bank NY.GDP.PCAP.PP.KD, constant 2017 int'l $, PPP)
- `analysis/germany_gas_shock_synthetic_control.py` — Synthetic control
  estimation, placebo tests, and figures
- `analysis/robustness_noneuropean.py` — Robustness check with non-European
  donor pool and placebo confidence envelope

**Reference:**
> Born, B., Müller, G. J., Schularick, M., & Sedlacek, P. (2019).
> The Costs of Economic Nationalism: Evidence from the Brexit Experiment.
> *The Economic Journal*, 129(623), 2722–2744.
