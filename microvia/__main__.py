import argparse
import html
import json
from pathlib import Path

from .benchmark import run
from .core import analyze, copper_balance, mask_metrics, plan, read_csv


def main():
    parser = argparse.ArgumentParser(
        description="Microvia quality analysis and experiment planner"
    )
    parser.add_argument(
        "command",
        choices=[
            "validate",
            "calibrate",
            "analyze",
            "plan-experiments",
            "benchmark",
            "robust-benchmark",
            "report",
            "mask",
        ],
    )
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--lot")
    parser.add_argument("--geometry")
    parser.add_argument(
        "--strategy",
        choices=["bounded-design", "uniform", "random", "adaptive", "conservative"],
        default="bounded-design",
    )
    parser.add_argument(
        "--recommendation-policy",
        choices=["raw", "fixed-margin", "calibrated-margin"],
        default="raw",
    )
    parser.add_argument("--calibration", type=Path)
    args = parser.parse_args()
    if args.strategy == "bounded-design" and (
        args.calibration or args.recommendation_policy != "raw"
    ):
        parser.error("recommendation options require an explicit research strategy")
    if args.command == "calibrate":
        from .calibration import calibrate

        if not args.input:
            parser.error("--input required")
        result = calibrate(json.loads(args.input.read_text()))
    elif (
        args.command in ("plan-experiments", "report")
        and args.strategy != "bounded-design"
    ):
        from .calibration import plan_measured

        if not args.input:
            parser.error("--input required")
        result = plan_measured(
            json.loads(args.input.read_text()),
            json.loads(args.calibration.read_text()) if args.calibration else None,
            args.strategy,
            args.recommendation_policy,
        )
        if args.command == "report":
            result = {"strata": [], "research_recommendation": result}
    elif args.command == "robust-benchmark":
        from .robust_benchmark import run as robust_run

        result = robust_run()
    elif args.command == "benchmark":
        result = run()
    elif args.command == "mask":
        data = json.loads(args.input.read_text())
        result = mask_metrics(data["mask"], data["pixel_um"])
    else:
        if not args.input:
            parser.error("--input required")
        data = read_csv(args.input)
        if args.command == "validate":
            result = data
        elif args.command == "plan-experiments":
            if not args.lot or not args.geometry:
                parser.error("--lot and --geometry required")
            result = plan(data, args.lot, args.geometry)
        else:
            result = analyze(data)
            result["balances"] = [
                {
                    "sample": r["sample"],
                    **copper_balance(
                        r["current_a_dm2"],
                        r["time_min"],
                        r["efficiency"],
                        r["diameter_um"],
                        r["depth_um"],
                    ),
                }
                for r in data["accepted"]
            ]
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.command == "report":
        table = "".join(
            "<tr><td>"
            + html.escape(str(row["lot"]))
            + "</td><td>"
            + html.escape(str(row["geometry"]))
            + "</td><td>"
            + str(row["n"])
            + "</td><td>"
            + f"{row['mean_fill_ratio']:.3f}"
            + "</td><td>"
            + html.escape(str(row["higher_minus_lower_current_fill"]))
            + "</td></tr>"
            for row in result["strata"]
        )
        text = (
            '<!doctype html><html lang="ko"><meta charset="utf-8">'
            "<title>Microvia quality report</title><style>"
            "body{max-width:1100px;margin:40px auto;font:16px sans-serif;line-height:1.6;padding:20px}"
            "table{border-collapse:collapse;width:100%}td,th{padding:12px;border:1px solid #ccc}"
            "pre{white-space:pre-wrap;background:#f4f6f8;padding:20px}"
            "</style><h1>마이크로비아 도금 품질 분석</h1><p>Microvia Plating Quality Analysis</p>"
            "<p>목적: 동일 로트와 형상에서 검사 결과를 비교하고 다음 확인 실험을 설계합니다. "
            "Purpose: compare inspections within matched lots and geometry to design follow-up experiments.</p>"
            "<p>관측 연관성은 원인 확정이 아닙니다. 욕조 상태와 교반을 통제한 반복 실험이 필요합니다. "
            "Association is not causation; control bath conditions and agitation in replicated experiments.</p>"
            "<table><tr><th>로트 / Lot</th><th>형상 / Geometry</th><th>N</th>"
            "<th>평균 충진율 / Mean fill</th><th>전류 상하군 차이 / Current contrast</th></tr>"
            + table
            + "</table><p>양산 수율 미검증 / Factory yield effect not validated.</p>"
            "<details><summary>계산, 가정 및 추적 결과 / Calculations, assumptions and audit</summary><pre>"
            + html.escape(text)
            + "</pre></details></html>"
        )
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
