# F003 詳細規劃核對記錄

日期：2026-10-13。範圍：將已有多源數據解析工作流落實到 F003，形成業務規格、實施計劃、任務與驗收用例；沒有執行產品實現。

## 交付與歸屬

- [Spec](../specs/F003-structured-evidence/spec.md)：12 條 AC，關聯 REQ-002/008、NFR-001/002/003/005 和 PSC-001/002/005/008；業務痛點、入口、輸出、異常、恢復及消費邊界明確。
- [Plan](../specs/F003-structured-evidence/plan.md)：承接局部架構，包含擬改路徑、F002 輸入草案、按格式分流、統一封裝、定位回放、覆蓋/恢復、知識建模交接、風險和逐 AC 驗收映射。
- [Tasks](../specs/F003-structured-evidence/tasks.md)：13 項未執行任務，含前置技術收斂；均有來源、依賴、修改位置、預期證據與驗證辦法。
- [Feature 用例](../../evals/F003.json)：12 條，覆蓋全部 F003 AC；[產品用例](../../evals/product.json)：2 條，僅承接 PG-001 與 PG-003 解析鏈相關組合。
- F002 仍主責登記/授權來源，F004 仍主責醫療上下文，F005 仍主責規則資格。F003 在 Map 中補列已存在的 NFR-001 / PSC-008 約束，主責、依賴、優先級均未改變。

## 文檔結構檢查

下列命令從外層工作區執行，最終均通過；僅證明規劃文檔的結構與追溯關係，不執行產品行為。

```bash
python3 -B .agents/skills/product-prd/scripts/validate_prd.py MedicalQuality --require-confirmed
python3 -B .agents/skills/product-spec/scripts/validate_product_spec.py MedicalQuality --require-confirmed
python3 -B .agents/skills/feature-spec-planning/scripts/validate_feature_specs.py MedicalQuality --feature F003
python3 -B .agents/skills/project-evals/scripts/validate_evals.py MedicalQuality --suite evals/F003.json --suite evals/product.json
```

- PRD：19 REQ、6 NFR、26 AC，confirmed；本輪只同步階段授權，業務要求未改動。
- Product Spec：13 PSC，confirmed；共享合同未改動。
- F003：來源、AC、任務引用和依賴檢查通過，無錯誤或警告。
- Evals：14 條定義結構通過，全部 check_ref=null、checks 為空，結果為 behavior=not_evaluated。

未運行 `--require-ready`、`--require-bound` 或業務測試：Plan 仍有明確的技術前置，產品代碼與實際檢查入口不存在。原 Skill 的 22 項測試是先前輔助工具驗證，未冒充本 Feature 的行為結果。

## 語義核對與停止點

已將真實痛點回鏈至來源，逐項核對讀取/失敗/恢復/交接旅程；沒有把 XML/XLSX 的受限適配、圖像/波形元數據擴大成通用解析或醫學診斷能力。來源角色隔離、原始資料只讀、定位精度與缺口繼續沿用既有合同。

Spec 為 ready，Plan 為 draft，Tasks 為 planned；Map 中 10 個 Feature 均仍 planned。PDF 模型/版本與本地運行條件、F002 實際交接字段分別由 T002/T001 收斂，再更新 Plan 的就緒狀態。組合用例在相關真實 Feature 具備後執行，消費者替身不代表 PG-001 / PG-003 通過。

本輪只創建文檔與用例定義；未建立 Python 環境、產品代碼或運行產物目錄，未轉換醫療數據、改動原型、構建本體或開展模型調用。
