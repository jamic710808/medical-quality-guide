---
name: build-fde-project
description: 面向 FDE 項目交付，從零創建帶內置 FF Logo 和統一品牌合同的產品項目：先準備外層工作目錄的 Raw 原始資料區，再創建同級的大駝峰項目並初始化標準目錄，依次落盤已確認的 PRD、Product Spec、Feature Map 和逐 Feature spec/plan/tasks，最後實現並驗證用戶授權的 Feature。用於空目錄或尚無實質產品源碼的新項目；不用於已有源碼現代化、只逆向補文檔或尚未準備落盤的想法討論。
---

# FDE 項目構建與交付

把標準骨架、產品合同和 Feature 規格作為首次產品代碼之前的必要準備，然後繼續實現用戶已經授權的
Feature。文檔初始化不是完成信號。

## 路由邊界

以下“目標”指實際開發的項目目錄。外層工作目錄已有客戶原件、文檔或 Skills，不影響在其中新建獨立開發項目。

- 目標沒有實質產品源碼，用戶準備從零落盤或開發：使用本 Skill。
- 目標已有可運行源碼、manifest、頁面、API 或歷史數據：在同一項目按 `$maintain-project` 處理本次迭代；不重新初始化。
- 用戶只要求從想法形成 PRD，尚未要求初始化或開發：使用 `$product-prd`。
- 用戶已有 confirmed PRD，只要求凍結項目總行為合同：使用 `$product-spec`。
- 用戶已有 confirmed PRD 與 Product Spec，只要求拆 Feature 文檔：使用 `$feature-spec-planning`。
- 只根據已有源碼補建文檔：按項目已有的文檔維護約定處理，不運行初始化流程。

## 先準備外層原始資料區

先確定外層工作目錄：用戶指定的位置優先，否則使用當前工作目錄；用戶已明確開發項目路徑時，外層工作目錄為該項目的父目錄。原始資料區與開發項目同級：

```text
<工作目錄>/
├── Raw/          # 客戶原始資料
├── .agents/skills/
└── AgenticRAG/   # 大駝峰命名的開發項目
```

第一項寫操作是在外層準備原始資料目錄，已有內容保持原樣：

```bash
mkdir -p "<工作目錄>/Raw"
```

告知用戶將客戶原始資料放入該位置，再引導確定大駝峰項目名及下列最小輸入；當前對話已明確的信息直接複用。
原件保留在 `Raw/`，不自動搬動其他位置的客戶資料；項目代碼和派生文檔寫入獨立開發項目。

## 開發項目的最小輸入

初始化開發項目之前至少確認：

- 符合 PascalCase 的項目根目錄名；
- `FF - <正式產品名>` 格式的對外名稱；
- 一句話產品定位；
- 唯一目標目錄以及本次是規劃、開發某些 Feature，還是完整開發。

目標用戶、旅程、範圍、技術路線等由後續 PRD/Architecture 流程收斂。只有缺失信息會實質改變寫入目標、
產品行為或不可逆範圍時才詢問，不為填模板重複訪談。

## 在開發項目內初始化標準骨架

先從實際加載的 `SKILL.md` 定位本 Skill 目錄，記為 `<SKILL_DIR>`。確認同級 `$product-prd`、
`$product-spec`、`$feature-spec-planning` 和 `$project-evals` 均存在，再運行：

```bash
python3 "<SKILL_DIR>/scripts/init_project.py" \
  "<工作目錄>/AgenticRAG" \
  --public-name "FF - <正式產品名>" \
  --summary "<一句話產品定位>"
```

腳本的目標是 `Raw/` 同級的大駝峰開發項目，不是外層工作目錄或 `Raw/`。腳本在寫入開發項目前校驗目錄名、共享模板、目標路徑類型與邊界和內置 FF Logo 完整性；路徑衝突先報錯，只創建缺失內容，不覆蓋已有文件。它創建：

```text
<project>/
├── frontend/
│   └── public/brand/ff-logo.png
├── backend/
├── docs/
│   ├── PRD.md
│   ├── specs/product-spec.md
│   ├── specs/feature-map.md
│   ├── architecture/architecture.md
│   └── verification/
├── README.md
├── AGENTS.md
└── CLAUDE.md
```

Feature 目錄由 `$feature-spec-planning` 在 Map 明確後創建。不在開工時創建最終交付目錄。

## 初始化後的產品合同

### 1. PRD

使用同級 `$product-prd` 把對話和已確認材料寫入 `docs/PRD.md`：

- 當前輸入足以確定用戶、核心旅程、範圍、需求、NFR 和驗收時，可在同一任務確認並繼續；
- 存在會改變產品行為的缺口時，保留 `draft`，只向用戶呈報這些決定，未確認前不寫產品代碼；
- confirmed 後運行其 `validate_prd.py --require-confirmed`。

### 2. Product Spec

使用同級 `$product-spec`，把 confirmed PRD 轉成 `docs/specs/product-spec.md`：

- 定義跨 Feature 的對象、狀態機、不變量、共享交互/事件、安全恢復、兼容與總體驗收；
- 使用穩定 `PSC-NNN`，覆蓋全部 PRD REQ/NFR/AC；
- 不重複 Feature 細節，不選擇技術棧；
- confirmed 後運行其 `validate_product_spec.py --require-confirmed`。

### 3. Feature Map 與 Feature Spec

使用同級 `$feature-spec-planning`：

1. 從 confirmed PRD 與 Product Spec 生成並確認 `docs/specs/feature-map.md`；
2. 每個 Feature 同時承接來源 REQ/NFR 與 PSC；
3. 為每個 Feature 創建目錄並先寫清 `spec.md` 的行為、邊界、狀態和 AC；
4. 此時不根據空目錄猜實現文件、框架或數據流，Plan/Tasks 可保持 draft。

Feature AC 明確後使用 `$project-evals` 設計本次 `evals/FNNN.json`，先確定測試輸入、動作與預期；
檢查入口可暫未綁定。跨 Feature 門檻按總 Spec 設計 product 套件，註明依賴和驗收時機。
`evals/` 在實際有用例時創建，不由初始化腳本預填假業務樣例。

確認意味著用戶批准了實際語義，不要求用戶說特定口令。當前請求已經明確給出並授權的範圍無需再次確認。

### 4. Architecture、Plan 與 Tasks

1. 根據 confirmed PRD、Product Spec、Feature Map、Feature Spec 和已確認技術選擇填寫 `docs/architecture/architecture.md` 與 `AGENTS.md`；沒有阻塞決策後把 Architecture 標為 `status: confirmed`。
2. 回到 `$feature-spec-planning`，基於 Architecture 完成本次授權 Feature 的 `plan.md` 與 `tasks.md`。不按前端、後端或集成車道拆 Task，不使用 FE/BE/INT 標籤；運行 `validate_feature_specs.py --feature FNNN --require-ready`，多個 Feature 重複傳入 `--feature`。其餘 Feature 可保留 draft 或延期狀態。
3. 本次包含業務前端時，在寫頁面代碼前完成下方“首次前端實現前”的設計；即使已有 API、選擇了組件庫或未單獨製作原型，也不能跳過。
4. 在 `frontend/`、`backend/` 中創建項目真正需要的框架、manifest、入口、測試和配置。由 `$project-evals`
   複用或補齊本次行為檢查，綁定用例；只在真實入口與輸入存在後要求 `--require-bound` 通過。
5. 只實現用戶點名或本次明確授權的 Feature；按 `tasks.md` 依賴執行，一個 Task 可跨頁面、服務、數據和測試。
6. 通過 `$project-evals` 執行本次必要用例，記錄真實結果、運行條件和未驗證項；只有完成證據和最窄驗證
   真實通過後才勾選 Task。Feature 完成後將 Map 行與 tasks 狀態改為 `completed`，
   運行 `validate_feature_specs.py --feature FNNN --require-complete`。
7. 從真實 manifest 和腳本回填 README 與 AGENTS 中的命令，不憑經驗編造。
8. 把驗收結果寫入 `docs/verification/`；完整交付還需執行本次範圍內跨 Feature 的產品門檻。日誌等運行
   產物先配置忽略規則，不把結構校驗冒充驗收。完成授權範圍後停止，不自動實現下一個 Feature。

### 首次前端實現前

把界面設計作為首次實現的一部分，不等用戶指出“看不懂、像說明頁、點進去找不到”後才補。使用項目已有的前端設計文檔或相關 Feature Plan，簡記下列決定即可，不另設審批關卡：

- **業務語言**：從來源資料/主數據核對主要對象名稱和狀態含義。有名稱時不能只用設備代號、字段鍵或運行 ID 作標題；用戶日常使用的訂單號等業務編號保留。名稱不足標為待核實，模擬名稱不冒充事實；按鈕用語與實際動作、結果一致。
- **頁面結構**：先確定用戶任務、主工作區、對象上下文、輔助信息及適合記錄規模的瀏覽方式。不要照搬接口/Feature 劃菜單，也不要用大標題、說明文字和卡片縱向堆疊替代應用設計。
- **詳情與導航**：按實際任務選擇頁籤、分欄或展開；不強制每頁分籤。明確主要入口 → 對象/頁面/頁籤 → 可見結果 → 返回位置；同一對象的名稱和狀態在直接相關入口一致，保存後可找到結果。
- **驗看**：把本次關鍵路徑交給 `$project-evals`，檢查來源名稱、按鈕落點、返回上下文和目標視口中的實際操作；不能僅以編譯成功或頁面有這些文字判斷完成。

同級 `build-frontend-prototype` 可用時，讀取並應用其中的 [應用產品設計方法](../build-frontend-prototype/references/product-design.md)。這裡複用設計方法，不啟動額外原型工程，也不將原型的模擬實現用於替代正式功能。獨立分發未包含該 Skill 時，直接執行以上要求；無需為此安裝額外設計工具。

重大 UI 方向影響本次產品決定且尚未明確時，先討論具體差異；用戶需要可點擊原型輔助對齊時，可使用
現有 `$build-frontend-prototype`，不把額外製作原型設為默認開發前提。

## 項目交付

完成當前授權範圍後，交付項目源碼、必要配置和文檔。README 提供已驗證的安裝、啟動、測試與構建命令，
`docs/verification/` 記錄驗收結果、未驗證項、外部依賴和已知限制；未定義的命令如實標註，不編造。

項目交付不默認附加培訓或推廣材料、演示截圖或視頻，也不為這些額外材料創建目錄。開發驗收所需的界面截圖仍可作為驗證證據。

## 不可覆蓋的項目合同

- 項目根使用 PascalCase，只允許英文字母和數字且以大寫字母開頭。
- 用戶可見名稱使用 `FF - <正式產品名>`；內部倉庫名和臨時代號不進入界面。
- 統一使用 Skill 內置 `assets/brand/ff-logo.png` 原始字節；初始化腳本固定安裝到 `frontend/public/brand/ff-logo.png`。目標已有相同文件時保留，字節不同時在任何其他寫入前停止，禁止覆蓋、重繪、反色、改色、裁切或拉伸。
- 前端全局導航或頁頭必須把 FF Logo 放在完整產品名左側；所有可滾動頁面在內容末尾提供 `@賦範空間 獨家研發`，固定高度工作臺將同一腳註放入側欄或應用殼底部。
- 不默認向最終用戶顯示“演示模式”“Mock”“測試版”等內部研發階段標籤；只有產品規格明確要求用戶告知時才展示。
- 使用用戶任務、業務對象、動作和可觀察狀態命名，避免包裝性黑話。
- 不讀取、回顯或提交真實憑證；不調用計費服務、不寫外部系統、不部署，除非用戶明確授權。
- 初始化報告中的 `kept_files` 屬於用戶已有資產；讀取並增量合併，不覆蓋。
- PRD、Product Spec、Feature Map、Spec、Plan、Tasks、Architecture、實現和驗證證據保持同一需求 ID、PSC 與驗收語義。

## 完成標準

- 外層 `Raw/` 與大駝峰開發項目同級，客戶原件與項目產物分開存放；
- 標準骨架在首次產品代碼之前建立；
- `docs/PRD.md`、`product-spec.md` 與 `feature-map.md` confirmed，授權 Feature 三件套通過 ready 校驗；
- 授權 Feature 的 Task 有真實完成證據並通過 complete 校驗；
- README 與 AGENTS 命令對應真實腳本；
- 本次包含前端時，業務名稱有來源，頁面結構與詳情落點有設計依據，必要界面路徑有真實驗看結果；
- 未把目錄初始化、文檔落盤或部分 Feature 完成誤報為整個產品或項目交付完成。
