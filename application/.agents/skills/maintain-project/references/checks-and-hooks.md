# 檢查與 Hooks 協議

## Skill、檢查腳本與 Hook 的分工

- **Skill**：指導 Agent 理解本輪需求、確定影響範圍、修改實現與相關文檔，並判斷內容是否符合需求。
- **檢查腳本**：讀取 Agent 事先聲明的文件範圍和實際檢查結果，核對有無漏改、誤改、漏驗或過期證據；它不會自行理解業務或生成修改方案。
- **Hook**：把調用腳本的動作接到宿主的指定時點。本適配在 Codex 準備結束一輪迴復時接收 `Stop` 事件；只有接入配置、加載並信任之後才會自動調用，不是複製 Skill 後就自動生效。

同一個 `scripts/maintenance.py` 提供手動檢查命令和 `hook` 事件入口。業務文件及檢查命令由項目傳入；當前事件適配面向 Codex，其他宿主需按其協議另行接入。

## 運行記錄

以下路徑由腳本相對於 `--project` 解析；該參數指工作區根，不一定是某個應用的源碼目錄。先讀實際文件並確定範圍，再把本輪 JSON 通過標準輸入交給 `begin`。以下僅演示字段結構：

```sh
python3 <SKILL_DIR>/scripts/maintenance.py begin --project <工作區根> <<'JSON'
{
  "id": "change-existing-behavior",
  "request": "按本輪已確認要求調整現有功能",
  "sources": ["src/feature.py"],
  "documents": [
    {"path": "docs/behavior.md", "action": "update", "reason": "當前行為約定隨本輪變更調整"},
    {"path": "README.md", "action": "keep", "reason": "啟動與使用方式不受本輪影響"},
    {"path": "docs/verification.md", "action": "update", "reason": "記錄本輪真實驗證"}
  ],
  "protected": ["inputs/original"],
  "checks": ["behavior-check"]
}
JSON
```

示例中的文件、目錄、語言和檢查名都必須替換為當前項目的實際範圍；不為套用示例創建這些文件。`documents.action` 為 `update` 或 `keep`，兩種決定都要寫理由。`protected` 只列本輪明確不應改變的已有路徑。源文件可預聲明尚未存在的新增文件。

腳本創建 `.codex/maintenance/runs/<id>.json` 和相應檢查輸出，並確保 `/.codex/maintenance/` 被項目 `.gitignore` 忽略。它們是本輪執行狀態，源碼與正式驗證記錄才是持久交付；無活動變更且正式記錄不再依賴其中的唯一證據時才能清理，仍需交付的證據先轉存到項目約定位置。相同 ID 不覆蓋已有記錄。

會話綁定優先顯式 `--session-id`，否則使用執行環境提供的 `CODEX_THREAD_ID`。後者必須在目標宿主確認與 Hook 事件的 `session_id` 相同後，才算原生接入通過；缺少綁定時仍可手動執行檢查，Hook 不猜測當前任務。

## 執行與收尾

```sh
python3 <SKILL_DIR>/scripts/maintenance.py run-check --project <根> --id <變更ID> --name <檢查名> -- <實際命令及參數>
python3 <SKILL_DIR>/scripts/maintenance.py check --project <根> --id <變更ID>
python3 <SKILL_DIR>/scripts/maintenance.py finish --project <根> --id <變更ID> --review '對照需求與當前設計核對了哪些行為'
```

命令以參數數組執行，不經 shell。檢查在項目根運行，保存退出狀態、輸出、聲明源文件和額外 `--input <相對路徑>` 的指紋。測試腳本、相關配置或數據不在 `sources` 中時，用 `--input` 顯式納入；只更新驗證記錄不會讓已完成的代碼檢查無故失效。

目錄輸入內指向項目內的目錄鏈接會追蹤目標內容；越出項目或形成循環的鏈接會報錯，不能形成有效收據。

`check` 讀取當前文件和已保存的結果，不重複運行測試。它核對：需要更新的文件確有變化、保留和保護的文件未改變、檢查實際執行且成功、檢查輸入仍有效。內容哈希差異只證明有改動，不證明文檔語義正確；`finish --review` 的內容由執行 Agent 在實際審閱後記錄。

接入項目 evals 時，`checks` 使用套件中的檢查 ID，`--input` 納入套件、來源規格、測試、數據和配置
（`project-evals` 校驗輸出的 `effective_inputs`）。多個用例可共用一次有充分斷言的檢查；在正式驗證
記錄中建立 eval ID → 檢查 ID → 證據的關聯。這裡仍只記錄進程結果與指紋，不解析業務斷言，也不把
沒有執行的 manual 檢查算作通過。純驗收且沒有源碼變更時使用項目原生檢查與驗證記錄，不虛構維護變更。

等待用戶決定時用 `pause --reason <原因>` 標記該變更；繼續時用 `resume`。它們只改變運行狀態，不改產品規格或驗收狀態。已完成記錄不自動接管下一輪請求；每輪使用新的 ID。

## Hooks

`hook --project <根>` 接收宿主標準輸入 JSON，目前只處理 `Stop`：

- 只查當前 `session_id` 綁定的未暫停、未完成變更；無匹配時靜默退出，純討論不會被拉入維護任務。
- 多個活動變更無法唯一定位、輸入損壞或檢查異常時報告 `error`，不猜測歸屬，不當作通過。
- 已知 `fail` 可返回具體文件與原因，請求 Codex 繼續處理一次；它延續當前工作，不替 Agent 修改文件。同一問題指紋或 `stop_hook_active` 已設置時只報告，避免反覆續跑。
- `not_run` 明確指出未完成的檢查，不把它偽裝成 `pass`。等待補充信息時應先暫停本輪變更。
- `pass` 只表示確定性條件滿足；業務語義與頁面驗看仍屬於 Skill 的工作。

Hook 只讀業務文件，可寫本輪檢查緩存。它不執行測試命令、不改寫業務文檔、不注入通用提示詞、不強制規劃，也不從聊天全文猜測需求。工作流可先由 Skill 調用檢查命令跑通，再連接 Hook。

當前協議以 [Codex Hooks 官方文檔](https://learn.chatgpt.com/docs/hooks) 為依據。stdin 協議測試通過不等於目標客戶端已經加載、信任並觸發 Hooks；原生事件、會話綁定、信任狀態必須單獨核驗並報告。
