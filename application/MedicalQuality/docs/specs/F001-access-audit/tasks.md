---
document: feature-tasks
feature: F001
status: completed
updated: "2026-10-14"
---

# F001 · 訪問授權與責任審計任務

## 任務規則

- U10 已授權開發。勾選表示本條軟件實現及代表性工程檢查完成；專業條件和完整驗收按[當前臺賬](../../verification/F001-implementation.md)單獨核對，不以勾選代替臨床批准。
- 按同一 [Spec](spec.md) / [Plan](plan.md) 和 [用例](../../../evals/F001.json)交付，不增業務規則；有效結果在輸入不變時複用。
- 任務跨模塊實現同一業務結果，原始數據、規則/簽字歷史和獨立評測邊界保持。

## 任務清單

- [x] T001 可信身份與默認拒絕
  - 來源：REQ-015, NFR-004, PSC-008, AC-F001-001
  - 依賴：無
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：實際 actor 映射、拒絕原因與無正文響應；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-001；可信身份/過期/角色偽造合同測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T002 角色動作與對象用途共同授權
  - 來源：REQ-015, NFR-001, PSC-008, AC-F001-002
  - 依賴：T001
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：允許/拒絕集合、實際有效條件和策略版本；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-002；角色×對象×用途的代表性決策矩陣測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T003 所有讀取表面遵守同一範圍
  - 來源：REQ-015, NFR-001, NFR-004, PSC-008, AC-F001-003
  - 依賴：T002
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：各入口實際集合、數據庫角色/事務上下文和拒絕記錄；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-003；代表病例的多入口授權與 RLS 運行角色測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T004 後臺與模型工具不能擴大數據域
  - 來源：REQ-015, NFR-001, PSC-008, AC-F001-004
  - 依賴：T002
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：固定任務範圍、拒絕事件、未授權網絡調用為零；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-004；Worker/模型工具拒絕與未外發探針測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T005 業務變更與必要審計共同成立
  - 來源：REQ-016, NFR-004, NFR-005, PSC-009, AC-F001-005
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：前後狀態、審計/事件 ID、一致提交或回滾；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-005；同庫提交邊界故障注入測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T006 重複請求與過期操作不造新事實
  - 來源：REQ-016, NFR-005, PSC-009, AC-F001-006
  - 依賴：T005
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：唯一操作結果、衝突記錄與當前版本；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-006；請求摘要/版本競爭與響應丟失測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T007 撤權和策略更新立即限制新消費
  - 來源：REQ-015, REQ-016, NFR-001, NFR-005, PSC-008, PSC-009, AC-F001-007
  - 依賴：T003, T004, T005
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：策略版本、失效時間和停止消費記錄；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-007；撤權傳播到緩存/Worker/下載的同範圍測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T008 審計查詢可追溯且最小化
  - 來源：REQ-016, NFR-001, NFR-004, PSC-008, PSC-009, AC-F001-008
  - 依賴：T003, T005, T006
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：授權軌跡、最小字段與拒絕/脫敏記錄；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-008；審計回查和敏感輸出邊界測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T009 缺生產留存和責任參數時限制啟用
  - 來源：REQ-015, REQ-016, NFR-001, NFR-004, PSC-008, PSC-009, AC-F001-009
  - 依賴：T002, T005
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：實際條件缺口、允許/限制用途及不啟用記錄；代表性工程結果見[實施臺賬](../../verification/F001-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F001-009；缺配置與用途隔離合同測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T010 完成本 Feature 驗收與真實交接
  - 來源：REQ-015, REQ-016, NFR-001, NFR-004, NFR-005, AC-F001-001, AC-F001-002, AC-F001-003, AC-F001-004, AC-F001-005, AC-F001-006, AC-F001-007, AC-F001-008, AC-F001-009
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008, T009
  - 修改：`backend/medical_quality/access.py`、`backend/medical_quality/common.py`、`backend/medical_quality/db.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐用例輸入/版本、實際斷言/結果、原文/責任引用、未運行與限制，以及直接消費者接收結果；完整驗收未結束，真實結果/限制見[實施臺賬](../../verification/F001-implementation.md)。
  - 驗證：EV-F001-001, EV-F001-002, EV-F001-003, EV-F001-004, EV-F001-005, EV-F001-006, EV-F001-007, EV-F001-008, EV-F001-009；運行一次覆蓋本 Feature 的必要檢查集，複用已有效收據，組合驗收按產品套件單獨說明範圍。

## Task 數量複核

- 任務總數：10。
- 原因：每項任務交付一個獨立可核對結果，最後彙總證據與實際交接；依賴僅指本 Feature 內任務，上下游按 Map 及 Plan 合同接續。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | Spec/Plan/Tasks 與用例定義已補齊，尚無功能執行證據 | 實現/專業前置按 Plan OQ 落實；未安裝、部署或處理實際業務 |


## 當前交接狀態

會話/CSRF、真實 OIDC 回調密碼學、RBAC/對象用途、RLS、撤權、事務審計和冪等。 代表性實現/檢查已完成。本 Feature 軟件任務與本輪直接檢查均已完成；專業或上游整體驗收仍沿 Feature Map 的狀態；詳情見[實現記錄](../../verification/F001-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
