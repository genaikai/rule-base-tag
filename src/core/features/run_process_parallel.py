"""
run_flags_parallel.py

병합된 대용량 CSV 한 개를 multiprocessing으로 검사해 Flags를 붙인다.

  python run_flags_parallel.py merged.csv -o flagged.parquet
  python run_flags_parallel.py merged.csv -o flagged.csv --workers 8 --chunksize 50000

동작 방식
  - 부모가 CSV를 chunksize 단위로 스트리밍해서 읽고,
    (질의, 답변) 두 컬럼만 워커로 보낸다.  (pickle 비용 최소화)
  - 워커는 태그 리스트만 돌려주고, 부모가 원본 청크에 붙여 바로 저장한다.
  - 한 번에 in-flight 상태로 두는 청크 수를 제한해서 메모리를 일정하게 유지한다.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from itertools import islice
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from response_quality_rules import CHECKS, QUERY_HEAD_LEN, evaluate_row

DEFAULT_INPUT_COL = "input_msg_content"
DEFAULT_OUTPUT_COL = "output_msg_content"
DEFAULT_FLAG_COL = "Flags"


# ---------------------------------------------------------------------------
# 워커
# ---------------------------------------------------------------------------

def _process_pairs(pairs: list[tuple[str, str]]) -> list[list[str]]:
    """(질의, 답변) 쌍 리스트를 받아 태그 리스트들을 반환. 워커에서 실행."""
    return [evaluate_row(q, a) for q, a in pairs]


# ---------------------------------------------------------------------------
# 저장 헬퍼 — CSV는 append, Parquet는 파일을 나눠 쓰고 마지막에 합침
# ---------------------------------------------------------------------------

class _Writer:
    def __init__(self, out_path: Path, keep_cols: list[str] | None):
        self.out_path = out_path
        self.keep_cols = keep_cols
        self.is_parquet = out_path.suffix.lower() in (".parquet", ".pq")
        self.first = True
        self.part_dir = None
        self.parts: list[Path] = []
        if self.is_parquet:
            self.part_dir = out_path.with_suffix("")
            self.part_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if out_path.exists():
                out_path.unlink()

    def write(self, df: pd.DataFrame) -> None:
        if self.keep_cols:
            cols = [c for c in self.keep_cols if c in df.columns]
            df = df[cols]
        if self.is_parquet:
            part = self.part_dir / f"part-{len(self.parts):05d}.parquet"
            df.to_parquet(part, index=False)
            self.parts.append(part)
        else:
            df.to_csv(self.out_path, mode="w" if self.first else "a",
                      header=self.first, index=False)
        self.first = False

    def close(self) -> None:
        if not self.is_parquet or not self.parts:
            return
        merged = pd.concat([pd.read_parquet(p) for p in self.parts], ignore_index=True)
        merged.to_parquet(self.out_path, index=False)
        for p in self.parts:
            p.unlink()
        self.part_dir.rmdir()


# ---------------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------------

def run_parallel(
    csv_path: str,
    out_path: str,
    workers: int | None = None,
    chunksize: int = 50_000,
    input_col: str = DEFAULT_INPUT_COL,
    output_col: str = DEFAULT_OUTPUT_COL,
    flag_col: str = DEFAULT_FLAG_COL,
    keep_cols: list[str] | None = None,
    usecols: list[str] | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    workers = workers or os.cpu_count() or 4
    # 동시에 메모리에 올릴 청크 수 — 워커 수의 2배면 파이프가 마르지 않는다
    in_flight = workers * 2

    writer = _Writer(Path(out_path), keep_cols)
    counts: dict[str, int] = {tag: 0 for tag, _, _ in CHECKS}
    total_rows = 0
    started = time.time()

    reader = pd.read_csv(
        csv_path,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,   # 빈 값이 NaN 되지 않게
        usecols=usecols,
        nrows=limit,
    )

    with Pool(processes=workers) as pool:
        while True:
            # in_flight 개수만큼만 미리 읽어서 메모리 상한을 건다
            batch = list(islice(reader, in_flight))
            if not batch:
                break

            # 워커로는 두 컬럼만 보낸다. 질의는 어차피 앞 100자만 쓰므로 잘라서 전송
            payloads = [
                list(zip(
                    chunk[input_col].str.slice(0, QUERY_HEAD_LEN),
                    chunk[output_col],
                ))
                for chunk in batch
            ]

            for chunk, tag_lists in zip(batch, pool.map(_process_pairs, payloads)):
                chunk = chunk.copy()
                chunk[flag_col] = tag_lists
                writer.write(chunk)

                total_rows += len(chunk)
                for tags in tag_lists:
                    for t in tags:
                        counts[t] = counts.get(t, 0) + 1

            elapsed = time.time() - started
            rate = total_rows / elapsed if elapsed else 0
            print(f"\r  {total_rows:,}행 처리  ({rate:,.0f}행/초)", end="", file=sys.stderr)

    writer.close()
    print(file=sys.stderr)

    print(f"\n총 {total_rows:,}행  /  {time.time() - started:.1f}초  /  워커 {workers}개")
    print(f"저장: {out_path}\n")
    for tag, _, _ in CHECKS:
        c = counts.get(tag, 0)
        pct = c / total_rows * 100 if total_rows else 0
        print(f"  {tag:24s} {c:9,d}  ({pct:5.2f}%)")
    return counts


def main() -> None:
    p = argparse.ArgumentParser(description="병합 CSV 병렬 rule-based 검사")
    p.add_argument("csv_path", help="입력 CSV 경로")
    p.add_argument("-o", "--out", required=True,
                   help="출력 경로 (.parquet 권장, .csv도 가능)")
    p.add_argument("-w", "--workers", type=int, default=None,
                   help="프로세스 수 (기본: CPU 코어 수)")
    p.add_argument("-c", "--chunksize", type=int, default=50_000,
                   help="청크당 행 수 (기본 50000)")
    p.add_argument("--input-col", default=DEFAULT_INPUT_COL)
    p.add_argument("--output-col", default=DEFAULT_OUTPUT_COL)
    p.add_argument("--flag-col", default=DEFAULT_FLAG_COL)
    p.add_argument("--usecols", default=None,
                   help="읽을 컬럼만 콤마로 지정 (메모리 절약)")
    p.add_argument("--keep-cols", default=None,
                   help="저장할 컬럼만 콤마로 지정 (예: id,Flags)")
    p.add_argument("--limit", type=int, default=None,
                   help="앞에서 N행만 처리 (테스트용)")
    args = p.parse_args()

    split = lambda s: [x.strip() for x in s.split(",")] if s else None

    run_parallel(
        csv_path=args.csv_path,
        out_path=args.out,
        workers=args.workers,
        chunksize=args.chunksize,
        input_col=args.input_col,
        output_col=args.output_col,
        flag_col=args.flag_col,
        keep_cols=split(args.keep_cols),
        usecols=split(args.usecols),
        limit=args.limit,
    )


if __name__ == "__main__":   # multiprocessing 필수 가드
    main()
