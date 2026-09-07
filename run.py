#!/usr/bin/env python3
"""진입점.

    python run.py --data <csv> [--limit N]
    python run.py --dry-run [--adversarial]

파일을 직접 실행하면 sys.path[0] 이 프로젝트 루트가 되므로 src 패키지들이 import 된다.
PYTHONPATH 도, 공용 venv 에 대한 설치도 필요 없다.

이 파일이 하는 일은 둘뿐이다: venv 를 갈아타는 것과 본체로 넘기는 것.
나머지는 전부 src/ 안에 있다.
"""

import os
import sys
from pathlib import Path

_SWITCH_FLAG = "_MYPKG_VENV_SWITCHED"


def _config_path(argv: list[str]) -> str:
    """--config 를 argparse 전에 훔쳐본다. venv 를 갈아타려면 파싱보다 먼저다."""
    for i, arg in enumerate(argv):
        if arg == "--config" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--config="):
            return arg.split("=", 1)[1]
    return ""


def _peek_venv(config: str) -> str:
    """설정에서 paths.venv 만 뽑는다."""
    try:
        text = Path(config).expanduser().read_text(encoding="utf-8")
    except OSError:
        return ""

    in_paths = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            in_paths = line.split(":")[0].strip() == "paths"
            continue
        if in_paths and line.strip().split(":")[0].strip() == "venv":
            value = line.split(":", 1)[1].split("#")[0].strip().strip("\"'")
            return "" if value in ("", "null", "~") else value
    return ""


def switch_venv(argv: list[str]) -> None:
    """설정에 적은 파이썬으로 갈아타고 같은 명령을 다시 시작한다."""
    if os.environ.get(_SWITCH_FLAG):
        return
    config = _config_path(argv)
    want = _peek_venv(config) if config else ""
    if not want:
        return

    venv = Path(want).expanduser()
    if venv.resolve() == Path(sys.prefix).resolve():
        return

    for python in (venv / "bin" / "python", venv / "Scripts" / "python.exe"):
        if python.exists():
            break
    else:
        print(f"설정({config})의 paths.venv 에 파이썬이 없습니다: {venv}\n"
              f"  경로를 고치거나, paths.venv 를 비우고 그 venv 를 activate 한 뒤 "
              f"실행하세요.", file=sys.stderr)
        raise SystemExit(2)

    print(f"[venv] {sys.prefix}\n    -> {venv}   (설정 paths.venv)", file=sys.stderr)
    os.environ[_SWITCH_FLAG] = "1"
    os.execv(str(python), [str(python), *sys.argv])


if __name__ == "__main__":
    switch_venv(sys.argv[1:])

    from src.template.main import main

    raise SystemExit(main())
