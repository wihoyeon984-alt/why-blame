\# why-blame Benchmark



실제 오픈소스 Git History를 이용해 why-blame의 정확성을 평가합니다.



\## 목표



1\. Unsupported Claim Rate 측정

2\. False-WHY Rate 측정



\## 원칙



Ground Truth를 먼저 작성한 뒤 why-blame 결과와 비교합니다.



평가 Claim은 다음 세 종류로 구분합니다.



\- Supported: 실제 Evidence가 뒷받침함

\- Unsupported: Evidence에서 확인할 수 없음

\- Ambiguous: Evidence만으로 확정하기 어려움

