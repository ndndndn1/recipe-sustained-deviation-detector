# Robust evaluation protocol v2

Goal: find fast feasible conditions under a fixed experiment budget, without recommending low-quality conditions. No official employer scoring rubric is available. This is an engineering evaluation, not a hiring score.

V1 shortcomings: one smooth family, no noise, fixed objective slopes, only ten seeds, no uncertainty estimates and reporting the best feasible observation rather than evaluating an observation-selected final recommendation. Its 90% requirement completion is software coverage, not industrial readiness.

Freeze before running: 8 initial + 12 additional observations; development seeds 0–19, test seeds 100–149; smooth, interacting, narrow feasible-region and temporal-drift families. Randomized objective slopes prevent a universally profitable corner. Measurement noise: quality SD .04 and time SD 2 in synthetic units. No FCBGA calibration is implied.

Compare random, maximin space filling, existing inverse-distance adaptive search and conservative local search. Choose one candidate and one baseline using development loss only. Do not change parameters after test inspection; a later version requires a fresh holdout.

Final recommendation uses measured observations only. Evaluator computes true quality at deployment time. Loss is 1 for unsafe recommendation, abstention or no feasible condition; otherwise normalized excess time relative to true feasible optimum. Report unsafe recommendations and abstentions separately to prevent abstention from hiding failure. Report no-feasible cases. Time normalization is 120 synthetic units, not measured factory minutes.

Promotion requires >=10% lower average test loss, positive lower bound of paired seed-cluster bootstrap 95% interval, and no higher violation rate. Resample seeds with all scenario families kept together. All 800 test trials remain in denominator. Simultaneous exploratory comparisons are descriptive, not additional significance claims.

Hypothesis: a conservative feasibility margin reduces noise-driven unsafe recommendations; counter-hypothesis is excessive abstention or missed fast regions. Even a passing result does not enable production recipes. Distribution families are still designed by the author and cannot establish external validity.
