# `.agents` 同步記錄

日期：2026-10-14。按用戶更正，以 `<PREVIOUS_CASE_WORKSPACE>/.agents/` 為來源，更新 `MedicalQualityCase/.agents/`。未反向修改來源項目。

## 同步結果

| 項目 | 結果 |
| --- | --- |
| 共同 Skills | 同名文件完整採用來源內容、目錄結構與權限，配套資源和許可保留 |
| 新增 | `understand-business` 的入口、Agent 元數據及三個參考文件，共 5 個文件 |
| 更新 | `prepare-business-data` 的入口、Agent 元數據、產物約定、工具路由、探測腳本及對應測試，共 6 個文件 |
| 本地保留 | `select-rag-architecture`、`select-agent-architecture` 共 12 個文件，以及數據治理、證據契約、Schema、示例、質量門禁、建模交接、校驗腳本及測試共 8 個文件 |
| 本體運行包 | 與來源相同，未更新運行環境；新增的安裝說明按醫療項目實際路徑及 stdio 調用方式適配 |
| 當前總數 | 25 個 Skills：來源 23 個 + 本項目獨有 2 個 |

不復制緩存、虛擬環境、依賴樹或來源項目業務狀態。醫療數據、產品代碼和運行中的服務不屬於此次同步範圍。

## 直接影響與入口

來源版 `prepare-business-data` 採用通用初篩，未包含此前醫療擴展探測及 `--no-preview`。本次按用戶指定版本同步，沒有重新合併舊腳本。保留的 EvidenceItem 校驗和治理資源仍可使用；正式醫療讀取由產品適配器承擔。

[數據工作流](../data-preparation/workflow.md)已更新為使用合成示例的有效命令，舊探測結果標註為歷史快照。[工作區約定](../../../AGENTS.md)已補充新 Skill、數量及醫療擴展入口。[本體安裝說明](../../../.agents/evoontology-installation.md)不沿用來源項目的訂單路徑、MCP 配置或信任記錄。

## 驗證

文件同步已核對：196 個來源共有文件的內容和權限一致，20 個目標獨有文件未變，來源文件未變。安裝說明為唯一按本項目環境適配的來源文件。

- 25 個 Skill 的名稱、描述及已有 Agent 元數據檢查通過；6 處圖標資源存在。
- Skills 文檔及本次關聯文檔中的 194 處本地 Markdown 鏈接可定位，無未解析鏈接；代碼塊中的輸出示例不作為已存在文件檢查。
- 項目 Python 環境執行 `unittest discover`，16 項通過：來源版探測 7 項、保留的證據校驗 9 項。覆蓋採樣與編碼、只讀行為、容器識別、證據定位約束及參考標註隔離，使用臨時夾具和合成示例。
- 產品代碼及運行包未變，此次未重複運行產品全量測試、臨床評測或本體構建。

逐文件摘要保存在忽略目錄 `MedicalQuality/artifacts/verification/agents-sync-20261014.json`，用途是本次同步核對，不保存業務內容。該記錄可在不再需要此次對比證據後清理；當前目錄對比可重新生成，但覆蓋前的摘要僅保留於本次記錄。未創建備份副本或額外運行環境。

## 初始化 Skills 資源核對與例外（歷史記錄）

2026-10-15 從外層 AGENTS 遷入以下原始核對記錄。代碼樣例中的路徑按工作區根目錄解釋；這些是歷史發現，本次沒有重跑 Skills 資源盤點。

- 初始化快照：22 個 Skill 入口及描述有效；87 處本地 Markdown 鏈接可定位，6 處 Agent 圖標引用存在，項目骨架與看板腳本使用的配套模板存在。2026-10-14 同步驗證見本文前面的記錄。
- `normalize-project-requirements/references/agents-md-guide.md` 中另有一處代碼塊示例鏈接 `docs/01_normalize-project-requirements/index.md`，是未來項目產物佔位，不是漏複製的資源。其他 `docs/` 輸出示例也不代表本工作區已有這些文檔。
- `playground` 中提及的 `assets/board.html` 和 `scripts/build_board.py` 屬於同級 `review-project-requirements`，對應文件已保留。
- `build-frontend-prototype/references/provenance.md` 的全局 Skill 路徑僅作歷史來源定位，文檔明確無需訪問這些來源；已整合的本地設計指引與許可完整保留。
- `maintain-project/tests/order-prototype.browser.cjs` 第 6 行仍引用 `<COURSE_CONTENT_WORKSPACE>/.agents/skills/excalidraw-diagram/scripts/node_modules/playwright`，並依賴舊訂單原型頁面；同目錄補丁及驗證記錄也保留舊工作區路徑。這些是來源中的歷史測試材料，原樣複製，不作為本醫療項目的運行或驗收入口。未來確需複用時，須適配當前應用及項目內依賴，不能直接運行或借用其他項目依賴。
- Skills 正式入口未發現指向 `MuYuFDECourse_Project_1` 或 `part10-anli` 的硬編碼運行路徑。三個本體 Skill 所需的 `evo-semantic` MCP 屬於獨立運行依賴，安裝與調用方式見[本體安裝說明](../../../.agents/evoontology-installation.md)。

## 2026-10-15：外層指令入口修訂

變更 ID：`outer-agents-entry-20261015`。依據本地 normalize-project-requirements 的 AGENTS 編寫規範與 maintain-project 的項目接入約定，修訂外層指令；本輪不修改產品內層 AGENTS、Skill 正文、代碼、原始資料或運行配置。

- 外層 AGENTS 補齊需求上下文索引、按需回查條件、依據衝突處理與確認狀態；區分需求看板、原型和正式應用。
- 明確原型反饋同步設計、頁面、相關需求與驗看記錄；正式變更按產品要求、共享行為或 Feature 的實際影響維護。
- 完整 Skills 清單和資源使用說明遷至[本地索引](../../../.agents/README.md)，產品 README 的盤點入口同步更新；複製歷史遷入[初始化記錄](initialization.md)。
- 原工作目錄、原始資料只讀、醫療數據不出域、標註隔離、路徑基準、本體及原生圖譜要求保留；當前進度和依賴狀態由既有產品文檔承載。

驗證結果：本次修改文件及需求索引共 6 份文檔中的 178 處本地鏈接均可定位，Skills 索引完整覆蓋 25 個本地 Skill；複製快照和資源例外已遷移保留。對照編寫規範審閱了按需回查條件、確認狀態、衝突處理、原型/正式工程入口及醫療數據邊界。檢查由維護腳本以 `outer-agents-links` 執行，退出碼 0；收據位於忽略的 `.codex/maintenance/`，正式結果保留於本節。沒有開啟新會話驗證指令自動加載，也沒有安裝或啟用 Hook。
