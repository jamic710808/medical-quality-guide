---
document: feature-tasks
feature: F003
status: completed
updated: "2026-10-14"
---

# F003 · 結構解析與統一證據輸出任務

## 任務規則

- 本輪只形成計劃；全部任務未執行，完成證據均為預期產物，不能據此勾選。
- T001～T002 是進入實現前的接口與技術驗證；只有對應開放項關閉、Plan 更新為 ready 後再進入正式功能實現。其餘任務依賴 T003 提供的共同合同。
- 各 Task 的來源回鏈至 [Spec](spec.md)，驗證回鏈至 [evals/F003.json](../../../evals/F003.json)。實際入口建立後再綁定檢查；不以 Skill 測試替代業務能力驗收。
- 每個 Task 交付獨立可檢查結果；相同條件已有有效證據時複用，不為每個用例重複執行等價檢查。

## 任務清單

- [x] T001 固定授權來源交接與代表樣本範圍
  - 來源：REQ-002, REQ-008, NFR-001, NFR-002, AC-F003-001, AC-F003-010
  - 依賴：無
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：字段映射與角色/範圍清單，明確 source/version、授權引用、路徑基準和真實/合成樣本；參考標註正文不在樣本中，關閉 Plan OQ-002。
  - 驗證：EV-F003-001、EV-F003-010 的前置；一次 F002 輸入合同與樣本清單審閱，完整行為檢查在 T011/T013 綁定後執行。

- [x] T002 驗證已選 PDF 路線並固定最小運行環境
  - 來源：REQ-002, NFR-002, NFR-003, AC-F003-004
  - 依賴：T001。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：按[掃描 PDF 定案](../../data-preparation/governance-cleaning-handoff.md#pdf-scan-decision)固定 Docling standard＋RapidOCR ONNX / PP-OCRv4 中英模型與字典；實際掃描頁覆蓋、結構/定位、離線/資源及模型路徑/摘要/大小有據可查。PP-StructureV3 只對主線明確缺口比較；關閉 Plan OQ-001 前不標完成。
  - 驗證：EV-F003-004；主線在獲准掃描/混合/表格或合成夾具上做實際 OCR/位置核對，僅有缺口才比備選；六頁數字 PDF 初查另記。結果有效時 T006/T013 複用，不重複等價檢查。

- [x] T003 建立產品證據合同與版本化封裝
  - 來源：REQ-002, NFR-002, NFR-005, AC-F003-006
  - 依賴：T001, T002；Plan 已更新 ready 後開始正式實現。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：與 Skill EvidenceItem 基線的字段/語義映射及摘要、產品 Schema 版本、原生引用與分片策略；不同來源/版本不誤合併。
  - 驗證：EV-F003-006；一組共同對象/身份合同測試，覆蓋六種內容分型與大內容引用。

- [x] T004 交付 SQLite、CSV、JSON 和壓縮 JSONL 原生讀取
  - 來源：REQ-002, NFR-002, AC-F003-002
  - 依賴：T003。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：聲明範圍內的結構和記錄產物；前導零、長標識、精度、空值、嵌套和邏輯記錄定位對照結果；原數據未改寫。
  - 驗證：EV-F003-002；固定原值夾具往返對照測試，不用同一解析實現自動生成預期。

- [x] T005 交付 Markdown 與受限 XML/XLSX 結構讀取
  - 來源：REQ-002, NFR-002, AC-F003-003
  - 依賴：T003。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：Markdown 樹與行範圍；XML 標籤/XPath、XLSX 表/單元格的實際支持範圍和原生引用；不支持結構有附件/缺口輸出。
  - 驗證：EV-F003-003；一次結構保留測試，斷言正常、缺段/空緩存和不支持分支，不擴展為完整 Office 引擎。

- [x] T006 實現經樣本確認的 PDF 解析與頁框映射
  - 來源：REQ-002, NFR-002, AC-F003-004
  - 依賴：T002, T003。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：文本/掃描/混合路由、原生結構引用、聲明頁覆蓋、座標轉換和未定位處理；不依賴默認前若干頁產生全篇成功。
  - 驗證：EV-F003-004；對適配後的產物執行同一逐頁核對，複用 T002 未變的解析質量證據，只新增適配層差異檢查。

- [x] T007 交付圖像與心電的附件和元數據範圍
  - 來源：REQ-002, NFR-002, NFR-003, AC-F003-005
  - 依賴：T003。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：PNG 原引用與可解碼說明、圖文關聯出處、WFDB 頭/信號引用和已讀通道/單位信息；未解碼及缺配對明確。
  - 驗證：EV-F003-005；固定完整與缺配對樣本的資產讀取測試，斷言無 OCR/診斷調用。

- [x] T008 實現同版本證據定位回放
  - 來源：REQ-002, REQ-008, NFR-002, NFR-003, AC-F003-007
  - 依賴：T004, T005, T006, T007。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：實際回查片段/字段/單元格與源值對照；過期來源、錯誤偏移和粗粒度位置明確拒絕或限制。
  - 驗證：EV-F003-007；一次真實來源回放測試，不以字符串路徑存在或 Schema 通過代替。

- [x] T009 實現完整覆蓋、空範圍與失敗分類
  - 來源：REQ-002, REQ-008, NFR-003, AC-F003-008
  - 依賴：T004, T005, T006, T007。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：manifest 逐單元清單、計數單位、可用/未讀/失敗/阻斷範圍；空與未知分別展示，無困難樣本從分母消失。
  - 驗證：EV-F003-008；混合批次聚合測試覆蓋部分成功、零範圍、未知總數與截斷。

- [x] T010 實現結果提交、冪等和受限恢復
  - 來源：REQ-002, REQ-008, NFR-005, NFR-003, AC-F003-009
  - 依賴：T009。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：單寫入者提交標記、重試/attempt 記錄、未變分片複用與新來源/配置產生新版本的證據；半成品不被消費。
  - 驗證：EV-F003-009；一次故障注入/恢復測試覆蓋提交前後、重複請求和來源變更。

- [x] T011 實現來源角色隔離與域內失敗處理
  - 來源：REQ-002, REQ-008, NFR-001, NFR-002, NFR-003, AC-F003-001, AC-F003-010, AC-F003-012
  - 依賴：T008, T010。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：有效授權與源版本檢查、標註/留出正文拒讀、未授權網絡調用拒絕、錯誤輸出最小化；規則/術語仍為來源參考。
  - 驗證：EV-F003-001、EV-F003-010、EV-F003-012；一次邊界測試組，分別斷言讀取探針、網絡探針和錯誤文本，結果逐用例可追溯。

- [x] T012 交付 F004/F005 可消費的建模輸入包
  - 來源：REQ-002, REQ-008, NFR-002, NFR-003, AC-F003-011
  - 依賴：T008, T010, T011。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：固定來源/運行的 handoff、結構字典、證據分片、原生引用、角色與可用範圍、失敗清單及回查說明；未知合同版本拒絕消費。
  - 驗證：EV-F003-011；一次消費者合同測試，明確它不證明患者關係、規則批准或真實工作臺已實現。

- [x] T013 綁定並完成 F003 局部驗收與交接記錄
  - 來源：REQ-002, REQ-008, NFR-001, NFR-002, NFR-003, NFR-005, AC-F003-001, AC-F003-002, AC-F003-003, AC-F003-004, AC-F003-005, AC-F003-006, AC-F003-007, AC-F003-008, AC-F003-009, AC-F003-010, AC-F003-011, AC-F003-012
  - 依賴：T012。
  - 修改：`backend/medical_quality/evidence.py`、`backend/medical_quality/replay.py`、`backend/medical_quality/worker.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：各用例的實際輸入/版本、檢查與 pass/fail/blocked/not_run；註明局部與組合邊界、未滿足項及原始數據不變；未通過不得完成 Feature。
  - 驗證：EV-F003-001～012、EV-F003-002、EV-F003-003、EV-F003-004、EV-F003-005、EV-F003-006、EV-F003-007、EV-F003-008、EV-F003-009、EV-F003-010、EV-F003-011、EV-F003-012、EV-F003-013、EV-F003-014；一次選定套件驗收，複用仍有效的前述結果，僅對尚無有效證據或已變輸入執行檢查。PG-001/PG-003 組合結果後續在 product 套件單列，不用替身通過代替。

## Task 數量複核

- 任務總數：13。
- 原因：按輸入合同、路線確認、證據封裝、各類讀取、定位、覆蓋、恢復、邊界及交接的獨立結果拆分；均服務同一 F003 輸出。F002 登記、F004 醫療建模和 F005 規則治理不被吸收到本 Feature。
- 依賴無環；下游真實組合驗收安排在相鄰能力具備後，不反過來要求 F003 等待 F004 才能建設。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | 本輪僅生成 Spec、Plan、Tasks 與用例定義；無任務完成證據 | Plan 的 PDF 路線及 F002 實際接口條件待收斂；尚未開發、安裝或運行產品驗收 |

## 當前交接狀態

原生格式讀取、EvidenceItem 1.0、真實 OCR、原值/定位回放、覆蓋/錯誤、原子結果提交與柵欄恢復。 代表性實現/檢查已完成。本 Feature 軟件任務與本輪直接檢查均已完成；專業或上游整體驗收仍沿 Feature Map 的狀態；詳情見[實現記錄](../../verification/F003-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
