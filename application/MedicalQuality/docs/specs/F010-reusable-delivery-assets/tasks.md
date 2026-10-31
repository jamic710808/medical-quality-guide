---
document: feature-tasks
feature: F010
status: in-progress
updated: "2026-10-14"
---

# F010 · 醫療資產固化與複用交付任務

## 任務規則

- U10 已授權開發。勾選表示本條軟件實現及代表性工程檢查完成；專業條件和完整驗收按[當前臺賬](../../verification/F010-implementation.md)單獨核對，不以勾選代替臨床批准。
- 按同一 [Spec](spec.md) / [Plan](plan.md) 和 [用例](../../../evals/F010.json)交付，不增業務規則；有效結果在輸入不變時複用。
- 任務跨模塊實現同一業務結果，原始數據、規則/簽字歷史和獨立評測邊界保持。

## 任務清單

- [x] T001 導出固定資產與依賴基線
  - 來源：REQ-019, NFR-002, NFR-005, PSC-001, PSC-012, AC-F010-001
  - 依賴：無
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：manifest、依賴/版本及變化拒絕記錄；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-001；多資產基線凍結與依賴一致性測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T002 授權、許可和來源角色限制導出
  - 來源：REQ-019, NFR-001, NFR-004, PSC-008, PSC-009, PSC-012, AC-F010-002
  - 依賴：T001
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：包含/排除與理由、目標用途、許可/授權引用；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-002；帶禁止資產的導出篩選與未讀取探針測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T003 候選和醫院定製狀態不被升級
  - 來源：REQ-019, NFR-002, NFR-005, PSC-001, PSC-012, AC-F010-003
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：資產狀態、限制和未放行記錄；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-003；資格/來源性質與導出狀態保真測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T004 生成與重試不發佈半成品
  - 來源：REQ-019, NFR-005, NFR-004, PSC-009, PSC-012, AC-F010-004
  - 依賴：T001, T002, T003
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：臨時/已發佈狀態、摘要/操作ID和對賬結果；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-004；資源/元數據提交邊界故障與冪等測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T005 接收檢查發現篡改、缺依賴與不兼容
  - 來源：REQ-019, NFR-002, NFR-005, PSC-001, PSC-012, AC-F010-005
  - 依賴：T003, T004
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐資產核對結果、可復現條件與拒絕原因；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-005；完整性/依賴/Schema 的受限接收檢查，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T006 下載與撤權遵守當前範圍
  - 來源：REQ-019, NFR-001, NFR-004, PSC-008, PSC-009, AC-F010-006
  - 依賴：T002, T004
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：實際下載範圍、拒絕與訪問審計；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-006；當前授權/過期引用/撤權下載測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T007 資產查看與交接說明可操作
  - 來源：REQ-019, NFR-002, NFR-006, PSC-001, PSC-012, PSC-013, AC-F010-007
  - 依賴：T003, T005, T006
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：可讀說明、兩視口、實際結果/返回狀態；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-007；代表資產選擇/受限導出旅程走查，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T008 與准入/生產者交付同一事實
  - 來源：REQ-019, NFR-001, NFR-005, PSC-001, PSC-008, PSC-009, PSC-012, AC-F010-008
  - 依賴：T004, T005, T006, T007
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：完整版本/責任鏈、當前限制與接手核對；代表性工程結果見[實施臺賬](../../verification/F010-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F010-008；PG-005 真實生產者→交付消費合同測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T009 完成本 Feature 驗收與真實交接
  - 來源：REQ-019, NFR-001, NFR-002, NFR-004, NFR-005, NFR-006, AC-F010-001, AC-F010-002, AC-F010-003, AC-F010-004, AC-F010-005, AC-F010-006, AC-F010-007, AC-F010-008
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008
  - 修改：`backend/medical_quality/delivery.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐用例輸入/版本、實際斷言/結果、原文/責任引用、未運行與限制，以及直接消費者接收結果；完整驗收未結束，真實結果/限制見[實施臺賬](../../verification/F010-implementation.md)。
  - 驗證：EV-F010-001, EV-F010-002, EV-F010-003, EV-F010-004, EV-F010-005, EV-F010-006, EV-F010-007, EV-F010-008；運行一次覆蓋本 Feature 的必要檢查集，複用已有效收據，組合驗收按產品套件單獨說明範圍。

## Task 數量複核

- 任務總數：9。
- 原因：每項任務交付一個獨立可核對結果，最後彙總證據與實際交接；依賴僅指本 Feature 內任務，上下游按 Map 及 Plan 合同接續。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | Spec/Plan/Tasks 與用例定義已補齊，尚無功能執行證據 | 實現/專業前置按 Plan OQ 落實；未安裝、部署或處理實際業務 |


## 當前交接狀態

固定規則/本體/權限/流程/評測資產、許可、不含敏感正文的 ZIP、冪等交接、完整性和必要依賴校驗。 代表性實現/檢查已完成。本 Feature 軟件任務與本輪直接檢查均已完成；專業或上游整體驗收仍沿 Feature Map 的狀態；詳情見[實現記錄](../../verification/F010-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
