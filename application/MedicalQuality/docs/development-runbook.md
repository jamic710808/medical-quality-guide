# 本地運行與工程交接

> **交付說明**：本文保留原項目的操作與重建文檔，供閱讀源碼時參考。本輪僅整理學員資料，未執行其中的安裝、下載、數據庫初始化或啟動命令；歷史截圖、模型收據和運行產物未隨包提供。

工作目錄為 `MedicalQualityCase/MedicalQuality`。正式應用入口是 **http://127.0.0.1:8180**，與保留的 5198 需求看板、5199 靜態原型分開。當前應用使用真實 FastAPI、PostgreSQL、獨立 Worker、LangGraph checkpoint 和原生圖譜組件。

## 直接使用

在登錄頁選擇本地工程身份。推薦先用“周瑾 · 質控”查看病例、證據與圖譜；“林辰 · 責任醫生”負責 A 組，“蘇禾 · 責任醫生”負責 B 組；陳一/何寧為獨立原判身份，鄭嵐承接仲裁與默認本體審核；許程負責資料和授權，方言負責准入與資產。身份由服務端會話解析，界面不通過自報角色獲得權限。

這些賬號是明確的工程驗證身份，不是醫院真實員工或生產電子簽名。14 份合成文書用於可重複流程驗證；已登記研究來源及導入的來源敘述分別標識，不將其當作完整目標醫院住院病歷或專業金標準。

推薦走查：

1. 工作臺翻頁進入陳**病例，選擇過敏記載問題，對照兩份原文；進入“查看證據關係”，再返回原任務。
2. 在知識圖譜查看本體/病例/規則三種視圖，搜索、選擇節點/關係、查有向路徑，切換原生主題；原生 Designer 可保存候選、撤銷重做、導入/導出及圖/RDF 預覽。
3. 質控確認問題後，醫生提交有理由的新文書；質控再次核驗並人工確認，兩個崗位分別簽署當前範圍。舊文書/簽字保留，新版不繼承舊完成狀態。
4. 在專家評測凍結運行/樣本與口徑，兩名原判者分別判斷，仲裁保留兩份原判；高風險漏報和無法判斷不被平均分抵消。
5. 管理人員創建准入申請，查看真實缺項；未滿足條件保持阻斷。交付包保留候選/未放行狀態，包含規則、本體、權限、評測定義/聚合報告與責任流程，排除病例原文、答案和憑據。

## 啟停與當前依賴

```sh
cd MedicalQualityCase/MedicalQuality
python3 scripts/manage.py status
python3 scripts/manage.py start
python3 scripts/manage.py stop
```

服務只監聽本機：應用 8180、模型 8191、獨立 PostgreSQL 55443。`stop` 只停止本項目記錄且經命令核對的進程，保留數據庫和責任記錄；不修改已有 Postgres.app 實例或其他項目。`start` 檢查應用健康後才報告入口。運行日誌位於 `.runtime/logs/`。

依賴鎖定入口：`backend/pyproject.toml` / `backend/uv.lock`、`frontend/package.json` / `frontend/package-lock.json`。主要實測版本包含 Python 3.12、PostgreSQL 17.10、React 19.2.4、Cytoscape 3.33.1/fCoSE 2.2.0、LangGraph 1.2.15、Docling 2.138.0、RapidOCR/ONNX 的 PP-OCRv4、FlagEmbedding/BGE-M3，以及 Qwen3-4B Q4_K_M / llama.cpp b11588。精確清單以鎖文件和資源 manifest 為準。

## 從本項目文件重新準備

本機已有 Node 24、uv、Python 3.12、PostgreSQL 17 與 pgvector；換機器需先準備兼容的系統前置。工具二進制清單目前固定 macOS arm64，其他平臺需選擇同版本對應發行物並核對摘要。

```sh
cd MedicalQualityCase/MedicalQuality/backend
uv sync --python 3.12 --extra ocr --extra models
cd ../frontend
npm ci --ignore-scripts
npm run build
cd ..
backend/.venv/bin/python scripts/prepare_runtime.py
backend/.venv/bin/python scripts/prepare_models.py
backend/.venv/bin/python scripts/prepare_ocr.py
python3 scripts/manage.py setup
python3 scripts/manage.py seed
backend/.venv/bin/python scripts/build_semantic.py
python3 scripts/manage.py start
```

`setup` 僅創建項目獨立集群/角色/Schema，運行 Alembic；生成的本地服務憑據保存在權限受限的 `.runtime/config.json`，不進入 Git 或輸出日誌，不讀取個人憑據庫。`seed` 發現已有業務狀態時退出，不覆蓋數據或重置責任記錄。模型下載只發生在顯式準備期；原件始終從工作區 `Data/醫療病歷質控/` 只讀讀取。

原生語義構建使用項目內 `.agents/vendor/evoontology` 的真實 stdio MCP 與固定五類對象；調用客戶端在 `backend/medical_quality/native_semantic.py`。運行端只允許讀工具，建設/演化/激活不在運行權限裡；原生 active 也不等於產品 SemanticRelease 或臨床批准。

## 工程檢查

```sh
cd MedicalQualityCase/MedicalQuality
backend/.venv/bin/python scripts/test_backend.py -q
npm --prefix frontend test
npm --prefix frontend run build
cd frontend
PLAYWRIGHT_BROWSERS_PATH=../.runtime/browser npx playwright test
```

瀏覽器首次準備可運行 `PLAYWRIGHT_BROWSERS_PATH=../.runtime/browser npx playwright install chromium`。自動化採用項目獨立瀏覽器，不使用個人 Chrome 登錄配置。內置 Browser 在本會話啟動失敗，因此頁面驗證使用此隔離環境。

後端檢查只清理 `medical_quality_test` 測試庫，業務試用庫 `medical_quality` 保持。測試含實際 PostgreSQL/RLS/事務、受控格式、語義、OIDC 密碼學/回調測試身份、版本/責任工作流及圖譜適配；臨床樣本、真實專家資格和醫院 IdP 連通性單獨記錄，不被工程測試替代。正式結果見[開發交付與驗證](verification/development-report.md)。

## 持久資源與清理

| 路徑 | 約大小與用途 | 安全清理條件 |
| --- | --- | --- |
| `backend/.venv` | 約 1.7 GiB，項目 Python 依賴 | 停止服務後可刪除，按 uv.lock 重建 |
| `frontend/node_modules` | 約 255 MiB，前端構建/測試依賴 | 可按 package-lock 重建；不刪除源碼 |
| `artifacts/models` | 約 5.1 GiB，固定本地權重與 OCR 資源 | 停止模型/解析服務，確認可按固定清單再生後可清理；清理後對應能力明確不可用 |
| `.runtime/tools` / `.runtime/browser` | 約 261 / 534 MiB，本體工具、模型運行器和隔離瀏覽器 | 按 scripts/runtime-sources.json 或 Playwright 鎖定版本再生；不進 Git |
| `.runtime/postgres` | 約 82 MiB，本地業務與測試庫，實際大小隨操作變化 | 含試用狀態、責任記錄；必須先保存需要的記錄，不能按緩存刪除 |
| `artifacts/parsing`、`document_revisions`、`ontology`、`exports` | 可回查原生解析、新文書、本體固定包和交付物 | 仍被業務/簽字/驗證引用時保留；不能僅因可再生就破壞歷史證據 |
| `.evoontology` | 原生語義候選/版本與構建記錄 | 保留已引用版本；版本不是生產批准，不與產品本體包混同 |

原始醫療數據約 2.24 GiB，屬於正式輸入，繼續保留原說明和許可；本輪沒有將其當緩存清理或複製到 Git。所有大產物、依賴樹、數據庫及模型均已忽略。

## 生產前仍需真實條件

目標醫院 OIDC/崗位映射、數據域與保留週期、病區樣本及獨立參照、規則/術語專業適用性、正式指標門檻、簽署方式和關鍵人責任接受仍需院方實際提供。當前生產門禁拒絕缺失條件；公開/合成/文獻來源和工程審核不會自動升級為生產資格。

PP-StructureV3 是有明確主線缺口時才啟用的備選；本輪已運行 Docling/RapidOCR 主線，沒有部署雲解析、MinerU 默認回退或未驗證備用模型。完整臨床效果和大規模醫院負載尚未驗收。

本輪最終實際模型重跑保留 14 個新 run 與舊歷史：12 個有效候選分支、1 個範圍阻斷、1 個引用受限；不是 14 個臨床通過。瀏覽器流程檢查留下明確標識的候選草稿、待專家評測批次、阻斷准入與工程 ZIP，可從對應頁面核對；沒有偽造專家原判。

掃描證據支持受權原頁/區域回看與視圖旋轉。旋轉表格即使文字可讀，行列結構仍標為待複核；未核對前不自動建模。資料頁默認展示最新解析批次，歷史證據仍以固定引用或 parse_run_id 查詢；重跑不疊加冒充當前覆蓋。
