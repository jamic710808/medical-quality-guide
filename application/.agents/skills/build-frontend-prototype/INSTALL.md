# 安裝與使用說明

這套工作流藉助 AI，把客戶需求、溝通記錄和我們希望呈現的方式轉成可點擊的體驗原型，讓雙方直觀討論未來如何使用系統。先明確溝通目標，把需求、業務對象與功能組織成整體設計，再明確頁面空間、列表瀏覽、滾動和工作承接，以代表性場景與模擬反饋驗看；不把各條鏈路分別做成孤立的小應用，也不以完整系統為交付目標。需求文件即可作為輸入，不要求提前提供 PRD、UI 稿或後端架構。

**新建默認使用多頁面 HTML、共享 CSS 和必要的原生 JavaScript。** 無需先創建 React 工程、安裝組件庫或執行 npm 構建。實現方式服務於本輪體驗，不代表正式產品的技術選型；已有原型沿用其技術棧。

## 1. 準備環境

| 項目 | 要求 | 用途 |
| --- | --- | --- |
| Codex | 可正常使用並能打開本地項目 | 讀取 Skill、設計、生成代碼和執行檢查 |
| 瀏覽器 | Codex 內置 Browser；或已有的項目瀏覽器測試環境 | 按選定場景查看頁面、體驗流程 |
| 本地靜態預覽工具 | 優先複用已有工具；例如已安裝 Python 3 的 `http.server` | 提供 HTML、CSS、JavaScript 的本地訪問地址 |

不把 Python、Node.js 或某個服務器作為統一安裝前提，先檢查現有可用的預覽方式。只有選擇 Vite、React 等需要 npm 的可選路線時，才準備 Node.js、包管理器和下載依賴所需的網絡；不需要數據庫、後端或設計工具賬號。

## 2. 把 Skill 放進自己的項目

安裝或分享時使用完整的 `build-frontend-prototype` 文件夾，保留內部目錄和許可證。複製到容納需求資料的工作區根目錄。該目錄與後續前端工程根目錄不同：

```text
工作區根目錄/
├── .agents/
│   └── skills/
│       └── build-frontend-prototype/
│           ├── SKILL.md
│           ├── INSTALL.md
│           ├── agents/openai.yaml
│           └── references/
├── 需求資料/                            # 沿用已有來源位置
└── docs/
    ├── 01_normalize-project-requirements/ # 已有需求資料
    ├── 02_requirement-playground/         # 已有需求看板
    ├── 03_prototype-design/               # 溝通目標、體驗設計與驗看記錄
    └── 04_frontend-prototype/             # 可點擊的演示載體，直接放源碼
```

使用文件管理器複製即可；`.agents` 是隱藏目錄。macOS 可用 `Command + Shift + .` 顯示隱藏文件。技能包僅包含文本規則與說明，不包含依賴或運行時。

在 Codex 中打開這個工作區根目錄，使用 `$build-frontend-prototype` 調用。若安裝後沒有出現在技能選擇中，重新打開項目或重啟 Codex。必要時明確讓 Codex 讀取 `.agents/skills/build-frontend-prototype/SKILL.md`。

四個編號表示階段職責；只有直接提供的三份需求文件時，也可以開始原型設計，不必先生成 01/02。只執行有實際任務的階段，不預建空目錄。詳細文件清單、已有項目處理和階段銜接見[目錄與產物約定](references/output-contract.md)。

應用產品設計方法與 Emil 設計心法已經隨包附帶：前者指導信息架構、空間和操作，後者打磨適用的組件細節。無需另裝全局設計 Skill、修改個人全局配置或安裝 UI/UX Pro Max。以後升級本技能時替換這一份目錄，避免項目級和全局級出現多個同名副本。

若只在前端子目錄單獨打開 Codex，應把這份技能安裝在該項目能發現的 `.agents/skills/` 下；不要假定任意外部父目錄都能被發現。

## 3. 用溝通目標與呈現意圖啟動原型

準備需求資料後，在工作區根目錄發出：

```text
使用 $build-frontend-prototype。
目的是讓甲方直觀體驗未來怎麼使用系統，討論流程和呈現是否符合預期。
請結合需求、溝通記錄及我的呈現想法，先確定本輪要討論的問題，
組織需求歸屬、業務對象、功能配合、頁面職責及共享狀態，形成原型的整體設計。
按包內產品設計方法明確關鍵頁面的空間、列表規模與瀏覽方式、滾動和返回上下文，
讓用戶能定位記錄、比較信息並接續處理，再用 Emil 心法打磨適用細節。
在同一系統中細化代表性使用場景，
讓本輪核心需求都有具體體現，相關功能與頁面的信息和結果保持一致。
用模擬內容和必要交互完成可點擊展示，不開發完整系統。
讓客戶從業務場景、信息主次和結果呈現中看懂解決什麼問題、對應什麼需求；
避免黑話和空泛口號，不把這一設計要求機械地做成頁面說明、按鈕或對話。
新建默認採用 HTML、共享 CSS 和必要 JavaScript；具體交互確實需要框架時再說明理由。
按約定把設計與驗看記錄放在 docs/03_prototype-design/，
把演示源碼放在 docs/04_frontend-prototype/，並完成必要的運行和場景驗看。
需求資料位置：填寫自己的相對路徑。
希望呈現的方式或演示重點：填寫已有想法或參考；尚無明確想法時請結合需求提出具體方向。
```

只想先看設計時，明確補充“本輪只做整體設計，只生成設計記錄，不創建工程、不寫實現代碼”。已有項目直接指出代碼目錄，工作流會先檢查並沿用其技術棧。

## 4. 默認生成與預覽

讓 Codex 按整體設計在 `docs/04_frontend-prototype/` 直接生成 `index.html`、按職責組織的業務頁面、共享樣式和腳本。內部示例見[目錄與產物約定](references/output-contract.md)。默認無需腳手架初始化，不預建 `src/`、`package.json` 或構建配置。

頁面生成後，從**工作區根目錄**啟動已有的靜態服務器。例如，本機已有 Python 3 時：

```sh
python3 -m http.server 5198 --bind 127.0.0.1 --directory docs/04_frontend-prototype
```

打開 `http://127.0.0.1:5198/`，按 `Ctrl+C` 停止。端口占用時更換端口並同步訪問地址，不停止其他項目服務。Windows 若使用 Python Launcher，可將 `python3` 換為 `py -3`；該 Windows 分支尚未實跑。缺少 Python 時使用已有等價靜態服務器，不為遵循這條示例強制安裝它。

該命令只提供本地靜態預覽。使用 JavaScript 模塊或讀取外部 JSON 時，通過 HTTP 打開；不要把雙擊 HTML 文件當成必然可用的運行方式。頁面跳轉、資源路徑和必要的跨頁狀態按實際體驗驗看；純 HTML 路線沒有必須執行的構建命令。

## 5. 分享與再次運行

一起提供 03 設計記錄和 04 原型目錄。默認保留 HTML、共享 CSS/JavaScript、實際用到的資源和 `README.md`；README 寫明運行目錄、已驗證的啟動方式、體驗順序、模擬內容與重置方式。接收方按同一說明啟動靜態預覽即可，無需 `npm ci`。

只在實際引入依賴時，才同時提供 `package.json`、相應鎖文件和運行配置。產生依賴、構建輸出或測試文件前配置忽略規則；`node_modules/`、`dist/`、緩存、錄屏和瀏覽器 profile 不作為原型源碼交付。

## 6. 可選：需要工具或框架時

按[實現方式選擇](references/stack-selection.md)判斷具體需要。Vite 可以單獨用於原生 HTML/JavaScript 的開發預覽和資源構建，不要求加入 React。使用 npm 工具時先檢查本機 Node.js 與包管理器是否滿足對應版本要求，再按官方說明安裝所需部分。

以下保留已驗證過的 React/shadcn 路線供確有需要時使用，**不是默認初始化步驟**。它基於 2026-09-28 的 macOS 驗證，Node.js 24.16.0 / npm 11.13.0；當前具體版本要求以官方說明為準。未在 Windows 上實跑。

### React 與 shadcn/ui

僅用於還沒有原型源碼、且已經選定此路線的新項目。在工作區根目錄執行；`04_frontend-prototype` 直接作為工程根目錄，不再改為業務名稱或嵌套一層應用：

```sh
node -e "require('node:fs').mkdirSync('docs', { recursive: true })"
cd docs
npx --yes shadcn@4.21.0 init --template vite --base radix --preset nova --no-monorepo --name 04_frontend-prototype --yes
```

此命令已實跑，會創建 React/TypeScript/Vite 工程，配置 Tailwind CSS、路徑別名和 shadcn/ui，並安裝依賴和 `button` 組件。它選擇 Radix 底層實現及 nova 預設；生成的 `components.json` 中 `style` 為 `radix-nova`。CLI 參數要寫 `--preset nova`，不要寫 `--preset radix-nova`。

進入新工程，按實際頁面需要添加組件。以本次驗證用到的彈窗為例：

```sh
cd 04_frontend-prototype
npx --yes shadcn@4.21.0 add dialog --yes
npm run dev -- --host 127.0.0.1
```

打開終端給出的本地地址，通常為 `http://127.0.0.1:5173`；端口占用時以實際輸出為準。按 `Ctrl+C` 停止服務。剛初始化的工程只是腳手架，具體業務頁面仍由工作流設計與實現。

以後從工作區根目錄啟動時，先執行 `cd docs/04_frontend-prototype`，再運行 npm 命令；從該工程目錄返回工作區根目錄使用 `cd ../..`。03 設計記錄始終位於外層 `docs/03_prototype-design/`，不在前端工程裡再建一套 `docs/prototype/`。

不要在已有工程上重複創建同名目錄或使用 `--force` 覆蓋配置。已有 React/Vite 工程如需加入 shadcn/ui，讓 Codex 按[官方現有工程安裝說明](https://ui.shadcn.com/docs/installation/vite)檢查其 Tailwind、別名和組件配置後增量接入。

### 此框架路線的構建與再次運行

在 `docs/04_frontend-prototype/` 前端工程目錄執行：

```sh
npm run build
npm run preview -- --host 127.0.0.1
```

`build` 包含 TypeScript 構建檢查；`preview` 用於本地檢查構建產物，以終端輸出地址為準。這不是公網發佈。

分享原型時同時提供 03 設計記錄與 04 工程；工程保留 `README.md`、`package.json`、`package-lock.json` 和源碼。接收方在 `docs/04_frontend-prototype/` 目錄執行：

```sh
npm ci
npm run dev -- --host 127.0.0.1
```

不要分享或提交 `node_modules/`、`dist/`、緩存、錄屏、瀏覽器 profile；創建工程後檢查 `.gitignore` 包含這些實際生成目錄。刪除 `node_modules/` 和 `dist/` 後可分別用 `npm ci`、`npm run build` 重建。

本次固定了 CLI 版本，但新建腳手架與 registry 仍可能隨上游變化。每個原型用自己的鎖文件固定解析結果；不要把 `@latest` 替換進安裝說明後直接聲稱已經驗證。

### Ant Design 分支

已有 Ant Design 工程直接沿用。新建原型只有在選定體驗確實需要複雜表格、表單等現成能力，或用戶明確指定時，才選擇該路線；不能僅因企業系統裡有表格就默認引入。此時不需要執行上面的 shadcn 初始化。

官方 Vite 路線的基本命令如下，從工作區根目錄執行，同樣遵守 04 工程目錄約定。此分支僅依據官方說明提供，本次未對其做完整安裝與 UI 驗收：

```sh
node -e "require('node:fs').mkdirSync('docs', { recursive: true })"
cd docs
npm create vite@9.2.1 04_frontend-prototype -- --template react-ts --no-interactive
cd 04_frontend-prototype
npm install
npm install antd@6.6.5
npm run dev -- --host 127.0.0.1
```

具體組件方案由 Codex 根據設計記錄編寫。不要為了“全都支持”同時安裝兩套主要 UI 組件庫。

## 7. 可選工具

- **shadcn 官方 Skill / MCP**：可協助檢索和添加組件，但不是本工作流的安裝前提。本輪未將它們寫入用戶配置。需要時再按[官方 Skill 文檔](https://ui.shadcn.com/docs/skills)或 [MCP 文檔](https://ui.shadcn.com/docs/mcp)安裝，並確認配置作用域。
- **其他 UI/UX 工具**：已有且適合時，可補充風格探索和設計審查。它們不替代場景編排、關鍵頁面設計和實際體驗驗看。

## 8. 驗證範圍與來源

歷史 React 路線在 macOS 上完成了環境安裝、組件添加、構建和基礎瀏覽器交互檢查；本輪 HTML 默認路線的檢查範圍單獨記錄，詳情見[驗證記錄](references/validation.md)。技術檢查不證明客戶原型已表達清楚或已獲得認可；本輪沒有重新生成客戶原型，Windows 環境及未註明實測的可選工具仍待驗證。

- [Codex 項目技能與發現規則](https://developers.openai.com/codex/skills/)
- [shadcn/ui 的 Vite 安裝](https://ui.shadcn.com/docs/installation/vite)
- [Vite 環境要求](https://vite.dev/guide/)
- [Python 本地靜態服務器](https://docs.python.org/3/library/http.server.html)
- [MDN JavaScript 模塊與本地預覽](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [Ant Design 與 Vite](https://ant.design/docs/react/use-with-vite/)
- [Emil 原始項目與本地副本說明](references/provenance.md)
- [應用產品設計方法](references/product-design.md)
