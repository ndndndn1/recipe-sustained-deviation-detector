# V3 실행 기록과 제한

## 구현한 것

`policies.py`는 관측 이력으로 탐색과 최종 추천을 분리한다. 평가기는 진실값을 정책 인자로 전달하지 않는다. `calibration.py`는 독립 기준 측정 잔차의 일방향 95% 경험 분위수를 사용한다. 이것은 선택된 최적점의 95% 안전 보장이 아니다. 입력 기준값의 독립성과 출처 진실성은 사용자가 확인해야 한다.

기본 CSV 동작은 유지한다. JSON 연구 모드는 4개 탐색 정책, 3개 추천 정책, 보정 범위 및 중복 측정 검사를 제공한다. 추천은 관측점 중 하나이며 다음 실험은 입력 후보 중 관측 좌표 범위 안에서만 선택한다. 범위 내부라는 이유만으로 실험 안전성이 입증되지는 않는다.

```bash
python -m microvia calibrate --input microvia/examples/calibration.json --output /tmp/calibration.json
python -m microvia plan-experiments --input microvia/examples/observations.json --strategy uniform --recommendation-policy calibrated-margin --calibration /tmp/calibration.json
python -m microvia report --input microvia/examples/observations.json --strategy uniform --recommendation-policy calibrated-margin --calibration /tmp/calibration.json --output /tmp/microvia-report.html
python -m unittest discover -s tests -v
```

예제는 모두 합성이다. `condition`은 두 개의 정규화 좌표다. 실제 단위와 좌표 변환, 설비별 허용 조건을 별도로 확정해야 하며 이 출력을 설비에 직접 전달하면 안 된다. 품질은 높이 충진율(`height_fill_ratio`, `ratio`)이다. `duration`과 bath_age, temperature, agitation은 동일 데이터 계약의 단위를 일관되게 사용해야 한다. 현재 단위 변환 기능은 없다.

## 고정 평가 결과

개발: 시드 0–9, 8개 함수군, 24개 설정, 총 1,920회. 평가: 예약 시드 1000–1099, 8개 함수군, 2개 확정 설정, 총 1,600회. 각 시행 8+12=20회이고 반복 설정은 추가 6회 탐색과 6회 재측정이다. 보정은 함수군당 독립 합성 기준값 40쌍을 별도로 소비한다. 비교 방법 모두 같은 보정 자료에 접근할 수 있다.

| 항목 | 균등 탐색 + 보정 여유 | 보수적 탐색 + 고정 여유 + 반복 |
|---|---:|---:|
| 평균 손실 | 0.31535 | 0.32679 |
| 최종 품질 미달 | 15.5% | 16.5% |
| 추천 보류 | 13.125% | 14.0% |
| 탐색 중 품질 미달 | 76.531% | 62.519% |

손실 개선의 seed 단위 paired bootstrap 95% 구간은 [-0.03291, 0.00885]. 후보의 우월성은 입증되지 않았다. 후보 채택은 거부하고 운영 기본값 bounded-design을 유지한다. 특히 센서 편향에서 후보가 악화됐고 후반 변화와 실행 가능 조건 없음에서는 두 방법 모두 손실 1이었다. 이분산이나 선택 편향까지 보정이 해결했다는 주장은 하지 않는다.

전체 합성 시행 기록은 비공개 GridFS에 보관하고 공개 요약은 `RESULTS_V3.json`에 둔다. 재현 명령은 `python -m microvia.evaluation_v3`이다. 기존 평가 시드는 이미 관측했으므로 이후 개선의 새 holdout으로 사용하지 않는다. 평가 후 예외 집계 wrapper와 CLI 입력 검사를 추가했으며 성공 시행 정책은 바꾸지 않았다. 같은 holdout을 재실행해 개선 수치를 만들지 않았다.

## 검증 및 남은 것

- 24개 자동 테스트 통과: 기존 CSV, CLI 보정/추천/HTML, 반복 예산, 표본 부족, 자료 중복, 범위/문맥 이탈, drift 플래그, feasible 없음, 실행 예외의 손실 1 처리.
- 실패 시행은 분모에 남고 오류가 있으면 채택하지 않는다. 오류 유형만 기록하며 원문 예외의 개인정보는 저장하지 않는다. 프로세스 강제 종료 후 자동 재개와 부분 결과 영속화는 미구현이다.
- drift_detected는 호출자가 제공한다. 자동 변화 검출, 보정 만료일 정책, 계측 반복오차와 공정 반복변동의 분리 추정은 미구현이다.
- 모듈 분리는 oracle 정보가 정책 인자에 전달되지 않게 하지만 Python 보안 격리는 아니다. 예산은 관측 호출 경로와 trace로 확인하며 별도의 독립 계측 감시기는 없다.
- Lean의 기존 4개 Boolean 정리는 유지한다. 이번 통계 보정 또는 전체 Python 코드의 형식 증명이 아니다. 기존 요구사항 10개 분모와 실제 공정 미실행 항목은 변경하지 않는다.
- 실제 욕조 데이터, 논문 수치 재현, 장비 제어, 생산 수율 개선은 미검증이다. 신규 이미지 독립 빌드의 이전 네트워크 문제도 해결했다고 표시하지 않는다.

다음 우선순위는 알고리즘 추가가 아니라 실제 동일 형상/욕조의 단위 계약과 독립 기준 측정 확보다. 후반 변화 검출은 별도 개발 자료에서 검증한 뒤 새로운 평가 시드로 평가해야 한다.
