# 技術依據與運行邊界

## 已驗證的接口合同

2026-09-28 在本機 `codex-cli 0.153.4` 核對官方文檔及該二進制生成的 JSON Schema，並對當前項目真實歷史做只讀調用。讀取接口不啟動模型，也不向來源會話發送消息。

腳本連接 `codex app-server --stdio`，按 JSON-RPC 發送 `initialize`（`capabilities.experimentalApi: true`），再發送 `initialized` 通知。只允許以下請求：

| 方法 | 用途與關鍵字段 |
| --- | --- |
| `thread/list` | 按 `cwd`、`searchTerm`、`archived`、`cursor` 定位會話。`searchTerm` 是標題子串過濾；`useStateDbOnly: true` 避免掃描 JSONL 來修復索引 |
| `thread/read` | `includeTurns: false` 取得元信息；不恢復或訂閱會話 |
| `thread/turns/list` | `itemsView: full`、`sortDirection: desc` 分頁讀持久化輪次；`nextCursor` 接續舊頁 |
| `thread/items/list` | 通過 `threadId` 與 `turnId` 分頁回查條目，返回 `turnId` 和 `item` |

分頁接口屬於實驗能力。Schema 中 `ThreadReadParams.includeTurns` 已提示：分頁會話不宜一次加載完整歷史，應使用元信息讀取和分頁方法。官方網頁不同段落的存儲能力描述可能存在版本差異，以安裝版本的 Schema 和實際調用為準；遇到不支持的方法就報告邊界，不自動遷移歷史或修改數據庫。

可以重新核對 Schema，輸出放臨時目錄，用後清理：

```bash
codex --version
codex app-server generate-json-schema --experimental --out /temporary/schema-directory
```

當前支持本機、當前環境 `CODEX_HOME` 對應的存儲。未接入遠程主機、其他賬戶或離線歸檔盤；不能把本機沒找到等同於該會話從未存在。默認候選來源包含 CLI、IDE、App Server、exec 的主會話，不自動搜索子代理樹。

## 輸出語義

`read` 的用戶/助手正文保留為可讀原文，不通過另一份摘要代替。工作記錄保留類型與成功/失敗字段，較長細節明確截斷，原文可通過 `show` 分段回查。附件只保留引用，不提取圖像內容。內部推理、Hook 提示和未知內部項不導出。

引用鍵為 `thread_id / turn_id / item_id`。條目按服務器返回的順序保留；舊記錄缺失時間時不推造時間。來源當前狀態、讀取時點、覆蓋範圍與增量檢查點分別標明，工作文件不構成新的歷史事實來源。

`read --all` 遍歷到無下一頁，但“已經導出完整記錄”不等於“模型已經閱讀全部導出內容”；Skill 仍要按任務範圍分段閱讀。`search` 是字面檢索，命中上限會明確標記不完整，不能據無命中斷言某個語義從未出現。

增量用 `--after-turn` 從最新輪向後掃描，包含前次末輪再停止。這個重疊處理用於補齊當時仍在寫入的輪次。錨點消失時失敗退出；不會從最新一頁重新開始卻把結果聲稱為完整增量。

## 原生壓縮為什麼沒有接入本版

官方已有兩種相關能力，但它們不是會話歷史的可讀摘要導出接口：

1. **App Server `thread/compact/start`**：本機 Schema 的參數只有 `threadId`；請求立即返回 `{}`，通過 `contextCompaction` 的條目生命週期報告進度。它處理目標線程的上下文，不能當作只讀查詢。`contextCompaction` 公開條目只帶 ID，不包含一份可以直接導出的交接正文。
2. **Responses API `/responses/compact`**：接收仍能放入模型上下文窗口的輸入，返回規範的下一段上下文，其中包含不供人閱讀的加密 compaction 項，也可能保留其他條目。官方要求將返回窗口完整用於後續 Responses 請求，不能抽出幾句文字就稱為同等壓縮。它需要額外的 API 調用與相應認證。

按任務整理溝通時間線與決定證據，屬於當前模型對歷史資料的分析。本版不會把它冒充官方 compaction，也不保證任何壓縮可無損保留全部原話。

後續若明確要求原生壓縮，可以單獨驗證“臨時 Fork → 在臨時線程壓縮 → 繼續一輪生成交接結果 → 回查來源關鍵證據”的組合。官方有 `thread/fork(ephemeral: true)`；分頁臨時分支還涉及 `excludeTurns`。這只是接口組合方案，尚未進行端到端驗證。接入前必須驗證臨時線程生命週期、模型支持、是否保留關鍵決定、引用回查及清理，並確認額外模型用量或 API 認證的授權。不得對來源 A 或當前窗口 B 自動調用壓縮，不得手動修改 `state_*.sqlite` 或 rollout 文件來注入內容。

## 來源

- [官方 App Server：讀取歷史、分頁、條目類型、Fork 與壓縮](https://learn.chatgpt.com/docs/app-server)
- [官方 Compaction：返回窗口、加密項與輸入限制](https://developers.openai.com/api/docs/guides/compaction)
- [官方 Skills：顯式調用、描述匹配、腳本與發現機制](https://learn.chatgpt.com/docs/build-skills)
- 本機 `codex app-server generate-json-schema --experimental` 的 `ThreadReadParams`、`ThreadTurnsListParams`、`ThreadItemsListParams`、`ThreadCompactStartParams`、`ThreadForkParams`；不在技能中複製整份生成物。

## 驗證入口

`python3 scripts/test_session_history.py` 使用合成記錄驗證決定撤回、執行失敗、分頁覆蓋、原文定位、增量重疊和只讀請求邊界，不讀取真實用戶歷史，也不調用模型。結構校驗使用 skill-creator 的 `quick_validate.py`。真實會話聯通性和技能發現結果在交付時單獨核對。
