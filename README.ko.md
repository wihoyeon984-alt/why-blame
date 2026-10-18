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
- 전체 테스트: `488 / 488`
- CI: Windows와 Ubuntu, Python 3.9·3.11·3.14에서 `6 / 6`
- Holdout v2 post-improvement:
  - 평가 대상: 동결된 사례 `10개`
  - Ground Truth claim: `40개`
  - Supported Ground Truth claim: `20개`
  - Supported claims presented: `20 / 20`
  - Claim precision: `1.000`
  - Supported recall: `1.000`
  - Unsafe presentation rate: `0.000`

> 위 결과는 동결된 Holdout v2 사례 10개와 Ground Truth claim 40개를
> 대상으로 한 내부 평가 결과입니다. Supported recall `1.000`은 이 평가
> 집합의 Supported Ground Truth claim 20개 중 20개가 제시되었음을
> 뜻합니다.
>
> Claim precision과 Unsafe presentation rate를 포함한 각 지표는 현재의
> 평가 집합과 판정 기준 안에서 계산되었습니다. 이 결과는 평가에 포함되지
> 않은 저장소, 프로그래밍 언어, 코드 구조 또는 변경 이력에서도 동일한
> 성능이 보장된다는 뜻이 아니며, Why-Blame의 일반 정확도가 100%임을
> 의미하지 않습니다.

## 4단계 빠른 실행

Why-Blame 저장소를 이미 내려받았고 GitHub CLI `gh`를 사용할 수 있다면,
다음 네 단계로 설치하고 첫 분석을 실행할 수 있습니다. 처음 설치하거나
문제가 발생한 경우에는 #5분-quick-start를 참고하십시오.

### 1. 가상환경 만들기

```powershell
python -m venv .venv
```

### 2. 안정 버전 다운로드하기

```powershell
gh release download v0.3.6 `
    --repo wihoyeon984-alt/why-blame `
    --pattern "why_blame-0.3.6-py3-none-any.whl"
```

### 3. 가상환경에 설치하기

```powershell
.\.venv\Scripts\python.exe -m pip install `
    .\why_blame-0.3.6-py3-none-any.whl
```

### 4. 설치 확인 후 첫 분석 실행하기

```powershell
.\.venv\Scripts\why-blame.exe --version
.\.venv\Scripts\why-blame.exe main.py:106-134
```

정상 설치되면 `why-blame 0.3.6`이 표시되고, 이어서 지정한 코드 범위의
변경 이력과 근거 평가가 출력됩니다.

## 5분 Quick Start

아래 절차는 Windows PowerShell 기준입니다. PowerShell 실행 정책 때문에
가상환경을 활성화하지 못해도 괜찮습니다. 가상환경의 Python과 실행 파일을
직접 사용합니다.

### 1. 준비하기

다음 프로그램이 필요합니다.

- Python 3.9 이상
- Git
- GitHub CLI `gh`

설치 상태를 확인합니다.

```powershell
python --version
git --version
gh --version
```

### 2. 저장소 내려받기

```powershell
git clone https://github.com/wihoyeon984-alt/why-blame.git
cd .\why-blame
```

이미 저장소를 내려받았다면 Why-Blame 저장소의 최상위 폴더로 이동합니다.

### 3. 가상환경 만들기

```powershell
python -m venv .venv
```

가상환경을 활성화할 필요는 없습니다. 이후 명령에서는 `.venv`의 Python과
실행 파일을 직접 사용합니다.

### 4. 안정 버전 다운로드

GitHub Release에서 `v0.3.6` wheel을 현재 폴더로 다운로드합니다.

```powershell
gh release download v0.3.6 `
    --repo wihoyeon984-alt/why-blame `
    --pattern "why_blame-0.3.6-py3-none-any.whl"
```

### 5. Why-Blame 설치

```powershell
.\.venv\Scripts\python.exe -m pip install `
    .\why_blame-0.3.6-py3-none-any.whl
```

이미 같은 버전이 설치되어 있다면 다음 안내가 표시될 수 있습니다.

```text
why-blame is already installed with the same version
```

이는 오류가 아닙니다.

### 6. 설치 확인

```powershell
.\.venv\Scripts\why-blame.exe --version
```

정상 결과:

```text
why-blame 0.3.6
```

### 7. 첫 분석 실행

Why-Blame 저장소에 실제로 존재하는 코드 범위를 분석합니다.

```powershell
.\.venv\Scripts\why-blame.exe main.py:106-134
```

이 예제에서는 다음 변경을 확인할 수 있습니다.

- CLI JSON 출력 기능이 처음 추가된 커밋
- 손상된 CLI 오류 메시지를 정상 한국어로 복구한 커밋
- 관련 PR과 실제 diff
- Confidence와 Coverage
- 현재 근거로 확인할 수 없는 한계

JSON 결과가 필요하면 `--json`을 추가합니다.

```powershell
.\.venv\Scripts\why-blame.exe `
    main.py:106-134 `
    --json
```

### 8. 결과 읽기

- `CURRENT CODE`: 지정한 범위의 현재 코드
- `WHY`: 근거로 확인할 수 있는 변경 과정
- `HISTORY`: 관련 커밋, diff, PR 및 Issue
- `COVERAGE`: 분석 범위에 연결된 근거의 범위
- `CONFIDENCE`: 현재 설명을 뒷받침하는 근거의 강도
- `LIMITATION`: 현재 근거만으로 확인할 수 없는 내용

`Coverage 100%`는 개발자의 실제 의도가 100% 입증됐다는 뜻이 아닙니다.
분석 범위의 근거 이벤트가 결과에 연결됐다는 뜻입니다.

Confidence 역시 Why-Blame 전체의 정확도나 모든 코드에 대한 성공률이
아닙니다.

### 9. 과거 diff에 `???`가 표시되는 경우

첫 분석 예제에는 다음과 같은 과거 diff가 표시될 수 있습니다.

```diff
- "--json ??? ? ?? ??? ? ????."
+ "--json 옵션은 한 번만 지정할 수 있습니다."
```

이 `???`는 현재 프로그램의 오류가 아닙니다. 과거 커밋에 실제로 존재했던
손상 문자열과 이를 복구한 후속 변경을 Git 이력에서 그대로 보여 주는
것입니다.

### 10. 다른 저장소 분석하기

다른 저장소를 분석할 때는 해당 Git 저장소의 최상위 폴더로 이동한 뒤,
실제로 존재하고 Git에 커밋된 파일을 지정해야 합니다.

추적 중인 파일은 다음 명령으로 확인할 수 있습니다.

```powershell
git ls-files
```

목록에 표시된 실제 파일과 줄 번호를 사용하십시오. 문서에 적힌 설명용
경로나 파일 이름을 그대로 실행하면 안 됩니다.

### 11. 오래된 설치 때문에 실행되지 않는 경우

다음 오류가 발생하면 이전에 설치한 오래된 Why-Blame이 실행되고 있을 수
있습니다.

```text
ModuleNotFoundError: No module named 'json_renderer'
```

명령 위치와 전역 설치 상태를 확인합니다.

```powershell
Get-Command why-blame -All
python -m pip show why-blame
```

오래된 전역 설치를 제거합니다.

```powershell
python -m pip uninstall -y why-blame
```

그다음 전역 명령 대신 가상환경의 실행 파일을 사용합니다.

```powershell
.\.venv\Scripts\why-blame.exe --version
```

### 12. 다운로드 파일 정리

설치가 끝난 뒤 wheel을 삭제해도 가상환경에 설치된 Why-Blame은 계속
사용할 수 있습니다.

```powershell
Remove-Item `
    .\why_blame-0.3.6-py3-none-any.whl `
    -Force
```

Why-Blame의 설명은 최종 판단을 대신하지 않습니다. 중요한 코드 변경을
검토할 때는 표시된 커밋, diff, PR과 Issue 원문을 함께 확인하십시오.

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

화면 상단의 언어 선택 상자에서 English와 한국어를 전환할 수 있습니다.
분석 결과가 표시된 상태에서 언어를 바꿔도 현재 결과는 유지됩니다.
화면의 제목과 안내 문구만 번역하며, JSON 필드명, 오류 코드, Confidence
등급과 같은 내부 값은 호환성을 위해 변경하지 않습니다.

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
