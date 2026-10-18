# Why-Blame 처음 사용하기

이 문서는 프로그래밍과 Git을 막 배우기 시작한 사람을 위한 안내서입니다. 모든 기능을 한 번에 이해하려 하지 말고, **설치 → 첫 분석 → 결과 읽기** 순서로 따라 해 보세요.

> 이 안내서는 Windows PowerShell과 저장소의 현재 개발 버전(`main`)을 기준으로 합니다. 안정 릴리스 `v0.3.6`을 설치하려면 [GitHub Releases](https://github.com/wihoyeon984-alt/why-blame/releases/tag/v0.3.6)와 [한국어 README](../README.ko.md)를 참고하세요.

## 1. Why-Blame은 무엇인가요?

일반적인 `git blame`은 코드의 각 줄을 마지막으로 수정한 커밋을 찾는 데 도움을 줍니다. Why-Blame은 Git 기록과 코드 변경 내용(diff), 커밋 메시지, 관련 PR·Issue 등을 살펴보고 **코드가 어떤 과정을 거쳐 지금 모습이 되었는지** 설명하려고 합니다.

중요한 원칙이 하나 있습니다. **관련 기록이 있다는 사실만으로 변경 이유까지 증명되는 것은 아닙니다.** 근거가 부족하면 이유를 단정하지 않고, 확인할 수 없는 부분을 표시하는 것이 목표입니다.

## 2. 먼저 알아둘 단어

| 단어 | 쉬운 뜻 |
|---|---|
| Git | 파일 변경 기록을 저장하고 관리하는 도구 |
| 저장소(repository) | 코드와 변경 기록이 들어 있는 프로젝트 폴더 |
| 커밋(commit) | 특정 시점의 변경 사항을 기록한 항목 |
| diff | 변경 전과 변경 후의 차이 |
| PR | 코드 변경을 제안하고 검토하기 위한 기록 |
| Issue | 작업이나 문제를 논의하는 기록 |
| 근거(evidence) | 설명을 뒷받침하는 코드나 기록 |

## 3. 준비하기

이 안내에서는 Windows PowerShell을 사용합니다. Python 3.9 이상과 Git이 필요합니다. GitHub CLI(`gh`)는 필요하지 않습니다.

PowerShell을 열고 다음 명령을 각각 실행하세요.

```powershell
python --version
git --version
```

각 명령이 버전 번호를 보여 주면 됩니다. 명령을 찾을 수 없다는 메시지가 나오면 Python 또는 Git을 설치한 뒤 PowerShell을 다시 여세요.

## 4. 코드 내려받기

아래 명령을 한 줄씩 실행합니다.

```powershell
git clone https://github.com/wihoyeon984-alt/why-blame.git
cd why-blame
```

첫 번째 명령은 프로젝트 파일을 컴퓨터로 복사합니다. 두 번째 명령은 복사된 프로젝트 폴더로 이동합니다.

## 5. 별도의 Python 환경 만들고 설치하기

가상환경은 프로젝트마다 사용하는 Python 패키지를 분리해 충돌을 줄여 줍니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

### Python 대화형 셸이 열린 경우

`.venv`의 Python 실행 파일만 다음처럼 실행하면 Python 대화형 셸이
열리고 화면에 `>>>`가 표시됩니다.

```powershell
.\.venv\Scripts\python.exe
```

이 화면에서는 PowerShell 명령을 실행할 수 없습니다. 다음 명령을
입력해 Python을 종료하고 PowerShell로 돌아오세요.

```python
exit()
```

Python 버전을 확인할 때는 `--version`, 개발 버전을 설치할 때는
`-m pip install -e .`을 Python 실행 파일 뒤에 붙여야 합니다.


이 방식은 현재 내려받은 저장소의 소스 코드를 설치합니다. 따라서 **최신 개발 버전**으로 실행하는 방법입니다. 안정 릴리스 버전이 필요한 경우에는 위쪽의 릴리스 안내를 사용하세요.

PowerShell의 실행 정책 때문에 가상환경 활성화가 거부되더라도 걱정하지 마세요. 이 안내에서는 가상환경을 활성화하지 않고 그 안의 Python을 직접 실행합니다.

## 6. 설치 확인하기

```powershell
.\.venv\Scripts\why-blame.exe --version
```

버전 정보가 나오면 실행 파일을 찾은 것입니다. 사용 가능한 옵션을 보려면 다음을 실행하세요.

```powershell
.\.venv\Scripts\why-blame.exe --help
```

## 7. 첫 분석 실행하기

프로젝트 폴더에서 다음 명령을 실행합니다.

```powershell
.\.venv\Scripts\why-blame.exe main.py:106-134
```

`main.py:106-134`는 `main.py` 파일의 106번째 줄부터 134번째 줄까지 분석하라는 뜻입니다. 이 예시는 Why-Blame 저장소 안의 파일을 대상으로 합니다. 코드가 바뀌면 결과도 달라질 수 있습니다.

JSON 형식이 필요할 때는 다음처럼 실행할 수 있습니다.

```powershell
.\.venv\Scripts\why-blame.exe main.py:106-134 --json
```

처음에는 JSON보다 기본 화면 출력을 먼저 확인하는 것을 추천합니다.

## 8. 결과를 읽는 방법

| 항목 | 쉬운 설명 |
|---|---|
| `CURRENT CODE` | 선택한 범위에 현재 들어 있는 코드 |
| `WHY` | 현재 근거로 설명할 수 있는 변경 과정 |
| `HISTORY` | 관련 커밋과 변경 기록 |
| `COVERAGE` | 분석 대상에 근거가 얼마나 연결되었는지 보여 주는 지표 |
| `CONFIDENCE` | 이번 설명을 뒷받침하는 근거가 얼마나 강한지 나타내는 지표 |
| `LIMITATION` | 현재 근거만으로 확정할 수 없는 내용 |

**주의:** Coverage가 100%라고 해서 개발자의 실제 의도까지 100% 입증됐다는 뜻은 아닙니다. Confidence 역시 모든 프로젝트에서의 성공률이나 프로그램 전체의 정확도를 뜻하지 않습니다. 중요한 변경은 커밋, diff, PR·Issue 원문을 함께 확인하세요.

## 9. 다른 프로젝트 분석하기

1. 분석할 프로젝트가 Git 저장소인지 확인합니다.
2. 그 프로젝트 폴더로 이동합니다.
3. 실제로 존재하고 Git에 기록된 파일과 줄 번호를 지정합니다.

Git이 추적하는 파일 목록은 다음 명령으로 확인할 수 있습니다.

```powershell
git ls-files
```

다른 프로젝트에서 Why-Blame 실행 파일을 호출할 때는 설치된 실행 파일의 전체 경로를 사용하거나, 가상환경의 `Scripts` 폴더가 경로에 잡혀 있는지 확인하세요. 예시 경로를 그대로 복사하지 말고 자신의 폴더 이름에 맞게 바꾸세요.

## 10. 자주 생기는 문제

### `python` 또는 `git` 명령을 찾을 수 없습니다
해당 프로그램이 설치되어 있는지 확인하고, 설치한 뒤 PowerShell을 다시 여세요.

### Git 저장소가 아니라는 오류가 나옵니다
현재 위치가 분석 대상 프로젝트의 폴더인지 확인하고, Git 저장소의 최상위 폴더로 이동하세요.

### 파일을 찾을 수 없다는 오류가 나옵니다
파일명과 폴더 경로가 맞는지 확인하세요. 분석하려는 파일이 해당 Git 저장소에 실제로 있는지도 확인합니다.

### 줄 번호 범위가 잘못되었다는 오류가 나옵니다
시작 줄이 끝 줄보다 크지 않은지, 요청한 줄 번호가 파일의 실제 범위 안에 있는지 확인하세요.

### 오래된 설치 때문에 모듈을 찾지 못한다는 오류가 나옵니다
전역에 설치된 오래된 버전이 실행되고 있을 수 있습니다. 이 안내에서는 전역 명령 대신 다음처럼 가상환경의 실행 파일을 직접 사용하세요.

```powershell
.\.venv\Scripts\why-blame.exe --version
```

## 11. 웹 대시보드는 CLI 다음에 시도하기

먼저 CLI로 한 번 분석한 뒤 웹 화면을 실행하는 것을 추천합니다. 저장소 폴더에서 다음 명령을 실행하세요.

```powershell
python -m venv .venv-web
.\.venv-web\Scripts\python.exe -m pip install -r .\requirements-web.txt
.\.venv-web\Scripts\python.exe -m streamlit run .\webapp\app.py
```

브라우저가 자동으로 열리지 않으면 `http://localhost:8501`에 접속합니다. 이 대시보드는 기본적으로 내 컴퓨터에서 실행되는 로컬 화면입니다.

## 마지막으로 기억할 점

Why-Blame은 개발자의 생각을 직접 읽는 도구가 아닙니다. Git 기록과 관련 자료를 바탕으로 변경 과정을 설명하려고 합니다. 근거가 부족하면 설명을 보류할 수 있습니다. **좋은 결과는 설명을 많이 만드는 결과가 아니라, 근거가 있는 부분과 아직 모르는 부분을 구분하는 결과입니다.**

- [저장소](https://github.com/wihoyeon984-alt/why-blame)
- [한국어 README](../README.ko.md)
- [안정 릴리스 v0.3.6](https://github.com/wihoyeon984-alt/why-blame/releases/tag/v0.3.6)
