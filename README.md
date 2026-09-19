# 📜 Why-blame: 코드 한 줄의 전기(傳記)

> **"Git blame tells you WHO. Why-blame tells you WHY."**  
> `git blame`은 "누가 썼는지"만 알려줄 뿐 "왜 그렇게 되었는지"는 알려주지 않습니다.  
> **Why-blame은 WHY를 억지로 지어내는 도구가 아니라, 증거가 충분할 때만 WHY를 주장하는 도구입니다.**  
> 코드 한 줄의 탄생, 결함 수정, 롤백, 정착까지의 Git 이력과 실제 GitHub PR/Issue 본문 맥락을 추적하여 **검증 가능한 코드의 일대기(Biography)**를 복원합니다.

---

## 💡 Why Why-blame? (Before vs After)

### 🔴 Before: `git blame service.py`
기존 `git blame`은 마지막으로 코드를 건드린 사람과 시점만 보여주므로, 복잡한 조건문이 **왜 생겨났는지 맥락을 전혀 알 수 없습니다.**

```text
7c4ff011 (Alice   2026-09-18 10:00) 1: def pay(user):
2c17f746 (Bob     2026-09-18 14:30) 2:     if user.is_active and not user.is_cancelled:
8857c0c1 (Charlie 2026-09-19 09:15) 3:         charge_payment(user)