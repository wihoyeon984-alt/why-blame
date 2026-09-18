\# 📜 Why-blame: 코드 한 줄의 전기(傳記)



> \*\*"Git blame tells you who. Why-blame tells you why."\*\*  

> `git blame`은 "누가 썼는지"만 알려주고, 정작 궁금한 "왜 이렇게 됐는지"는 알려주지 않습니다.  

> \*\*Why-blame\*\*은 코드의 변경 이력과 GitHub 이슈/PR을 추적하여 시간순 발자취(Timeline)를 복원해 주는 개발자 도구입니다.



\---



\## ✨ 핵심 기능



1\. \*\*시계열 타임라인 (Timeline)\*\*: 탄생(`🌱 BIRTH`)부터 롤백(`↩ REVERT`), 버그 수정(`🐛 BUG FIX`)까지 시간순 흐름 시각화

2\. \*\*GitHub API 실시간 결합\*\*: 커밋 메시지의 `#번호`를 감지하여 실제 GitHub 웹의 PR/이슈 제목을 자동으로 연동

3\. \*\*증거 기반 신뢰도 (Evidence Strength)\*\*: 롤백 유무와 변경 횟수를 바탕으로 분석 신뢰도를 투명하게 판정

4\. \*\*다중 라인 범위 지원\*\*: 단일 줄뿐만 아니라 `service.py:1-3`처럼 함수 블록 전체의 변천사 추적 지원



\---



\## 🖥️ 실행 화면 예시



```text

┌────────────────────────────────────────────────────────┐

│ 📜 WHY-BLAME                                           │

│ service.py:1-3                                         │

│ 🌐 GitHub: octocat/Hello-World                         │

├────────────────────────────────────────────────────────┤

│ CURRENT (현재 코드)                                    │

│ > def pay(user):                                       │

│ >     if user.is\_active and not user.is\_cancelled an   │

│ >         charge(user)                                 │

├────────────────────────────────────────────────────────┤

│ TIMELINE (시간순 발자취)                               │

│                                                        │

│ 2026-09-18  🌱 BIRTH (7c4ff01)                        │

│   feat: initial payment check (#101)                   │

│   ↳ #101 ('Update README')                             │

│                      ↓                                 │

│ 2026-09-18  🐛 BUG FIX (2c17f74)                      │

│   fix: prevent duplicate charge (#205) Fixes #200      │

│   ↳ #205, #200                                         │

│                      ↓                                 │

│ 2026-09-19  🐛 BUG FIX (2f467c3)                      │

│   fix: handle cancelled orders (#310)                  │

│   ↳ #310 ('Laborum enim explicabo labore neque tenet') │

│                      ↓                                 │

│ 2026-09-19  ↩ REVERT (8857c0c)                        │

│   revert: rollback temporary condition                 │

│                      ↓                                 │

│ 2026-09-19  ✨ FEATURE (887d17e)                       │

│   feat: verify user status (#1347)                     │

│   ↳ #1347 ('Yellow !')                                 │

│                                                        │

├────────────────────────────────────────────────────────┤

│ EVIDENCE STRENGTH                                      │

│ • Total Events: 5개                                    │

│ • Reverts: 1회                                         │

│ • Evidence Strength: STRONG                            │

└────────────────────────────────────────────────────────┘

