# PRD、Feature 與技術落盤完整性檢查

> 歷史審查記錄：下文保留本輪審查當時的缺口與結果。用戶隨後授權全量補齊，文檔/定義層 G-01～03 已按[全量規劃核對](planning-completion.md)關閉，實施合同進一步明確；G-04～06 的真實工程/專業/執行前置仍須落實。當前入口見[評估計劃](../evaluation-plan.md)，不要把歷史五個缺目錄視為現狀。

日期：2026-10-13。變更/審查 ID：audit-spec-chain-20261013。用戶要求檢查當前 PRD、文件、各 Feature 和技術是否落齊、是否還有空白。本輪範圍為現有規格鏈審查、少量同步修正與本報告；未展開新 Feature、安裝運行環境或執行醫療業務。

## 1. 檢查結論

**核心技術方向已落盤，但一期詳細規劃尚未全部齊備。** PRD 的 19 個功能需求、6 個非功能要求、26 條驗收標準，以及 Product Spec 的 13 項合同已有結構與歸屬；10 個 Feature 的依賴無環，沒有發現 REQ/NFR/PSC 在 Map 中無人承接。

當前有五個 Feature 的詳細目錄尚不存在；已展開五個 Feature 有 53 項 planned 任務和 48 條局部用例。產品級另有 8 條組合用例，總計 56 條，全部未綁定檢查、未執行。技術專題寫得詳細不能替代各 Feature 的具體規格/計劃/任務和真實驗收。

狀態判斷分三層：

| 層次 | 當前結論 |
| --- | --- |
| 產品需求和共享合同是否已成形 | 是，PRD/Product Spec 為 confirmed，編號/歸屬結構檢查通過 |
| 核心技術選擇是否有依據和文檔 | 是，讀取清洗、PDF、RAG、本體、Agent、應用底座均有主方案/邊界/驗證安排 |
| 所有 Feature 是否有完整詳細規劃且可開始整體開發 | 否；5 個未展開，已展開 Plan 均 draft，仍有接口/資源/樣本和專業前置 |
| 是否已有可運行並通過業務驗收的正式產品 | 否；後端無業務代碼，正式前端只有品牌圖片，原型獨立存在 |

本次完整 Feature 校驗返回失敗，明確列出 F001/F002/F008/F009/F010 缺目錄。這是真實規劃缺口，不將其改成空目錄以製造通過。

## 2. 逐 Feature 清單

完整性中的“規格/計劃/任務”指真實存在的 spec.md、plan.md、tasks.md；“用例”指本 Feature 的 evals 文件，未綁定不等於已通過。

| Feature | 當前詳細文件 | 任務/用例 | 已有設計依據 | 缺口及優先順序 |
| --- | --- | --- | --- | --- |
| F001 訪問授權與責任審計 | 三件套均缺 | 無獨立套件 | Map、逐需求詳解 REQ-015/016、TP-14 | **優先補**：實際角色/對象/用途判斷、拒絕/審計合同、身份與 RLS 責任、計劃/驗收 |
| F002 多源資料接入與版本登記 | 三件套均缺 | 無獨立套件 | Map、REQ-001、F003 輸入草案 | **優先補**：來源/快照/授權對象、讀取範圍、接入錯誤/更新、與 F003 的正式接口 |
| F003 結構解析與統一證據 | 已有；Spec ready、Plan draft、Tasks planned | 13 / 12 | EvidenceItem、讀取/清洗專題、掃描 PDF 定案 | 掃描包/模型/定位/資源實測、F002 接口凍結 |
| F004 醫療上下文與工作臺 | 已有；Spec ready、Plan draft、Tasks planned | 9 / 8 | 必需應用本體、TP-01/02/15、SG/SB/CQ | 本體包/工具/許可/專業定義、源關係核查、語義服務及正式用例細化 |
| F005 規則知識版本治理 | 已有；Spec ready、Plan draft、Tasks planned | 9 / 8 | BM25/BGE-M3/RRF、資格/索引/語義版本 | 模型/詞典/分塊實測、專業資格、F004 語義和 F001/F003 接口 |
| F006 聯合質控與證據解釋 | 已有；Spec ready、Plan draft、Tasks planned | 10 / 9 | 8 條規則、LangGraph SG-01～10、失敗關閉 | 真正可用的語義模型、規則處理器/接口、圖恢復與語義消費驗證 |
| F007 複核整改與責任簽字 | 已有；Spec ready、Plan draft、Tasks planned | 12 / 11 | 人工分支、版本、業務事務/outbox/checkpoint | 真實身份/簽署與上游接口，持久恢復/併發故障驗證 |
| F008 專家評測與分歧仲裁 | 三件套均缺 | 無獨立套件 | Map、REQ-017、TP-16 | **必須補**：批次/抽樣、獨立原判/仲裁、指標分母/參照、任務與驗收 |
| F009 上線准入與責任接受 | 三件套均缺 | 無獨立套件 | Map、REQ-018、階段放權設計 | **必須補**：准入組合條件、實際責任記錄、停用/回退/重驗、任務與驗收 |
| F010 醫療資產固化與複用交付 | 三件套均缺 | 無獨立套件 | Map、REQ-019、導出 manifest 設計 | **一期 P1 後補**：資產合同/依賴/許可/導出範圍與消費者驗證；未被批准移出一期 |

這些未展開 Feature 已有產品範圍和總體解釋，缺的是可執行的局部交付設計。無需為解決它們另造平臺 Feature，沿[現有 Map](../specs/feature-map.md)展開即可。

## 3. 各技術是否已經落盤

| 技術項 | 已定方案與主要入口 | 當前沒有的部分 |
| --- | --- | --- |
| 讀取/清洗/統一證據 | [工作流](../data-preparation/workflow.md)、[治理方案](../data-preparation/governance-cleaning-handoff.md)：原生讀取、非破壞性規範化、EvidenceItem/質量/血緣 | 正式讀取器/轉換管線、全量受控處理與真實來源回放 |
| 掃描 PDF | [3.4 定案](../data-preparation/governance-cleaning-handoff.md#pdf-scan-decision)：Docling standard＋RapidOCR ONNX、顯式 PP-OCRv4，中文複雜表格備選域內 PP-StructureV3 | 包/權重/字典鎖定及真實掃描效果；六頁數字 PDF 初查不是 OCR 驗收 |
| RAG / 結構化查詢 | [檢索決定](../architecture/knowledge-retrieval.md)：受控 SQL、BM25＋BGE-M3 dense/pgvector＋RRF | 分塊/詞典/模型 revision 的實測凍結、索引與真實消費服務 |
| 醫療本體 | [第 8 節](../data-preparation/governance-cleaning-handoff.md#ontology)：本體必需、OWL/映射/SHACL、離線檢查及 PostgreSQL 投影 | 批准本體包、具體獲准外部子集/映射、專業審核、依賴/接口和真實 CQ 結果 |
| Agent / semantic Skills | [Agent 決定](../architecture/agent-runtime.md)、[SG/SB/ASV](../data-preparation/governance-cleaning-handoff.md#agent-semantic)：LangGraph、固定語義版本、建設/運行權限分開 | 實際 evo-semantic Core/MCP、項目適配器、圖節點與持久恢復；當前沒有 callable |
| 應用/存儲/權限/任務 | [FA-01～12](../architecture/architecture.md)、[TP-13～16](../architecture/technical-points/platform-and-clinical-contracts.md)：React/FastAPI/PostgreSQL、Worker、OIDC/RBAC/ABAC/RLS | 真實服務、Pydantic/OpenAPI/DDL/遷移和鎖文件、身份配置、環境/故障驗證 |
| 醫療人工責任流程 | [F007 Plan](../specs/F007-remediation-accountability/plan.md)：複核、整改/申訴、重核、雙崗簽字、同事務審計 | 實際業務對象/人員/簽署和工作臺/API 接續，不是原型切角色 |
| 專業評測與放權 | TP-16 與 REQ-017/018 已寫原則、分層指標和門檻 | F008/F009 詳細規劃、真實專家參照/閾值/樣本與業務簽字 |

結論是“技術方向有文檔”，不等於“每個庫的精確版本、每個接口/字段和每條檢查均已凍結”。其中精確依賴、部署預算和目標醫院配置屬於已列明的實施前置；醫療語義模型的專業資格仍未定型，Qwen 4B 只保留工程聯調用途。

## 4. 仍需補齊的具體清單

### G-01 · 五個 Feature 詳細交付缺失

位置為 docs/specs/F001-access-audit、F002-source-registration、F008-expert-evaluation、F009-release-gates、F010-reusable-delivery-assets；它們當前沒有目錄，也沒有對應 evals/FNNN.json。

閉合條件：每個 Feature 有範圍/輸入輸出/狀態與異常、Spec/Plan/Tasks、與上游合同一致的局部 AC 和用例。不能只建空文件或複製通用模板後把狀態標 ready。

### G-02 · 新增本體/Agent 場景尚未完整進入正式驗收定義

本體 CQ-01～14、Agent SG/SB/ASV-01～12 已在技術專題和任務中細化，已有 F004/F006 用例也涵蓋一般語義/版本/授權。但正式 JSON 套件仍沒有顯式展開以下關鍵機制的輸入與可觀察預期：

- 原生 ontology_vN/active 改變不切換正在運行的 SemanticRelease。
- 原生五類語義對象到 OWL/映射/SHACL 的有損/不支持轉換拒絕。
- 空形狀圖或 unknown 結構合法時，不能冒充完整證據與業務通過。
- 實際 MCP Schema/版本能力不足時拒絕，不給原生工具猜造參數。
- 構建/發佈/演化工具不進入病例 Agent 的運行允許集。
- 原生演化 Accept 不自動成為產品激活或專業放權。

對應現有 F004 AC-002/006/007/008 與 F006 AC-001/005/007/009 等，無需機械把每個技術條目變成新業務 AC。應補明確場景/矩陣並映射到正式套件；代碼具備後才綁定檢查。本輪未擴寫全部用例，避免以審查替代另一輪完整驗收設計。

### G-03 · 產品級評測/放權/資產閉環覆蓋不足

[product.json](../../evals/product.json)目前聲明並覆蓋的是 10 項 PSC。尚未納入 PSC-010（專家評測）、PSC-011（漸進放權）、PSC-012（資產交付），PG-004/PG-005 缺完整組合用例。

本輪小修後，PRD AC-019、AC-021、AC-022、AC-023 仍未在產品套件 source_ac 中出現；它們對應缺失的評測、否決、晉級/回退和交付能力。AC-020 已有上游覆蓋/棄答傳播的局部引用，但不是完整專家指標管線的驗收。

閉合條件：展開 F008～F010 後補真實跨模塊的正常/拒絕/失敗恢復用例及必要合同集合；不只把缺的 PSC 編號加進數組。

### G-04 · 實施合同與正式環境未落工程

技術文檔已有接口路徑、對象字段草案和表組；backend 尚無業務源碼，frontend 只有 public/brand/ff-logo.png。backend/pyproject.toml、frontend/package.json、項目虛擬環境、本體工作區/運行配置仍不存在。

尚需將現有設計落實為同一版實際合同：F001 的授權/審計，F002 的來源版本/範圍，F003 的證據/coverage，F004 的 SemanticRelease/CaseContext，以及 F005/F006/F007 的版本/錯誤/事務接口。DDL、遷移、包/模型 lock 與啟動命令是實施階段產物，本輪不虛構已存在。

### G-05 · 專業與目標醫院條件待落實

PRD OQ-003～006 已記錄：中文成人肺炎代表文書、必要文書清單、規則/指南適用性、本體定義/映射與外部內容許可、專家參照和樣本/指標閾值、真實身份/數據域/留存/簽署，以及資源/恢復預算。

這些不是繼續寫方案就能自動關閉的空白。須取得真實數據/專業/工程證據；缺失時沿已有 Fail Closed 與用途限制處理。尤其不能把公開病例、合成示例、模型分數或文檔 confirmed 當作專業批准。

### G-06 · 當前 56 條用例無實際執行綁定

所有 check_ref=null、checks=[]。沒有有效的命令/人工檢查綁定，也沒有實際業務通過記錄。已展開 Feature 的 AC 在各自用例定義中可找到，但這隻能說明定義層的追溯，不證明任何功能已運行。

閉合條件：實現對應能力後，以真正斷言該行為的項目檢查綁定，記錄正常/拒絕/恢復及實際結果。當前不能通過填假腳本、空成功命令或 mock 全流程消除此項。

## 5. 本輪直接修正的同步遺漏

1. F003 Spec OQ-001：將“路線尚未定型”修正為“主備已定、依賴/掃描效果/資源未驗證”，與已定 PDF 方案一致。
2. F005 Spec/Plan 的輸入和 OQ-003：補入已經在 Map 中要求的 F004 SemanticRelease、映射/值集與語義接口，保留獨立候選登記/原文查看路徑。
3. EV-PRODUCT-005：已有工作臺/列表/詳情同源預期補回 PRD AC-005 的追溯引用；未新增預期、檢查或通過狀態。

PRD、Product Spec、Feature Map 和原始資料保持原樣。其他尚未完成內容作為本報告缺口，未把此次檢查擴大為五個 Feature 的建設。

## 6. 實際檢查與證據邊界

所有命令在 MedicalQualityCase 執行。以下為文檔/用例定義檢查，不是業務測試。

| 檢查 | 實際方法 | 結果 |
| --- | --- | --- |
| PRD 合同 | python3 -B .agents/skills/product-prd/scripts/validate_prd.py MedicalQuality --require-confirmed | 通過；19 REQ、6 NFR、26 AC |
| Product Spec | python3 -B .agents/skills/product-spec/scripts/validate_product_spec.py MedicalQuality --require-confirmed | 通過；13 PSC，覆蓋既有 25 項 REQ/NFR 與 26 AC |
| 全部 Feature | python3 -B .agents/skills/feature-spec-planning/scripts/validate_feature_specs.py MedicalQuality | **未通過**；僅報 F001/F002/F008/F009/F010 缺目錄 |
| 六個現有 eval 套件 | validate_evals.py MedicalQuality --suite evals/FNNN.json；product 使用 evals/product.json | 定義結構通過；全部 behavior=not_evaluated，56 條均未綁定 |
| 歸屬/依賴與目錄 | 只讀讀取 Map、規格/任務/evals 與 frontend/backend 文件清單 | 無未歸屬 REQ/NFR/PSC；10 Feature 依賴無環；53 planned 任務；缺失如上 |
| 最新技術與正式用例對照 | 對照本體/Agent 場景及 F004/F006/product 的 Given/When/Expected | 發現 G-02/G-03，未把文字章節當運行覆蓋 |
| 修正後受影響合同與用例 | 維護收據 audit-affected-features / audit-product-eval | 本節下方記錄實際結果 |
| 報告與入口鏈接 | 維護收據 audit-report-links | 本節下方記錄實際結果 |

首次調用 eval 校驗器時把 --suite 誤傳成 F003 等 scope，工具按路徑報不存在；隨後改為實際 evals/FNNN.json 並完成六套校驗。該調用錯誤不計為項目缺口。完整 Feature 校驗的五個目錄缺失則屬於真實未完成項，未被局部通過掩蓋。

修正後 F003/F005 的局部規格鏈校驗通過；product、F003、F005 三套受影響用例定義校驗通過，狀態仍為 not_evaluated、沒有新增綁定。其餘未改輸入的 PRD、總 Spec、F004/F006/F007 定義檢查沿用本輪已取得結果。報告和 README 的本地入口通過 audit-report-links 核對。維護檢查的 pass 只覆蓋本輪同步修正，完整 Feature 檢查仍因 G-01 的五個缺目錄而未通過。

本輪維護記錄位於外層 .codex/maintenance/，已由腳本加入 Git 忽略；僅保存文件基線與檢查收據，不安裝 Hooks。本報告是審查結論的持久入口；維護運行結束且無唯一證據依賴後，該輔助記錄可清理。

## 7. 補齊順序

1. **先 F001、F002**：補授權/審計與來源接入的詳細合同、計劃、任務和用例，解決 F003～F007 共同前置。
2. **同步補 G-02 的正式驗收定義**：讓本體、Agent 和語義版本要求從專題/任務進入明確測試場景。
3. **再 F008、F009，隨後 F010**：形成專家評測、放權/回退和交付資產的詳細方案，並補 PG-004/PG-005。
4. **進入實際技術驗證與開發**：鎖依賴/模型、核對掃描和本體/semantic 工具、實現正式接口，綁定並運行用例；專業和醫院條件在對應啟用前落實。

不需要重寫已確認 PRD 或重選全部技術棧。應補齊尚缺的局部交付設計和真實前置，再按既有依賴推進。
