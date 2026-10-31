---
document: feature-tasks
feature: F004
status: in-progress
updated: "2026-10-14"
---

# F004 · 醫療上下文與病例工作臺任務

## 任務規則

- 本輪只有規劃，任務全部未執行。先關閉 Plan 中阻塞實施的技術前置，再開始正式實現；技術核查不冒充功能已完成。
- 任務以獨立可觀察結果組織，來源回到 [Spec](spec.md)，方法回到 [Plan](plan.md)及[用例](../../../evals/F004.json)。
- 不改原始數據或原型；只在真實結果和有效驗證證據存在時勾選。相同檢查已通過且輸入未變時直接引用，不重複製造等價結果。

## 任務清單

- [x] T001 固定命名空間與關聯證據規則
  - 來源：REQ-003, NFR-002, PSC-001, PSC-003, AC-F004-001
  - 依賴：無
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：命名空間與關係證據對照，以及[本體專項](../../data-preparation/governance-cleaning-handoff.md#ontology)中概念/關係範圍、中文定義、來源與候選/審核邊界；當前未執行。
  - 驗證：EV-F004-001；身份/關係反例集合測試，實現後綁定真實入口。

- [x] T002 形成帶不確定性的字段、時間線與斷言
  - 來源：REQ-003, NFR-002, PSC-003, AC-F004-002
  - 依賴：T001
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：原表達、主體/極性/時間/條件、規範化與衝突斷言，本體定義/映射/形狀及專業核對和形式檢查記錄；當前未執行。
  - 驗證：EV-F004-002；字段/時間/斷言語境測試，實現後綁定真實入口。

- [x] T003 交付受控只讀查詢與集合口徑
  - 來源：REQ-003, REQ-004, NFR-001, NFR-002, PSC-003, PSC-008, AC-F004-003
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：實際對象集合、總數及拒絕範圍；當前未執行。
  - 驗證：EV-F004-003；授權集合與獨立預期結果對照測試，實現後綁定真實入口。

- [x] T004 實現同源病例列表與詳情入口
  - 來源：REQ-004, NFR-006, PSC-013, AC-F004-004
  - 依賴：T003
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：篩選/分頁/詳情與兩視口操作記錄；當前未執行。
  - 驗證：EV-F004-004；一次代表旅程瀏覽器走查，實現後綁定真實入口。

- [x] T005 接續 F006/F007 已保存結果
  - 來源：REQ-004, REQ-014, NFR-006, PSC-006, PSC-013, AC-F004-005
  - 依賴：T004
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：F007 版本引用與前後視圖記錄；當前未執行。
  - 驗證：EV-F004-005；狀態投影與返回路徑走查，實現後綁定真實入口。

- [x] T006 傳播覆蓋與受限上下文
  - 來源：REQ-003, NFR-002, NFR-003, PSC-002, PSC-003, AC-F004-006
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：缺口/可用範圍與下游輸入對照；當前未執行。
  - 驗證：EV-F004-006；部分覆蓋合同測試，實現後綁定真實入口。

- [x] T007 固定上下文快照與變化影響
  - 來源：REQ-003, REQ-014, NFR-002, NFR-005, PSC-001, PSC-003, PSC-006, AC-F004-007
  - 依賴：T005, T006, T010, T011
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：輸入快照、SemanticRelease 與映射/形狀/值集版本、只讀投影發佈及舊/新上下文斷言；當前未執行。
  - 驗證：EV-F004-007；版本變更與舊引用回放測試，實現後綁定真實入口。

- [x] T008 交付穩定 CaseContext 與回查合同
  - 來源：REQ-003, NFR-002, PSC-001, PSC-003, AC-F004-008
  - 依賴：T003, T006, T007, T011
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：CaseContext、實際原文回查、本體語義服務的 F005/F006 消費及缺版本/歧義拒絕，包含[SG/SB 專項合同](../../data-preparation/governance-cleaning-handoff.md#agent-semantic)與原生/產品發佈身份對照；當前未執行。
  - 驗證：EV-F004-008；最小消費者與定位回放合同測試，實現後綁定真實入口。

- [x] T010 交付有據且可核驗的應用本體包
  - 來源：REQ-003, NFR-002, NFR-003, NFR-005, PSC-001, PSC-003, AC-F004-009
  - 依賴：T001, T002
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：版本化本體候選、原始支持、形式檢查/專業狀態與不可用範圍；當前未執行。
  - 驗證：EV-F004-009, EV-F004-010；本體發佈/消費合同集成檢查，真實入口存在後綁定。

- [x] T011 交付語義 adapter 與運行能力邊界
  - 來源：REQ-003, NFR-001, NFR-002, NFR-003, NFR-005, PSC-001, PSC-003, PSC-008, AC-F004-010
  - 依賴：T010
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：真實工具契約、有損/歧義/缺能力結果、原生/產品版本對應和運行只讀限制；當前未執行。
  - 驗證：EV-F004-011；原生工具與產品 adapter 合同檢查，不偽造缺失 MCP 的調用。

- [ ] T009 完成本 Feature 驗收與真實交接記錄
  - 來源：REQ-003, REQ-004, REQ-014, NFR-001, NFR-002, NFR-003, NFR-005, NFR-006, AC-F004-001, AC-F004-002, AC-F004-003, AC-F004-004, AC-F004-005, AC-F004-006, AC-F004-007, AC-F004-008, AC-F004-009, AC-F004-010
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008, T010, T011
  - 修改：`backend/medical_quality/clinical_context/context.py`、`backend/medical_quality/clinical_context/query_catalog.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/native_semantic.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐用例實際輸入/版本、結果與限制，包含本體 CQ-01～14、定義/映射與消費者核對，標明通過/失敗/受阻/未運行及獨立或組合範圍；當前無完成證據。
  - 驗證：EV-F004-001, EV-F004-002, EV-F004-003, EV-F004-004, EV-F004-005, EV-F004-006, EV-F004-007, EV-F004-008、EV-F004-009、EV-F004-010、EV-F004-011；一次選定套件驗收，複用仍有效的結果，僅執行缺失或受變化影響的檢查。

## Task 數量複核

- 任務總數：11。
- 原因：每項獨立結果直接承接一組業務 AC，最後完成證據交接；職責仍屬於同一 Feature，不按前後端或固定時長拆分。依賴只指本 Feature 任務，上下游按 Map 合同銜接。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | 本輪只完成文檔與用例定義，沒有執行任務 | Plan 技術前置及真實集成待落實；未安裝、開發或運行專業驗收 |

## 當前交接狀態

命名空間與未關聯病例、臨床斷言、固定上下文、受控結構查詢、OWL/SHACL 包與原生語義橋接。 代表性實現/檢查已完成。未勾選的任務包括正式責任/專業核對（若適用）與整組最終驗收；詳情見[實現記錄](../../verification/F004-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
