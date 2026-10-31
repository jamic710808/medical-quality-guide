# 一期本地開發交付與驗證

更新：2026-10-14。用戶 U10 授權按既有計劃連續開發、準備必要運行環境並驗證，次日查看結果。本次已經形成可運行的正式應用：**http://127.0.0.1:8180**。從登錄頁選擇“周瑾 · 質控”即可進入。

11 個 Feature 均已有軟件實現，React 頁面、FastAPI、PostgreSQL/pgvector、獨立 Worker、LangGraph、本地模型、真實解析、本體工具與原生圖譜已連通。當前是可本地試用的工程交付版；**119 項原任務及 133 條正式用例的完整驗收沒有全部結束**。工程完成、組合覆蓋和臨床/生產資格分別記賬，準確狀態見本文與逐 Feature 臺賬。

## 交付內容與實際落點

| Feature | 當前軟件行為 | 主要實現 | 驗證臺賬 |
| --- | --- | --- | --- |
| F001 | 會話/CSRF、OIDC 回調、角色/對象/用途、RLS、審計、撤權與冪等 | `access.py`、`common.py`、`db.py`、API/權限頁 | [授權審計](F001-implementation.md) |
| F002 | 允許目錄/上傳、來源版本/摘要、SQLite 只讀目錄、用途與許可 | `sources.py`、資料接入頁 | [來源](F002-implementation.md) |
| F003 | 原生格式讀取、Docling/RapidOCR、統一 EvidenceItem、定位重放、覆蓋與 Worker 柵欄 | `evidence.py`、`replay.py`、`worker.py` | [解析證據](F003-implementation.md) |
| F004 | namespace/未關聯、斷言、固定上下文、四表受控查詢、應用本體和語義橋接 | `clinical_context/`、`ontology.py`、`native_semantic.py` | [醫療上下文](F004-implementation.md) |
| F005 | 規則/資格版本、候選審核、BM25+BGE-M3/pgvector/RRF、精確編號、限定擴展與索引代次 | `retrieval.py`、`governance.py`、規則頁 | [規則檢索](F005-implementation.md) |
| F006 | 八條文書規則、真實本地模型候選、三值結果、引用校驗、語義/覆蓋失敗關閉 | `quality.py`、PG checkpoint、病例頁 | [聯合質控](F006-implementation.md) |
| F007 | 複核、整改新版本、申訴/升級、改派/期限、重核/人工確認、雙崗位簽字和持久等待 | `remediation.py`、病例責任操作 | [責任閉環](F007-implementation.md) |
| F008 | 固定批次與口徑、兩份原判/仲裁、分母/棄答/風險分層、rubric 和配對比較 | `evaluation.py`、專家評測頁 | [評測](F008-implementation.md) |
| F009 | 固定準入基線、逐項條件、風險否決、責任意見、階段攔截、停止/重驗 | `release.py`、准入頁 | [准入](F009-implementation.md) |
| F010 | 固定資產 ZIP、來源/許可/資格、冪等生成、敏感項排除、摘要/必要依賴檢查 | `delivery.py`、交付資產頁 | [交接](F010-implementation.md) |
| F011 | 原生圖譜與 Designer、三種視圖、證據/版本/內部候選/格式與導出適配 | `GraphPage.tsx`、原生 vendor、`knowledge_graph.py` | [知識圖譜](F011-implementation.md) |

物理結構保持模塊化單體。原 Plan 中按職責拆出的許多細小文件合併在上述模塊，未另造微服務、圖數據庫或第二套事實源。原始 SQLite、影像和規則資料始終只讀；應用文書修訂只產生帶父版本的新記錄和固定原文文件。

## 實際運行方式

[運行手冊](../development-runbook.md)包含啟動、賬號/角色、重建、依賴和清理方式。核心命令：

```sh
cd MedicalQualityCase/MedicalQuality
python3 scripts/manage.py status
python3 scripts/manage.py start
python3 scripts/manage.py stop
```

本機端口：應用 8180，模型 8191，項目獨立 PostgreSQL 55443；均僅綁定 127.0.0.1。API/Worker 使用無 owner/superuser/BYPASSRLS 的運行角色，checkpoint 使用單獨角色和 Schema。慢模型計算在業務事務外進行，提交前重驗當前授權、輸入和租約令牌。必要審計失敗時業務事務回滾。

項目生成憑據只在 `.runtime/config.json` 和模型 key 文件中，不打印或進入 Git；未讀取個人憑據庫、未部署公網或調用付費模型。運行配置與模型權重均在本項目內。

## 數據、解析、本體和模型的實際結果

| 項目 | 本輪實際觀察 | 明確邊界 |
| --- | --- | --- |
| 本地資料 | 六類目錄來源已登記並實際解析：結構庫 69 項目錄（含元數據目錄表），中文病例前 30 條、文獻病例前 30 條、參考規則前 30 項、表目錄前 30 行、六頁 PDF 67 項證據 | 大來源保持 partial；不是全量醫療數據轉換。原參考答案/留出正文未讀入建設 |
| 真實來源敘述 | 一份來源敘述進入病例入口，身份/就診保持 unlinked、範圍未確認 | 不製造患者/就診關聯，不當作目標醫院成人肺炎病歷 |
| 結構化查詢 | MIMIC demo 受控查詢得到 275 個就診、100 個源患者；樣例就診有 282 條觀測，展示 3 條且 has_more；同主體 63 條未關聯就診觀測單列 | 數量來自明確表/鍵，原日曆為脫敏移位時間；不是患者診斷或本院業務規模 |
| PDF 主線 | Docling 2.138.0 + RapidOCR/ONNX PP-OCRv4；原六頁規範輸出 67 項，另有數字/掃描/旋轉續頁組合輸出 3 頁、18 項證據和 2 張表；原圖定位框已核對，旋轉表的行列關係標為部分完成/需複核 | 原生矩陣保留；旋轉表禁止自動建模，需對照原圖複核，未宣稱結構已經正確；低質量真實醫院掃描的專業泛化效果尚未驗收 |
| 純掃描夾具 | 實際 OCR 保留中文“青黴素”“否認”和比較符 `<0.05`，保存引擎/模型/字典摘要及輸出 | 該頁是顯式合成夾具，不是臨床掃描準確率 |
| 原生格式 | CSV 邏輯記錄/原值，JSON pointer/GZ 錯誤，Markdown AST/表格/圍欄/CRLF，安全 XML，XLSX 座標/原值/公式緩存，PNG 與 WFDB 元數據 | 圖片/波形未做診斷；WFDB 默認不解碼信號數值；不把公式計算或 OCR 猜測當原值 |
| 應用本體 | 28 個應用類、22 條對象關係和 5 條 subclass 邊；ROBOT 1.9.11 + EL profile/ELK、RDFLib/pySHACL 實際運行 | `semantic-v1` 是工程發佈；外部詞表/專業映射未啟用，專業定義/CQ 仍待驗收 |
| 原生 semantic | 項目自有 Evo 真實 stdio MCP 完成配置/工作負載/保存/註釋/發佈/瀏覽/解析；修復方向的 `ontology_v1` 保留 `ontology_v0` | 不是偽造工具結果；不冒稱臨床或自演化效果改善；運行工具僅只讀 |
| 檢索 | 固定 BGE-M3 revision 生成 1024 維歸一化向量，規則向量進入 PostgreSQL；詞法/向量經 RRF，三條不同工程問法的目標規則均居首 | 保留名次和證據；三條工程查詢不代表獨立臨床準確率；缺向量時顯示 lexical_only/blocked |
| 生成模型 | 固定 Qwen3-4B Q4_K_M / llama.cpp b11588 本機端點；最終 Worker 重跑 14 份合成病例，12 份 candidate_only、1 份範圍阻斷、1 份引用受限 partial；引用必須來自輸入並逐字匹配 | 沒有模型任意工具調用、自動診斷或簽字；生成候選效果未獲專業確認 |

混合掃描原頁和正式交接證據在 `artifacts/verification/pdf-combination/`，可用 `backend/.venv/bin/python scripts/verify_pdf_pipeline.py` 重建純解析夾具；該腳本不自動修改已登記業務來源。其他原始觀察保存在 `artifacts/verification/real-source-ingestion.json`、`structured-query.json`、`pdf-smoke.json`、`scan-fixture/result.json`、`local-model-case-smoke.json`、`real-model-reruns.json`、`retrieval-query-observations.json`、`native-tools.json`、`native-semantic-build.json` 和 `native-direction-fix.json`。模型/工具來源、版本和摘要由 `scripts/runtime-sources.json`、模型/OCR manifest 與鎖文件固定。換輸入或改模型後不能直接複用舊觀察。早期 14 份運行保留了模型不可用的歷史狀態；最終聯調發現後通過正式 API 創建新運行，Worker 實際調用成功並保存新的結果，沒有清庫或改寫舊記錄。

## 自動檢查與瀏覽器結果

本輪後端最終 **56 個唯一檢查通過**，無跳過。新增了索引事務/柵欄、階段能力、零範圍/混合覆蓋、執行版本和真實原頁回放檢查。最終全集為 `artifacts/verification/backend-final-tests.xml`；隨後對新病例評測指派的直接 7 項再次通過，收據為 `evaluation-assignment-tests.xml`，按測試身份替代舊結果，不累計成 63 項。解析當前/歷史批次與 PDF 範圍的最後 8 項收據為 `parser-scope-final-tests.xml`，同樣替代直接相關舊結果。下列早期局部報告保留排查歷史：

- `artifacts/verification/backend-tests.xml`：46 項初始完整迴歸。
- `artifacts/verification/delivery-final-tests.xml`：5 項交付增量，替代該模塊舊結果。
- `artifacts/verification/workflow-final-tests.xml`：6 項責任/圖譜/評測，替代該模塊舊結果，含跨獨立 Python 進程的 PostgreSQL 人工等待與恢復。
- `artifacts/verification/data-final-tests.xml`：12 項格式/語義檢查，替代該模塊舊結果；顯式零範圍讀取 0 條，非法範圍拒絕而非自動擴大。

執行方式：`backend/.venv/bin/python scripts/test_backend.py -q`，需要局部重驗時傳入對應 `tests/test_*.py`。腳本只清理可重建的 `medical_quality_test`，試用庫保持。測試覆蓋真實數據庫/RLS/審計回滾、OIDC JWT 簽名/nonce/audience/時效、讀取/定位、版本/資格、Worker 柵欄、模型端點/偽引用、責任/仲裁、評測分母與導出校驗。OIDC 的簽發方是本地測試替身；確定性工作流測試只替換生成響應，另有真實本地模型運行證據。

前端 **397 項通過**：原生相關 395 項與醫療 IRI/未知基數適配 2 項，24 個測試文件，無跳過。`npm --prefix frontend test` 的報告為 `artifacts/verification/frontend-tests.json`。未納入醫療運行範圍的上游教學 `QuizCompile`、`questIntegrity` 保留源碼，不計作通過。上游嵌套 `vi.mock` 有兼容性警告，當前不是失敗；後端 RDFLib 有棄用警告，尚未影響本輪結果。

`npm --prefix frontend run build` 已通過 TypeScript 與 Vite 生產構建。原生能力較完整，當前未拆分後的 JS 約 1.11 MB（gzip 約 338 KB），CSS 約 109 KB；這不是移動端/弱網加載 SLA。

瀏覽器最終 **13 個唯一場景通過**：病例分頁/原文/返回、1440×1000 與 1280×800 原生圖譜、搜索/路徑/主題/快捷鍵、Designer 保存/撤銷重做/恢復、證據回原任務、規則/資料/權限、支持角色拒絕、評測/阻斷准入/資產、圖接口故障、候選保存失敗、舊響應亂序及掃描原圖/視圖旋轉。整輪結果在 `browser-before-assignment-fix.json`，新病例評測指派的最終結果在 `browser-assignment-final.json`，PDF 視圖旋轉及結構限制的最終結果在 `browser-results.json`；以最後有效結果為準。一次 exact 定位器錯誤屬於測試修正；新病例專家權限無法接續屬於實際產品缺口，已修復並重驗。

最終頁面截圖在 `artifacts/verification/screenshots/`：`workbench-final.png`、`graph-1440.png`、`graph-1280.png`、`case-final.png`、`evaluation-final.png`、`pdf-source-final.png`。已實際查看，核對主要內容、動作、路徑高亮、圖例/控件、並列檢查器和長頁；修復了圖例/控件重疊、路徑聚焦、評測待判重複計數及請求切換時舊數據短暫複用。

千元素圖採用明確合成的 500 節點＋500 邊夾具，保留上游 grid 閾值和第 100 項後的檢索。連續 15 次加載可交互 p50/p95 為 208/253 ms，選擇反饋 p50/p95 為 960/990 ms，最高 JS heap 為 54.2 MiB，原始觀察見 `graph-performance.json`；預算為本機工程 5 秒可交互、1 秒選擇反饋。JSHeapUsedSize 不含瀏覽器/Canvas 總內存，不是長時洩漏或真實醫院容量證明。

## 原生圖譜完整性與產品適配

上游固定 `defb487b133786c826eab60b99fcef9b8d3c6fbd`，保留 101 個原生來源文件、MIT 及逐文件初始摘要。具體補丁見 `frontend/src/vendor/ontology-playground/README.md`；直接依賴許可見 `frontend/THIRD_PARTY_NOTICES.md`，全文隨前端 `/licenses/` 提供。

| 原生能力 | 產品實現/驗證 |
| --- | --- |
| OP-01/02 渲染與畫布 | 原 OntologyGraph/Cytoscape/fCoSE；節點/關係/拖動/縮放/重置/鄰域/PNG。增加可選醫療佈局和導出授權，不替換渲染器 |
| OP-03/04 搜索與檢查器 | 原搜索及 Inspector；醫療元數據區分類型/實例/斷言/問題與版本，未知基數明確顯示 |
| OP-05/06 路徑/統計/圖例/命令/幫助 | 原有向 BFS 路徑、統計/圖例和命令面板；主題/路徑/快捷鍵瀏覽器驗證；幫助說明醫療邊界 |
| OP-07/08 Designer/預覽 | 原實體/屬性/關係表單、圖標配色、撤銷重做、圖/RDF 預覽；保存和提交接內部候選，不直接改變正式語義 |
| OP-09 格式 | 原 JSON/RDF/XML 子集；醫療模式保留 IRI/URN/中文與未知基數；Turtle 和完整 OWL/SHACL 由正式後端處理並報告損失 |
| OP-10/11 主題/規模 | dark/light/aurora/crimson 保留；1000 元素 grid、列表上限提示與後續對象搜索均保留 |
| OP-12 當前圖查詢 | 複用原確定性查詢與高亮，只回答當前投影，禁用 Coffee 等示例答案，不稱醫學推理或數據庫執行 |
| OP-13/14 目錄/分享/平臺擴展 | 原源碼保留；產品用固定語義目錄、無病例載荷的域內鏈接和受控導出；公共倉庫/身份表單不進入醫療產品 |

## 規格、任務與完整驗收狀態

PRD/總 Spec/Feature Map 的編號和業務邊界不變。每個 Plan 已寫明真實物理文件及工程前置；Tasks 為 **110 項已勾選、9 項真實專業責任或目標環境終驗未勾選**。F001/F002/F003 已完成本輪 Feature 驗收，其他狀態保留專業或上游完整驗收前置。逐用例臺賬為 **122 項本輪工程範圍 pass、11 項專業/生產前置 blocked**；沒有仍可在本輪獨立完成卻未執行的工程用例。122 不是臨床驗收通過數。全部 133 條用例已綁定實際檢查與核對流程，**沒有用空成功腳本或定義校驗代替行為驗證**。

逐項結論見 [F001～F011 臺賬](../specs/feature-map.md)及[產品組合臺賬](product-implementation.md)。原先待驗的混合/旋轉掃描、五單元覆蓋、已提交單元複用、不同問法、索引發布故障、圖/規則資格失效、階段能力與圖響應亂序已經補驗。發佈單元採用一個有界來源範圍的一次事務，多範圍通過獨立 Job 接續；這滿足當前有限數據工作流，不宣稱已經實現無限流式調度。

專業用例沒有被刪除或改成工程夾具通過。當前可進行本地試用與客戶操作反饋，目標醫院的專業判斷、真實簽署和生產放權仍需真實責任人完成。

## 真正需要目標環境提供的條件

1. 醫院 OIDC 與真實崗位映射、數據域/用途、保留週期和刪除/備份責任。
2. 目標中文病區的獲准樣本、獨立參照、兩名真實專家和仲裁責任。
3. 八條規則、應用本體定義、外部術語許可/適用性及專業映射審核。
4. 風險分層指標與門檻、模型校準、實際簽署方式、關鍵人責任接受和影子運行觀察。

當前系統會展示這些缺項並阻斷生產；本地待評測批次沒有填答案，工程准入記錄保持 blocked，交接資產保留 not_granted。沒有把測試賬號冒充真實員工，或將公開數據認作生產證據。

## 文件、資源和清理

原始數據約 2.24 GiB，保持完整原目錄和許可。新運行資源約 8 GiB：模型 5.1 GiB、Python 環境 1.6 GiB、前端依賴 255 MiB、瀏覽器 534 MiB、工具 261 MiB、項目 PostgreSQL 約 82 MiB。未初始化 Git、未創建持久第二 checkout 或額外工作樹。

依賴/模型/瀏覽器按固定清單可再生，均在忽略目錄；數據庫、文書修訂、原生解析、本體版本和仍被責任記錄引用的資產須先保留需要的歷史再清理。交接核對時磁盤餘量約 5.6 GiB。詳細路徑、用途與安全清理條件見運行手冊；不要用清緩存方式刪除業務庫。

本輪使用的本地工作流為 [feature-spec-planning](../../../.agents/skills/feature-spec-planning/SKILL.md)、[project-evals](../../../.agents/skills/project-evals/SKILL.md)、產品設計參考及 [build-ontology](../../../.agents/skills/build-ontology/SKILL.md)。沒有對外發送消息或觸發發佈。

## 文檔核對與輸入版本

PRD confirmed、Product Spec confirmed、Feature 三件套 ready 和全部 eval require-bound 四項校驗均通過（無錯誤）；eval 校驗仍明確 behavior=not_evaluated，因為它只檢查定義。報告分別在 artifacts/verification/*-validation.json。正式源碼、鎖文件、規格/用例與當前報告的內容摘要記錄在 artifacts/verification/development-inputs.json；倉庫尚未初始化 Git，因此不虛構提交號。

最後核對：相關規格/任務/交付文件的 519 個本地鏈接均可定位；原生來源清單 101 文件無缺失，16 個醫療適配文件有明確記錄。所有新增原頁圖片、模型與測試產物仍在忽略目錄中。
