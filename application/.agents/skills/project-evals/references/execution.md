# 執行與維護銜接

## 校驗與執行分開

```sh
python3 <SKILL_DIR>/scripts/validate_evals.py <項目根> --suite evals/F001.json --require-bound
```

輸出的 `checks` 包括檢查 ID、關聯用例和 `effective_inputs`，後者合併套件、來源與顯式輸入。命令只讀文件，不調用模型、不執行 suite 中的命令。`ok: true` 表示定義校驗通過；`behavior: not_evaluated` 始終提醒尚未執行驗收。

執行前實際審閱命令是否驗證了關聯斷言、會產生什麼副作用及其授權。聲明的 argv 不構成付費調用、部署或遠程寫入的額外授權。

## 已有維護變更

當前正由 `$maintain-project` 處理變更時，沿用它的活動記錄，將本次檢查 ID 列入 `begin` 的 `checks`。建立記錄前確定用例、數據、測試文件的預期路徑；執行前確保真實存在。每個 command 檢查只執行一次，不先裸跑再為記錄重複跑：

```sh
python3 <MAINTAIN_SKILL_DIR>/scripts/maintenance.py run-check \
  --project <項目根> --id <本輪變更ID> --name F001-export-behavior \
  --input evals/F001.json \
  --input docs/PRD.md \
  --input docs/specs/product-spec.md \
  --input docs/specs/F001-export/spec.md \
  --input backend/tests/check_export.py \
  --input backend/tests/fixtures/orders.json \
  -- python3 backend/tests/check_export.py
```

示例路徑需替換。把校驗輸出中所有 `effective_inputs` 逐項作為 `--input`；已在維護記錄 `sources` 中的實現文件可省略。這樣用例、測試、輸入和規格變更都會讓相關收據失效。最終由維護流程完成 `check`、業務語義審閱和 `finish`；其收尾規則保持不變。

已有活動記錄漏列檢查時不要繞過白名單或覆蓋原基線。現有腳本沒有追加檢查命令：新發現的檢查按下方
“單獨驗收”方式執行並寫入正式記錄，同時註明它未納入該維護記錄的自動門檻；原有檢查與收尾仍照常
完成。後續變更在 begin 時完整聲明。manual 檢查的實際操作與結論也記在正式驗證記錄，不用無意義
成功命令冒充機器檢查。

## 新項目或單獨驗收

按綁定 argv 在項目根直接運行項目原生檢查，記錄真實退出狀態和斷言輸出。人工或瀏覽器操作按 manual 定義執行。沒有維護變更時，不為驗收虛構源碼修改，也不創建依賴“源碼必須變化”的維護收尾記錄。

原生測試報告與必要日誌放入已有產物目錄；缺少約定時使用 `.codex/project-evals/`，在產生文件前將 `/.codex/project-evals/` 加入項目 `.gitignore`。正式驗證記錄是驗收結論事實源；該運行目錄僅保存可重建產物，若記錄仍引用唯一證據，先保留到約定的交付存儲再清理。只產生需要的日誌，不復制工程或依賴樹。

正式記錄至少包含：

| 項目 | 記錄內容 |
|---|---|
| 範圍 | suite、eval ID、來源 AC / PSC |
| 條件 | 代碼版本；有未提交改動時記錄相關 inputs 指紋；樣本和評分版本；實際運行環境 |
| 方法 | 實際 argv 或人工操作，運行時間、必要的重複次數 |
| 結果 | 每項預期是否滿足；pass / fail / not_run / blocked / error |
| 證據 | 原生報告、日誌或必要截圖的位置；不能只寫“測試通過” |
| 限制 | 未運行項及原因，哪些總體驗收仍未覆蓋 |

一次真實觀察也可作為 manual 證據。它不能被包裝成自動化測試，也不能無條件複用於不同實現或環境。

## 不誤報結果

- 運行前缺少依賴或授權，記 `blocked`；尚未嘗試記 `not_run`；運行命令或基礎設施異常記 `error`。
- 斷言不符合預期記 `fail`，全部本次必需斷言實際執行且滿足才記 `pass`。
- 退出 0 只是命令檢查的必要證據，仍需核對測試數量和跳過項；它不證明測試覆蓋了全部業務語義。
- 維護腳本檢測到過期輸入時會報告失敗及“檢查證據已過期”；正式驗收記錄將對應舊證據標為 `stale`，重新執行受影響項。單獨驗收時同樣對照所記錄的版本/指紋。
- 採用模型評分時，分數來自真實評分輸出；業務閾值來自合同。未授權運行或只有評分腳本而未執行時，不填寫模擬分數。
