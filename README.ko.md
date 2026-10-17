# Why-Blame 한국어 안내

[English README](README.md)

Why-Blame은 Git 이력, diff, 커밋 메시지, PR 및 Issue를 바탕으로
코드가 현재 형태에 도달한 과정을 설명하는 증거 중심 분석 도구입니다.

## 핵심 원칙

> 근거가 뒷받침할 수 있는 내용만 설명하고, 근거가 끝나는 지점에서 멈춥니다.

- 확인되지 않은 정보를 사실처럼 제시하지 않습니다.
- 근거가 부족하면 신뢰도를 낮추고 한계를 명확하게 표시합니다.
- 사람용 CLI, 프로그램용 JSON, 로컬 웹 대시보드를 제공합니다.
- 분석 결과와 원본 근거를 함께 확인할 수 있습니다.

## 현재 상태

- 최신 안정 릴리스: `v0.3.6`
- 최신 웹 대시보드: `main` 브랜치
- 전체 테스트: `450 / 450`
- CI: Windows와 Ubuntu, Python 3.9·3.11·3.14에서 `6 / 6`
- Claim precision: `1.000`
- Supported recall: `1.000`
- Unsafe presentation rate: `0.000`

## CLI 사용 방법

GitHub Release에서 wheel을 내려받아 설치할 수 있습니다.

    python -m pip install .\why_blame-0.3.6-py3-none-any.whl
    why-blame --version

파일과 줄 범위를 지정해 분석합니다.

    why-blame service.py:10
    why-blame service.py:10-15
    why-blame service.py:10 --json

## 웹 대시보드 실행

웹 전용 가상환경을 준비하고 대시보드를 실행합니다.

    python -m venv .venv-web
    .\.venv-web\Scripts\python.exe -m pip install -r .\requirements-web.txt
    .\.venv-web\Scripts\python.exe -m streamlit run .\webapp\app.py

브라우저가 열리지 않으면 http://localhost:8501 에 접속합니다.

## 분석 결과 읽는 방법

- Confidence: 코드 변경 이유를 설명할 수 있는 최종 신뢰도입니다.
- Coverage: 확인된 근거가 분석 대상에 연결되는 범위입니다.
- Evidence events: 발견된 변경 이력의 수입니다.
- Rollbacks: 되돌리기 이력이 발견된 횟수입니다.
- Limitations: 현재 근거만으로 확정하기 어려운 내용입니다.

Confidence가 WEAK인 결과는 프로그램 오류가 아닙니다.
PR 또는 Issue 근거가 확인되지 않거나 rollback 이력이 복잡한 경우,
Why-Blame은 설명을 과장하지 않고 신뢰도를 낮추며 한계를 공개합니다.

## JSON 오류 코드

- INVALID_ARGUMENTS: 잘못된 명령행 인자
- NO_HISTORY: 관련 Git 이력이 없음
- FILE_NOT_FOUND: 파일을 찾을 수 없음
- NOT_A_GIT_REPOSITORY: Git 저장소가 아님
- LINE_RANGE_OUT_OF_BOUNDS: 요청한 줄 범위가 파일 길이를 초과함
- FILE_READ_ERROR: 파일을 읽을 수 없음
- GIT_COMMAND_FAILED: Git 이력 분석 명령이 실패함

JSON의 필드 이름, schema_version, 오류 코드는 번역하지 않습니다.
표시 언어와 프로그램 연동 형식을 분리해 호환성을 유지합니다.

## 알려진 한계

- 로컬 웹 대시보드는 사용자 컴퓨터의 저장소를 분석합니다.
- 공개 웹 서버에서는 사용자 컴퓨터의 로컬 경로에 접근할 수 없습니다.
- PR 또는 Issue를 조회할 수 없으면 Coverage가 낮아질 수 있습니다.
- rollback이 포함된 이력은 최종 설명의 모호성을 높일 수 있습니다.

## 발표용 빠른 시연

1. 웹 대시보드를 실행합니다.
2. 저장소 경로와 service.py, 줄 1-1을 입력합니다.
3. 현재 코드와 변경 이력을 확인합니다.
4. Confidence, Coverage, Rollbacks와 한계를 설명합니다.
5. Diff evidence와 관련 참조를 펼칩니다.
6. Raw JSON과 JSON 다운로드 기능을 보여줍니다.

Why-Blame의 핵심은 설명을 많이 만드는 것이 아니라,
확인 가능한 근거의 범위 안에서만 설명하는 것입니다.
