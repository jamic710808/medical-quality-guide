# F006 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：八條文書規則、三值結果、真實 Qwen3 候選、逐字引用過濾、LangGraph/PG checkpoint 與本體形狀檢查。

邊界：確定性集成檢查只替換生成模型響應；另有真實模型運行記錄。模型候選尚無專業準確率或校準結論。

## 實際落點

- [backend/medical_quality/quality.py](../../backend/medical_quality/quality.py)
- [backend/medical_quality/worker.py](../../backend/medical_quality/worker.py)
- [backend/medical_quality/ontology.py](../../backend/medical_quality/ontology.py)
- [frontend/src/App.tsx](../../frontend/src/App.tsx)
- [frontend/src/pages/CasePage.tsx](../../frontend/src/pages/CasePage.tsx)
- [frontend/src/pages/OperationsPages.tsx](../../frontend/src/pages/OperationsPages.tsx)
- [backend/tests/test_workflow_graph.py](../../backend/tests/test_workflow_graph.py)
- [backend/tests/test_retrieval_inputs.py](../../backend/tests/test_retrieval_inputs.py)
- [backend/tests/test_data_semantics.py](../../backend/tests/test_data_semantics.py)
- [backend/tests/test_recovery_permissions.py](../../backend/tests/test_recovery_permissions.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_workflow_graph.py tests/test_retrieval_inputs.py tests/test_data_semantics.py tests/test_recovery_permissions.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F006-001 · 運行固定適用範圍與完整版本 | pass | 由上述真實工程檢查和實現核對覆蓋“運行固定適用範圍與完整版本”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-002 · 確定性規則條件與臨床結論分開 | pass | 由上述真實工程檢查和實現核對覆蓋“確定性規則條件與臨床結論分開”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-003 · 跨段模型輸出保持候選性質 | blocked | 本地模型產生了可核查候選，偽引用被拒絕；跨段專業語義正確性仍需專家參照。 |
| EV-F006-004 · 單條問題呈現完整分層證據 | pass | 由上述真實工程檢查和實現核對覆蓋“單條問題呈現完整分層證據”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-005 · 失敗與部分覆蓋禁止自動通過 | pass | 由上述真實工程檢查和實現核對覆蓋“失敗與部分覆蓋禁止自動通過”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-006 · 風險分流不替代專業確認 | pass | 由上述真實工程檢查和實現核對覆蓋“風險分流不替代專業確認”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-007 · 整改版本、配置變化與重試可追溯 | pass | 由上述真實工程檢查和實現核對覆蓋“整改版本、配置變化與重試可追溯”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-008 · 人工與專業評測消費同一結果 | pass | 由上述真實工程檢查和實現核對覆蓋“人工與專業評測消費同一結果”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-009 · 模型故障、惡意正文與假引用受限 | pass | 由上述真實工程檢查和實現核對覆蓋“模型故障、惡意正文與假引用受限”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-010 · 形狀通過與完整性/臨床通過分開 | pass | 由上述真實工程檢查和實現核對覆蓋“形狀通過與完整性/臨床通過分開”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-011 · 運行語義工具只讀且事件流最小化 | pass | 由上述真實工程檢查和實現核對覆蓋“運行語義工具只讀且事件流最小化”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F006-012 · 語義版本故障與節點重放有界恢復 | pass | 真實 PG checkpoint 拒絕未知圖版本、失效語義和變更規則資格，模型調用次數為零；持久恢復及 Worker 柵欄另有實際檢查，合法原文保持可訪問。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。確定性集成檢查只替換生成模型響應；另有真實模型運行記錄。模型候選尚無專業準確率或校準結論。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

上述未覆蓋組合保留原用例，不刪除要求或把部分執行寫成全套通過。當前軟件可進行本地試用；本 Feature 的最終完整驗收任務仍按臺賬結果保留。
