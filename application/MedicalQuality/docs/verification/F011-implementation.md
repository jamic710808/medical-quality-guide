# F011 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：固定上游原生圖譜與 Designer、三種投影、證據回查、內部審核、IRI/基數保真和受控導出。

邊界：圖像/顯示投影不代替完整 OWL/SHACL；公共 GitHub/Fabric 提交未裝配到醫療界面。

## 實際落點

- [backend/medical_quality/knowledge_graph.py](../../backend/medical_quality/knowledge_graph.py)
- [backend/medical_quality/ontology.py](../../backend/medical_quality/ontology.py)
- [backend/medical_quality/governance.py](../../backend/medical_quality/governance.py)
- [frontend/src/pages/GraphPage.tsx](../../frontend/src/pages/GraphPage.tsx)
- [frontend/src/vendor/ontology-playground](../../frontend/src/vendor/ontology-playground)
- [frontend/src/features/knowledge-graph](../../frontend/src/features/knowledge-graph)
- [backend/tests/test_workflow_graph.py](../../backend/tests/test_workflow_graph.py)
- [backend/tests/test_governance.py](../../backend/tests/test_governance.py)
- [backend/tests/test_recovery_permissions.py](../../backend/tests/test_recovery_permissions.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_workflow_graph.py tests/test_governance.py tests/test_recovery_permissions.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F011-001 · 完整原生圖譜能力進入產品 | pass | 由上述真實工程檢查和實現核對覆蓋“完整原生圖譜能力進入產品”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-002 · 三種視圖保持類型、實例和判斷層次 | pass | 由上述真實工程檢查和實現核對覆蓋“三種視圖保持類型、實例和判斷層次”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-003 · 圖節點回查固定原文與規則 | pass | 由上述真實工程檢查和實現核對覆蓋“圖節點回查固定原文與規則”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-004 · 有向路徑、搜索與範圍表達一致 | pass | 由上述真實工程檢查和實現核對覆蓋“有向路徑、搜索與範圍表達一致”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-005 · 原生設計器修改候選並承接審核 | pass | 由上述真實工程檢查和實現核對覆蓋“原生設計器修改候選並承接審核”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-006 · 導入導出不吞併本體語義 | pass | 由上述真實工程檢查和實現核對覆蓋“導入導出不吞併本體語義”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-007 · 圖譜所有入口遵守當前對象授權 | pass | 由上述真實工程檢查和實現核對覆蓋“圖譜所有入口遵守當前對象授權”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-008 · 域內分享、導出與來源許可 | pass | 由上述真實工程檢查和實現核對覆蓋“域內分享、導出與來源許可”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-009 · 版本變化不會混合圖、來源和歷史判斷 | pass | 後端固定文書/語義/證據版本；瀏覽器掛起舊本體響應，在規則視圖加載後放回，舊對象與計數沒有覆蓋當前圖；原文/任務入口保持。 |
| EV-F011-010 · 大圖原生策略與可到達性 | pass | 由上述真實工程檢查和實現核對覆蓋“大圖原生策略與可到達性”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-011 · 簡潔平臺中的連續工作與無障礙 | pass | 由上述真實工程檢查和實現核對覆蓋“簡潔平臺中的連續工作與無障礙”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-012 · 失敗恢復保持證據與原工作路徑 | pass | 由上述真實工程檢查和實現核對覆蓋“失敗恢復保持證據與原工作路徑”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-013 · 導入內容不能觸發外部讀取或腳本 | pass | 由上述真實工程檢查和實現核對覆蓋“導入內容不能觸發外部讀取或腳本”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F011-014 · 中文醫學名稱與未知基數不被 Fabric 默認值覆蓋 | pass | 由上述真實工程檢查和實現核對覆蓋“中文醫學名稱與未知基數不被 Fabric 默認值覆蓋”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。圖像/顯示投影不代替完整 OWL/SHACL；公共 GitHub/Fabric 提交未裝配到醫療界面。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

上述未覆蓋組合保留原用例，不刪除要求或把部分執行寫成全套通過。當前軟件可進行本地試用；本 Feature 的最終完整驗收任務仍按臺賬結果保留。
