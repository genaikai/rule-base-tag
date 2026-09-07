# Rule-Based Tagging Framework

LLM 답변을 평가하여 다양한 태그를 부여하는 다중 프로젝트 프레임워크입니다.

## 구조

```
run.py
src/
  framework/           (공유 - 수정 금지)
    contracts.py       입력 스키마
    base.py            Tagger 베이스
    report.py, load.py, synth.py
  
  template/            (복사해서 프로젝트 생성)
    main.py, pipeline.py
  
  error_keyword/, ...  (10개 태거 - 모든 프로젝트 공유)
  
  taggers/             (추가 태거들)
```

## 새로운 프로젝트 추가

```bash
# 1. template 복사
cp -r src/template src/my_project

# 2. my_project의 pipeline.py 구현
$EDITOR src/my_project/pipeline.py

# 3. 실행
python run.py --dry-run
```

## 태그 종류

- 에러 키워드
- 답변 잘림
- 언어 Mixing
- Format 깨짐
- 민감정보 포함
- Empty Retrieved Docs
- Empty Search Query
- 질답 언어 불일치
- 유효하지 않은 링크
- 모델 생각중 멈춤

## 사용법

```bash
python run.py --dry-run          # 합성 데이터 테스트
python run.py --data input.csv   # 실제 데이터 처리
```
