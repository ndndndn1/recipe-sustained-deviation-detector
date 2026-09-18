# Benchmark review: measurement before optimization

## Main judgment

This is a reproducible research prototype, not a validated FCBGA optimization system or a state-of-the-art result. The earlier 90% checklist completion describes software functionality only. Real process data, calibrated chemistry, measurement repeatability and independent physical validation are absent.

V1's zero median regret was not robust evidence: it used a single smooth, noiseless family and fixed objective direction. V2 freezes development/test separation, noisy observations, four families, randomized slopes, deployed-condition evaluation, failures in the denominator and seed-cluster confidence intervals.

## Held-out results

200 scenarios per method (50 seeds x 4 families), 20 observations per trial:

| Method | Mean penalized loss | Quality violation | Abstention |
|---|---:|---:|---:|
| Uniform | 0.1723 | 14.5% | 0% |
| Random | 0.1707 | 14.0% | 0.5% |
| Existing adaptive | 0.2231 | 21.5% | 0% |
| Conservative | 0.0692 | 4.5% | 0% |

Development-selected conservative vs development-selected uniform: mean loss reduction about 59.8%; paired seed-cluster gain interval [0.0591, 0.1502]. This passes the frozen synthetic promotion gate, not a factory acceptance gate. The fixed 0.08 margin is heuristic, not calibrated confidence or a safety guarantee. Experimental query safety is not guaranteed either.

## Counter-experiment: what actually helped?

Post-evaluation diagnostic on separate seeds 200–219, 80 scenarios per combination:

| Search | Final quality margin | Mean loss | Violation |
|---|---:|---:|---:|
| Uniform | 0 | 0.2204 | 20.0% |
| Uniform | 0.08 | 0.0753 | 3.75% |
| Conservative | 0 | 0.2248 | 21.25% |
| Conservative | 0.08 | 0.0989 | 3.75% |

The main effect appears to be final recommendation margin, not sophisticated search. The claim that conservative search itself is superior is rejected. This diagnostic is exploratory; it is not used to retune or re-label the held-out results. Existing production recommendation continues to abstain. The v1 result no longer exposes a deployment-default field.

## Upper-tier research comparison

- Gardner et al., *Bayesian Optimization with Inequality Constraints*, ICML 2014, pp. 937–945: objective and constraint uncertainty are modelled separately. [Official abstract](https://proceedings.mlr.press/v32/gardner14.html).
- Sui et al., *Safe Exploration for Optimization with Gaussian Processes*, ICML 2015, pp. 997–1005: safe sequential optimization uses explicit assumptions and uncertainty. [Official abstract](https://proceedings.mlr.press/v37/sui15.html).

Only abstracts were reviewed here. No implementations or direct benchmark comparisons against these algorithms were performed. Transferable lesson: feasibility uncertainty and query safety deserve their own metrics; a fixed margin is not an implementation of either paper.

## Highest-value next experiment

Obtain repeated, calibrated section measurements at matched geometry and bath state to estimate quality measurement variability. Compare uniform search + empirically calibrated final margin against uncertainty-aware constrained optimization with equal budgets on a newly frozen dataset. Keep both unsafe-query rate and unsafe-final-recommendation rate. Accept an optimizer only with a positive paired improvement interval, >=10% lower loss and no increase in violations. If margin alone explains improvement, keep the simpler method. Without real measurements, report software stress robustness rather than production yield gains.

## Reproduce

`python -m microvia robust-benchmark` emits all 800 test and 320 development trials and a source hash. `python -m unittest discover -s tests -v` checks failure scoring, oracle isolation, reproducibility and existing functionality. The diagnostic ablation uses the same `trial` with `final_margin=0` or `0.08`, seeds 200–219, all four families, uniform/conservative methods. Full run evidence is retained privately in MongoDB/GridFS.
