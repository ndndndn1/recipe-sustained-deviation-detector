# Microvia Plating Quality and Experiment Planner

마이크로비아 도금 품질 분석 및 실험 설계 도구. 공정 조건과 검사 결과를 연결하고 다음 확인 실험을 제시한다. 실제 FCBGA 생산 수율 또는 현장 설비 성능은 검증하지 않았다.

## Run / 실행

Python 3.12 standard library, no third-party runtime packages:

```bash
python -m microvia validate --input microvia/example.csv
python -m microvia analyze --input microvia/example.csv
python -m microvia plan-experiments --input microvia/example.csv --lot SYNTHETIC --geometry cylindrical
python -m microvia benchmark
python -m microvia report --input microvia/example.csv --output /tmp/microvia-report.html
python -m unittest discover -s tests -v
```

The example is synthetic, not a literature dataset. `example.csv` header defines units exactly. `fill_ratio` must consistently mean measured filled height divided by original depth in that dataset; never mix it with area fill ratio. The `mask` command separately accepts JSON `{"pixel_um":2,"mask":[[1,1,0],[1,2,0]]}`; 0=outside, 1=copper, 2=unfilled region. This does not perform automatic segmentation or infer internal defects from top-view AOI.

`source` identifies a measurement provenance record. For private work resolve it to MongoDB/GridFS evidence. It is not proof that the cited measurement is accurate. Keep original units, microscope calibration and image origin with that record.

## What is implemented

- Reject/quarantine missing values, nonfinite inputs, inconsistent units (header), impossible ratios, duplicate samples and reversed lot timestamps.
- Faraday planar copper balance, cylindrical empty-volume calculation and idealized bottom-only time. No moving boundary or additive transport solver.
- Stratify by lot and exact geometry; report association with current density and a matched, randomized follow-up experiment. Associations are not causal attribution.
- Recommend a replicated current contrast inside the observed range for one lot/shape only. Production recipe recommendation always abstains because no bath-specific calibration exists.
- Compare a separate synthetic adaptive optimizer to space-filling and random search with equal 8+12 budgets and ten fixed seeds. The optimizer sees only previous observations. Synthetic benchmark performance does not validate the experimental design in a real bath.
- Generate bilingual HTML with escaped input. No browser service, device control or credentials required.

## Evidence and limits

See [literature and learning](LITERATURE.md), [requirements](requirements.json), [Lean contract](Specification.lean), and [verification](VERIFICATION.md).

The four Lean theorems prove properties of a Boolean recommendation gate. They do not prove the floating-point physics, measurement quality, Python implementation or optimization benefit. Exhaustive Python gate tests cover all 16 inputs. End-to-end tests separately cover the actual planner.

No FCBGA/OSAT manufacturing experience, customer audit experience, graduate degree or employment eligibility is created by this project. Real bath calibration, cross-section metrology repeatability, ABF materials qualification, independent process datasets and actual yield improvement remain unvalidated.

## Container

Use the existing pinned repository Dockerfile:

```bash
docker build -t microvia-quality-planner:local .
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true --memory 512m --cpus 1 --pids-limit 64 microvia-quality-planner:local python -m microvia benchmark
```

For private runs, retain reports and full logs in MongoDB/GridFS. Public source contains only synthetic examples and source references. Licensed papers are not redistributed.

Verified on this server without downloading dependencies:

```bash
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true --memory 512m --cpus 1 --pids-limit 64 -v "$PWD:/workspace:ro" career2026/recipe-drift-evidence:v1 python -m microvia benchmark
```

The existing runtime image must already be present. This mount uses the current source rather than the image's old source.
