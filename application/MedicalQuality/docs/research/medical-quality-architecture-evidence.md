# 醫療病歷質控架構：研究依據與適用邊界

檢索日期：2026-10-13。目標：回答現有多格式資料、8 條文書質控規則、證據回查和人工責任閉環應如何落到基礎架構；不評選“通用最好模型”。本輪按主題檢索、篩選 20 項代表性論文/研究資料，並檢查相關官方工程文檔和開源方案。不是宣稱窮盡文獻的系統性綜述。

檢索主題包括 EHR 數據質量、臨床語境/錯誤檢測、醫學 RAG、引用/幻覺、長上下文、Agent 故障、提示注入、人機協作、臨床評測及運行存儲。優先作者/期刊/ACL/arXiv/PubMed 和項目官方來源；一般以摘要、方法/結論相關片段與元數據為核對範圍，未復現論文實驗。部分 PMC/Nature 頁面訪問失敗時使用 PubMed、作者預印本或同文發表入口，不把搜索結果冒充全文精讀。

訪問限制單列：L01/L02 採用 PubMed 摘要補充初次 PMC 訪問失敗；L17 的全文/部分正文入口訪問受限，使用官方檢索返回的摘要和書目信息，只借鑑早期評價/人因的概括原則；L19 主要依據 PubMed 摘要。沒有將這些條目標記為全文復現或系統性證據綜合。

## 20 項研究如何改變設計

下表“本項目動作”是結合論文機制與本地需求的工程推論，不是論文作者對本項目的驗證。預印本/技術報告與同行評審結果區分；不引用榜單數值作為上線指標。

| ID / 研究 | 可支持的判斷 | 本項目動作 | 不能外推的內容 |
| --- | --- | --- | --- |
| L01 · Kahn 等，2016，[EHR 數據質量框架](https://pubmed.ncbi.nlm.nih.gov/27713905/) | 區分 conformance、completeness、plausibility，驗證語境也要明確 | 解析結構合規、材料覆蓋與臨床合理性分層；規則逐項聲明輸入完整性 | 結構合法不等於臨床正確，數據庫完整不等於病歷完整 |
| L02 · Harkema 等，2009，[ConText](https://pubmed.ncbi.nlm.nih.gov/19435614/) | 否定、時間及 experiencer 是臨床文字解釋的重要屬性 | 原片段保留主體、極性、時間/假設和段落語境，支持衝突判斷 | 英文觸發詞及歷史效果不能原樣保證中文臨床性能 |
| L03 · Johnson 等，2023，[MIMIC-IV](https://www.nature.com/articles/s41597-022-01899-x) | 數據有特定機構、時期、脫敏和表格結構 | 固定 namespace/粒度，源時間不恢復真實日曆，JOIN 先驗證 | 本地 Demo 的規模、完整性或人群不能用完整 MIMIC 論文代替 |
| L04 · Zhao 等，[PMC-Patients](https://arxiv.org/abs/2202.13876)，2022 預印本/2023 數據論文 | 文獻病例摘要支持患者到文章/患者檢索研究 | 文獻敘述作為獨立來源與檢索材料，不當完整住院文書 | 論文早期版本數量不同於本地 V2；相似度不證明患者同一或診療事件發生 |
| L05 · Yu 等，2025，[CMQCIC-Bench](https://arxiv.org/abs/2502.11703)，arXiv | 質控指標任務可分臨床事實核查與規則推理 | 將“找事實/核對證據”和“執行已定義規則”分開，保留失敗歸因 | 785 實例/76 指標不是本項目 8 條規則和完整責任流程；發佈方標註不自動成專家金標準 |
| L06 · Xiong 等，2024，[MedRAG / MIRAGE](https://arxiv.org/abs/2402.13178) | 醫學 RAG 的語料、檢索器和模型組合需要實際比較 | 保留詞法基線，比較混合檢索、上下文和模型配置 | 醫學 QA 正確率不能替代原始病歷缺項、定位、整改或專業簽字驗收 |
| L07 · Ben Abacha 等，2025，[MEDEC](https://aclanthology.org/2025.findings-acl.1159/) | 臨床筆記的錯誤檢測/糾正是專門任務 | 評測分別測錯誤發現、定位、解釋與建議，不只測答案語言 | 其診斷/治療等錯誤範圍大於本期文書質控；不能據此增加自動治療或自動改病歷 |
| L08 · Thakur 等，2021，[BEIR](https://arxiv.org/abs/2104.08663) | 檢索有跨域差異，BM25 是有價值的比較基線 | 用規則號、專名、改寫與中文樣本比較 BM25 和 dense/融合 | 沒有普遍最優檢索器；英文通用集合不能證明本地中文醫學質量 |
| L09 · Chen 等，2024，[M3-Embedding](https://arxiv.org/abs/2402.03216) | 多語言及多種檢索表徵提供工程候選 | 保留 BGE-M3 dense 驗證路線，版本/語言與原生分數明確 | 模型多語言能力不證明醫療否定/罕見術語或本地準確率 |
| L10 · Liu 等，2023/2024，[Lost in the Middle](https://arxiv.org/abs/2307.03172) | 證據位置及上下文長度影響利用效果 | 構造按規則收集的有限證據包，檢查截斷與位置效應 | 不能將長上下文窗口等同完整理解，也不能只固定 top-k 後忽略必要證據 |
| L11 · Gao 等，2023，[ALCE](https://arxiv.org/abs/2305.14627) | 引用完整性/支持性需要專門評價 | 區分“引用 ID 存在”“原文能回查”“原文支持主張” | 顯示鏈接不是真實性保證，非醫學引用評測不替代專業判斷 |
| L12 · 2024，[RAGTruth](https://arxiv.org/abs/2401.00396) | RAG 條件下仍有細粒度幻覺 | 假引用、無支持數值、遺漏限制條件進入負例與阻斷 | 檢索命中不保證生成正確；不能把幻覺檢測器作為唯一門禁 |
| L13 · Edge 等，2024，[GraphRAG](https://arxiv.org/abs/2404.16130)，研究預印本 | 社區摘要針對全庫主題/歸納問題 | 當前病例/規則級任務先不用社區圖，保留有據關係查詢 | 全局歸納增益不能證明病例級精確統計或醫學因果 |
| L14 · 2024，[Docling 技術報告](https://arxiv.org/abs/2408.09869) | 文檔結構與佈局解析提供統一處理能力 | 原生結構先讀，掃描/複雜 PDF 用樣本驗證結構解析；保留頁框和原生結果 | 統一序列化不表示 OCR 無錯，也不表示任意 XML/JSON 都適配 |
| L15 · Debenedetti 等，2024，[AgentDojo](https://arxiv.org/abs/2406.13352) | 外部工具數據可注入指令，攻擊與正常任務同時需評估 | 病歷/指南文本不獲工具權；授權在應用/工具層執行，加入惡意正文用例 | 一段提示詞或檢測模型不能證明不存在越權路徑 |
| L16 · 2025，[多 Agent 失敗分析](https://arxiv.org/abs/2503.13657)，arXiv | 協作會引入設計、對齊、驗證/停止等失敗模式 | 固定 LangGraph 流程，只有獨立任務有增益才引入多個 Agent | 多 Agent 投票不等於兩名獨立臨床專家複核 |
| L17 · Vasey 等，2022，[DECIDE-AI](https://pubmed.ncbi.nlm.nih.gov/35585198/)，共識指南 | 早期真實使用評測要關注流程、安全和人因 | 離線→影子→人確認輔助，記錄真實工作負擔、錯誤與責任接受 | 本項目借鑑評測思路，不宣稱滿足醫療器械分類或法規認證 |
| L18 · Goddard 等，2012，[Automation bias 系統綜述](https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751/) | 人會過度依賴自動化，驗證複雜度影響使用 | 不預選“接受”，顯示原文/限制；雙人評測先保留獨立原判，再仲裁 | 讓人在環中點擊一次並不能證明有效監督 |
| L19 · Dahlberg 等，2026，[臨床筆記質量評測綜述與實驗](https://pubmed.ncbi.nlm.nih.gov/41955894/) | 評測方法對改寫、臨床變化的敏感度及模型/語言表現不同 | 同時測細粒度事實、關鍵錯誤與人工可用性；Judge 經專家對照 | 自動分數或文本相似度不能單獨代表安全可用 |
| L20 · 2026，[臨床筆記錯誤檢測的提示優化](https://aclanthology.org/2026.healing-1.20/) | 提示與模型配置會改變錯誤檢測結果 | prompt/model/量化一起版本化，調優與保留評測分開 | 不能將特定模型在 MEDEC 上的結果移植給 Qwen 4B 或中文病區；不能在留出集上調提示 |

## 成熟方案可借什麼

| 方案 / 標準 | 借鑑與當前選擇 | 不直接引入的原因 |
| --- | --- | --- |
| [OHDSI DataQualityDashboard](https://github.com/OHDSI/DataQualityDashboard) | 借鑑規則化數據檢查、明確分母及結果清單 | 它面向 OMOP CDM；本地不是 OMOP，不為運行工具遷移全部醫療數據，也不把其默認閾值搬作本項目規則 |
| [medspaCy](https://github.com/medspacy/medspacy) | 借鑑段落、臨床斷句、ConText 和模塊化語境處理；英文樣本可作為局部比較 | 不是中文全規則開箱即用方案；破壞性預處理仍需原文位置映射 |
| [MedRAG 官方實現](https://github.com/gzxiong/MedRAG) | 借鑑固定題集下組合語料/檢索/模型的評測方式 | 不復制其全量語料/模型部署，不以問答分數替代病歷質控合同 |
| [FHIR R4 Provenance](https://hl7.org/fhir/R4/provenance.html) / [AuditEvent](https://hl7.org/fhir/R4/auditevent.html) | 借鑑“內容怎樣產生”與“誰在何時訪問/操作”分離 | 當前內部 EvidenceItem/業務決定不宣稱是 FHIR 合規資源；一期不為此增加 FHIR/HIS 外部接入 |
| [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) / [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | 複用執行檢查點和顯式人工等待，業務狀態/審計/outbox 獨立 | 不能從 checkpoint 推斷外部事務恰好一次；同樣數據庫中也可能是不同事務 |
| [PostgreSQL 17](https://www.postgresql.org/docs/17/ddl-rowsecurity.html) / [pgvector](https://github.com/pgvector/pgvector) | 統一業務事務、版本與受限向量查詢；初期精確搜索 | RLS 非默認保證，owner/superuser/BYPASSRLS 有繞過條件；向量數學近鄰召回不是臨床證據召回 |

## 對此前架構的審視結果

保留：原始資料只讀、統一 EvidenceItem、按任務分流、最小語義映射、BM25+dense/RRF、確定性規則與模型候選分層、LangGraph、真人決定/簽字、失敗關閉與獨立評測。

本次調整：正式工作臺採用 React/TypeScript，業務 API 採用 FastAPI；多人業務事實源和 checkpoint 採用 PostgreSQL；dense 歸入 pgvector，初期精確搜索，NumPy 只保留數學對照用途。此前 SQLite 應用庫/SQLite saver 是輕量驗證設想，本次不再作為正式業務默認，也不開發雙數據庫兼容層。原始輸入 SQLite 仍只讀，完全不遷寫。

必須補齊：患者/家屬主體、否定/不確定/假設、事件/文書時間、文書範圍完整性、證據包截斷、多語言語義差異、重複病例的評測分組、撤權/更新、併發責任寫入和真正的恢復演練。

Qwen3-4B-GGUF 繼續作已有工程聯調/故障測試基線，不再讓“已選模型”被誤讀成“臨床可用模型已定型”。臨床語義能力只有在代表性資料、規則負責人及獨立評測具備後，才能選擇並固定滿足條件的模型/配置；論文和品牌無法填補該缺口。

## 研究範圍與驗證限制

本輪不讀取參考標註/留出答案來設計算法，不運行論文代碼，不下載新數據集或模型，不產生醫療判斷、吞吐或質量指標。研究使用公開論文/官方工程資料，結論仍需本地樣本驗證。

具體基礎架構與決定見 [總體架構](../architecture/architecture.md)，實施細節見 [TP-13～16](../architecture/technical-points/platform-and-clinical-contracts.md)。後續選型變化應留下新依據及影響範圍，不靠“最先進”替代業務驗證。
