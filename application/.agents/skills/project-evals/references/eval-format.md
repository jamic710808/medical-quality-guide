# 用例格式與示例

這是本項目 Skills 的輕量約定，不是 OpenAI 的強制格式。所有業務敘述使用簡體中文；既有編號不重排。

## 套件

`evals/FNNN.json` 表示一個 Feature；`evals/product.json` 表示選定的跨 Feature 門檻。

| 字段 | 含義 |
|---|---|
| `schema_version` | 固定為整數 `1` |
| `scope` | `F001` 等 Feature ID 或 `product` |
| `sources` | 項目相對文檔路徑數組，包含 PRD、總 Spec 與相關 Feature Spec；必要時加入 Map / shared Spec |
| `product_contracts` | 僅 product 使用，聲明本次必須組合驗證的 PSC；由總 Spec 的產品級門檻確定 |
| `cases` | 非空用例數組 |
| `checks` | 檢查定義數組；純設計階段可為空 |

校驗器按 frontmatter 確定定義歸屬：PRD 定義 `AC-NNN`，Feature Spec 定義與自身 `feature` 一致的
`AC-FNNN-NNN`，Product Spec 在索引表第一列定義 `PSC-NNN`。AC 必須是標題，正文提及和代碼塊示例
不算定義。Map、shared Spec 等輔助來源僅補充上下文與輸入追蹤，不重複定義或擴充驗收編號。
綁定時正式來源須 confirmed / ready；輔助資料若聲明狀態也須 confirmed，沒有狀態的輔助資料不因
被引用就成為已確認合同。它覆蓋本 Feature 來源文檔中的所有 AC；product 覆蓋聲明的
`product_contracts`，PSC 選擇是否充分仍需對照總 Spec 做語義審閱。

## 用例與檢查

用例必填 `id`、`title`、`source_ac`、`given`、`when`、非空字符串數組 `expected` 和 `check_ref`。`source_ac` 至少關聯一項已定義 AC。product 用例還需 `source_psc`，引用本套件選定的 PSC。

- Feature 用例 ID 為 `EV-F001-001`；product 為 `EV-PRODUCT-001`。
- `check_ref` 是本套件 `checks` 內的 ID；未綁定為 JSON `null`。
- 檢查 ID 在同批套件中唯一，例如 `F001-export-behavior`，可直接用於 maintenance 的檢查名。
- 每個檢查有 `id`、`method` 和 `inputs`。`method` 為 `command` 時需非空 `argv` 數組；為 `manual` 時需 `procedure` 與 `evidence` 兩個非空字符串。
- `inputs` 列實現、測試、數據和配置，可包含目錄（其內容均納入）。綁定校驗時這些路徑必須存在且在項目內；聲明完整性仍需 Agent 審閱。suite 和 sources 由校驗器自動加入輸出的 `effective_inputs`。
- 檢查定義不得放密碼或 Token；需要憑證時遵循當前項目授權與注入方式。

以下僅為假設的訂單導出示例，不能直接當作客戶批准的業務規則。示例路徑需對應真實項目後才能通過校驗：

```json
{
  "schema_version": 1,
  "scope": "F001",
  "sources": [
    "docs/PRD.md",
    "docs/specs/product-spec.md",
    "docs/specs/F001-export/spec.md"
  ],
  "cases": [
    {
      "id": "EV-F001-001",
      "title": "導出當前篩選結果",
      "source_ac": ["AC-F001-001"],
      "given": "O-001、O-003 為待交付，O-002 已完成；用戶擁有導出權限",
      "when": "按待交付狀態篩選後執行導出",
      "expected": ["導出訂單集合恰為 O-001、O-003", "每筆訂單隻出現一次"],
      "check_ref": null
    }
  ],
  "checks": []
}
```

工程與測試存在後，可將 `check_ref` 改為 `F001-export-behavior`，並加入：

```json
{
  "id": "F001-export-behavior",
  "method": "command",
  "argv": ["python3", "backend/tests/check_export.py"],
  "inputs": ["backend/export.py", "backend/tests/check_export.py", "backend/tests/fixtures/orders.json"]
}
```

該測試必須實際觸發導出並核對結果；寫下 argv 本身不提供行為證據。一個命令關聯多條用例時，它的輸出或報告須逐條可追蹤，任何必要用例未運行都不能把整組記為通過。

## 變更與範圍

用例預期與來源衝突時先解決合同差異，不以當前代碼輸出作為標準答案。只有實現方式變更時，只更新檢查綁定與相關 inputs；業務行為變更時先更新上游合同，再調整用例。保留舊驗證記錄的適用版本。

CLI 的 `--suite` 明確限定本次範圍，可重複；不會自動遞歸執行或檢查其他 Feature。全量驗收需要顯式選擇所有相關套件並核對總體驗收範圍。
