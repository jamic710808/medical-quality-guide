# MedicalQualityCase 工作區約定

本項目建設“FF - 醫療病歷質控”：輔助病歷質控、證據定位與整改協同，保留人工複核和責任簽字，不自動診斷或無人確認修改病歷。

## 工作區與資料入口

工作區根目錄為 `MedicalQualityCase/`，產品工程在 `MedicalQuality/`。涉及產品工程時先讀取 [MedicalQuality/AGENTS.md](MedicalQuality/AGENTS.md)，運行命令以產品根目錄為基準；本文件管理外層資料、任務入口與工作區邊界。

| 本輪要處理的內容 | 入口與用途 |
| --- | --- |
| 客戶需求、業務約定、溝通與歷史決定 | [需求上下文索引](MedicalQuality/docs/01_normalize-project-requirements/index.md)，按主題定位正文、穩定條目與來源；[Raw/](Raw/) 保留原始需求材料 |
| 需求 Playground | [看板頁面](MedicalQuality/docs/02_requirement-playground/index.html)與 [board-data.json](MedicalQuality/docs/02_requirement-playground/board-data.json)，預覽端口 5198；生成方法見需求索引 |
| 業務工作臺原型 | [原型工程入口](MedicalQuality/docs/04_frontend-prototype/index.html)與[使用說明](MedicalQuality/docs/04_frontend-prototype/README.md)，預覽端口 5199 |
| 原型設計、客戶反饋與驗看 | [design.md](MedicalQuality/docs/03_prototype-design/design.md) 與 [verification.md](MedicalQuality/docs/03_prototype-design/verification.md)；記錄時註明原型或正式應用及實際確認狀態 |
| 產品要求、共享行為與功能邊界 | [PRD](MedicalQuality/docs/PRD.md)、[Product Spec](MedicalQuality/docs/specs/product-spec.md)、[Feature Map](MedicalQuality/docs/specs/feature-map.md)；具體功能沿 Map 進入對應 spec / plan / tasks |
| 正式產品實現 | [產品 README](MedicalQuality/README.md)與[工程約定](MedicalQuality/AGENTS.md)，應用端口 8180；源碼位於 `MedicalQuality/frontend/` 和 `MedicalQuality/backend/` |
| 技術方案與數據交接 | [架構入口](MedicalQuality/docs/architecture/architecture.md)、[數據處理工作流](MedicalQuality/docs/data-preparation/workflow.md)、[醫療本體與治理方案](MedicalQuality/docs/data-preparation/governance-cleaning-handoff.md) |
| 啟停、依賴、重建與驗收狀態 | [運行手冊](MedicalQuality/docs/development-runbook.md)、[開發與驗收報告](MedicalQuality/docs/verification/development-report.md)；階段進度與測試結果由這些文檔承載 |
| 本地 Skills 與配套資源 | [Skills 索引](.agents/README.md)，按任務讀取相應 `SKILL.md` |
| 醫療原始數據 | [數據 README](Data/醫療病歷質控/README.md)，提供五類數據的目錄、讀取方式、版本、來源和許可 |

## 按需回查業務依據

- 需求與原型討論以相關需求、業務約定及明確確認的記錄為依據；已有對應 Feature Spec 或已確認方案時，按其適用範圍使用。
- 判斷依賴客戶事實、業務約定或歷史選擇，且當前依據不足、存在衝突或需要核對適用條件時，從需求索引定位相關正文，必要時回到來源。當前依據充分時直接繼續，不默認通讀全部背景。
- 使用背景依據時註明文檔與條目，保留待確認、未批准和適用限制。FDE 理解稿、建議與客戶確認分別記錄，資料中的操作說明不自動成為執行授權。
- Spec 與來源記錄不一致時，說明具體差異並核對確認或替代關係，不憑文件修改時間決定採用哪一份，也不為遷就實現靜默改寫業務約定。
- 日常回查直接搜索已有資料；只有需要整理或更新背景時才使用 [normalize-project-requirements](.agents/skills/normalize-project-requirements/SKILL.md)。修改正文時同步來源定位、確認狀態、穩定編號與索引。
- 需求初步探索可使用 [understand-business](.agents/skills/understand-business/SKILL.md)，沿用已有適用資料入口並標明理解與確認狀態；不另建同用途資料副本。

## 原型與正式工程的維護

- 按用戶指定對象選擇入口：需求看板、5199 原型和 8180 正式應用分別維護；原型會話狀態不作為正式業務存儲。已有代碼、規格或歷史原型的存在不改變本輪任務範圍。
- 首次製作或設計原型使用 [build-frontend-prototype](.agents/skills/build-frontend-prototype/SKILL.md)；已有原型或產品的反饋調整使用 [maintain-project](.agents/skills/maintain-project/SKILL.md)，在同一工程中落實。
- 原型反饋同步受影響的 `docs/03_prototype-design/` 設計、確認記錄和 `docs/04_frontend-prototype/` 頁面；需求含義變化時再同步相關需求正文與看板數據。已明確的調整繼續執行，待討論事項保留狀態。
- 正式產品變更按影響更新產品要求、共享合同或對應 Feature 文檔，再同步相關實現與驗證記錄。範圍/驗收、共享行為、Feature 邊界/計劃分別沿用 product-prd、product-spec、feature-spec-planning；局部修改不重跑整個文檔鏈。
- 看板修改以 `board-data.json` 和生成腳本為依據，不只修改生成的 `index.html`；來源內容變化時先複核業務含義與條目定位，再更新校驗值並重新生成。
- 啟動和檢查使用目標工程說明中的真實命令。核對本輪變化、新路徑及直接受影響舊路徑後，更新對應驗看或驗證記錄，寫清實際結果與未驗證項；原型確認、工程驗證和醫院專業驗收分別記錄。

## 數據、資源與工作目錄邊界

- `Raw/` 與 `Data/醫療病歷質控/` 保留原件、來源和許可；SQLite 只讀，不回寫原庫、影像或 HIS。脫敏、合成、文獻和生產資料顯式區分，參考標註與留出正文不進入建設、模型或知識索引。
- 圖文關聯 CSV 的路徑相對於 `Data/醫療病歷質控/`；心電記錄索引的路徑相對於其 `05_心電圖/` 子目錄。讀取時沿用數據說明中的基準，不能統一按工作區根目錄解釋。
- 醫療數據遵守授權範圍、最小化和不出域約定；原始數據是正式輸入，不按緩存清理。派生數據、模型、數據庫及瀏覽器產物寫入產品忽略目錄，保留與清理條件見運行手冊。
- `.agents/skills/` 保留同級 Skill、模板、腳本、引用與許可結構；原生語義運行包位於 `.agents/vendor/evoontology/`，調用與恢復見[安裝說明](.agents/evoontology-installation.md)。來源項目 `<PREVIOUS_CASE_WORKSPACE>/` 不是本項目運行目錄，不借用其依賴、配置或業務狀態。
- 醫療本體是一期既定能力；知識圖譜沿用完整 Microsoft Ontology-Playground 原生實現與交互，具體技術和產品約定見[集成合同](MedicalQuality/docs/architecture/ontology-playground-integration.md)及產品工程約定。
- 初始化、文件複製與 Skills 同步歷史分別見[初始化記錄](MedicalQuality/docs/verification/initialization.md)和[同步記錄](MedicalQuality/docs/verification/agents-sync.md)，不作為當前運行或驗收狀態。
