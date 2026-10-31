# 原生知識圖譜規劃增量核對

日期：2026-10-13；來源為用戶 U09 / DEC-012。範圍是記住並落盤指定原生圖譜、詳細展示模塊與平臺產品設計，供後續開發；本輪未執行正式實現、原型改造、安裝或部署。

## 新增結果

- [原生集成與 TP-17/18](../architecture/ontology-playground-integration.md)：固定上游 SHA、原生能力 OP-01～14、源碼集成選擇、依賴/許可、醫療顯示投影、格式/候選/權限邊界。
- [產品設計增量](../03_prototype-design/design.md#knowledge-graph-design)：Apple 式簡潔殼、主圖空間、詳細 Inspector、三種視圖、原生 Designer、病例/規則入口、並列原文、返回與異常恢復。
- [F011](../specs/F011-knowledge-graph-workbench/spec.md)：Spec ready、Plan draft、Tasks planned，12 條局部 AC、13 項任務、14 條未運行用例；另外 2 條產品組合承接 PG-006。
- PRD 新增 REQ-020 / AC-027～029，Product Spec 新增 PSC-014；Map 追加 F011，F009 納入此一期 P0 模塊的驗收前置；原有編號保持。
- 工作區和工程 AGENTS、README、總體/逐需求架構、評估計劃和直接消費者計劃同步；原十個 Feature 的[歷史記錄](planning-completion.md)保留原統計。

## 實際檢查

以下為在 `MedicalQualityCase` 實際執行的**文檔結構檢查**，不是業務測試：

| 命令 | 結果與範圍 |
| --- | --- |
| `python3 -B .agents/skills/product-prd/scripts/validate_prd.py MedicalQuality --require-confirmed` | 通過；20 REQ、6 NFR、29 PRD AC |
| `python3 -B .agents/skills/product-spec/scripts/validate_product_spec.py MedicalQuality --require-confirmed` | 通過；14 PSC，29 PRD AC 來源有效 |
| `python3 -B .agents/skills/feature-spec-planning/scripts/validate_feature_specs.py MedicalQuality` | 通過；11 個 Feature、14 PSC、Map/任務來源與依賴一致；首次發現 F011 Plan 缺模板標題和任務 NFR 引用，補齊後通過 |
| `python3 -B .agents/skills/project-evals/scripts/validate_evals.py MedicalQuality --suite evals/F011.json --suite evals/product.json` | 通過；F011 全 12 AC 與 product 全 14 PSC 覆蓋；新增 14 局部＋2 組合設計用例，無執行綁定 |

補充只讀文檔檢查已通過：23 份本輪相關 Markdown 的 527 處本地鏈接可定位，顯式錨點無重複、表格列數一致；F011 的全部 12 條 AC 都實際出現在 Plan“驗收映射”表中。

當前統計已從文件計算：11 個 Feature、108 條局部 AC、119 項未勾選任務；117 條局部＋16 條產品用例，共 133 條，全部 `check_ref: null` 且沒有執行檢查綁定。需求覆蓋不代表業務通過。

## 未執行與開發前置

GitHub API 與固定 raw 源碼只讀核查完成，上游提交為 `defb487b133786c826eab60b99fcef9b8d3c6fbd`。未下載完整上游工程或複製其業務代碼。內置瀏覽器打開參考站時啟動失敗，返回 `failed to start Node runtime: No such file or directory`，所以沒有上游頁面截圖、實際交互或視覺驗收證據；沒有為此安裝工具或啟用用戶 Chrome。

正式前端/backend 尚未實現，圖譜不在現有 04 原型中。待開發先復現固定原生基線、核對依賴/版權、凍結真實圖投影與候選合同樣本、目標設備和性能預算，再按 F011 Tasks 集成。真實權限/原文/語義審核、專業條件及生產准入仍由原主責 Feature 驗證。

本輪未讀取憑據、上傳病例、調用付費模型、公共提交/發佈，未改變原始醫療數據及許可。沒有新增運行環境、依賴樹、完整第三方副本或大型二進制產物；持久產物僅為項目規格和用例定義。
