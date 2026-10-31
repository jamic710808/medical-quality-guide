# 檢索技術與 F004～F006 規劃核對

日期：2026-10-13。請求：按已討論技術選型落盤，結合業務需求補充對應 Feature，並將細節落到所選技術點。當前工作只完成技術/規劃文件，未實施業務代碼或模型運行。

## 交付

- [技術決定](../architecture/knowledge-retrieval.md)：KD-01～10；SQLite 受控查詢、語義映射、BM25/BGE-M3/RRF、固定規則及本地 Qwen/llama.cpp 候選路線。
- 技術專題：[TP-01/02](../architecture/technical-points/semantic-query.md)、[TP-03～06](../architecture/technical-points/hybrid-retrieval.md)、[TP-07～09](../architecture/technical-points/quality-orchestration.md)。細節只在專題維護，Feature 計劃負責實施歸屬與驗收映射。
- [F004](../specs/F004-clinical-context/plan.md)、[F005](../specs/F005-rule-knowledge-governance/plan.md)、[F006](../specs/F006-quality-evidence-review/plan.md)分別新增完整三件套，合計 25 條 AC、28 項未執行任務；現有 F003 僅補充直接交接引用。
- 新增 25 條 Feature 用例，在現有 product 套件追加 2 條組合用例；舊用例 ID 和既有定義保留。
- PRD 僅補記 U04 / DEC-007 與技術前置進展；Product Spec 共享語義不變，Map 補列實際繼承的約束，未新增 Feature 或改變依賴/優先級。

## 本輪觀察與來源

沿用已有數據畫像；另以只讀 PRAGMA 核對 patients、admissions、labevents、d_labitems 四表的真實字段/類型/主外鍵聲明。未讀取業務行：聲明主鍵為內部 `_source_record_number`，業務列為 TEXT，四表未聲明外鍵。語義映射仍需樣本和完整性核查，不能據字段名認定關係已驗證。

技術包/模型能力引用官方文檔，鏈接集中在技術決定。沒有下載包或模型、沒有填入未測的準確率/速度/成本。RRF 和候選數量只是顯式實驗起點，不是生產驗收門檻。

## 結構與追溯驗證

以下從工作區根執行，最終全部通過：

```bash
python3 -B .agents/skills/product-prd/scripts/validate_prd.py MedicalQuality --require-confirmed
python3 -B .agents/skills/product-spec/scripts/validate_product_spec.py MedicalQuality --require-confirmed
python3 -B .agents/skills/feature-spec-planning/scripts/validate_feature_specs.py MedicalQuality --feature F003 --feature F004 --feature F005 --feature F006
python3 -B .agents/skills/project-evals/scripts/validate_evals.py MedicalQuality --suite evals/F003.json --suite evals/F004.json --suite evals/F005.json --suite evals/F006.json --suite evals/product.json
```

| 檢查 | 結果 |
| --- | --- |
| 產品需求 | 19 REQ、6 NFR、26 AC，confirmed，無錯誤/警告 |
| 共享規格 | 13 PSC，confirmed，無錯誤/警告 |
| Feature 文檔 | F003～F006 來源、AC、任務與依賴通過；新任務均未勾選 |
| 驗收定義 | F003/F004/F005/F006 為 12/8/8/9 條，product 為 4 條，共 41 條；全部未綁定，behavior=not_evaluated |
| 本地文檔鏈接 | 核對當次 21 份相關文檔的 196 處路徑及其中 19 處 TP 錨點，無失效；本記錄新增鏈接另行核對 |

首次 Feature 校驗發現生成器的任務字段錯位及 Map 輔助表被識別為主錶行，已修正並複驗通過；沒有通過放寬校驗規則掩蓋錯誤。

語義核對還明確：業務關聯字段不等於數據庫約束；語義/規則/專家結論分層；病例證據不進入全局規則知識索引；未知、無命中、模型失敗與臨床通過分開；共享 Schema 與模塊消費校驗分別維護。

## 當前狀態與未執行項

F003～F006 的 Spec 為 ready、Plan 為 draft、Tasks 為 planned，全部 10 個 Feature 仍 planned。模型資源/效果、精確依賴版本、真實接口、樣本適配與專業批准尚待各 Plan 的核查步驟落實。

本輪未創建運行環境、下載模型、建索引、生成業務代碼或處理真實醫療記錄；沒有調用付費模型、讀取憑據或改動原型。結構校驗只證明文檔與引用關係，不能作為 RAG 質量、醫療有效性、專業簽字或生產准入證據。
