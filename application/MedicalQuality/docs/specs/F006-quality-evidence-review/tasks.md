---
document: feature-tasks
feature: F006
status: in-progress
updated: "2026-10-14"
---

# F006 · 聯合質控與證據解釋任務

## 任務規則

- 本輪只有規劃，任務全部未執行。先關閉 Plan 中阻塞實施的技術前置，再開始正式實現；技術核查不冒充功能已完成。
- 任務以獨立可觀察結果組織，來源回到 [Spec](spec.md)，方法回到 [Plan](plan.md)及[用例](../../../evals/F006.json)。
- 不改原始數據或原型；只在真實結果和有效驗證證據存在時勾選。相同檢查已通過且輸入未變時直接引用，不重複製造等價結果。

## 任務清單

- [x] T001 凍結質控輸入與用途
  - 來源：REQ-006, NFR-001, NFR-002, NFR-005, PSC-001, PSC-004, PSC-008, AC-F006-001
  - 依賴：無
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：運行清單、允許/拒絕範圍及 SemanticRelease/mapping/shape/value-set 固定引用；當前未執行。
  - 驗證：EV-F006-001；啟動前置與版本凍結測試，實現後綁定真實入口。

- [x] T002 落實 8 條規則的職責和必要輸入
  - 來源：REQ-006, NFR-002, NFR-003, PSC-004, PSC-005, AC-F006-002
  - 依賴：T001
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐規則語義依賴、形狀/完整性前置、輸入/輸出與無法判斷原因；當前未執行。
  - 驗證：EV-F006-002；規則處理器的獨立預期夾具測試，實現後綁定真實入口。

- [x] T003 產生受限的跨段語義候選
  - 來源：REQ-006, REQ-007, NFR-002, NFR-003, PSC-005, AC-F006-003
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：模型配置、候選與證據對應記錄；當前未執行。
  - 驗證：EV-F006-003；固定樣本的結構化候選與支持性核對，實現後綁定真實入口。

- [x] T004 交付可複核的問題與證據解釋
  - 來源：REQ-007, NFR-002, PSC-001, PSC-005, AC-F006-004
  - 依賴：T002, T003
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：問題字段、原文回放和失效反饋；當前未執行。
  - 驗證：EV-F006-004；問題響應與證據對照走查，實現後綁定真實入口。

- [x] T005 傳播缺口與失敗關閉
  - 來源：REQ-008, NFR-003, PSC-002, PSC-005, AC-F006-005
  - 依賴：T002, T003, T004
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：檢查覆蓋、blockers 與允許人工入口；當前未執行。
  - 驗證：EV-F006-005；混合失敗運行聚合測試，實現後綁定真實入口。

- [x] T006 限制風險信號的用途
  - 來源：REQ-008, NFR-003, PSC-005, AC-F006-006
  - 依賴：T004, T005
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：校準狀態與推進約束斷言；當前未執行。
  - 驗證：EV-F006-006；分流信號與禁用條件測試，實現後綁定真實入口。

- [x] T007 實現受影響範圍再次核驗
  - 來源：REQ-006, REQ-008, NFR-002, NFR-005, PSC-001, PSC-004, PSC-005, AC-F006-007
  - 依賴：T001, T005, T006, T011
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：[SG-01～10](../../data-preparation/governance-cleaning-handoff.md#agent-semantic-graph)真實調用、新舊運行、原生 active/產品 release 隔離、依賴、檢查點/結果提交邊界與重複結果斷言；當前未執行。
  - 驗證：EV-F006-007；版本/冪等與節點重放故障測試，實現後綁定真實入口。

- [x] T008 交接同一質控結果與責任前提
  - 來源：REQ-007, REQ-008, NFR-002, NFR-003, PSC-005, AC-F006-008
  - 依賴：T004, T005, T007
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：QualityRun 與消費者收到的版本/覆蓋；當前未執行。
  - 驗證：EV-F006-008；跨模塊結果消費者合同測試，實現後綁定真實入口。

- [x] T009 約束模型能力與失敗數據流
  - 來源：REQ-006, REQ-008, NFR-001, NFR-003, PSC-005, PSC-008, AC-F006-009
  - 依賴：T003, T004, T005
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：工具/網絡探針、語義只讀允許集、構建/發佈/演化拒絕及最小化日誌/SSE 記錄；當前未執行。
  - 驗證：EV-F006-009；模型邊界和引用負例測試，實現後綁定真實入口。

- [x] T011 交付本體消費與分層結果的真實執行
  - 來源：REQ-006, REQ-008, NFR-001, NFR-002, NFR-003, NFR-005, PSC-001, PSC-002, PSC-004, PSC-005, PSC-008, AC-F006-010
  - 依賴：T001, T002, T003
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：固定 SemanticRelease 的真調用、空/未知形狀與覆蓋區分、只讀工具和錯版本/缺基線拒絕；當前未執行。
  - 驗證：EV-F006-010, EV-F006-011, EV-F006-012；語義/覆蓋/工具及恢復合同集成檢查，未實現不綁定假命令。

- [ ] T010 完成本 Feature 驗收與真實交接記錄
  - 來源：REQ-006, REQ-007, REQ-008, NFR-001, NFR-002, NFR-003, NFR-005, AC-F006-001, AC-F006-002, AC-F006-003, AC-F006-004, AC-F006-005, AC-F006-006, AC-F006-007, AC-F006-008, AC-F006-009, AC-F006-010
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008, T009, T011
  - 修改：`backend/medical_quality/quality.py`、`backend/medical_quality/worker.py`、`backend/medical_quality/ontology.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐用例實際輸入/版本、結果與限制，標明通過/失敗/受阻/未運行及獨立或組合範圍；當前無完成證據。
  - 驗證：EV-F006-001, EV-F006-002, EV-F006-003, EV-F006-004, EV-F006-005, EV-F006-006, EV-F006-007, EV-F006-008, EV-F006-009、EV-F006-010、EV-F006-011、EV-F006-012；一次選定套件驗收，複用仍有效的結果，僅執行缺失或受變化影響的檢查。

## Task 數量複核

- 任務總數：11。
- 原因：每項獨立結果直接承接一組業務 AC，最後完成證據交接；職責仍屬於同一 Feature，不按前後端或固定時長拆分。依賴只指本 Feature 任務，上下游按 Map 合同銜接。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | 本輪只完成文檔與用例定義，沒有執行任務 | Plan 技術前置及真實集成待落實；未安裝、開發或運行專業驗收 |

## 當前交接狀態

八條文書規則、三值結果、真實 Qwen3 候選、逐字引用過濾、LangGraph/PG checkpoint 與本體形狀檢查。 代表性實現/檢查已完成。未勾選的任務包括正式責任/專業核對（若適用）與整組最終驗收；詳情見[實現記錄](../../verification/F006-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
