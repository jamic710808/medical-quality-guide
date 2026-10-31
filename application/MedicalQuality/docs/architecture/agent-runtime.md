# Agent 編排與運行技術決定

> 2026-10-14 實施更新：本地正式應用、原生圖譜、數據/模型/本體工具與責任流程已落地。本文保留設計和研究依據，設計當日的“尚未實現/未實測”不再代表當前狀態；實際文件、已驗證範圍及仍缺的專業/完整驗收見[開發報告](../verification/development-report.md)。

日期：2026-10-13。用戶要求按業務比較指定 Agent 技術、沉澱 Skill，並落到對應 Feature。本次完成選型、詳細設計和驗收設計，未運行 Agent、安裝框架、修改原型或調用模型服務。

## 決定與業務歸屬

醫療一期採用 **Python LangGraph 顯式編排 + 業務狀態/責任記錄獨立持久化 + 固定工具合同**。LangChain 只在具體適配確有收益時引入；既有 sqlite3、BM25/BGE-M3/RRF、Qwen/llama.cpp 決定不變。框架不接管醫生、專家或質控崗位的判斷權。

| 決定 | 本期採用 | 業務原因與歸屬 |
| --- | --- | --- |
| AG-01 編排層 | LangGraph StateGraph，確定節點/邊；不使用自由規劃循環決定規則是否執行 | F006 的有限質控步驟、失敗和版本重核需要明確可檢查路徑 |
| AG-02 持久恢復 | LangGraph PostgreSQL checkpointer 保存執行遊標，固定 thread/graph/schema 版本，獨立 schema/權限 | F006 計算恢復、F007 跨時人工等待；內存 saver 不能證明重啟可恢復 |
| AG-03 業務狀態源 | PostgreSQL 保存任務、決定、意見、簽字及審計/outbox，業務事務與 checkpoint 保存分開 | F007 責任事實不能依賴模型記憶或圖當前節點；冪等由業務層保證 |
| AG-04 人工輸入 | 工作臺經 F001 校驗後形成帶主體、對象/版本、理由和冪等鍵的 BusinessDecision，再恢復圖 | 真正的質控複核、醫生整改/申訴和分崗位簽字；工具審批不等於業務簽署 |
| AG-05 工具邊界 | 模型只獲取允許的只讀證據/候選能力；寫業務狀態由授權應用處理器執行 | 保持 F004/F005/F006/F007 的合同；不向模型開放任意 SQL、shell、改庫、代簽 |
| AG-06 運維與驗證 | 節點結果/覆蓋、嘗試、檢查點和業務提交分別記錄；中斷/重複/過期回調做故障測試 | 不把框架 SUCCESS、流結束或單次演示當全閉環成功 |
| AG-07 本體語義消費與建設分離 | LangGraph 固定 SemanticRelease 調 F004 只讀語義/關係/形狀接口；build/explore/evolve-ontology 用於建設與回放，原生 active 不激活產品 | F004 提供本體服務，F005 受限檢索，F006 SG-01～10 顯式消費；[具體合同和 Skills 步驟](../data-preparation/governance-cleaning-handoff.md#agent-semantic) |

執行/責任機制集中在 [TP-10～12](technical-points/agent-orchestration.md)，本體及 semantic／Evo Skills 的專項合同維護在[數據治理文檔 8.21～8.31](../data-preparation/governance-cleaning-handoff.md#agent-semantic)，實施歸屬為 [F006 Plan](../specs/F006-quality-evidence-review/plan.md) 與 [F007 Plan](../specs/F007-remediation-accountability/plan.md)。不新增泛化 Agent 平臺 Feature，也不把其他框架為了展示而同時接入。

## 按不同業務比較候選

| 候選 | 適合優先比較的業務 | 在本項目的取捨 |
| --- | --- | --- |
| 普通 Python 處理 | 確定性解析/計算、少量無長期等待步驟 | F003 讀取、F004 查詢和 F005 檢索仍可保持普通模塊，作為圖節點調用，無需全面 Agent 化 |
| LangChain / LangGraph | 模型/工具適配，以及有狀態分支、等待、恢復的業務流程 | 選 LangGraph 為 F006/F007 編排層；可直接調現有客戶端，不強制引入第二套模型循環 |
| AgentScope 2.0 | 獨立資料分析、不同上下文/工具的角色協作及 Agent 服務 | 作為後續獨立分析任務備選；當前多崗位是人類責任，不由多 Agent 投票替代；TeamPipeline 實驗接口需固定版本驗證 |
| Pi | 自有 CLI、研發助手、專用工作臺的可嵌入工具循環 | 本期不自建此類運行底座；未來若有該產品需要再比較 SDK/RPC，不接管臨床狀態源 |
| DeepSeek Harness | 模型/工具/會話/策略需要插件化替換的定製運行底座 | 當前為 developer preview，接口可能破壞兼容；醫療一期沒有收益依據支持引入該維護面 |
| Hermes Agent | 持續資料整理、重複任務、跨會話助手 | 研究/支持助手的候選；記憶、自動形成的 Skills 不能當規則批准、病歷事實或簽字記錄 |
| Codex | 工程開發維護、批處理自動化；也可通過 SDK/app-server 嵌入產品 | 當前用作開發協作工具，未把它嵌入醫療業務執行鏈；代碼/工具批准不等於臨床複核。新接入需單獨核對數據流、賬號/模型、協議與實驗接口 |

這些是結合本項目目標作出的選擇，不是通用排行榜。若以後獨立多角色分析、插件運行底座或持續助手成為明確業務目標，按真實問題驗證備選；當前無需替換已選的檢索與本地模型。

## 用戶材料與官方核對

用戶此前提供的三份 Excalidraw 是選型維度的歷史來源。此次補充核對發現下列三處原路徑當前不可定位，保留引用以說明出處，不作為當前運行或驗證依賴；本次設計使用已沉澱的項目合同、本地 Skills 和本輪核對的官方文檔，未改寫或重建這些原文件：

- [業務編排材料](<COURSE_CONTENT_WORKSPACE>/excalidraw/courseware/fde-medical-part10/52-選型-LangGraph與AgentScope業務編排.excalidraw)
- [定製運行材料](<COURSE_CONTENT_WORKSPACE>/excalidraw/courseware/fde-medical-part10/53-選型-Pi與DeepSeekHarness定製運行.excalidraw)
- [應用接入材料](<COURSE_CONTENT_WORKSPACE>/excalidraw/courseware/fde-medical-part10/54-選型-Hermes與Codex應用接入.excalidraw)

材料中的推薦不是生產驗收記錄；產品仍按真實業務、現有 PRD/PSC 與責任條件設計。

| 核對項 | 已查事實與限制 | 官方依據 |
| --- | --- | --- |
| LangGraph | checkpointer 支持線程狀態恢復；interrupt 的節點恢復會重跑，副作用要防重放 | [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)、[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| LangChain | 提供可配置 agent/model/tool 層，LangGraph 是較低層編排，不必捆綁全部服務 | [Overview](https://docs.langchain.com/oss/python/langchain/overview) |
| AgentScope | TeamPipeline 文檔解析到 2.0.10dev，pipeline 明確實驗性；達到最大迭代也可能 SUCCESS | [TeamPipeline](https://docs.agentscope.io/en/versions/2.0.10dev/building-blocks/pipeline/team) |
| Pi | SDK / RPC 的進程邊界不同，擴展與宿主有同等 OS 權限 | [SDK](https://pi.dev/docs/latest/sdk)、[RPC](https://pi.dev/docs/latest/rpc)、[Extensions](https://pi.dev/docs/latest/extensions) |
| DeepSeek Harness | 官方確認 Cordis 插件架構及 developer preview；網站抓取沒有正文，未編造插件 API | [官方倉庫](https://github.com/deepseek-ai/deepseek-harness) |
| Hermes | profile 記憶與會話快照有明確生命週期，不能當多方責任數據源 | [Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)、[Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) |
| Codex | 本機 CLI 0.153.4 與 app-server 幫助已只讀核對；未查看賬號/憑據或運行任務。官方 SDK、協議/傳輸需分版本核對，WS 與實驗方法不能默認視為生產支持 | [SDK](https://learn.chatgpt.com/docs/codex-sdk)、[App Server](https://learn.chatgpt.com/docs/app-server)、[平臺說明](https://developers.openai.com/blog/codex-as-a-platform) |

## 本體與 semantic／Evo 的接入決定

Agent 框架保持 LangGraph。建設期優先複用已有 build/explore/evolve-ontology 指導宿主代理，通過實際 evo-semantic 工具形成五類候選/軌跡；經產品 adapter、形式檢查和專業核對後成為 SemanticRelease。運行期優先直接調用 F004 的固定版本只讀服務，不讓病例 Agent 獲得構建/演化/發佈工具。

定義層推理由 ROBOT/ELK 離線執行，SHACL 檢查限定實例視圖，業務條件仍由 F006 Python 處理器負責；語義發現、形式推導和臨床結論不混同。原生 browse/resolve 文檔未展示逐請求版本/完整授權，未核驗前不作為凍結醫療運行的直接入口。當前會話無 evo-semantic callable，項目缺 Core/config/workspace；本輪只寫設計，不建立環境或模擬工具結果。

## 最小驗證與當前狀態

優先驗證顯式單圖路徑，不先開多 Agent 團隊：

1. 固定 F006 輸入/規則/模型版本，節點錯誤、模型超時和執行恢復不產生完整通過的假象。
2. F007 在人工作業處持久暫停，重啟後仍有真實待辦；過期、重複和錯身份的恢復請求不能改變任務。
3. 在業務提交後、圖檢查點/響應前故障，恢復不重複產生決定、任務或簽字；寫入結果未知先對賬。
4. 原判、爭議、整改和簽字版本固定；新文書/依據創建新核驗鏈，不能繼承舊簽字。
5. 取消計算與業務撤銷分開；圖/協議升級遇舊檢查點能遷移或受控停止，不盲目回放舊寫入。

LangGraph/checkpoint 包尚未安裝，準確版本、持久化兼容與接口須在首次實施鎖定並驗證。本次[基礎架構](architecture.md)將原先輕量 SQLite saver 設想收斂為正式 PostgreSQL checkpointer；業務事務、圖事務與真實併發故障仍須實測。Spec/Plan/Tasks 與結構校驗不能替代這些證據。
