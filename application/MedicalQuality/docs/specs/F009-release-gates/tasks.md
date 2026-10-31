---
document: feature-tasks
feature: F009
status: in-progress
updated: "2026-10-14"
---

# F009 · 上線准入與責任接受任務

## 任務規則

- U10 已授權開發。勾選表示本條軟件實現及代表性工程檢查完成；專業條件和完整驗收按[當前臺賬](../../verification/F009-implementation.md)單獨核對，不以勾選代替臨床批准。
- 按同一 [Spec](spec.md) / [Plan](plan.md) 和 [用例](../../../evals/F009.json)交付，不增業務規則；有效結果在輸入不變時複用。
- 任務跨模塊實現同一業務結果，原始數據、規則/簽字歷史和獨立評測邊界保持。

## 任務清單

- [x] T001 准入申請固定範圍與基線
  - 來源：REQ-018, NFR-005, PSC-001, PSC-011, AC-F009-001
  - 依賴：無
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：scope/manifest、版本衝突與新申請關係；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-001；申請基線與配置變更合同測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T002 必要條件與缺項可解釋
  - 來源：REQ-018, NFR-001, NFR-003, PSC-008, PSC-011, AC-F009-002
  - 依賴：T001
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：條件結果、證據引用、明確阻斷與負責人；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-002；必要前置缺失的代表條件矩陣測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T003 高風險否決優先於平均指標
  - 來源：REQ-018, NFR-003, PSC-011, AC-F009-003
  - 依賴：T002
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：否決條目、申請狀態與不可豁免記錄；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-003；高風險否決獨立判定測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [ ] T004 關鍵人驗收與責任接受真實
  - 來源：REQ-018, NFR-004, NFR-005, PSC-008, PSC-009, PSC-011, AC-F009-004
  - 依賴：T001, T002, T003
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：具名決定、責任記錄、審計和拒絕；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-004；責任接受/缺崗位/事務故障測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T005 階段能力在服務端受控
  - 來源：REQ-018, NFR-001, NFR-003, PSC-008, PSC-011, AC-F009-005
  - 依賴：T004
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：允許動作、直接 API 拒絕及階段來源；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-005；三階段實際入口能力矩陣測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T006 條件失效後停用和回退保留歷史
  - 來源：REQ-018, NFR-003, NFR-004, NFR-005, PSC-009, PSC-011, AC-F009-006
  - 依賴：T005
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：停止事件、運行拒絕、歷史仍可回查；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-006；資格失效與受影響範圍回退測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T007 修復與擴大範圍必須重新核驗
  - 來源：REQ-018, NFR-003, NFR-005, PSC-001, PSC-011, AC-F009-007
  - 依賴：T001, T003, T006
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：新舊申請關係、複驗清單與拒絕原因；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-007；修復/版本變化/範圍擴大重驗測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T008 管理視圖顯示真實門檻與責任
  - 來源：REQ-018, NFR-004, NFR-006, PSC-008, PSC-009, PSC-011, PSC-013, AC-F009-008
  - 依賴：T004, T006, T007
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：條件明細、兩視口、返回狀態和審計；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-008；代表准入旅程與拒絕路徑瀏覽器走查，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T009 向運行與交付提供同一准入事實
  - 來源：REQ-018, NFR-003, NFR-005, PSC-001, PSC-009, PSC-011, AC-F009-009
  - 依賴：T005, T006, T008
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：同版 GateDecision、限制傳播和冪等結果；代表性工程結果見[實施臺賬](../../verification/F009-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F009-009；F009→運行/F010 合同與重複事件測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [ ] T010 完成本 Feature 驗收與真實交接
  - 來源：REQ-018, NFR-001, NFR-003, NFR-004, NFR-005, NFR-006, AC-F009-001, AC-F009-002, AC-F009-003, AC-F009-004, AC-F009-005, AC-F009-006, AC-F009-007, AC-F009-008, AC-F009-009
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008, T009
  - 修改：`backend/medical_quality/release.py`、`backend/medical_quality/access.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐用例輸入/版本、實際斷言/結果、原文/責任引用、未運行與限制，以及直接消費者接收結果；完整驗收未結束，真實結果/限制見[實施臺賬](../../verification/F009-implementation.md)。
  - 驗證：EV-F009-001, EV-F009-002, EV-F009-003, EV-F009-004, EV-F009-005, EV-F009-006, EV-F009-007, EV-F009-008, EV-F009-009；運行一次覆蓋本 Feature 的必要檢查集，複用已有效收據，組合驗收按產品套件單獨說明範圍。

## Task 數量複核

- 任務總數：10。
- 原因：每項任務交付一個獨立可核對結果，最後彙總證據與實際交接；依賴僅指本 Feature 內任務，上下游按 Map 及 Plan 合同接續。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | Spec/Plan/Tasks 與用例定義已補齊，尚無功能執行證據 | 實現/專業前置按 Plan OQ 落實；未安裝、部署或處理實際業務 |


## 當前交接狀態

固定準入基線、逐項缺項/風險否決、責任意見、服務器階段攔截、停用及重驗。 代表性實現/檢查已完成。未勾選的任務包括正式責任/專業核對（若適用）與整組最終驗收；詳情見[實現記錄](../../verification/F009-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
