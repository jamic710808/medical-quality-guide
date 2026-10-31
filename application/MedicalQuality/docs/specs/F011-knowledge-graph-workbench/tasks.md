---
document: feature-tasks
feature: F011
status: in-progress
updated: "2026-10-14"
---

# F011 · 知識圖譜工作臺任務

## 任務規則

全部任務待執行；以[計劃](plan.md)和[原生集成決定](../../architecture/ontology-playground-integration.md)為實施入口。現有上游/產品代碼未被本輪下載、安裝或開發。先完成 Plan 就緒前置，再進入實現；不得以靜態截圖或圖引擎重寫代替用戶指定的原生工作臺。

## 任務清單

- [x] T001 保留固定上游原生工作臺及來源清單
  - 來源：REQ-020, NFR-006, AC-F011-001
  - 依賴：無
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：固定版本原生對照、依賴閉包和 OP 能力清單；原生可運行且許可齊全；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-001；同一夾具的上游/集成原生能力對照走查；工程入口建立後綁定。

- [x] T002 實現三種醫療視圖的無歧義顯示投影
  - 來源：REQ-020, NFR-002, NFR-003, AC-F011-002
  - 依賴：T001
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：類型/實例/證據/規則/斷言及未知基數、版本和覆蓋附錄可消費；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-002, EV-F011-014；固定圖投影合同及語義負例檢查；工程入口建立後綁定。

- [x] T003 提供當前授權下的圖範圍與元素接口
  - 來源：REQ-020, NFR-001, NFR-004, AC-F011-007
  - 依賴：T002
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：先過濾後返回、計數/路徑/鄰居不洩漏及撤權清理證據；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-007；圖 API 與導出入口的角色/對象權限集成檢查；工程入口建立後綁定。

- [x] T004 貫通節點到同版本原文與規則
  - 來源：REQ-020, NFR-002, AC-F011-003
  - 依賴：T002, T003
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：雙段原文、PDF 定位/缺口和規則引用實際可回查；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-003；投影到原文/規則服務的最窄集成回查；工程入口建立後綁定。

- [x] T005 保留原生搜索、路徑與鄰域交互
  - 來源：REQ-020, NFR-002, NFR-006, AC-F011-004
  - 依賴：T001, T002, T003
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：中文/別名定位、有向路徑、高亮、局部無路徑與退出焦點的實際結果；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-004；固定有向圖搜索/路徑操作檢查；工程入口建立後綁定。

- [x] T006 將原生 Designer 接入同一候選審核流
  - 來源：REQ-020, NFR-004, NFR-005, AC-F011-005
  - 依賴：T001, T002, T003
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：實體/關係編輯、撤銷重做、保存、衝突拒絕與審核任務；生效版本未被直接改寫；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-005；Designer 到候選存儲/審核的單條狀態流檢查；工程入口建立後綁定。

- [x] T007 實現子集與完整本體包的格式邊界
  - 來源：REQ-020, NFR-002, NFR-003, AC-F011-006
  - 依賴：T002, T006
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：語義損失報告、中文/IRI 保留、Turtle 正式適配與危險輸入拒絕；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-006, EV-F011-013, EV-F011-014；格式適配與往返語義夾具檢查；工程入口建立後綁定。

- [x] T008 封裝域內鏈接和受控原生導出
  - 來源：REQ-020, NFR-001, NFR-004, AC-F011-008
  - 依賴：T003, T007
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：無患者 URL 載荷、無公共提交、PNG/子集/完整包分別授權審計；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-008；受控出口與瀏覽器網絡/存儲觀察；工程入口建立後綁定。

- [x] T009 實現固定圖會話及歷史版本一致性
  - 來源：REQ-020, NFR-002, NFR-005, AC-F011-009
  - 依賴：T002, T003, T004
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：S1/S2 和舊/新文書不混用，歷史引用保留及不匹配響應捨棄；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-009；圖會話版本一致性與亂序響應檢查；工程入口建立後綁定。

- [x] T010 保留大圖原生策略並驗證可到達性
  - 來源：REQ-020, NFR-002, NFR-006, AC-F011-010
  - 依賴：T001, T002, T005
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：規模邊界/第 100 項之後定位、真實設備性能與內存記錄；預算先凍結後驗收；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-010；固定設備上的規模邊界與交互性能走查；工程入口建立後綁定。

- [x] T011 完成業務導航、空間與視覺交互
  - 來源：REQ-020, NFR-006, AC-F011-011
  - 依賴：T004, T005, T006, T008, T009, T010
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：雙視口、原生主題/高亮、鍵盤、減少動態效果及返回原工作位置的走查；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-011；兩目標視口的代表性產品任務驗看；工程入口建立後綁定。

- [x] T012 完成錯誤反饋和原工作恢復
  - 來源：REQ-020, NFR-002, NFR-003, NFR-006, AC-F011-012
  - 依賴：T003, T006, T009, T011
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：空/部分/失敗/拒絕可區分，舊圖無閃現，合法原任務可接續；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-F011-012；圖工作區故障注入與恢復場景檢查；工程入口建立後綁定。

- [x] T013 交付圖譜組合驗證與完整性證據
  - 來源：REQ-020, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006, AC-F011-001, AC-F011-003, AC-F011-005, AC-F011-007, AC-F011-011, AC-F011-012
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008, T009, T010, T011, T012
  - 修改：`backend/medical_quality/knowledge_graph.py`、`backend/medical_quality/ontology.py`、`backend/medical_quality/governance.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：PG-006 真實組合與 OP 差異清單齊全；複用已有效局部結果，不重複全量跑同一檢查；完成後引用實際版本及驗證記錄，當前無。
  - 驗證：EV-PRODUCT-015, EV-PRODUCT-016；僅執行真實 PG-006 組合路徑並審閱已有局部證據；工程入口建立後綁定。

## Task 數量複核

共 13 項，每項交付一個可獨立檢查的結果。原生能力復現、業務投影、受權讀取、證據、探索、候選、格式、導出、版本、規模、體驗、恢復和組合分別留證；不按前後端技術車道拆重複任務。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | 本輪只有規劃結構核查，業務證據無 | Plan 前置與 13 項任務均待執行 |


## 當前交接狀態

固定上游原生圖譜與 Designer、三種投影、證據回查、內部審核、IRI/基數保真和受控導出。 代表性實現/檢查已完成。本 Feature 軟件任務與本輪直接檢查均已完成；專業或上游整體驗收仍沿 Feature Map 的狀態；詳情見[實現記錄](../../verification/F011-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
