---
document: feature-tasks
feature: F005
status: in-progress
updated: "2026-10-14"
---

# F005 · 規則與知識版本治理任務

## 任務規則

- 本輪只有規劃，任務全部未執行。先關閉 Plan 中阻塞實施的技術前置，再開始正式實現；技術核查不冒充功能已完成。
- 任務以獨立可觀察結果組織，來源回到 [Spec](spec.md)，方法回到 [Plan](plan.md)及[用例](../../../evals/F005.json)。
- 不改原始數據或原型；只在真實結果和有效驗證證據存在時勾選。相同檢查已通過且輸入未變時直接引用，不重複製造等價結果。

## 任務清單

- [x] T001 建立規則與知識版本目錄
  - 來源：REQ-005, NFR-002, NFR-005, PSC-001, PSC-004, AC-F005-001
  - 依賴：無
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：版本記錄、來源與允許轉換；當前未執行。
  - 驗證：EV-F005-001；版本/狀態轉換合同測試，實現後綁定真實入口。

- [x] T002 執行規則資格與訪問過濾
  - 來源：REQ-005, NFR-001, NFR-003, PSC-004, PSC-008, AC-F005-002
  - 依賴：T001
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：允許/拒絕集合和原因；當前未執行。
  - 驗證：EV-F005-002；適用性與權限矩陣測試，實現後綁定真實入口。

- [x] T003 保留條款結構與詞法入口
  - 來源：REQ-005, NFR-002, PSC-001, PSC-004, AC-F005-003
  - 依賴：T002
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：片段/父上下文及 locator 對照；當前未執行。
  - 驗證：EV-F005-003；固定條款索引與回查測試，實現後綁定真實入口。

- [x] T004 交付可核對的混合召回
  - 來源：REQ-005, NFR-002, NFR-003, PSC-001, PSC-004, AC-F005-004
  - 依賴：T003
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐問題命中、版本、範圍與差異；當前未執行。
  - 驗證：EV-F005-004；同問題集的基線/混合檢索對照，實現後綁定真實入口。

- [x] T005 明確空結果和受限檢索
  - 來源：REQ-005, NFR-002, NFR-003, PSC-001, PSC-004, AC-F005-005
  - 依賴：T004
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：覆蓋、狀態與拒絕原因；當前未執行。
  - 驗證：EV-F005-005；空結果/故障範圍測試，實現後綁定真實入口。

- [x] T006 管理索引生命週期與失效範圍
  - 來源：REQ-005, NFR-001, NFR-004, NFR-005, PSC-004, PSC-008, PSC-009, AC-F005-006
  - 依賴：T001, T002, T005
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：manifest、責任記錄引用和可訪問集合；當前未執行。
  - 驗證：EV-F005-006；發佈/失效與故障恢復測試，實現後綁定真實入口。

- [x] T007 交付版本化規則知識基線
  - 來源：REQ-005, NFR-002, NFR-005, PSC-004, PSC-012, AC-F005-007
  - 依賴：T006
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：固定版本清單及不變資格；當前未執行。
  - 驗證：EV-F005-007；歷史引用與資產消費者合同測試，實現後綁定真實入口。

- [x] T008 守住檢索模型的授權域
  - 來源：REQ-005, NFR-001, NFR-003, PSC-004, PSC-008, AC-F005-008
  - 依賴：T004, T006
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：網絡調用、日誌與實際模式斷言；當前未執行。
  - 驗證：EV-F005-008；域內嵌入與錯誤路徑探針測試，實現後綁定真實入口。

- [x] T009 完成本 Feature 驗收與真實交接記錄
  - 來源：REQ-005, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, AC-F005-001, AC-F005-002, AC-F005-003, AC-F005-004, AC-F005-005, AC-F005-006, AC-F005-007, AC-F005-008
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008
  - 修改：`backend/medical_quality/retrieval.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：逐用例實際輸入/版本、結果與限制，標明通過/失敗/受阻/未運行及獨立或組合範圍；當前無完成證據。
  - 驗證：EV-F005-001, EV-F005-002, EV-F005-003, EV-F005-004, EV-F005-005, EV-F005-006, EV-F005-007, EV-F005-008、EV-F005-009；一次選定套件驗收，複用仍有效的結果，僅執行缺失或受變化影響的檢查。

## Task 數量複核

- 任務總數：9。
- 原因：每項獨立結果直接承接一組業務 AC，最後完成證據交接；職責仍屬於同一 Feature，不按前後端或固定時長拆分。依賴只指本 Feature 任務，上下游按 Map 合同銜接。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | 本輪只完成文檔與用例定義，沒有執行任務 | Plan 技術前置及真實集成待落實；未安裝、開發或運行專業驗收 |

## 當前交接狀態

獨立規則/資格版本、候選審核、BM25/BGE-M3/pgvector/RRF、精確編號、限定本體擴展、索引發布。 代表性實現/檢查已完成。本 Feature 軟件任務與本輪直接檢查均已完成；專業或上游整體驗收仍沿 Feature Map 的狀態；詳情見[實現記錄](../../verification/F005-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
