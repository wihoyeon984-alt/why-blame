# 📜 Why-blame: 코드 한 줄의 전기(傳記)

> **"Git blame tells you who. Why-blame tells you why."**  
> `git blame`은 "누가 썼는지"만 알려줄 뿐 "왜 이렇게 됐는지"는 알려주지 않습니다.  
> **Why-blame**은 코드의 변경 이력, 코드 Diff(-/+), GitHub PR/이슈를 추적하여 시간순 발자취(Timeline)와 변경 사유를 복원하는 개발자 생산성 도구입니다.

---

## ✨ 핵심 기능

1. **시간순 타임라인 & 코드 Diff 복원**:
   * 탄생(`🌱 BIRTH`), 롤백(`↩ REVERT`), 버그 수정(`🐛 BUG FIX`), 기능 추가(`✨ FEATURE`) 등 시계열 흐름 시각화
   * 각 커밋에서 **어떤 코드가 빠지고(`-`), 들어왔는지(`+`)** 실제 Diff 라인을 직접 노출
2. **실시간 GitHub API 결합**:
   * 원격 저장소를 자동 감지하여 커밋 메시지의 `#번호`에 해당하는 실제 GitHub 제목을 동적으로 연동
3. **정밀 증거 가중치 매트릭스 (Evidence Matrix)**:
   * 단순 커밋 횟수가 아닌 `Diff(+2)`, `Issue/PR 참조(+3)`, `제목 확인(+2)`, `Revert(+3)` 등을 종합 평가
   * 점수대별 등급: `LOW` (0~2) / `WEAK` (3~4) / `MODERATE` (5~7) / `HIGH` (8~10) / `VERY HIGH` (11+)
   * *Evidence score is a heuristic, not a factual certainty.*
4. **엄격한 할루시네이션 방지 (Zero-Hallucination Guard)**:
   * 증거 점수가 `LOW`(2점 이하)일 경우 추측하지 않고 `No reliable historical explanation found`로 명시적 거절
5. **다중 라인 범위 지원 & Windows 경로 안정성**:
   * `service.py:1-3` 코드 블록 범위 분석 지원 및 드라이브 문자(`C:\...`) 절대 경로 지원

---

## 🏗️ 아키텍처 (관심사 분리 모듈 구조)

* `git_tracker.py`: 로컬 Git 명령어(`git log -L`) 실행 및 라인 Diff 추출
* `github_client.py`: GitHub REST API 통신 및 예외 처리
* `timeline.py`: Conventional Commits 분류기 및 증거 가중치 매트릭스 계산 (순수 로직)
* `viewer.py`: 터미널 카드 렌더링 및 할루시네이션 가드 표기
* `main.py`: CLI 인자 파싱 및 전체 파이프라인 조립 진입점

---

## 🧪 단위 테스트 (Unit Tests)

`timeline.py`의 핵심 분류 및 스코어링 로직을 7종의 단위 테스트로 검증합니다:

```bash
python -m unittest test_timeline.py