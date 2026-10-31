# 交付清單與檢查

`scripts/delivery_manifest.py` 僅用 Python 3 標準庫，讀取明確列出的項目文件並保存/核對 SHA-256。它不掃描工程、不讀取環境變量、不調用外部服務、不運行項目測試、不壓縮或發佈文件。

## 一份可維護清單

默認路徑為 `docs/delivery/delivery-manifest.json`。先由 Agent 根據實際交付範圍填寫下面的結構；示例名稱和路徑需要改為當前項目。`inputs` 是本次版本核對的依據，`artifacts` 是實際交付文件，`omissions` 是已識別的缺項。

```json
{
  "schema_version": 1,
  "project": "訂單協同",
  "release": "v1.0-review",
  "scope": "本地訂單查詢功能及接手材料",
  "inputs": [
    {"path": "docs/specs/F001-query/spec.md", "role": "範圍依據"},
    {"path": "backend/query.py", "role": "當前實現"},
    {"path": "docs/verification/F001.md", "role": "正式驗收記錄"}
  ],
  "artifacts": [
    {"id": "D-001", "title": "交付總覽", "path": "docs/delivery/README.md", "audience": "recipient"},
    {"id": "D-002", "title": "運行手冊", "path": "docs/operations.md", "audience": "recipient"}
  ],
  "omissions": [
    {"id": "D-003", "title": "目標環境接手記錄", "reason": "尚未提供目標環境", "next_step": "由運維崗位提供環境後執行手冊中的接手檢查"}
  ]
}
```

字段約定：

- `schema_version` 為 `1`；`project`、`release`、`scope` 是非空文字，按實際範圍寫明版本。
- `inputs` 至少一項，每項有 `path` 和說明其用途的 `role`。選擇與交付結論相關的現行規格、實現、配置和證據；複用測試結果時，核對其涉及的輸入，不只列報告文件。它不聲稱記錄了整棵工程。
- `artifacts` 至少一項，每項有唯一 `id`、`title`、`path` 和 `audience`。`recipient` 表示供本輪接收者使用，`internal` 表示內部材料；這只是分發標記，不是訪問控制或自動授權。
- `omissions` 為數組，無缺項填 `[]`。每項有唯一 `id`、`title`、`reason`、`next_step`；責任和時間可在交接記錄中補充，不能編造。缺項與已交付文件不能使用相同 ID。
- 路徑相對應用根，使用 `/`，不能是目錄、絕對路徑、`..` 或指向根外的符號鏈接。清單不能把自身作為輸入或產物。目錄型源碼交付通過交付總覽指向工程或確切源碼包，不把一個 README 的哈希冒充源碼完整性證明。
- `snapshot` 為每個文件增加 `sha256`、`bytes`，並更新 `prepared_at`。`check` 只讀比較；修改產物或輸入後會報告不一致。

源數據、內部成本、原始日誌和認證文件不自動成為交付文件。填寫清單前檢查所列文件是否適合對應接收範圍；腳本不識別正文中的秘密，也不證明權限和許可正確。

## 命令

在交付文檔和證據適用性已核對後建立快照，`<SKILL_DIR>` 指本 Skill 實際安裝目錄：

```sh
python3 <SKILL_DIR>/scripts/delivery_manifest.py snapshot \
  --project <應用根> --manifest docs/delivery/delivery-manifest.json

python3 <SKILL_DIR>/scripts/delivery_manifest.py check \
  --project <應用根> --manifest docs/delivery/delivery-manifest.json
```

`snapshot` 會更新指定清單中的文件指紋，除此之外不改工程文件；失敗時保留原清單。`check` 成功退出 0，文件缺失、版本變化或結構錯誤退出 1，並輸出具體問題；命令參數錯誤退出 2。

更改文件後先處理真實影響：實現/規格變化可能使舊驗收證據失效，應補驗或保留 `stale`；交付文字變化則核對對應說明。然後更新交付版本和清單。不能僅重新 `snapshot` 就宣稱舊測試適用於新實現。

腳本輸出始終註明 `behavior: not_evaluated` 和 `recipient_signoff: not_evaluated`。有缺項時文件檢查仍可能通過，輸出會保留缺項數量；這表示現有文件可核對，不表示交付範圍完整。文檔語義、鏈接目標是否適合接收者、驗收覆蓋及真實接手由 Agent 對照現有證據核查。

默認不創建副本、ZIP 或運行目錄。用戶要求分發包時先確定來源、範圍和保存位置，交付中的相對路徑以實際分發根為準；在目標包上使用同一檢查並檢查接手入口。只交付所需資產，依賴樹、緩存、認證狀態、內部材料和無關原件不能通過全目錄複製混入。
