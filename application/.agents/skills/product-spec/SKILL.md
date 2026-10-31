---
name: product-spec
description: 把已確認的項目級 docs/PRD.md 轉成唯一的 docs/specs/product-spec.md，定義跨 Feature 的產品對象、全局狀態機、不變量、共享交互與事件、安全恢復、兼容能力和總體驗收，並建立 REQ/NFR/AC → PSC 追蹤。用於編寫或更新項目總 Spec、凍結跨功能行為合同、在拆 Feature 前收斂共享語義；不用於寫 PRD、展開單個 Feature、選擇技術架構、拆 Plan/Tasks 或根據源碼逆向建檔。
---

# 產品總規格

把已確認 PRD 轉成所有 Feature 必須共同遵守的產品行為合同。只依賴 Markdown 模板和 Python 標準庫
校驗器，不依賴 Spec Kit、Superpowers 或外部規格框架。

## 輸入與職責邊界

1. 鎖定項目根，讀取適用的 `AGENTS.md`、`docs/PRD.md`、已有總規格、共享規格和架構文檔。
2. 運行同級 `$product-prd` 校驗器，確認 PRD 為 `status: confirmed`；PRD 未確認時停止。
3. 一個項目只維護一份 `docs/specs/product-spec.md`。已有文件時保留穩定 PSC ID、有效合同和確認歷史，
   增量合併，不整文件覆蓋。
4. 按以下邊界寫文檔：

| 文檔 | 唯一職責 |
|---|---|
| `docs/PRD.md` | 為什麼做、給誰、範圍、REQ/NFR 和產品驗收 |
| `docs/specs/product-spec.md` | 跨 Feature 的統一產品行為與不變量 |
| `docs/specs/feature-map.md` | Feature 邊界、需求/PSC 歸屬、依賴和狀態 |
| `docs/specs/FNNN-*/spec.md` | 單個 Feature 的流程、狀態、邊界和局部驗收 |
| `docs/architecture/` | 框架、依賴、數據、服務、協議實現和部署選擇 |

總 Spec 不重複 PRD 背景，不彙編全部 Feature 細節，也不選擇框架、數據庫、類、文件或部署拓撲。

## 落盤總 Spec

從 `assets/product-spec.template.md` 創建或更新 `docs/specs/product-spec.md`，狀態先設為 `draft`。

### 1. 建立全局模型

根據 PRD 寫清：

- 所有 Feature 共用的產品對象、對象身份、關係和職責；
- 跨頁面或跨能力的狀態機、生命週期、允許轉換和確定終態；
- 不得被單個 Feature 改寫的業務不變量、順序、冪等與一致性語義；
- 共享交互、事件、能力探測、可觀察證據和失敗恢復合同；
- 產品級安全、權限、憑證、隱私、兼容、降級和產品語言邊界；
- 只有組合多個 Feature 才能證明的總體驗收門檻。

大型橫切主題可以拆到 `docs/specs/shared/<topic>-spec.md`，但總 Spec 必須保留該主題的權威摘要、
PSC ID 和鏈接；不得讓共享文件形成第二個衝突總規格。

按實際產品填寫這些章節，不適用時說明原因；不為了模板補造對象、事件或恢復機制。延續 PRD 的來源、
假設和適用條件，引用既有需求即可，不復制背景材料。

### 2. 建立穩定 PSC 追蹤

- 全局合同使用 `PSC-001` 起的三位穩定編號。
- 每條 PSC 在“全局合同索引”只定義一次，引用至少一個 REQ/NFR 和一個 PRD `AC-NNN`。
- 每個 REQ/NFR 與 PRD AC 至少由一條 PSC 承接。
- 在對象、狀態、不變量、安全等詳細章節再次引用對應 PSC ID，不能只有索引沒有合同正文。
- 刪除或替換合同時保留變更記錄；不要回收舊編號給不同語義。

PSC 描述產品必須如何表現，不描述具體代碼怎麼實現。若發現新的產品範圍、行為或驗收，先回
`$product-prd` 更新並重新確認 PRD，不能在總 Spec 中靜默新增需求。

### 3. 確認總合同

確認前核對：PSC 的適用範圍是否確實跨 Feature；狀態轉換是否有明確觸發、前置條件、結果和失敗出口；
不同章節是否給同一對象或動作定義了衝突含義；產品級門檻能否觀察到真實結果。以具體條目指出缺口，
不按 PSC 數量推定文檔過重。索引中的每條 PSC 必須在對應行為章節有正文承接。

集中向用戶呈報會影響多個 Feature 的對象語義、狀態機、不變量、共享交互、安全恢復、兼容與總體門檻。
當前指令已經明確批准的語義無需要求特定口令。只有合同獲確認、沒有阻塞問題且無模板槽位時，才將
frontmatter 改為 `status: confirmed`。

開放問題沿用 PRD 的“待確認/處理中/已解決/已關閉”（也接受 open/closed）。關閉項寫結論與依據，
非阻塞假設保留驗證方式與時機；沒有新產品決定時沿用已有授權，不重複確認。

### 4. 校驗

從實際加載的 `SKILL.md` 定位 `<SKILL_DIR>`，運行：

```bash
python3 "<SKILL_DIR>/scripts/validate_product_spec.py" \
  "<項目根>" --require-confirmed
```

校驗器檢查 PRD 前置狀態、章節、PSC 唯一性、REQ/NFR/PRD AC 覆蓋、行為章節引用、索引必填內容、
開放問題與模板殘留；它不把
結構通過冒充用戶確認，也不判斷產品方案是否優秀。

## 變更與下游規則

- 產品目標、範圍、需求或驗收變化：先更新並確認 PRD，再更新總 Spec、Feature Map 和受影響 Feature。
- 只改變跨 Feature 行為合同：更新並重新確認總 Spec，再更新 Map 與受影響 Feature Spec。
- 只改變單個 Feature 行為：更新該 Feature Spec；若觸及共享不變量，必須上提總 Spec。
- 只改變實現方法：更新 Architecture/Plan/Tasks，不改 PRD 或總 Spec。
- 總 Spec confirmed 且校驗通過後，使用 `$feature-spec-planning` 拆 Feature Map 和三件套。

## 完成標準

- `docs/specs/product-spec.md` 是唯一項目級總行為合同；
- PRD 的 REQ/NFR/AC 全部進入 PSC 追蹤；
- 全局對象、狀態、不變量、共享交互、安全恢復、兼容和總體驗收完整；
- 總 Spec 不重複 Feature 細節、不承載技術選型或開發任務；
- 狀態為 `confirmed`，且校驗器通過。
