"""실행 흐름 및 태거 조율.

진입점은 run.py 이지만, 메인 로직은 여기서 처리한다.
모든 태거를 동적으로 로드하고 실행한다.
"""

import argparse
import sys
import time
from pathlib import Path

from .contracts import validate
from .load import load_csv
from .pipeline import process_data, apply_tags
from .report import render
from .synth import generate


def read_version() -> str:
    """VERSION 파일에서 버전을 읽는다."""
    path = Path(__file__).resolve().parent.parent / "VERSION"
    return path.read_text().strip() if path.exists() else "unversioned"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="run.py", description=__doc__.splitlines()[0])
    ap.add_argument("--data", help="입력 CSV 경로. --dry-run 이 아니면 필수")
    ap.add_argument("--dry-run", action="store_true", help="합성 데이터로 전 구간 스모크")
    ap.add_argument("--limit", type=int, default=0, help="앞 N행만 처리 (0=전체)")
    ap.add_argument("--rows", type=int, default=1000, help="--dry-run 이 생성할 행 수")
    ap.add_argument("--seed", type=int, default=0, help="--dry-run 생성 시드")
    ap.add_argument("--adversarial", action="store_true", help="--dry-run 에 사고 유형 주입")
    ap.add_argument("--config", help="설정 파일. paths.venv 를 여기서 읽는다")
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    if not args.dry_run and not args.data:
        ap.error("--data is required unless --dry-run")

    started = time.perf_counter()
    if args.dry_run:
        mode = "adversarial" if args.adversarial else "normal"
        rows = generate(args.rows, seed=args.seed, mode=mode)
        source = f"synthetic(n={args.rows}, seed={args.seed}, mode={mode})"
    else:
        try:
            rows = load_csv(args.data, args.limit)
        except OSError as exc:
            print(f"입력을 열 수 없습니다: {exc}", file=sys.stderr)
            return 2
        source = args.data

    print(f"실행 조건: {source} / {len(rows):,} rows", file=sys.stderr)

    report = validate(rows)
    metrics = process_data(rows)
    tags = apply_tags(rows)

    print(render(
        version=read_version(),
        args=" ".join(argv if argv is not None else sys.argv[1:]) or "(none)",
        source=source,
        n_rows=len(rows),
        n_cols=len(rows[0]) if rows else 0,
        violations=report.violations,
        notes=report.notes,
        metrics=metrics,
        tags=tags,
        runtime_s=time.perf_counter() - started,
        status="OK" if report.ok else "CONTRACT MISMATCH",
    ))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
