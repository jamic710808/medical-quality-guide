# F005 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：獨立規則/資格版本、候選審核、BM25/BGE-M3/pgvector/RRF、精確編號、限定本體擴展、索引發布。

邊界：已運行真實 BGE-M3，尚無目標醫院獨立召回對照；不宣稱選型已證明最優醫學效果。

## 實際落點

- [backend/medical_quality/retrieval.py](../../backend/medical_quality/retrieval.py)
- [backend/medical_quality/governance.py](../../backend/medical_quality/governance.py)
- [frontend/src/App.tsx](../../frontend/src/App.tsx)
- [frontend/src/pages/CasePage.tsx](../../frontend/src/pages/CasePage.tsx)
- [frontend/src/pages/OperationsPages.tsx](../../frontend/src/pages/OperationsPages.tsx)
- [backend/tests/test_retrieval_inputs.py](../../backend/tests/test_retrieval_inputs.py)
- [backend/tests/test_governance.py](../../backend/tests/test_governance.py)

- [test_index_lifecycle.py](../../backend/tests/test_index_lifecycle.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_retrieval_inputs.py tests/test_governance.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F005-001 · 規則知識身份與生命週期分離 | pass | 由上述真實工程檢查和實現核對覆蓋“規則知識身份與生命週期分離”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F005-002 · 用途、範圍與授權共同決定可選依據 | pass | 由上述真實工程檢查和實現核對覆蓋“用途、範圍與授權共同決定可選依據”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F005-003 · 原文、編號與上下文可準確回查 | pass | 由上述真實工程檢查和實現核對覆蓋“原文、編號與上下文可準確回查”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F005-004 · 問法變化召回仍保留共同證據語義 | pass | 三條工程問法實際經過 BGE-M3/詞法/RRF，目標規則分別居首；保留版本、證據及分數。見 retrieval-query-observations.json；不作為獨立臨床準確率。 |
| EV-F005-005 · 無答案與部分檢索不偽裝完整依據 | pass | 由上述真實工程檢查和實現核對覆蓋“無答案與部分檢索不偽裝完整依據”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F005-006 · 更新、撤權與發佈保持責任一致 | pass | test_index_lifecycle.py 實測重複複用、審計失敗回滾、生成中資格變化、舊柵欄拒絕、完整新代次發佈及舊代次與當前資格分離。僅替換向量計算；真實模型另有運行收據。 |
| EV-F005-007 · 運行與交付固定原有依據基線 | pass | 由上述真實工程檢查和實現核對覆蓋“運行與交付固定原有依據基線”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F005-008 · 故障不會擴大模型數據流 | pass | 由上述真實工程檢查和實現核對覆蓋“故障不會擴大模型數據流”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F005-009 · 本體限定擴展與原 query/資格保持 | pass | 由上述真實工程檢查和實現核對覆蓋“本體限定擴展與原 query/資格保持”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。已運行真實 BGE-M3，尚無目標醫院獨立召回對照；不宣稱選型已證明最優醫學效果。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

上述未覆蓋組合保留原用例，不刪除要求或把部分執行寫成全套通過。當前軟件可進行本地試用；本 Feature 的最終完整驗收任務仍按臺賬結果保留。
