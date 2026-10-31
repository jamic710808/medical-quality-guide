# MedicalQuality 工程約定

產品根目錄為 `MedicalQualityCase/MedicalQuality/`，本文路徑均相對此目錄。外層 [AGENTS.md](../AGENTS.md) 管理資料回查與工作區邊界；產品使用方式見 [README](README.md)，實際進度與驗收狀態見[開發報告](docs/verification/development-report.md)。

## 項目定位

- 工程名：`MedicalQuality`；對外產品名：`FF - 醫療病歷質控`。
- 服務質控人員、責任醫生、複核/仲裁專家、信息科與管理人員，輔助病歷質控、證據定位及整改協同。
- 一期範圍為單一內科病區、成人肺炎住院文書、八條有限質控規則與獨立工作臺；具體範圍與驗收以 PRD 為準。
- 核心旅程：授權與資料接入 → 聯合質控 → 查看原文及規則證據 → 質控複核 → 醫生申訴或整改 → 再次核驗 → 責任簽字。
- 不自動診斷、生成處方、無人確認修改病歷或回寫 HIS。公開脫敏、文獻、合成與生產資料顯式區分；工程驗證不等於臨床批准或生產放權。

## 品牌與產品語言

- 用戶可見名稱逐字使用 `FF - 醫療病歷質控`；內部目錄名、工程縮寫和臨時代號不作為產品名。
- Logo 使用 `frontend/public/brand/ff-logo.png` 原始文件，SHA-256 為 `522944bbaee48d98190c8c5a0a0ac80f05b71b1975838807742a782e2aeceedc`。不覆蓋、重繪、反色、改色、裁切、拉伸或添加裝飾效果。
- 全局導航或頁頭將 Logo 放在完整產品名左側，保持比例，無障礙文本為 `FF - 醫療病歷質控 Logo`；不以菜單圖標或臨時字母替代。
- 研發署名逐字使用 `@賦範空間 獨家研發`。可滾動頁面在內容末尾提供統一腳註；固定高度工作臺可放在側欄或應用殼底部，不遮擋操作。
- 沿用 Apple 式簡潔平臺風格，以實際任務組織主工作區、列表瀏覽、證據比較和操作承接。按[產品設計](docs/03_prototype-design/design.md)及相關 Feature 計劃實施。
- 產品文案使用業務對象、動作與可觀察狀態；有來源名稱時展示名稱，編號輔助追溯。缺失名稱標明待核實，不猜造；不同業務狀態保持原有含義。
- 不默認向最終用戶展示“演示模式”“Mock”“測試版”等研發階段標籤；必要的數據來源、專業資格和能力限制按產品規格告知。

## 目錄與架構邊界

| 路徑 | 職責 |
| --- | --- |
| `frontend/` | 前端源碼、頁面、組件、靜態資源、構建配置與測試；`frontend/e2e/` 保存瀏覽器檢查 |
| `frontend/src/vendor/ontology-playground/` | 固定上游原生圖譜與 Designer、許可及醫療適配記錄 |
| `backend/` | FastAPI、數據/證據、本體/檢索、Agent、業務流程、遷移與測試 |
| `backend/medical_quality/clinical_context/ontology/` | 應用本體與形狀定義；發佈副本固定版本保存，不改寫歷史發佈 |
| `scripts/` | 現有服務管理、資源準備、語義構建及工程檢查入口 |
| `docs/`、`evals/` | 中文產品規格、設計與驗證記錄；驗收用例定義及實際檢查關聯 |
| `docs/02_requirement-playground/`、`docs/04_frontend-prototype/` | 需求看板和靜態原型，分別在 5198、5199 預覽；正式應用入口為 8180 |
| `artifacts/`、`.runtime/`、`.evoontology/` | 已忽略的派生證據、模型、運行依賴、獨立數據庫及原生語義工作區；保留與清理遵循運行手冊 |

新增前端專屬實現放入 `frontend/`，後端、Agent 與數據服務實現放入 `backend/`；根部沿用現有跨進程管理和資源準備腳本，不為套模板搬動已工作的工程或另建服務。

原始需求在 `../Raw/`，原始醫療資料見[數據說明](../Data/醫療病歷質控/README.md)，均保留原件與許可，SQLite 只讀。圖文與心電索引各用數據說明中的路徑基準；參考標註與留出正文不進入建設、模型或知識索引。依賴、配置和業務狀態使用本項目副本。

業務狀態、責任意見、文書版本、簽字與審計以應用數據庫為準；checkpoint 只恢復執行，不授予權限。模型只讀固定語義與證據，不能構建、演化、發佈或代簽；原生 Evo active 不自動成為產品 SemanticRelease，外部術語缺許可或專業審核時保持未映射。

知識圖譜完整採用 Microsoft Ontology-Playground 原生實現與 Designer，按[集成合同](docs/architecture/ontology-playground-integration.md)保留佈局、搜索、檢查器、路徑、主題、預覽及大圖策略。候選不直接發佈，病例實例不能導出為 OWL 類，醫療內容不提交到公共分享入口。

## 文檔職責

| 文檔 | 唯一職責與使用方式 |
| --- | --- |
| [需求上下文索引](docs/01_normalize-project-requirements/index.md) | 業務背景、約定、溝通及來源定位；依據不足或有衝突時按主題回查 |
| [PRD](docs/PRD.md) | 產品目標、範圍、穩定 REQ/NFR 與 Given/When/Then 驗收 |
| [Product Spec](docs/specs/product-spec.md) | 跨 Feature 的對象、狀態、不變量、共享交互、恢復與兼容合同，使用穩定 PSC 編號 |
| [Feature Map](docs/specs/feature-map.md) | 已確認功能邊界、需求/PSC 歸屬、優先級、依賴和狀態 |
| `docs/specs/FNNN-<slug>/spec.md` | 該 Feature 的行為、邊界、狀態和 AC |
| 同目錄 `plan.md`、`tasks.md` | 實現方案、影響範圍、實施與驗證順序；可獨立驗證的任務、依賴和完成證據 |
| [Architecture](docs/architecture/architecture.md)及專題 | 技術選擇、組件職責、數據和服務邊界；[檢索](docs/architecture/knowledge-retrieval.md)、[Agent](docs/architecture/agent-runtime.md)、[數據治理與本體](docs/data-preparation/governance-cleaning-handoff.md)承載對應細節 |
| [設計](docs/03_prototype-design/design.md)與[驗看](docs/03_prototype-design/verification.md) | 頁面職責、業務名稱來源、交互、反饋和實際操作檢查；標明原型或正式應用 |
| `evals/FNNN.json`、`evals/product.json` | 引用 AC/PSC 的用例、輸入、預期和檢查綁定；具體測試在對應工程測試目錄，不另定義業務規則 |
| `docs/verification/` | 實際命令、輸入/版本、觀察結果、未驗證項及逐 Feature/產品驗收臺賬 |
| [運行手冊](docs/development-runbook.md)與 README | 安裝、啟停、使用、環境重建、資源保留及交接 |

保留 REQ/NFR、PSC、Feature、AC、Task 與證據的對應關係。歷史輸入保留來源和確認狀態，當前規格按明確的確認或替代關係更新；不從代碼倒推業務批准，不復制平行規格或在指令文件中維護階段統計。

## 技術基線與真實命令

- 前端採用 React / TypeScript / Vite，使用 npm；入口為 `frontend/src/`，版本由 `frontend/package.json` 與 `package-lock.json` 固定。
- 後端採用項目 Python 3.12 環境、FastAPI、SQLAlchemy/Alembic、PostgreSQL/pgvector、獨立 Worker 與 LangGraph PG checkpoint；版本由 `backend/pyproject.toml` 與 `uv.lock` 固定。
- 數據和模型沿用 Docling/RapidOCR、本地 BGE-M3/Qwen3、OWL/ROBOT/ELK/SHACL 與項目 Evo stdio 橋接；具體版本、模型摘要和準備方式以運行手冊及資源 manifest 為準。
- 重新準備環境按[運行手冊](docs/development-runbook.md)執行：後端在 `backend/` 運行 `uv sync --python 3.12 --extra ocr --extra models`；前端在 `frontend/` 運行 `npm ci --ignore-scripts`。模型、OCR、數據庫和語義包另按手冊準備，不能把安裝 Python/npm 依賴視為完整環境就緒。

從產品根目錄執行；根據本次影響選擇檢查，不默認全部重跑：

```sh
python3 scripts/manage.py status
python3 scripts/manage.py start
python3 scripts/manage.py stop
npm --prefix frontend run build
npm --prefix frontend test
backend/.venv/bin/python scripts/test_backend.py -q
```

瀏覽器檢查在 `frontend/` 執行 `PLAYWRIGHT_BROWSERS_PATH=../.runtime/browser npx playwright test`。後端局部驗證可向 `scripts/test_backend.py` 追加對應 `tests/test_*.py`；測試使用可重建的 `medical_quality_test`，不得指向業務試用庫 `medical_quality`。瀏覽器業務操作可能留下明確標識的工程候選、批次與交接記錄，不形成真實專家判斷。

服務僅監聽本機：API 8180、模型 8191、PostgreSQL 55443。運行角色無 superuser、表 owner 或 BYPASSRLS 權限；遷移角色不用於 API/Worker。`seed` 不覆蓋已有狀態。本地服務憑據保存在忽略的 `.runtime/config.json`（0600），不輸出或提交；不讀取個人憑據庫。

## 開發規則

- 本項目已有源碼，使用 [maintain-project](../.agents/skills/maintain-project/SKILL.md) 在同一工程迭代。按當前授權選擇 Feature、原型或文檔範圍，保留已有改動和有效入口。
- 產品範圍/驗收變化沿用 [product-prd](../.agents/skills/product-prd/SKILL.md)，共享行為變化沿用 [product-spec](../.agents/skills/product-spec/SKILL.md)，功能邊界/計劃變化沿用 [feature-spec-planning](../.agents/skills/feature-spec-planning/SKILL.md)。僅同步受影響內容，不在子 Feature 中發明上游合同。
- 新增或調整 Feature 時保留穩定編號與歷史；PRD、總 Spec、Map 的確認關係和已選架構須支持本輪實現。Plan/Tasks 基於真實文件與明確技術決定，不能靠模板猜框架、接口或依賴。
- 業務功能開發前使用 [Feature 校驗器](../.agents/skills/feature-spec-planning/scripts/validate_feature_specs.py)，以當前產品根為目標、僅選擇本輪 Feature，核對三件套的 `--require-ready` 條件；任務按可獨立驗證的結果拆分，可跨前後端和數據，不使用 FE/BE/INT 或 Pack 技術車道標籤。只在真實完成證據成立時勾選 Task。
- 前端變更按[應用產品設計方法](../.agents/skills/build-frontend-prototype/references/product-design.md)，先在已有設計或 Feature Plan 中說明對象名稱來源、主工作區、列表瀏覽與詳情組織，梳理“入口 → 對象/頁籤 → 操作結果 → 返回”。共享名稱、狀態和直接相關頁面保持一致；字號、滾動留白、證據比較與返回上下文須在目標視口驗看。
- 正常、加載、空、失敗和成功狀態按真實業務合同實現；不得用模擬結果、硬編碼成功或隱藏錯誤代替正式能力。證據、權限或資格不足時按既有合同受限或阻斷。
- 使用 [project-evals](../.agents/skills/project-evals/SKILL.md) 維護本次 AC/PSC 對應的用例和真實檢查綁定；入口與輸入真實存在後核對 `--require-bound`。複用一個最窄且充分的檢查，輸入未變化的有效證據不重複執行。必要的界面路徑實際操作，構建通過不代替業務驗收。
- 記錄實際輸入/版本、命令或操作、結果和證據。受影響的舊證據失效時如實標記；未運行、受阻或需要專業確認的項不能標成完成。滿足對應合同後更新 Task 與 Feature Map 狀態，並使用 Feature 校驗器核對 `--require-complete`；跨 Feature 門檻單獨驗收。
- 醫療數據域、權限與責任邊界繼續適用。改變外發、計費、外部寫入或部署範圍時按當前授權處理；不把工程賬號、試用結果或候選資產當成醫院批准。

## Definition of Done

- 本輪行為能追溯到適用的 REQ/NFR、PSC、Feature AC；局部修復或文檔維護沿用已有合同。
- 新路徑和直接受影響舊路徑已核對，相關頁面、API、數據與後臺狀態一致；含前端時有實際操作與可見結果。
- 最窄必要檢查真實完成並有有效證據；任務狀態與結果一致，未執行、失敗及專業受阻項如實保留。
- 受影響的規格、計劃/任務、實現、用例、使用說明和驗證記錄已同步；命令或長期約定變化時更新 README / AGENTS。
- 授權 Feature 的局部驗收與本輪需要的產品組合門檻分別完成，才能聲明對應範圍完成；不能以資料齊全或結構校驗代替業務通過。

## 項目交付

交付當前授權範圍內的源碼、必要配置和文檔；README 與運行手冊承載真實安裝、啟動、測試及構建入口，`docs/verification/` 記錄實際結果、未驗證項、外部依賴與限制。保留被文書、簽字或驗收引用的歷史版本和證據，資源清理沿用運行手冊。

目標醫院身份/崗位、授權數據域、病區樣本、專家參照、規則/術語專業資格、正式指標與簽署責任由目標環境實際提供，缺項不放行。產品可運行、局部工程驗收與醫院准入分別交付；不默認追加培訓、推廣材料、演示視頻或其他未請求產物。
