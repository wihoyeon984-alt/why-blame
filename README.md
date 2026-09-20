# 📜 why-blame: 코드 변경의 이유를 Evidence로 추적하기

> **Git blame tells you WHO. Why-blame shows the evidence behind WHY.**

`why-blame`은 Git과 GitHub의 변경 이력을 추적하여  
**코드가 어떤 역사와 근거를 거쳐 현재 형태에 이르렀는지 설명하는 CLI 도구**입니다.

기존 `git blame`이 주로 다음 질문에 답한다면:

> 누가 이 코드를 변경했는가?

`why-blame`은 한 단계 더 나아가 다음을 추적합니다.

> 이 코드는 어떤 변경 이력과 Evidence를 거쳐 현재 형태가 되었는가?

하지만 가장 중요한 원칙이 있습니다.

> **설명할 수 없는 것은 설명하지 않습니다.**

`why-blame`은 그럴듯한 WHY를 임의로 생성하지 않습니다.

Commit Message, Diff, PR/Issue, Timeline 등의 Evidence를 수집하고  
Consistency와 Confidence를 평가한 뒤,  
**확인된 Evidence가 허용하는 범위에서만 WHY를 설명합니다.**

---

## 💡 Why why-blame?

기존 `git blame`은 코드의 마지막 변경 정보를 확인하는 데 유용합니다.

예:

```text
7c4ff011 (...) 1: def pay(user):
2c17f746 (...) 2:     if user.is_active:
8857c0c1 (...) 3:         charge(user)