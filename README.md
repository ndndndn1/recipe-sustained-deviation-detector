# Recipe drift evidence

A runnable experiment for recipe-specific sustained-deviation triage. It explores a
hypothesis relevant to manufacturing-data analysis: isolated sensor spikes can
increase operator review work, while persistent shifts need prompt investigation.
This is not a finding about a particular factory's existing monitoring system.

## Run

Python 3.12+, standard library only:

```sh
python baseline/workload.py
python benchmark.py
python -m unittest discover -s tests
python tests/conformance.py
```

Stream JSON records with `recipe`, `t`, and `value` to `python solution.py`.
Recipe A has a synthetic center of 0 and B of 40. Values are dimensionless.
Specify different centers in `Detector` for other experiments; do not treat these
values as semiconductor process limits.

## Design and evidence

The baseline independently alarms on each recipe-relative deviation above 2 units.
The proposed detector requires three consecutive above-threshold samples per recipe.
Missing samples break continuity; invalid data and reordered samples are rejected.
An alternative is EWMA, which is not implemented or benchmarked here.

`requirements.json` fixes the objective, workload identity, three seeds and acceptance
criteria. `Specification.lean` proves bounded streak state, reset behavior, no early
alarm and a reachable alarm. It was checked with Lean 4.33.1 before implementation.
`tests/conformance.py` compares the implementation's eight state/input combinations
with the transition model. `tests/negative.py` injects incorrect persistence settings;
exit 1 with `defect_detected: true` is the expected successful detection.

Results are reproducible synthetic evidence. Actual fab data, calibrated thresholds,
distribution drift, yield benefit, device reliability and single-pulse hazard detection
are not validated. Three-sample persistence intentionally delays alerts and can miss
short events. Never use this experiment as a safety interlock or automatic tool controller.

## Business context

The problem selection is informed by publicly described specialty-foundry operations
and a manufacturing/quality data-analysis role. No employer endorsement or deployment
is claimed. References and collection dates are in `requirements.json`; job text and
candidate information are not redistributed.

## Reproduce the container

```sh
docker build -t recipe-drift-evidence .
docker run --rm --network none --read-only --tmpfs /tmp recipe-drift-evidence
```

The Dockerfile pins its base and patched runtime package. The comparison output reports
every seed; `RESULTS.json`, when included, is a recorded run rather than a forecast.
