# Microvia Plating Quality and Experiment Planner

마이크로비아 도금 품질 분석 및 실험 설계 도구. 공정 조건과 검사 결과를 연결하고 다음 확인 실험을 제시한다. 실제 FCBGA 생산 수율 또는 현장 설비 성능은 검증하지 않았다.

## 현재 잘 되는 것과 안 되는 것

현재 수준은 **실행 가능한 연구용 분석 도구**다. 아래 상태는 코드와 기록된 테스트 기준이며 실제 공장 성능을 뜻하지 않는다.

| 구분 | 현재 상태 | 적용 범위 또는 제한 |
|---|---|---|
| CSV 검증 | 구현 및 테스트 통과 | 필수값, 유한수, 비율, 중복, 로트별 시간 순서와 헤더 검사. 헤더가 올바르더라도 값이 잘못된 단위로 입력된 것은 자동 식별하지 못함 |
| 구리 석출량 계산 | 해석 사례 검증 통과 | 일정 전류효율을 가정한 평면 Faraday 계산. 첨가제 반응, 이동경계, 실제 충진 형상은 계산하지 않음 |
| 단면 마스크 면적 계산 | 알려진 마스크 검증 통과 | 사용자가 제공한 마스크와 픽셀 보정값 필요. 이미지 자동 분할과 3D 내부 보이드 검출은 미구현 |
| 로트/형상별 분석 | 구현 및 테스트 통과 | 전류와 충진율의 관측 연관성. 불량 원인 확정이나 교란 제거는 하지 못함 |
| 다음 실험 설계 | 제한적 구현 | 관측 전류 범위의 하한/중간/상한과 반복 횟수 제안. 실행 순서의 실제 무작위 배정, 욕조 조건 자동 통제, 최적 생산 레시피는 미구현 |
| 최적화 벤치마크 | 합성 평가 실행 완료 | v2 개발 320회, 평가 800회, 별도 진단 320회. V3에서는 명시적 연구용 전략 옵션으로 CLI 연결 완료 |
| 한영 보고서 | 생성 및 입력 이스케이프 확인 | 분석과 가정 출력. 벤치마크 전체 결과의 보고서 자동 통합은 미구현 |
| Lean 검증 | Boolean 조건 정리 4개 통과 | 물리 모델, 실험 안전성, 전체 Python 코드 또는 양산 성능을 증명하지 않음 |
| 컨테이너 | 기존 이미지에서 오프라인 실행 확인 | 신규 이미지 빌드는 패키지 서버 연결 실패. 깨끗한 환경의 독립 빌드 완료로 표시하지 않음 |
| 측정 보정과 연구용 추천 | 구현 및 CLI 통합 시험 통과 | 독립 기준값 30개 이상, 정확한 문맥/조건 범위 검사. 자동 드리프트 검출, 보정 유효기간 판정과 계측/공정 변동 분리 추정은 미구현 |
| 실제 공정 개선 | 미검증 | 실제 반복 측정, 욕조 보정, ABF 공정 적합성, 수율/원가 개선 근거 없음 |

**기존 적응형 방법이 더 좋다는 주장은 유지하지 않는다.** v2 평가에서 품질 미달 추천은 기존 적응형 21.5%, 균등 탐색 14.5%, 보수적 방법 4.5%였다. 추가 분리 실험에서는 같은 품질 여유 기준을 적용한 균등 탐색이 더 낮은 손실을 보였다. 따라서 복잡한 탐색의 우월성은 입증되지 않았고, 고정 여유값 0.08도 실제 측정 오차에 맞게 보정된 값이 아니다.

[코드 반영 계획](IMPLEMENTATION_PLAN_V3.md)의 핵심 구현과 합성 평가를 완료했다. [V3 실행 방법과 미완료 범위](V3_EXECUTION.md), [V3 결과](RESULTS_V3.json)를 확인한다. [평가 리뷰](BENCHMARK_REVIEW.md)와 [수치 결과](ROBUST_RESULTS.json)는 실행 완료 기록이다. 기능 체크리스트 90%를 공정 성숙도나 채용 적합도 점수로 해석하지 않는다.

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

- Reject/quarantine missing values, nonfinite inputs, unexpected unit-labelled headers (not incorrectly scaled values under correct headers), impossible ratios, duplicate samples and reversed lot timestamps.
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

## References / 참고문헌

### 설계에 참조한 자료

1. **Mark Lefebvre, George Allardyce, Masaru Seita, Hideki Tsuchida, Masaru Kusaka, and Shinjiro Hayashi.** “Copper Electroplating Technology for Microvia Filling.” *IPC Printed Circuits Expo / APEX / Designers Summit*, 2004, paper S23-2. [원문 PDF](https://www.electronics.org/system/files/technical_resource/E18%26S23-2.pdf).
   - 열람: 계획 단계에서 본문 확인. DOI는 확인하지 못했다.
   - 반영: 공정 변수 선정, 동일 형상별 비교, 높이 충진율과 단면적 충진율 구분. 특히 Figure 1, Figures 2–4 및 Tables 1–2를 참고했다.
   - 해당 논문의 욕조 조성을 현재 FCBGA 양산 조건으로 사용하거나 실험 결과를 재현했다고 주장하지 않는다.

2. **Thomas P. Moffat, Daniel Wheeler, and Daniel Josell.** “Superconformal Film Growth.” *202nd Meeting of The Electrochemical Society*, 2002. [NIST 공식 서지 및 초록](https://www.nist.gov/publications/superconformal-film-growth).
   - 열람: 공식 초록만 확인. 논문 전체와 DOI는 미확인이다.
   - 반영: 첨가제 피복과 형상 변화의 관계를 정성적 한계 설명에 사용했다. 평면 석출량 계산을 비아 충진 형상 예측으로 해석하지 않는다.
   - CEAC 모델 구현이나 논문 수치 재현의 근거로 사용하지 않는다.

### 후속 검토 문헌: 구현 근거에 포함하지 않음

3. “Fast Filling of Microvia by Pre-Settling Particles and Following Cu Electroplating.” *Nanomaterials* **12**(10), 1699, 2022. [DOI: 10.3390/nano12101699](https://doi.org/10.3390/nano12101699), [PubMed 서지](https://pubmed.ncbi.nlm.nih.gov/35630921/).
   - 서지와 초록 검색 결과만 확인했다. 본문은 미열람이며 수치나 공정 조건을 구현에 사용하지 않았다.

상세한 주장, 반증 실험 및 열람 상태는 [문헌 근거표](LITERATURE.md)에 기록했다. `example.csv`와 최적화 벤치마크는 직접 만든 합성 데이터이며 위 논문의 실험 데이터가 아니다. Faraday 계산은 일반 전기화학 전하량 관계를 구현한 것으로, 위 논문을 해당 코드나 상수의 직접 출처로 표시하지 않는다.

## Robustness review (v2)

[Benchmark review and failure analysis](BENCHMARK_REVIEW.md), [frozen evaluation protocol](BENCHMARK_PROTOCOL_V2.md), [numerical summary](ROBUST_RESULTS.json). Run `python -m microvia robust-benchmark`. The original adaptive result is not a deployment recommendation; noisy held-out evaluation and a separate ablation identify final feasibility margin as the main improvement. No claim of state-of-the-art or factory validation is made.
