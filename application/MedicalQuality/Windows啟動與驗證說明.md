# Windows 啟動與驗證說明

建立日期：2026-10-30。這是學員資料包的獨立 Windows 工程副本，採用本機 Python 3.13.7 虛擬環境，沒有更換全機 Python。

## 使用

- 工作臺：<http://127.0.0.1:8180/>；本地工程身份可選「周瑾 · 質控」。
- 啟動：雙擊 `啟動工作臺.cmd`，或在本目錄執行 `py -3.13 scripts/manage.py start`。
- 停止：雙擊 `停止工作臺.cmd`，或執行 `py -3.13 scripts/manage.py stop`。資料庫和業務記錄保留。
- 狀態：`py -3.13 scripts/manage.py status`。
- 服務均使用本機迴環：工作臺 8180、模型 8191、專案 PostgreSQL 55443。工程身份沒有醫院身分或電子簽章效力，不可將本地模式暴露於網路。

## 已完成

- 原生 Windows PostgreSQL 17.10 和 pgvector；專案資料庫、角色與 schema 獨立。
- 前端 npm 構建、API、Worker；合成資料初始化 14 個病例、8 個工程候選規則、10 個本地身份。
- Java 21 與 ROBOT 1.9.11；ROBOT 套件摘要與原 manifest 核對通過；本體 profile、ELK 和 SHACL 工程夾具檢查通過。
- Qwen3-4B Q4_K_M / llama.cpp b11588 本地模型；模型權重 SHA-256 與固定 Hugging Face revision 的資料一致。初始版本為 CPU 運行，首次推論較慢，質控請求等待上限調整為 180 秒。
- 瀏覽器登入、病例、來源原文、知識圖譜及一次合成病例模型候選；該候選引用了兩份文書標題，引用確實屬於輸入，但不構成對醫學主張的充分支持，應由人工核對。
- 前端 397 項測試通過；後端 Windows 56 項測試通過。原兩項測試因 Windows 換行自動轉換失敗，測試夾具改為明確寫入 LF bytes；原有 CRLF 測試保留。仍有上游相容與棄用警告。
- 已驗證本專案服務停止與重新啟動，業務資料保留。運行日誌位於 `.runtime/logs`。`.runtime/config.json` 及模型 key 限制目前 Windows 使用者存取，不應分享。

## 來源與限制

PostgreSQL Windows binary 來自 EDB；Windows pgvector 0.8.6 為社群預編譯版本（andreiramani/pgvector_pgsql_windows），不是 pgvector 官方提供的 Windows 二進位。使用前應考慮供應鏈風險；正式醫院環境應採經驗證的發行來源、自行建置或機構批准的部署。教師原始醫療資料和歷史 artifacts 未附；不要把合成病例視為真實病患。

`build_semantic.py` 需要原始結構化資料庫，本副本未取得該資料，因此未執行原始資料本體建設；現有產品工程 semantic-v1 與專業審核待確認分開。OCR、向量索引及 GPU 的狀態應以本次實際準備及驗證紀錄為準；無法因程式存在而宣稱已通過。

## Windows 適配

`manage.py` 使用 Windows venv 路徑、項目內 PostgreSQL binary、隱藏背景程序，對進程以 Windows API 檢查，停止前核對項目命令及 PID；`ontology.py` 使用 PATH 中的 Java。CPU 模型推論較慢，timeout 延長不改變專業判斷或失敗阻斷邊界。具體修改位於此副本，原課程資料未被修改。

前端依賴稽核：2026-10-30 執行 npm audit --omit=dev，報告 3 項（1 低、1 中、1 高）；未因啟動工作自動升級鎖定依賴，尚未完成逐項可利用性評估。

