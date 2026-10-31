# F004 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：命名空間與未關聯病例、臨床斷言、固定上下文、受控結構查詢、OWL/SHACL 包與原生語義橋接。

邊界：28 個應用概念為工程基線；外部臨床詞表及專業等價映射未啟用，不能稱醫學本體已獲專業批准。

## 實際落點

- [backend/medical_quality/clinical_context/context.py](../../backend/medical_quality/clinical_context/context.py)
- [backend/medical_quality/clinical_context/query_catalog.py](../../backend/medical_quality/clinical_context/query_catalog.py)
- [backend/medical_quality/ontology.py](../../backend/medical_quality/ontology.py)
- [backend/medical_quality/native_semantic.py](../../backend/medical_quality/native_semantic.py)
- [backend/medical_quality/clinical_context/ontology](../../backend/medical_quality/clinical_context/ontology)
- [frontend/src/App.tsx](../../frontend/src/App.tsx)
- [frontend/src/pages/CasePage.tsx](../../frontend/src/pages/CasePage.tsx)
- [frontend/src/pages/OperationsPages.tsx](../../frontend/src/pages/OperationsPages.tsx)
- [backend/tests/test_data_semantics.py](../../backend/tests/test_data_semantics.py)
- [backend/tests/test_retrieval_inputs.py](../../backend/tests/test_retrieval_inputs.py)
- [backend/tests/test_governance.py](../../backend/tests/test_governance.py)
- [backend/tests/test_workflow_graph.py](../../backend/tests/test_workflow_graph.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_data_semantics.py tests/test_retrieval_inputs.py tests/test_governance.py tests/test_workflow_graph.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F004-001 · 有據身份與未關聯 | pass | 由上述真實工程檢查和實現核對覆蓋“有據身份與未關聯”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-002 · 原值、時間與單位不被吞併 | pass | 由上述真實工程檢查和實現核對覆蓋“原值、時間與單位不被吞併”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-003 · 結構化結果粒度與授權範圍一致 | pass | 由上述真實工程檢查和實現核對覆蓋“結構化結果粒度與授權範圍一致”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-004 · 列表定位與桌面入口可操作 | pass | 由上述真實工程檢查和實現核對覆蓋“列表定位與桌面入口可操作”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-005 · 崗位處理後接續同一任務 | pass | 由上述真實工程檢查和實現核對覆蓋“崗位處理後接續同一任務”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-006 · 解析缺口在上下文中保持可見 | pass | 由上述真實工程檢查和實現核對覆蓋“解析缺口在上下文中保持可見”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-007 · 更新上下文不改寫歷史 | pass | 由上述真實工程檢查和實現核對覆蓋“更新上下文不改寫歷史”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-008 · 交接對象可回到實際證據 | pass | 由上述真實工程檢查和實現核對覆蓋“交接對象可回到實際證據”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-009 · 必需本體定義、數據綁定和約束可消費 | blocked | 真實 OWL EL/ELK/SHACL 與產品消費已經運行；專業定義、外部術語許可及完整臨床 CQ 核對未獲得。 |
| EV-F004-010 · 原生活動版本不切換產品語義運行 | pass | 由上述真實工程檢查和實現核對覆蓋“原生活動版本不切換產品語義運行”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F004-011 · 原生工具與五類對象適配不能偽造能力 | pass | 由上述真實工程檢查和實現核對覆蓋“原生工具與五類對象適配不能偽造能力”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。28 個應用概念為工程基線；外部臨床詞表及專業等價映射未啟用，不能稱醫學本體已獲專業批准。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

上述未覆蓋組合保留原用例，不刪除要求或把部分執行寫成全套通過。當前軟件可進行本地試用；本 Feature 的最終完整驗收任務仍按臺賬結果保留。
