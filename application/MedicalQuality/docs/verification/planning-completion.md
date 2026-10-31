# 一期全量規劃與評估補齊記錄

> 本文是 U08 的歷史快照，原統計和檢查不重寫。後續 U09 已新增 F011 原生圖譜；當前增量及統計見[圖譜規劃核對](ontology-playground-planning.md)。

日期：2026-10-13。依據 PRD U08 / DEC-011，完成全部 Feature 詳細規劃和評估設計，沿用既有醫療範圍、技術選型及責任邊界。本文記錄規劃完成，**不宣稱正式功能、專業評測或上線已完成**。

## 完成範圍

| 項目 | 本輪結果 |
| --- | --- |
| 產品合同 | 原 19 REQ、6 NFR、26 PRD AC 和 13 PSC 保留；補記全量規劃授權 |
| Feature | F001～F010 均有 spec.md / plan.md / tasks.md，共 30 份；10 個 Feature 均 planned |
| 局部驗收 | 96 條 Feature AC，全部有計劃/任務/正式用例承接 |
| 任務 | 106 項 planned；依賴按既有 Map 和局部任務組織，不預先勾選 |
| 正式用例 | 103 條局部＋14 條產品組合，共 117 條；均未綁定、未執行 |
| 產品覆蓋 | product 套件顯式包含全部 26 條 PRD AC，聲明並覆蓋 PSC-001～013，PG-001～005 有具體組合場景 |
| 共同實施 | [實施合同](../architecture/implementation-contracts.md)：模塊字段/版本/錯誤/授權/事務和消費者 |
| 評估方法 | [全項目評估計劃](../evaluation-plan.md)：樣本/專家/指標分母/rubric/門禁/正式用例/需求追蹤 |

新補齊 F001/F002/F008/F009/F010 的 15 份三件套及各自套件；在已有 F004/F006 追加本體交付/適配/不可繞過消費 AC 與獨立任務。既有用例保留編號與預期，增補 OCR、清洗、本體、Agent 和責任恢復場景。此前缺少的專家評測、准入/回退和資產交付進入產品套件。

F008～F010 顯式繼承其實際消費的原有域/責任/版本/界面不變量；沒有新增 PRD 需求、醫院接入形態或自由 Agent 權限。Feature 的邊界、優先級及依賴沿原 Map，F005 仍消費 F004 的本體基線。

## 前次審查缺口如何處理

| 前次問題 | 本次處理 | 是否還需實際實施 |
| --- | --- | --- |
| G-01 五個 Feature 缺三件套/套件 | 已補齊全部目錄、詳細 Spec/Plan/Tasks/AC/EV | 是，文件完整不代表功能實現 |
| G-02 本體/Agent 等場景停留專題 | 新增/細化正式局部 AC、Task 和 EV；CQ/ASV 映射到評估計劃 | 是，需真實工具/接口/執行證據 |
| G-03 專家評測/准入/交付產品覆蓋不足 | product 聲明全部 PSC，補 PG-004/005 及本體/OCR 組合，全部 PRD AC 可追溯 | 是，組合用例尚未運行 |
| G-04 實施合同/環境未落工程 | 已進一步固定共同字段、狀態、錯誤、事務與接口職責 | 運行代碼、依賴鎖、DDL/遷移和正式環境仍待開發 |
| G-05 專業/目標醫院條件 | 已有責任者類別、凍結時機、缺項阻斷及評估方法 | 仍需真實樣本/專家/閾值/許可/身份/簽署/留存等 |
| G-06 用例無執行綁定 | 已設計全量可追蹤用例與最窄方法，保留 check_ref=null / checks=[] | 工程入口存在後才能合法綁定和執行 |

[前次審查](specification-completeness-audit.md)保留當時事實，開頭已回鏈本次結果，不覆寫歷史檢查或偽造通過。

## 關鍵交付入口

- [Feature Map](../specs/feature-map.md)：十個 Feature、依賴及每項詳細計劃。
- [F001 權限審計](../specs/F001-access-audit/plan.md)、[F002 來源接入](../specs/F002-source-registration/plan.md)。
- [F003 數據讀取/OCR](../specs/F003-structured-evidence/plan.md)、[F004 本體與上下文](../specs/F004-clinical-context/plan.md)、[F005 規則知識/RAG](../specs/F005-rule-knowledge-governance/plan.md)。
- [F006 聯合質控/Agent](../specs/F006-quality-evidence-review/plan.md)、[F007 人工責任](../specs/F007-remediation-accountability/plan.md)。
- [F008 專家評測](../specs/F008-expert-evaluation/plan.md)、[F009 准入回退](../specs/F009-release-gates/plan.md)、[F010 資產交付](../specs/F010-reusable-delivery-assets/plan.md)。

## 驗證記錄

實際完成的檢查如下（2026-10-13）：

| 方法 | 結果與範圍 |
| --- | --- |
| validate_prd.py MedicalQuality --require-confirmed | 通過：19 REQ、6 NFR、26 AC，無錯誤/警告 |
| validate_product_spec.py MedicalQuality --require-confirmed | 通過：13 PSC，共同合同與來源完整 |
| validate_feature_specs.py MedicalQuality | 通過：全部 10 個 Feature 存在，ID/來源/依賴/任務格式無錯誤；後續受影響 Plan 修正又做局部核對通過 |
| validate_evals.py MedicalQuality，顯式傳入 evals/F001.json～F010.json 及 product.json | 11 套全部通過定義校驗；117 條未綁定，checks 均為空，behavior=not_evaluated |
| 需求→Feature AC→Plan 驗收表→Task→EV 的獨立覆蓋核對 | 25 項 REQ/NFR 無遺漏，96 條局部 AC 均落入實際驗收表/任務/用例；26 PRD AC 和 13 PSC 均在產品套件覆蓋 |
| 文件/引用及表格 | 本輪相關文檔 544 處本地引用可定位；32 份 Feature/評估/合同文檔的 100 張表列結構一致，章節/任務無模板佔位 |
| 合成指標算例 | 20 單元的端到端/條件召回、決策覆蓋與未判斷分母一致；只驗證文檔算例，不是臨床分數 |

覆蓋複核發現並修正 F004/F006 新增本體 AC 的驗收映射表位置，隨後對應映射與表格核對通過；沒有用正文中出現 AC 編號代替驗收表。新 Feature 的 Plan 還明確區分實現前的最小技術試驗與實現後的完整業務驗收，避免以“必須先做完整 Feature 才能進入實現”形成循環。

| Feature | 局部 AC | planned 任務 | 正式用例 |
| --- | ---: | ---: | ---: |
| F001 | 9 | 10 | 9 |
| F002 | 9 | 10 | 9 |
| F003 | 12 | 13 | 14 |
| F004 | 10 | 11 | 11 |
| F005 | 8 | 9 | 9 |
| F006 | 10 | 11 | 12 |
| F007 | 11 | 12 | 12 |
| F008 | 10 | 11 | 10 |
| F009 | 9 | 10 | 9 |
| F010 | 8 | 9 | 8 |
| 合計 | 96 | 106 | 103 |

產品組合另有 14 條，故總用例為 117。舊用例保留，新增內容使用新 ID；沒有真實運行收據時沒有任何 Task 被標完成。前次審查的五個缺目錄與評估定義覆蓋缺口已在規劃層補齊，原始材料/原型/運行代碼未修改。


本輪只做文檔與用例定義檢查，不運行 --require-bound 或把所有 Plan 標 ready 來掩蓋真實前置。正式運行/專業證據不足時的阻斷仍有效；Spec ready / Plan draft / Tasks planned 與既有流程一致。沒有讀取獨立答案/留出內容，沒有生成患者記錄、專家簽字、部署或模型調用。

## 後續開發與啟用

先實現 F001/F002 的授權/來源合同，再按 F003→F004→F005→F006 接續數據、本體和質控；F007 與 F008 基於真實上游分別完成責任閉環和評測，F009 組合門禁後由 F010 固化獲准資產。每個 Feature 的實施前置、最窄驗證與回退見其 Plan/Tasks。

醫學能力是否達到目標，須由實際樣本、獨立專家和運行結果證明。本輪建立完整實施與評估路徑，並未代替這些事實。
