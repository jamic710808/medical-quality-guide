# F009 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：固定準入基線、逐項缺項/風險否決、責任意見、服務器階段攔截、停用及重驗。

邊界：已實際建立阻斷申請；未建立或偽造生產批准。目標環境的准入/備份恢復驗收尚未取得。

## 實際落點

- [backend/medical_quality/release.py](../../backend/medical_quality/release.py)
- [backend/medical_quality/access.py](../../backend/medical_quality/access.py)
- [backend/medical_quality/quality.py](../../backend/medical_quality/quality.py)
- [frontend/src/App.tsx](../../frontend/src/App.tsx)
- [frontend/src/pages/CasePage.tsx](../../frontend/src/pages/CasePage.tsx)
- [frontend/src/pages/OperationsPages.tsx](../../frontend/src/pages/OperationsPages.tsx)
- [backend/tests/test_evaluation_delivery.py](../../backend/tests/test_evaluation_delivery.py)
- [backend/tests/test_access.py](../../backend/tests/test_access.py)

- [test_stage_capabilities.py](../../backend/tests/test_stage_capabilities.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_evaluation_delivery.py tests/test_access.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F009-001 · 准入申請固定範圍與基線 | pass | 由上述真實工程檢查和實現核對覆蓋“准入申請固定範圍與基線”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F009-002 · 必要條件與缺項可解釋 | pass | 由上述真實工程檢查和實現核對覆蓋“必要條件與缺項可解釋”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F009-003 · 高風險否決優先於平均指標 | pass | 由上述真實工程檢查和實現核對覆蓋“高風險否決優先於平均指標”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F009-004 · 關鍵人驗收與責任接受真實 | blocked | 崗位/版本/理由記錄和本地身份限制已實現；關鍵人的實際責任接受尚未取得。 |
| EV-F009-005 · 階段能力在服務端受控 | pass | test_stage_capabilities.py 驗證 shadow/assisted、範圍/模型不匹配、條件失效、停止與無權崗位。專業前置使用顯式替身，只證明執行機制，不是實際生產批准。 |
| EV-F009-006 · 條件失效後停用和回退保留歷史 | pass | 由上述真實工程檢查和實現核對覆蓋“條件失效後停用和回退保留歷史”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F009-007 · 修復與擴大範圍必須重新核驗 | pass | 由上述真實工程檢查和實現核對覆蓋“修復與擴大範圍必須重新核驗”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F009-008 · 管理視圖顯示真實門檻與責任 | pass | 由上述真實工程檢查和實現核對覆蓋“管理視圖顯示真實門檻與責任”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F009-009 · 向運行與交付提供同一准入事實 | pass | 由上述真實工程檢查和實現核對覆蓋“向運行與交付提供同一准入事實”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。已實際建立阻斷申請；未建立或偽造生產批准。目標環境的准入/備份恢復驗收尚未取得。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

上述未覆蓋組合保留原用例，不刪除要求或把部分執行寫成全套通過。當前軟件可進行本地試用；本 Feature 的最終完整驗收任務仍按臺賬結果保留。
