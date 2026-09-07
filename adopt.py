#!/usr/bin/env python3
"""Rule-based tagging 프로젝트를 설정합니다.

프로젝트와 태거들을 생성합니다.

사용법:
  python adopt.py
"""

import shutil
import sys
from pathlib import Path


def create_tagger_template():
    """태거 템플릿이 없으면 생성합니다."""
    taggers_dir = Path("src/taggers")
    template_dir = taggers_dir / "template"

    if not template_dir.exists():
        template_dir.mkdir(parents=True, exist_ok=True)

        # __init__.py
        (template_dir / "__init__.py").write_text(
            '"""태거 템플릿."""\n'
            'from .detector import Tagger\n'
            '__all__ = ["Tagger"]\n'
        )

        # detector.py
        (template_dir / "detector.py").write_text(
            '"""태거 구현."""\n'
            'from ..framework.base import Tagger\n'
            '\n'
            'class TemplateTagger(Tagger):\n'
            '    """TODO: 태거 이름과 로직 구현하세요."""\n'
            '    name = "template"\n'
            '    \n'
            '    def tag(self, rows: list[dict]) -> dict:\n'
            '        """행 데이터를 태깅합니다."""\n'
            '        flagged = []\n'
            '        for i, row in enumerate(rows):\n'
            '            if self._detect(row):\n'
            '                flagged.append(i)\n'
            '        return {\n'
            '            "count": len(flagged),\n'
            '            "rows": flagged,\n'
            '            "note": f"{len(flagged)}/{len(rows)} 행에서 감지됨",\n'
            '        }\n'
            '    \n'
            '    def _detect(self, row: dict) -> bool:\n'
            '        """TODO: 검출 로직 구현."""\n'
            '        return False\n'
        )

        print(f"  + src/taggers/template/ (태거 템플릿)")


def create_project_template():
    """프로젝트 템플릿이 없으면 생성합니다."""
    template_dir = Path("src/template")
    if not template_dir.exists():
        template_dir.mkdir(parents=True, exist_ok=True)
        print(f"  + src/template/ (프로젝트 템플릿)")


def main():
    print("Rule-Based Tagging 프로젝트 설정\n")

    # 템플릿 생성
    print("템플릿 생성 중...")
    create_project_template()
    create_tagger_template()

    # 프로젝트 개수
    print("\n몇 개 프로젝트? (1~5)", end=" ")
    try:
        num_projects = int(input().strip())
        if not 1 <= num_projects <= 5:
            print("1~5 사이의 숫자를 입력하세요")
            sys.exit(1)
    except ValueError:
        print("숫자를 입력하세요")
        sys.exit(1)

    projects = []
    for i in range(num_projects):
        print(f"프로젝트 {i + 1} 이름? ", end="")
        name = input().strip()
        if not name or not name.replace("_", "").isalnum():
            print("유효한 이름 (알파벳, 숫자, 언더스코어)")
            sys.exit(1)
        projects.append(name)

    # 태거 개수
    print(f"\n몇 개 태거? (1~10)", end=" ")
    try:
        num_taggers = int(input().strip())
        if not 1 <= num_taggers <= 10:
            print("1~10 사이의 숫자를 입력하세요")
            sys.exit(1)
    except ValueError:
        print("숫자를 입력하세요")
        sys.exit(1)

    taggers = []
    for i in range(num_taggers):
        print(f"태거 {i + 1} 이름? ", end="")
        name = input().strip()
        if not name or not name.replace("_", "").isalnum():
            print("유효한 이름")
            sys.exit(1)
        taggers.append(name)

    # 프로젝트 생성
    print("\n생성 중...")
    template_dir = Path("src/template")
    for proj in projects:
        proj_dir = Path("src") / proj
        if proj_dir.exists():
            print(f"  ⊘ src/{proj}/ (이미 있음)")
        else:
            shutil.copytree(template_dir, proj_dir)
            print(f"  + src/{proj}/")

    # 태거 생성
    taggers_template = Path("src/taggers/template")
    for tagger in taggers:
        tagger_dir = Path("src/taggers") / tagger
        if tagger_dir.exists():
            print(f"  ⊘ src/taggers/{tagger}/ (이미 있음)")
        else:
            shutil.copytree(taggers_template, tagger_dir)
            # detector.py의 클래스명 수정
            detector = tagger_dir / "detector.py"
            content = detector.read_text()
            class_name = "".join(w.capitalize() for w in tagger.split("_")) + "Tagger"
            content = content.replace("TemplateTagger", class_name)
            content = content.replace('name = "template"', f'name = "{tagger}"')
            detector.write_text(content)
            # __init__.py 수정
            init = tagger_dir / "__init__.py"
            init.write_text(
                f'"""태거: {tagger}."""\n'
                f'from .detector import {class_name}\n'
                f'__all__ = ["{class_name}"]\n'
            )
            print(f"  + src/taggers/{tagger}/")

    print(f"\n✓ 완료!")
    print(f"  프로젝트: {', '.join(projects)}")
    print(f"  태거: {', '.join(taggers)}")
    print(f"\n다음:")
    print(f"  $EDITOR src/framework/contracts.py")
    print(f"  $EDITOR src/{projects[0]}/pipeline.py")
    print(f"  python run.py --dry-run")


if __name__ == "__main__":
    main()
