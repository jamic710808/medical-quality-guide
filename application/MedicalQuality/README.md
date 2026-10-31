# FF - 醫療病歷質控

> **學員源碼副本**：本包未攜帶教師電腦上的運行環境、數據庫、模型和原始醫療數據，也未在本輪啟動應用。下文“已實現並運行”及驗證結果均描述原開發環境的歷史記錄。完整源碼、鎖文件和重建腳本已保留；本次交付不執行依賴安裝。

病歷質控、證據定位與整改協同 Copilot。一期面向單一內科病區的成人肺炎住院病歷，通過有限規則、原文證據和人工複核貫通整改與責任簽字流程。

一期本地應用已實現並運行：**http://127.0.0.1:8180**。登錄選擇“周瑾 · 質控”可直接查看病例、原文、完整原生圖譜與整改任務。界面採用簡潔的平臺風格，正式狀態由服務端和 PostgreSQL 保存。

[開發結果與驗證臺賬](docs/verification/development-report.md) · [運行、角色與重建手冊](docs/development-runbook.md)

本地工程驗證、真實醫院專業驗收和生產放權分別記錄。當前可獨立完成的工程組合已核對；專業與目標環境驗收仍有前置，不把應用可運行寫成 133 條用例全部通過。

## 從哪裡開始

- [圖譜設計階段記錄](docs/verification/ontology-playground-planning.md)保留歷史；當前 11 個 Feature、108 條局部 AC、119 項任務、133 條用例的實現/結果見開發報告。[原十個 Feature 規劃記錄](docs/verification/planning-completion.md)保留歷史。[前次缺口審查](docs/verification/specification-completeness-audit.md)保留歷史。
- [Apple 風格產品原型](docs/04_frontend-prototype/index.html)：質控工作臺、證據與整改、規則、評測和權限審計；[運行與體驗說明](docs/04_frontend-prototype/README.md)。本地入口為 `http://127.0.0.1:5199/`。
- [需求上下文索引](docs/01_normalize-project-requirements/index.md)：三類標準資料、來源覆蓋關係與一期業務約定。
- [一期需求 Playground](docs/02_requirement-playground/index.html)：14 組“痛點—功能—預期效果”，支持字號、行距與留白調節；[標準數據](docs/02_requirement-playground/board-data.json)作為生成依據。
- [F011 知識圖譜工作臺](docs/specs/F011-knowledge-graph-workbench/plan.md)：完整採用 Ontology-Playground 原生圖譜/Designer，12 條局部 AC、13 項任務、14 條用例；[源碼核查與 TP-17/18](docs/architecture/ontology-playground-integration.md)、[詳細頁面設計](docs/03_prototype-design/design.md#knowledge-graph-design)。現已進入正式 React 應用；舊靜態原型保持歷史內容。
- [產品需求](docs/PRD.md)：20 項功能需求、6 項非功能要求、29 條驗收標準及實施前置條件。
- [全項目評估與驗收計劃](docs/evaluation-plan.md)：全需求追蹤、分層樣本/專家原判/仲裁、指標公式與棄答/覆蓋分母、PG-001～005 組合門檻。
- [模塊實施合同](docs/architecture/implementation-contracts.md)：授權/來源/語義/質控/責任/評測/准入/交付的字段、版本、錯誤與事務。
- [F001 授權審計](docs/specs/F001-access-audit/plan.md)、[F002 來源接入](docs/specs/F002-source-registration/plan.md)、[F008 專家評測](docs/specs/F008-expert-evaluation/plan.md)、[F009 准入放權](docs/specs/F009-release-gates/plan.md)、[F010 資產交付](docs/specs/F010-reusable-delivery-assets/plan.md)：新補齊的局部詳細計劃，配套規格、任務與已綁定用例。
- [產品總規格](docs/specs/product-spec.md)：14 條跨 Feature 共享合同，定義統一對象、狀態、證據與責任語義。
- [Feature Map](docs/specs/feature-map.md)：11 個 Feature 的邊界、輸入輸出、獨立驗收及依賴；[階段完成記錄](docs/verification/planning-through-feature-map.md)。
- [多源數據解析與知識建模交接工作流](docs/data-preparation/workflow.md)：現有數據特性、各類解析主選與備選、統一 EvidenceItem、來源質量核對和建模交接；已包含官方項目/Skills 調研與可運行的探測、契約校驗入口。
- [醫療數據治理、清洗與 RAG／本體交接](docs/data-preparation/governance-cleaning-handoff.md)：格式讀取、18 項清洗決定、質量/變換記錄與消費視圖。第 8 節現明確[一期必需醫療本體](docs/data-preparation/governance-cleaning-handoff.md#ontology)：研究/工具、28 個概念、18 組關係、14 項約束、14 個 CQ 及 OWL/SHACL/發佈接入方案；應用本體已構建並由工程版本消費，專業資格仍待核對。
- [F003 詳細實施計劃](docs/specs/F003-structured-evidence/plan.md)：承接上述工作流，寫明業務痛點、上下游接口、讀取分支、文件影響、失敗恢復和驗收；配套 [Spec](docs/specs/F003-structured-evidence/spec.md)、[13 項任務](docs/specs/F003-structured-evidence/tasks.md)與 [14 條用例](evals/F003.json)。
- [一期知識檢索技術決定](docs/architecture/knowledge-retrieval.md)：受控 SQLite 查詢、最小語義映射、BM25+BGE-M3/RRF、域內模型候選；具體細節見 [語義與查詢](docs/architecture/technical-points/semantic-query.md)、[混合檢索](docs/architecture/technical-points/hybrid-retrieval.md)、[聯合質控](docs/architecture/technical-points/quality-orchestration.md)。
- 對應 Feature 計劃：[F004 病例語義與工作臺](docs/specs/F004-clinical-context/plan.md)、[F005 規則知識與檢索](docs/specs/F005-rule-knowledge-governance/plan.md)、[F006 聯合質控與證據](docs/specs/F006-quality-evidence-review/plan.md)；三者均有配套規格、任務與已綁定用例。
- [知識檢索選型與構建 Skill](../.agents/skills/select-rag-architecture/SKILL.md)：已沉澱業務任務選型、代表問題驗證、構建交接與決定模板；[探索基線](docs/research/rag-selection-skill-exploration.md)保留調研依據。新 Skill 不改變本項目選型或 Feature 實施狀態。
- [Agent 選型 Skill](../.agents/skills/select-agent-architecture/SKILL.md)：按業務比較 LangChain/LangGraph、AgentScope、Pi、DeepSeek Harness、Hermes、Codex；項目採用的[編排方案](docs/architecture/agent-runtime.md)與 [TP-10～12](docs/architecture/technical-points/agent-orchestration.md)落實到 F006 和 [F007 責任閉環計劃](docs/specs/F007-remediation-accountability/plan.md)。
- [Agent 藉助本體與 semantic／Evo Skills 構建詳解](docs/data-preparation/governance-cleaning-handoff.md#agent-semantic)：SG-01～10 運行節點、只讀語義合同與恢復，SB-01～12 構建/回放、原生版本到產品發佈、演化與 ASV-01～12 驗證；現已有項目自有原生運行包與真實 stdio MCP 橋接，不依賴當前會話新增工具名。
- [基礎架構與技術設計基線](docs/architecture/architecture.md)：12 項技術決定、組件/數據流、部署與進程邊界、正式存儲和選型取捨；[20 項論文與成熟方案對照](docs/research/medical-quality-architecture-evidence.md)提供依據；[TP-13～16](docs/architecture/technical-points/platform-and-clinical-contracts.md)展開 API、事務/權限、臨床語境、評測和運維。
- [逐需求解決方案與技術落地詳解](docs/architecture/requirement-solution-design.md)：逐項解釋 20 個功能需求和 6 項非功能要求的現狀、方案比較、選擇理由、數據處理/輸出、最終架構、異常恢復及驗收，回鏈到既有 Feature 和技術點。
- [工程約定](AGENTS.md)、[初始化核對](docs/verification/initialization.md)與[Playground 驗看記錄](docs/verification/requirement-playground.md)。

## 項目結構與資料入口

```text
MedicalQualityCase/
├── Raw/                            # 原始需求資料
├── Data/醫療病歷質控/               # 原始醫療資料與許可，只讀
├── .agents/skills/                  # 項目本地 Skills，入口見 .agents/README.md
├── .agents/vendor/evoontology/      # 原生語義運行包與 MIT
└── MedicalQuality/
    ├── frontend/src/pages/         # 正式產品頁面
    ├── frontend/src/vendor/        # 完整原生圖譜來源
    ├── frontend/e2e/               # 瀏覽器流程
    ├── backend/medical_quality/    # 業務、證據、語義、Agent 與存儲
    ├── backend/migrations/         # 獨立 PostgreSQL
    ├── backend/tests/              # 直接工程檢查
    ├── scripts/                    # 準備、啟停、構建語義與驗證
    ├── docs/specs/                 # 總 Spec、Feature Map、11 個三件套
    ├── docs/verification/          # 逐 Feature/產品驗收臺賬
    ├── evals/                      # 133 條正式用例與實際綁定
    ├── artifacts/                  # 忽略：模型/證據/本體包/測試產物
    ├── .runtime/                   # 忽略：本地數據庫/工具/瀏覽器
    └── .evoontology/               # 忽略：原生語義工作區
```

需求來源位於 [Raw](../Raw/)。現有醫療資料入口為[數據 README](../Data/醫療病歷質控/README.md)，保留原位置與許可。Skills 與配套資源見[本地索引](../.agents/README.md)，工作目錄和資料回查規則見[外層工作區約定](../AGENTS.md)。

## 本地運行

```sh
cd MedicalQualityCase/MedicalQuality
python3 scripts/manage.py start
python3 scripts/manage.py status
```

停止：`python3 scripts/manage.py stop`，數據保留。應用 8180、域內模型 8191、項目獨立 PostgreSQL 55443，均只監聽本機。安裝/測試/固定版本/資源再生與清理見運行手冊。已有試用數據不重置。

舊需求 Playground 可從 `docs/02_requirement-playground/` 在 5198 獨立預覽，靜態原型從 `docs/04_frontend-prototype/` 在 5199 預覽；兩者不是真實服務入口。原始資料和來源項目未回寫。

`@賦範空間 獨家研發`
