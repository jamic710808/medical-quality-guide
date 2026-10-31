---
name: feature-spec-planning
description: 根據 PRD、Product Spec 與架構，按業務功能、處理階段或能力模塊討論可獨立驗證和迭代的 Feature 拆分，確認後落盤 Feature Map，並按授權範圍展開 spec.md、plan.md 和 tasks.md，建立 PRD → PSC → Feature → AC → Task → 證據追蹤。用於開發前討論邊界與依賴、拆 Feature、補局部規格、制定實施計劃或任務清單；不用於寫 PRD、寫項目總 Spec、逆向建檔或直接實現功能。
---

# Feature 規格與任務規劃

把已確認的 PRD 和產品總規格轉成職責清楚、可獨立驗證和迭代的 Feature 文檔。交付結果可以供業務用戶使用，
也可以由明確的下游模塊消費；按當前目標和用戶意圖選擇拆分主線，不固定採用業務旅程或技術模塊。
依賴只有 Markdown 模板與 Python 標準庫校驗器；不依賴外部規格框架、命令插件或技術分層 Pack。

## 本次工作範圍

- 僅討論拆分：讀取材料，呈報推薦邊界、依據與取捨；不創建或修改 Map、Feature 三件套及驗收文件。
- 創建或調整 Map：按本次授權落盤和確認 Map；不因 Map 完成而自動展開 Feature。
- 展開 Feature：沿用已確認的 Map，只為本次選擇的 Feature 編寫三件套及對應驗收用例。
- 用戶明確要求完整規劃時，可在授權範圍內銜接上述階段；規劃不包含代碼實現。

## 前置條件

1. 鎖定目標項目根並讀取適用的 `AGENTS.md`、`docs/PRD.md`、`docs/specs/product-spec.md`、架構文檔和已有規格。
2. 正式確認 Map 或展開 Feature 前，運行 `$product-prd` 的校驗器，確認 `docs/PRD.md` 為 `status: confirmed`。
3. 同階段運行 `$product-spec` 的校驗器，確認項目總規格為 `status: confirmed`。僅討論時可基於已有草稿提出
   候選，但須標明影響邊界的假設與缺口，不編造來源 ID，也不把候選寫成已確認決定。
4. PRD 缺範圍或驗收時回 `$product-prd`；跨 Feature 對象、狀態、不變量或共享行為不清時回 `$product-spec`。
   不得在 Feature 文檔裡靜默發明上游合同。
5. 已有 Feature Map 或 Feature 目錄時保留穩定 ID、歷史狀態和用戶內容，做增量合併，不整套重號。
6. `plan.md` 必須以真實代碼上下文和已明確的架構決策為依據。全新項目的技術邊界尚未收斂時，可以先確認
   Map 與 Feature Spec，但要在 Architecture 明確後再完成 Plan/Tasks；不得在 Feature Plan 中替用戶猜技術路線。

## 標準落盤結構

```text
docs/
├── PRD.md
└── specs/
    ├── product-spec.md
    ├── feature-map.md
    ├── F001-<kebab-slug>/
    │   ├── spec.md
    │   ├── plan.md
    │   └── tasks.md
    └── F002-<kebab-slug>/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

`docs/PRD.md` 是產品需求事實源；`product-spec.md` 是跨 Feature 行為事實源；`feature-map.md` 是 Feature
邊界和依賴事實源。Feature 目錄不得反向修改上游合同或偷偷重組 Map。

## 1. 拆 Feature Map

新增或調整拆分時，先讀 [通用拆分規則](references/feature-decomposition.md)，根據具體材料形成一套
推薦方案，說明拆分主線、交付結果、範圍、需求覆蓋與依賴。階段或模塊型 Feature 要說明輸入、輸出、消費方、
獨立驗證方式及可單獨優化的邊界。沿用已確認 Map 展開 Feature 時無需重新拆分。

獲准落盤時，從 `assets/feature-map.template.md` 創建或更新 `docs/specs/feature-map.md`，使用 `F001` 起的
三位穩定編號和 `F001-kebab-slug` 目錄。保留 Map 的八列表格，拆分理由、輸入輸出、具體範圍和依賴依據寫在正文，
不額外創建一份拆分報告。已有 Map 按需補充依據，不為套用新模板重排歷史內容。

Map 在拆分方案獲得確認前標為 `draft`。默認由 Agent 提出推薦，用戶整體確認；若本次授權已明確批准同一
拆分，或明確委託 Agent 自行決定該 Map，則在授權範圍內完成判斷並記錄依據，無需重複確認。上游文檔已確認
不等於當前拆分已批准。滿足上游條件、覆蓋與邊界檢查且無影響拆分的阻塞後，才標記 `status: confirmed`。
修改已確認 Map 時，說明邊界、覆蓋和依賴的變化並按同一授權規則確認，不能在子目錄裡改邊界。

## 2. 為每個 Feature 落三件套

從對應模板創建文件，並保持同一 Feature ID。

### `spec.md`：What 與邊界

使用 `assets/spec.template.md`，寫清：來源 REQ/NFR、來源 `PSC-NNN`、對應的 PRD `AC-NNN`、使用者或消費方、
交付結果、輸入輸出語義、主流程、對象狀態、成功/空/失敗/恢復、範圍邊界和 `AC-F001-001` 格式的 Given/When/Then。
不得寫技術選型或把計劃偽裝成需求。Map 分配的需求與 PSC 在本 Feature 承擔的部分必須由 Feature AC 承接；
一條 PRD AC 需跨 Feature 完成時，說明各自承接的條件或輸出，組合驗收保留在產品級，不要求中間階段獨自完成整條旅程。

按實際場景寫明用戶或消費方入口、前置條件、可觀察結果、退出與必要的恢復路徑；階段或模塊型結果可通過產物、
查詢或調用驗證，不要求單獨的用戶頁面。無關狀態說明不適用，不補造業務規則。複用全局合同的 PSC 引用，
局部 Spec 只展開本 Feature 的應用方式。開放問題用 OQ 表記錄影響、
是否阻塞、驗證方式與時機、狀態和關閉依據，沿用 PRD 的中英文狀態約定；有實施阻塞不能標 ready。

本次新建或修訂的 Feature AC 明確後，使用同級 `$project-evals` 設計 `evals/FNNN.json`，把條件轉為
具體輸入、操作和預期。此時允許檢查尚未綁定，不要求先有實現或 ready Plan。對總 Spec 中必須組合
Feature 才能證明的門檻，安排 product 套件及其執行時機；不因局部 Feature 完成而宣稱全產品驗收通過。

### `plan.md`：How 與實施順序

使用 `assets/plan.template.md`，根據當前代碼和架構寫文件影響、複用點、狀態/數據流、實施順序、依賴、
風險、回退及每條 AC 的驗證方法。明確與上下游的輸入輸出對接、本模塊可單獨調整的實現部分和直接受影響的消費方；
Feature 邊界不強制對應獨立服務、進程、倉庫或部署單元。Plan 只能實現 Spec，不能新增產品行為。

驗收映射關聯對應 eval ID、擬複用或新增的檢查及證據；同一檢查可覆蓋多個用例，不重複執行等價檢查。
檢查綁定在工程入口存在後由 `$project-evals` 完成；規劃階段只運行其結構校驗，不把未綁定命令當作
已經可運行。已有 Plan 沿用原表結構增量加引用，不為適配模板重排歷史內容。

“驗收映射”表至少保留 AC、實現結果、最窄驗證方法、預期證據四項；已採用 evals 時加 Eval 引用。
正文其他位置提到 AC 不等於完成映射。規劃階段寫預期證據，完成 Task 後引用實際結果並說明適用版本。

### `tasks.md`：獨立可驗證結果

使用 `assets/tasks.template.md`。每個 Task 必須：

- 使用本 Feature 內唯一的 `T001` 起三位編號；
- 對應一個能獨立完成、驗證和留下證據的結果；
- 同時引用至少一個 REQ/NFR 和一個本 Feature AC；
- 寫明依賴、預計修改位置、完成證據和唯一的最窄驗證方法；
- 項目採用 evals 時，驗證字段關聯 eval ID 與實際檢查，完成證據引用真實結果；
- 可以跨前端、後端、數據、模型和測試完成同一結果；
- 不使用 `[FE]`、`[BE]`、`[INT]`、Pack 或其他技術車道標籤；
- 不以“2–5 分鐘”等固定時長作為拆分標準。

通常每個 Feature 為 6–18 個 Task。18 是複核線而非硬上限：超過 18 個時，先判斷是否包含多個獨立
交付結果；確實不可再拆時，在“Task 數量複核”寫明原因。少於 6 個可以成立，但應確認沒有把多個結果
塞進一個 Task。

## 3. 校驗並進入實現

從實際加載的 `SKILL.md` 定位 `<SKILL_DIR>`，運行：

```bash
python3 "<SKILL_DIR>/scripts/validate_feature_specs.py" \
  "<項目根>" --feature F001 --require-ready
```

用實際授權的 Feature ID 替換示例，多個 Feature 可重複傳入 `--feature`；只有確認整批均準備好時才
省略該參數。不為了啟動一個 Feature，把其他 Feature 的 draft 或延期項提前標成 ready。

進入實現前對照來源審閱 AC 是否表達同一業務含義、Plan 是否有真實複用與驗證方法、Task 是否能獨立
交付結果。校驗通過只證明結構、ID、覆蓋、依賴、開放問題和任務格式一致，不證明預期合理或證據真實。
若生成過程暴露新的產品決定，仍需回 PRD、
Product Spec 或 Map 確認。
本次已生成或更新的 eval 套件另運行 `$project-evals` 的結構校驗；不以此替代上述文檔校驗或行為驗收。
`spec.md` 與 `plan.md` 狀態設為 `ready`，`tasks.md` 設為 `planned` 後，才允許實現該 Feature。

## 4. 執行期維護

- 開始 Feature 時把 Map 行和 `tasks.md` 狀態改為 `in-progress`。
- 只有對應結果和驗證證據真實存在時才勾選 Task；不要預先批量打勾。
- 對已採用 evals 的 Feature，使用 `$project-evals` 綁定並執行本次必要檢查；失敗、未運行、受阻或過期
  證據不能作為完成依據。舊 Feature 沒有 evals 時保留已有有效驗收，不默認批量補建。
- Feature 全部 Task 完成後把 `tasks.md` 和 Map 行改為 `completed`，並運行：

```bash
python3 "<SKILL_DIR>/scripts/validate_feature_specs.py" \
  "<項目根>" --feature F001 --require-complete
```

- 新需求或 PRD 驗收變化：先更新並確認 PRD，再更新總 Spec、Map 和受影響三件套。
- 跨 Feature 合同變化：先更新並確認總 Spec，再更新 Map 和受影響 Feature Spec。
- 只有實現方法變化：更新 Plan/Tasks，不改 Feature Spec、Product Spec 或 PRD。
- 每次只實現用戶授權或當前計劃明確選擇的 Feature，不自動擴展到下一個。

## 完成標準

- 僅討論：已呈報拆分主線、推薦邊界、來源、理由和依賴；階段/模塊的輸入輸出、消費方及獨立驗證方式明確；
  需要用戶決定的關鍵取捨可直接審閱，未落盤後續文件。
- 僅 Map：已按授權落盤，需求與 PSC 覆蓋完整、結果歸屬與迭代邊界明確、依賴無環；待確認時如實保持 draft。
  正式確認時，PRD、Product Spec 與 Map 均為 confirmed，並有拆分確認依據。
- 展開 Feature：本次授權的 Feature 各有唯一目錄和完整三件套；其他 Feature 可保留在 Map 中待展開。
  分配給本次 Feature 的 PRD 需求/AC 與 PSC 無遺漏，Feature AC 全部進入 Plan 並由 Task 承接；Task
  依賴有效且無環，必填字段完整；沒有 FE/BE/INT 標籤、固定時長標準或未說明的超量任務。
  下游能從 Task 回到 Feature AC、PSC、Feature 和 PRD 需求，並能定位預期或實際驗證證據。
