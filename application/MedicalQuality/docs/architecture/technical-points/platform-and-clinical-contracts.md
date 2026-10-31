# 應用底座、臨床語境與驗證技術點

承接[總體架構 FA-01～12](../architecture.md)，補齊既有 TP-01～12 的應用與運行細節。以下路徑、數據表和接口是實現設計，尚未創建服務或數據庫；業務對象/狀態仍以 Product Spec 為準。

<a id="tp-13"></a>
## TP-13 · 模塊化單體、API 與持久任務

### 代碼與進程

正式前端位於 `frontend/src/`，按病例工作臺、規則依據、問題證據、責任流程、評測/准入組織組件；React + TypeScript + Vite，延續原型品牌、字號/留白和返回路徑。瀏覽器僅保存可重建的瀏覽條件與 UI 狀態，簽字/意見/任務狀態以服務端為準，不信角色切換按鈕。

`backend/medical_quality/` 內按既有 Feature 保持 `access`、`sources`、`structured_evidence`、`clinical_context`、`knowledge`、`quality`、`remediation`、`evaluation`、`release` 與 `delivery` 職責。共享 `contracts` 定義內部請求/結果，API adapter 不復制領域規則。不同模塊不是單獨微服務；Worker 導入同一領域代碼，減少兩套業務語義。

FastAPI 負責 Pydantic 結構校驗和統一響應，領域處理器另做用途/狀態/版本校驗。JSON Schema 合法、HTTP 200 或結構化模型輸出均不證明業務前置成立。

### 內部接口設計

| 方法與擬議路徑 | 操作 | 必要條件 / 返回 |
| --- | --- | --- |
| POST `/api/v1/sources` | 登記允許的文件/數據庫來源 | 服務端已配置的數據根/adapter；不接任意服務器路徑或網絡 URL；返回 source_id/version 與範圍 |
| POST `/api/v1/source-versions/{id}/parse-runs` | 提交限定解析任務 | 授權、用途、固定版本與讀取範圍；受理返回 job/run ID，202 不表示解析成功 |
| GET `/api/v1/cases` | 授權病例列表/計數/分頁 | 查詢字段/排序白名單，同一過濾與快照；不從向量命中算全量總數 |
| GET `/api/v1/cases/{id}/context` | 取得固定上下文 | 命名空間、就診、context_version；包含未知、覆蓋和可回查證據 |
| POST `/api/v1/knowledge/search` | 請求適用依據 | purpose、規則/知識範圍、版本/時間口徑與授權由服務端確認；無命中與無資格分開 |
| POST `/api/v1/quality-runs` | 發起有限質控 | 固定輸入/規則/模型配置與 idempotency_key；受理後 Worker 執行 |
| POST `/api/v1/tasks/{id}/decisions` | 複核/整改/申訴/裁決/簽字等明確命令 | 真實 actor、action、expected_version、範圍和理由；同事務保存業務結果/審計/outbox |
| GET `/api/v1/evidence/{id}` | 授權原文/字段/原生資源回放 | 驗證 source_version、locator 與當前訪問；大資源受控流式傳輸，不能暴露存儲路徑 |
| GET `/api/v1/runs/{id}` 與 `/events` | 查詢狀態及 SSE 進度 | 同對象授權；斷線重連攜帶事件遊標並可回查權威狀態，不只靠內存事件流 |

查詢響應保留 request_id、對象/版本、狀態、coverage/限制及錯誤碼。403/404 的對象存在性策略由授權層一致處理；過期對象變更用衝突響應並要求重新核對。後端不得通過模型文本匹配決定是否成功。

同源部署使用服務端會話/BFF 方式對接 OIDC，瀏覽器敏感令牌不放可任意讀取的 localStorage。寫命令防 CSRF，渲染原文/Markdown 不執行 HTML/腳本，PDF/圖片通過授權 viewer 取內容。內部 REST 不新增一期對外 HIS API/SDK 產品能力。

### 慢任務與恢復

API 在 PostgreSQL 事務裡寫 job/outbox 後返回；OCR、嵌入、模型和圖恢復由獨立 Worker 消費。FastAPI BackgroundTasks 可做不承擔業務可靠性的短操作，不保存必須跨重啟完成的質控任務。[官方邊界](https://fastapi.tiangolo.com/tutorial/background-tasks/)

job 記錄 input_manifest、purpose/允許範圍、operation_key、state、attempt、lease_owner、lease_until、fencing_token、heartbeat、result_ref 和失敗原因。領取使用短事務及行鎖/可用的 SKIP LOCKED；立即提交，不能持鎖等待模型/真人。[PostgreSQL SELECT](https://www.postgresql.org/docs/17/sql-select.html)

租約到期後可能由新 Worker 接管；提交結果時必須以最新 fencing_token/attempt 條件寫入，阻止舊 Worker 遲到結果覆蓋新嘗試。操作唯一鍵和結果輸入摘要保證同一有效結果不重複；上游外部調用本身仍可能重複，不能承諾全局 exactly-once。

區別 job（計算）、task（人工責任）、run（凍結業務判斷）、thread/checkpoint（執行進度）。未知提交結果先按 operation_key 查狀態；配置/輸入變化創建新運行，取消計算不刪除業務待辦或簽字。失敗和超時有界，重試次數/預算在實際配置中固定，不自動改雲端或無限循環。

<a id="tp-14"></a>
## TP-14 · PostgreSQL 數據、權限與事務

### 三類數據的邊界

1. 外層 `Data/` 與原 SQLite：正式輸入只讀；來源層記錄本次內容版本/快照和可讀取範圍。不能為了 ORM 方便複製/改寫整個源庫。
2. PostgreSQL 應用庫：業務身份、證據元數據、原值/規範化映射、規則資格、運行、人工責任、授權/審計和任務投遞。大原件/解析資產使用受控版本引用。
3. 派生計算：向量、詞項、解析緩存、checkpoint、模型緩存各自有版本/範圍和保留規則；不能將原件、專家意見、簽字當作任意可再生緩存清除。

前述應用 SQLite / SQLite saver 不再是正式默認。採用 PostgreSQL 17 系列、SQLAlchemy 2 和 Alembic 遷移；checkpoint 使用同版本兼容的 PostgreSQL saver、獨立 schema/權限。物理同庫不意味著業務事務與 checkpoint 的保存原子。[SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)、[Alembic](https://alembic.sqlalchemy.org/en/latest/)、[LangGraph](https://docs.langchain.com/oss/python/langgraph/persistence)

### 邏輯數據表與約束

表名是擬實現名稱，字段/業務含義映射現有合同；不會據此補造醫院元數據。

| 對象組 | 核心鍵/字段 | 一致性與使用要求 |
| --- | --- | --- |
| source / source_version | namespace、內容摘要/快照、kind/role、用途/許可、範圍 | 不以文件名/時間戳冒充內容一致性；版本不可靜默改寫 |
| evidence_item / parse_run | source_version、kind、locator、原文/原值引用、provenance、quality/coverage | 每個對象回原版本；失敗和未知總數保留；規範化值不覆蓋原值 |
| case / encounter / document_version | namespace+原業務 ID，源記錄映射、版本鏈 | 業務鍵與源記錄序號分開；實際唯一/關聯核對後才啟用，不跨來源同號合併 |
| clinical_assertion / semantic_mapping | 原文 span、主體/極性/時間/條件、來源類型、映射/抽取版本 | 僅記錄原文主張及其解釋，不自動成為醫學事實；不確定保留 |
| rule_version / knowledge_version | 用途、適用範圍、審核狀態、批准/生效時間、evidence_refs | 索引加載不改變專業資格；舊運行固定舊依據 |
| retrieval_chunk / embedding / index_manifest | evidence_id/version、chunk/parent、model/tokenizer/index 版本、允許分區 | vector 與分塊元數據一致；相同文本不同來源不誤去重 |
| quality_run / check_result / issue | 輸入版本集合、rule/check ID、判定/執行狀態、候選與阻斷 | 同有效 operation_key 唯一；覆蓋分母不刪困難項 |
| workflow_task / decision / signature | actor、role、scope、expected/current_version、決定 ID、簽署範圍 | 狀態更新比較版本；同冪等鍵請求必須校驗請求摘要，不同請求體不能偽裝同一次操作 |
| audit_record / job / outbox | 主體、對象版本、用途、前後狀態、operation/decision ID、投遞狀態 | 業務變更+必要責任記錄+outbox 同事務；普通日誌不替代責任證據 |
| evaluation_batch / judgment / arbitration / gate | 固定樣本/版本/口徑、兩個身份原判、仲裁、否決/准入範圍 | 原判不覆蓋；驗證答案不進入構造輸入；未測不能填成績 |

生產審計由受限寫入接口追加，普通業務角色不能隨意 UPDATE/DELETE；這不構成對數據庫管理員的絕對防篡改或法律簽名保證。真正簽署機制、保全和留存由目標醫院明確。

### 併發與責任命令

BusinessDecision 使用真實 actor、task_id、action、expected_version、scope/document/rule/run 版本、reason 與 idempotency_key。命令短事務內校驗當前狀態/權限/版本，保存決定、狀態、必要審計和 outbox，再返回業務提交結果。兩個用戶併發操作時只有滿足版本條件的一次生效，另一方得到衝突並重新核對。

簽字時檢查簽署人自己的職責及範圍，禁止靠前端切換角色冒充另一崗位；兩次簽署都綁定當前版本及前置。業務已提交、圖尚未恢復時由 outbox 接續；圖前進、投遞標記未更新時按決定 ID 去重。不得持數據庫鎖等待人工，也不能用 checkpoint 回滾抹掉已提交簽字。

### 身份、範圍與數據庫縱深限制

應用採用 RBAC + 對象屬性/用途/期限校驗，OIDC 只負責身份認證，不替代業務權限。列表、計數、原文、索引、SSE、緩存、下載和恢復都執行範圍策略；checkpoint thread_id 或難猜 UUID 不是訪問憑證。

對病例/文書/證據/責任等表啟用經測試的 RLS。正常應用/Worker 角色不得為 superuser、owner 或 BYPASSRLS；連接池的事務上下文采用受控 SET LOCAL 並核驗回收後不會串用身份。後臺作業以 job 固定範圍及當前授權共同校驗，不能拿服務身份無限讀全庫。[RLS 官方語義](https://www.postgresql.org/docs/17/ddl-rowsecurity.html)

### 向量和詞法實現

正式 dense 向量存 pgvector，與元數據/索引版本關聯；1024 維 BGE-M3 首批使用授權範圍內精確餘弦排序，查詢與索引模型/歸一化一致。pgvector 的精確近鄰只是向量空間的數學結果，不能稱為醫學 Recall=100%。[pgvector](https://github.com/pgvector/pgvector)

BM25 繼續對當前允許分區使用固定詞典和版本；與向量路由的候選集合/資格一致，用 RRF 合併，規則號直達獨立處理。不要以 PostgreSQL 默認分詞自動替代已明確的中文醫學分詞。初期不啟用 ANN；以後若 HNSW 需要投入，須在同樣授權過濾下測召回及延遲，不能從近似索引先取全庫 top-k 再過濾後聲稱範圍內無答案。

撤權/失效先更新服務入口允許集合，再清索引/緩存和重建；歷史記錄存在不授權當前讀取。向量、summary、臨時 prompt、checkpoint 都可能含敏感信息，不能僅對最終回答過濾。

<a id="tp-15"></a>
## TP-15 · 臨床斷言、完整性與分層證據

### 一條臨床主張怎樣表示

在 F004 的 CaseContext 中增加可追溯斷言屬性，複用 EvidenceItem 而不擴展一套競爭的原件封裝：

- 來源/文本：evidence_id、source_version、document_version、段落/字段/實際 span、section、原詞/原值。
- 主體：patient / family / other / unknown，以及有據關聯；家屬病史不能變成患者事實。
- 極性與確定性：肯定、否定、不確定、假設/條件等；沒有記錄不自動歸為否定。
- 時間：事件時間、文書記錄時間、原始相對錶達/偏移、可比較性；歷史、當前、計劃和無法確定分別表達。
- 解釋：規範化值、單位/概念映射、解析/抽取/映射版本、支持來源和限制；自動抽取標 candidate，不能直接當專家確認。

例如“否認過敏史”“家屬有過敏史”“曾疑似藥物過敏”即使包含相同詞，也應形成不同斷言與證據。跨段差異先核對同一主體、時段、文書目的和上下文；病情演變不能自動判為錯誤。ConText 支持此類語境劃分的必要性，但中文/醫療長尾的實現必須單獨驗證。[研究依據 L02](../../research/medical-quality-architecture-evidence.md)

結構化字段可使用確定性讀取；正文語義採用有限模板/詞典與模型候選對照，而不憑英文詞典直接覆蓋中文。任何清洗/分詞用於檢索的副本保留到原文字節/字符範圍的映射，做不到精確 span 時標實際粒度。

### 文書缺失需要完整性證據

規則檢查分三步：適用條件成立 → 聲明範圍資料已枚舉/讀取且覆蓋可說明 → 在該範圍查找所需內容。缺少清單、上游不完整、權限隱藏、OCR 失敗或上下文截斷時，輸出無法判斷/證據不足；不能由 top-k 沒命中推出“沒有記錄”。

例：MQC-DOC-001 只有當前場景文書清單、病例/就診匹配及讀取覆蓋均可靠，才能提出“在本次材料範圍缺少某文書”的候選；它仍不能斷言現實中未完成診療。MQC-DOC-004 查不到被提及的結果時，報告當前材料缺可定位來源；不推斷臨床沒檢查。

### 規則結果的三個正交維度

| 維度 | 需表達 | 防止的誤讀 |
| --- | --- | --- |
| 適用性 | 適用 / 不適用 / 未確定，及所用條件/版本 | 範圍外不能當規則通過 |
| 執行與覆蓋 | 完成 / 部分 / 失敗 / 未執行，單位與分母 | 程序結束不能當完整檢查 |
| 條件判定 | 成立 / 不成立 / 無法判斷，證據與影響範圍 | 無數據、無檢索命中、模型拒答都不能當陰性 |

它們映射既有 PSC-002/004/005 狀態，不發明新的業務終態。問題、無問題（僅聲明範圍）、未知與臨床“合格”不能混同。

### 證據包與模型邊界

F006 以一條規則/明確檢查範圍組織輸入，包含允許上下文、相關原文、必要父段/表頭/單位、適用依據與覆蓋。先取得該規則的必要證據集再按資源預算裁剪；丟掉必須條件時標不可判斷，不靠截斷後餘下內容強行得結論。

凍結 model/revision/量化、prompt、tokenizer、採樣、輸入/輸出限制、解析/語義/規則/索引版本。生成結果依次通過結構校驗、引用屬於允許輸入、版本/定位回放、主張是否受支持的核對；最後一步不能用 ID 存在或簡單字符串包含冒充。

保留 Qwen 4B 作為工程基線，以當前任務實測決定是否滿足某類語義項。沒有通過時不自動換更大/外部模型掩蓋缺口，也不將確定性檢查的成功擴展到語義項。模型、檢索、事實抽取和專家結論分層，源字段不被生成結果寫回。

<a id="tp-16"></a>
## TP-16 · 評測、上線門檻與運行保障

### 按失敗機制建樣本

以 8 條規則、來源/語言/文書類型、長短、風險、正常/問題/未知和同規則例外分層。包含主體變化、否定、假設、歷史/當前、單位/數值衝突、源缺失、引用錯位、未審核規則、截斷、撤權、惡意正文及重複提交等直接相關反例。

真實、需求派生、合成來源分組報告。按患者/文書家族/來源文本哈希及近重複關係分組劃分，CMQCIC 同文本不同指標不跨建設/獨立驗證集合；可識別患者時保持其相關文書同組，來源不同同號不做錯誤歸併。參數/提示在建設/調試範圍選擇，驗證/留出答案只交 Evaluator，不進入檢索或語義構造。

| 層 | 核對方法 | 不可省略的範圍 |
| --- | --- | --- |
| 解析/覆蓋 | 原值、結構、頁/記錄/通道及 locator 回放 | 未讀/損壞/不支持、未知總數及限量截斷 |
| 語義斷言 | 專家核對主體、極性、時間/條件、單位與原文 | 長尾/中英表達、缺失/衝突，不把候選當事實 |
| 檢索 | 證據 ID/支持集合的覆蓋與排序，BM25 基線對照混合 | 版本/資格過濾、無答案、關鍵詞和改寫，權限範圍內的分母 |
| 規則/候選 | 按適用機會計算漏報/誤報、證據與建議可用性 | 不適用/無法判斷/人工移交另報，別刪除困難樣本提高分數 |
| 人工評測 | 兩名具權限的真實身份先獨立原判，再仲裁 | 一致性用仲裁前結果；模型多數票不代替雙人複核 |
| 責任流程 | 真路徑複核、申訴、整改、重核、雙籤與返回 | 寫後崩潰、租約搶佔、重複/過期決定、審計失敗和跨進程恢復 |
| 試用/人因 | 離線→影子→人確認輔助，觀察誤用、處理負擔與移交 | 不預選接受，不讓高亮/分數掩蓋缺證據；用戶接受率不單獨當質量指標 |

Recall/precision 只對明確參照與分母計算，分母為零標不可計算；按規則/風險/語言分層並保留不確定區間。重複病例會影響獨立性，不能把重複任務當額外獨立樣本。高風險漏報的一票否決沿 PRD，零次觀察漏報不證明總體風險為零。

模型/提示/量化、規則/適用範圍、索引/語義或來源實質變化時，只重驗受影響範圍，影響不明則擴大到聲明範圍。不得修改原判、答案、題目或閾值來挽救已失敗候選。臨床問題的專業判斷與工程指標分開。

### 可觀測性與運行隔離

記錄 source/version、run/job/attempt、task/decision、thread/checkpoint、配置摘要、開始/結束、實際調用/覆蓋和錯誤碼。普通日誌不保存病例全文/完整 prompt/憑據/私有推理；確需調試證據包時存受控資料域並關聯用途、訪問和留存。外部遙測默認不啟用。

常見故障處置：DB 不可用不確認業務寫入；模型失敗保留局部結果和語義缺口；SSE 斷線重新授權後查詢權威狀態；磁盤不足不發佈半成品；源/權限變化先停止受影響消費；恢復發現版本不兼容時受控停止。沒有“所有錯誤都自動重試到成功”的策略。

### 備份、遷移和發佈

數據庫使用受控備份/WAL 方案並做恢復演練，原件與版本化資產按同一可核對時間/manifest 保留。只保存 SQL dump 或複製模型緩存不等於完成災難恢復；須恢復一個固定舊病例結果及其原文/簽字鏈驗證。RPO/RTO、保留週期和密鑰管理由目標運行條件確定後再作為門禁，不憑當前筆記本設生產保證。

遷移使用 Alembic 和向前兼容的接口/數據步驟；圖/Schema 變更核對未完成任務和舊 checkpoint，必要時暫停新的進入、保留現有業務決定並顯式遷移。新索引先構建核驗再切換，回退只能服務仍有資格/授權的舊範圍，不能恢復撤權內容或失效規則。

部署先凍結依賴/鏡像/模型摘要、模型資產來源與許可，再在域內運行；開發 Compose 不等於生產編排完成。原始 Data、業務責任記錄、可重建索引、checkpoint 和模型緩存有不同清理條件；未確認保全/留存要求時不執行刪除。

## 與現有 Feature 的承接

- TP-13：F001 的身份/接口、F002/F003 的來源任務、F004～F007 的實際工作臺/API入口。
- TP-14：F001 授權/責任、F004 查詢、F005 索引、F006/F007 版本/事務/恢復；不改變原職責劃分。
- TP-15：F004 原表達與醫療上下文、F006 條件和候選證據；補充已有 AC 的具體樣本，不增加自動診療。
- TP-16：F008 專家評測、F009 准入與各 Feature 的直接驗證；F008/F009 已展開詳細計劃，指標/分母見[統一評估計劃](../../evaluation-plan.md)，接口見[實施合同](../implementation-contracts.md)；本文不冒充已實現。
