# F001 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：會話/CSRF、真實 OIDC 回調密碼學、RBAC/對象用途、RLS、撤權、事務審計和冪等。

邊界：醫院 IdP、實際崗位映射、生產留存及簽署約定尚未取得。

## 實際落點

- [backend/medical_quality/access.py](../../backend/medical_quality/access.py)
- [backend/medical_quality/common.py](../../backend/medical_quality/common.py)
- [backend/medical_quality/db.py](../../backend/medical_quality/db.py)
- [backend/medical_quality/app.py](../../backend/medical_quality/app.py)
- [frontend/src/App.tsx](../../frontend/src/App.tsx)
- [frontend/src/pages/CasePage.tsx](../../frontend/src/pages/CasePage.tsx)
- [frontend/src/pages/OperationsPages.tsx](../../frontend/src/pages/OperationsPages.tsx)
- [backend/tests/test_access.py](../../backend/tests/test_access.py)
- [backend/tests/test_oidc.py](../../backend/tests/test_oidc.py)
- [backend/tests/test_recovery_permissions.py](../../backend/tests/test_recovery_permissions.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_access.py tests/test_oidc.py tests/test_recovery_permissions.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F001-001 · 可信身份與默認拒絕 | pass | 由上述真實工程檢查和實現核對覆蓋“可信身份與默認拒絕”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-002 · 角色動作與對象用途共同授權 | pass | 由上述真實工程檢查和實現核對覆蓋“角色動作與對象用途共同授權”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-003 · 所有讀取表面遵守同一範圍 | pass | 由上述真實工程檢查和實現核對覆蓋“所有讀取表面遵守同一範圍”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-004 · 後臺與模型工具不能擴大數據域 | pass | 由上述真實工程檢查和實現核對覆蓋“後臺與模型工具不能擴大數據域”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-005 · 業務變更與必要審計共同成立 | pass | 由上述真實工程檢查和實現核對覆蓋“業務變更與必要審計共同成立”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-006 · 重複請求與過期操作不造新事實 | pass | 由上述真實工程檢查和實現核對覆蓋“重複請求與過期操作不造新事實”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-007 · 撤權和策略更新立即限制新消費 | pass | 由上述真實工程檢查和實現核對覆蓋“撤權和策略更新立即限制新消費”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-008 · 審計查詢可追溯且最小化 | pass | 由上述真實工程檢查和實現核對覆蓋“審計查詢可追溯且最小化”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F001-009 · 缺生產留存和責任參數時限制啟用 | pass | 由上述真實工程檢查和實現核對覆蓋“缺生產留存和責任參數時限制啟用”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。醫院 IdP、實際崗位映射、生產留存及簽署約定尚未取得。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

本 Feature 的本輪工程用例和交接已完成；目標醫院的生產身份、數據和責任條件仍由產品准入另行核驗。原始驗收要求和專業邊界保持。
