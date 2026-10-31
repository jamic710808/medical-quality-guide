---
document: feature-tasks
feature: F002
status: completed
updated: "2026-10-14"
---

# F002 · 多源資料接入與版本登記任務

## 任務規則

- U10 已授權開發。勾選表示本條軟件實現及代表性工程檢查完成；專業條件和完整驗收按[當前臺賬](../../verification/F002-implementation.md)單獨核對，不以勾選代替臨床批准。
- 按同一 [Spec](spec.md) / [Plan](plan.md) 和 [用例](../../../evals/F002.json)交付，不增業務規則；有效結果在輸入不變時複用。
- 任務跨模塊實現同一業務結果，原始數據、規則/簽字歷史和獨立評測邊界保持。

## 任務清單

- [x] T001 只登記允許來源與用途
  - 來源：REQ-001, NFR-001, PSC-001, PSC-008, AC-F002-001
  - 依賴：無
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：實際讀取清單、拒絕原因、允許用途；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-001；允許根/URI/符號鏈接和拒絕讀取探針測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T002 文件與數據庫版本語義真實
  - 來源：REQ-001, NFR-002, NFR-005, PSC-001, AC-F002-002
  - 依賴：T001
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：摘要/快照標識、版本差異與受限說明；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-002；內容變化與一致性邊界合同測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T003 數據庫結構和業務記錄分開
  - 來源：REQ-001, NFR-002, PSC-001, AC-F002-003
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：真實表/字段/聲明約束、讀取粒度及未讀範圍；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-003；只讀結構目錄與查詢範圍核對測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T004 路徑基準和定位口徑可回查
  - 來源：REQ-001, NFR-002, PSC-001, AC-F002-004
  - 依賴：T002, T003
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：固定源句柄、路徑/計數說明和錯誤定位拒絕；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-004；雙路徑基準及邏輯記錄口徑夾具測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T005 來源性質與評測角色隔離
  - 來源：REQ-001, NFR-001, NFR-002, PSC-001, PSC-008, AC-F002-005
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：角色矩陣、建模集合與零答案讀取探針；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-005；分角色登記與建設讀取隔離測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T006 內容重複不混淆業務身份
  - 來源：REQ-001, NFR-002, NFR-005, PSC-001, PSC-009, AC-F002-006
  - 依賴：T002, T005
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：operation、來源/版本唯一性與不同任務關係；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-006；重複/併發與身份分離事務測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T007 接入覆蓋包含失敗和未讀
  - 來源：REQ-001, NFR-002, PSC-001, PSC-009, AC-F002-007
  - 依賴：T001, T002, T004
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：聲明清單、單位、實際統計和未完成項；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-007；混合接入覆蓋與空/未知範圍測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T008 更新與撤權保留歷史並限制新讀取
  - 來源：REQ-001, NFR-001, NFR-005, PSC-001, PSC-008, PSC-009, AC-F002-008
  - 依賴：T002, T006, T007
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：版本鏈、失效/拒絕與變更事件；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-008；新舊來源/撤權與舊句柄消費測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T009 向解析方交付穩定受限合同
  - 來源：REQ-001, NFR-001, NFR-002, NFR-005, PSC-001, PSC-008, PSC-009, AC-F002-009
  - 依賴：T003, T004, T005, T007, T008
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：請求/響應、實際回查及拒絕結果，註明替身範圍；代表性工程結果見[實施臺賬](../../verification/F002-implementation.md)；專業與整組未測項按該臺賬保留。
  - 驗證：EV-F002-009；最小真實 F002→F003 消費合同測試，已綁定實際檢查與人工核對入口；參見本 Feature 的實現臺賬。

- [x] T010 完成本 Feature 驗收與真實交接
  - 來源：REQ-001, NFR-001, NFR-002, NFR-005, AC-F002-001, AC-F002-002, AC-F002-003, AC-F002-004, AC-F002-005, AC-F002-006, AC-F002-007, AC-F002-008, AC-F002-009
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008, T009
  - 修改：`backend/medical_quality/sources.py`、`backend/medical_quality/app.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐用例輸入/版本、實際斷言/結果、原文/責任引用、未運行與限制，以及直接消費者接收結果；完整驗收未結束，真實結果/限制見[實施臺賬](../../verification/F002-implementation.md)。
  - 驗證：EV-F002-001, EV-F002-002, EV-F002-003, EV-F002-004, EV-F002-005, EV-F002-006, EV-F002-007, EV-F002-008, EV-F002-009；運行一次覆蓋本 Feature 的必要檢查集，複用已有效收據，組合驗收按產品套件單獨說明範圍。

## Task 數量複核

- 任務總數：10。
- 原因：每項任務交付一個獨立可核對結果，最後彙總證據與實際交接；依賴僅指本 Feature 內任務，上下游按 Map 及 Plan 合同接續。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | Spec/Plan/Tasks 與用例定義已補齊，尚無功能執行證據 | 實現/專業前置按 Plan OQ 落實；未安裝、部署或處理實際業務 |


## 當前交接狀態

來源登記、內容摘要、不可變快照、受控目錄/上傳、SQLite 只讀結構和研究用途。 代表性實現/檢查已完成。本 Feature 軟件任務與本輪直接檢查均已完成；專業或上游整體驗收仍沿 Feature Map 的狀態；詳情見[實現記錄](../../verification/F002-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
