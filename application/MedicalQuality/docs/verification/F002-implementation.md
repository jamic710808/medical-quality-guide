# F002 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：來源登記、內容摘要、不可變快照、受控目錄/上傳、SQLite 只讀結構和研究用途。

邊界：原庫始終只讀；登記和前 30 條解析不能宣稱全量臨床接入。

## 實際落點

- [backend/medical_quality/sources.py](../../backend/medical_quality/sources.py)
- [backend/medical_quality/app.py](../../backend/medical_quality/app.py)
- [frontend/src/App.tsx](../../frontend/src/App.tsx)
- [frontend/src/pages/CasePage.tsx](../../frontend/src/pages/CasePage.tsx)
- [frontend/src/pages/OperationsPages.tsx](../../frontend/src/pages/OperationsPages.tsx)
- [backend/tests/test_data_semantics.py](../../backend/tests/test_data_semantics.py)
- [backend/tests/test_recovery_permissions.py](../../backend/tests/test_recovery_permissions.py)
- [backend/tests/test_retrieval_inputs.py](../../backend/tests/test_retrieval_inputs.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_data_semantics.py tests/test_recovery_permissions.py tests/test_retrieval_inputs.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F002-001 · 只登記允許來源與用途 | pass | 由上述真實工程檢查和實現核對覆蓋“只登記允許來源與用途”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-002 · 文件與數據庫版本語義真實 | pass | 由上述真實工程檢查和實現核對覆蓋“文件與數據庫版本語義真實”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-003 · 數據庫結構和業務記錄分開 | pass | 由上述真實工程檢查和實現核對覆蓋“數據庫結構和業務記錄分開”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-004 · 路徑基準和定位口徑可回查 | pass | 由上述真實工程檢查和實現核對覆蓋“路徑基準和定位口徑可回查”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-005 · 來源性質與評測角色隔離 | pass | 由上述真實工程檢查和實現核對覆蓋“來源性質與評測角色隔離”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-006 · 內容重複不混淆業務身份 | pass | 由上述真實工程檢查和實現核對覆蓋“內容重複不混淆業務身份”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-007 · 接入覆蓋包含失敗和未讀 | pass | 由上述真實工程檢查和實現核對覆蓋“接入覆蓋包含失敗和未讀”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-008 · 更新與撤權保留歷史並限制新讀取 | pass | 由上述真實工程檢查和實現核對覆蓋“更新與撤權保留歷史並限制新讀取”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F002-009 · 向解析方交付穩定受限合同 | pass | 由上述真實工程檢查和實現核對覆蓋“向解析方交付穩定受限合同”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。原庫始終只讀；登記和前 30 條解析不能宣稱全量臨床接入。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

本 Feature 的本輪工程用例和交接已完成；目標醫院的生產身份、數據和責任條件仍由產品准入另行核驗。原始驗收要求和專業邊界保持。
