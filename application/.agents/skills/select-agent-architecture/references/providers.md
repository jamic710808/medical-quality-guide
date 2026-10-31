# 官方能力與版本核對入口

核查基線：2026-10-13。這裡只保存改變選型的差異，採用時核對目標版本、語言 SDK、接口/傳輸和實際環境。不要將“官方有此能力”寫成用戶項目已驗證。

## LangChain / LangGraph

LangChain 提供模型、工具與可配置 agent harness；LangGraph 提供更低層的顯式編排，二者可分層使用。現有 Python 函數和模型客戶端可以直接成為圖節點，不強制把全部業務包裝成自由工具循環。[LangChain](https://docs.langchain.com/oss/python/langchain/overview)

LangGraph checkpointer 保存 thread 的執行狀態，store 用於跨線程信息；內存 saver 不能提供進程重啟後的持久恢復。SQLite saver 用於本地開發驗證，正式部署按實際存儲與併發條件選擇。[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)、[Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)

`interrupt()` 暫停並等待外部輸入，恢復依賴 thread 和保存狀態；恢復會重跑包含 interrupt 的節點，副作用須可安全重放。即使寫操作放在 interrupt 後，也應按實際故障窗口檢查冪等，不從一次示例推導所有業務恰好一次執行。[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

## AgentScope 2.0

當前官方倉庫以 2.0 為主，提供 Agent、Toolkit、運行/服務與管線能力。TeamPipeline 的 leader 分配任務，成員在獨立上下文中工作，結果回到 leader；能按成員轉發工具確認，但應用仍須設計業務授權與責任。[官方倉庫](https://github.com/agentscope-ai/agentscope)

本輪 Team 文檔解析到 `2.0.10dev`，明確 pipeline 模塊為實驗接口；正常結束或達到最大迭代次數都可能標為 SUCCESS，不能因此認定任務目標完成。採用前鎖定版本，並核對 `reply_id`、暫停/取消、成員上下文保留及真實結果狀態。[TeamPipeline](https://docs.agentscope.io/en/versions/2.0.10dev/building-blocks/pipeline/team)

## Pi

Pi 提供 SDK 進程內會話和 RPC 子進程接入；RPC 用標準輸入輸出上的 JSON 記錄，適用於其他語言宿主或自定義客戶端。兩種方式的默認資源/擴展加載不應假定一致。[SDK](https://pi.dev/docs/latest/sdk)、[RPC](https://pi.dev/docs/latest/rpc)

擴展與 Pi 進程擁有相同 OS 權限，不是自動隔離沙箱。工具、事件、會話與 UI 的具體接口按版本核對；取消與恢復需測試整個業務調用，不能僅看一條 cancel 事件。[Extensions](https://pi.dev/docs/latest/extensions)

## DeepSeek Harness

`deepseek-ai/deepseek-harness` 是基於 Cordis 的插件化 Agent Harness，和 DeepSeek 模型服務、LangChain Deep Agents 分開。官方當前標 developer preview 並提示破壞性兼容變化；適合需要擁有插件/運行生命週期且可承擔驗證維護的場景，不能寫成已穩定的所有業務默認底座。[官方倉庫](https://github.com/deepseek-ai/deepseek-harness)

核對具體插件、Profile、工具/策略、會話存儲及事件契約。文檔網站當次抓取未返回可讀正文，因此本 Skill 不憑空列其未核實 API 或性能；實際實施應讀對應固定源碼/文檔後再接入。

## Hermes Agent

Hermes 是具有工具、會話、Skills 與跨會話記憶的現成 Agent。官方說明默認記憶可由工具維護並按 profile 隔離，啟動時注入快照；共享一個 home 的多個寫入者會產生干擾。[架構](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture)、[記憶](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)

持續助手可考慮它，但要先確定各用戶/客戶的記憶邊界、過期/糾錯和可寫內容。自動生成的記憶/Skills 不等於審核過的業務規則；在有責任場景中只允許驗證過的變更進入運行路徑。

## Codex

區分使用入口：工程交互用 CLI/App/IDE，非交互任務考慮 exec，程序化任務考慮對應語言 SDK，持續會話/事件/審批接入考慮 app-server。它們可在產品中使用，但 harness、模型訪問與託管服務是不同邊界。[平臺概覽](https://developers.openai.com/blog/codex-as-a-platform)

SDK 的實現與版本要分別核查；當前官方 Python SDK 通過 app-server 控制本地運行並有其固定運行時依賴，不應把某個 TypeScript SDK 版本的內部機制外推到所有語言。[SDK](https://learn.chatgpt.com/docs/codex-sdk)

app-server 提供會話、事件和審批協議；方法/字段及傳輸有穩定/實驗差別。官方與本機 `codex-cli 0.153.4` 幫助均提示實驗邊界，WebSocket 不能默認當生產受支持傳輸；精確語義按該版本生成的 Schema/官方資料驗證。公開模型列表或 CLI 已安裝也不證明賬號有訪問權、模型在本地或調用已成功。[App Server](https://learn.chatgpt.com/docs/app-server)

Codex 相關問題優先使用可用的 OpenAI 官方文檔能力；只讀安裝版本/幫助可驗證本機入口，不讀取憑據測試賬戶，也不為研究運行實際收費任務。不得把工具調用批准映射為醫生/財務/管理人的業務簽字。
