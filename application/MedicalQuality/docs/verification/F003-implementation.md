# F003 實現與驗收記錄

更新：2026-10-14。本文是當前實現記錄；2026-10-13 的規劃記錄保留歷史。

已實現：原生格式讀取、EvidenceItem 1.0、真實 OCR、原值/定位回放、覆蓋/錯誤、原子結果提交與柵欄恢復。

邊界：當前 PDF 實測為六頁規範和一頁純掃描合成夾具；複雜跨頁/旋轉/低質量掃描沒有專業驗收。

## 實際落點

- [backend/medical_quality/evidence.py](../../backend/medical_quality/evidence.py)
- [backend/medical_quality/replay.py](../../backend/medical_quality/replay.py)
- [backend/medical_quality/worker.py](../../backend/medical_quality/worker.py)
- [frontend/src/App.tsx](../../frontend/src/App.tsx)
- [frontend/src/pages/CasePage.tsx](../../frontend/src/pages/CasePage.tsx)
- [frontend/src/pages/OperationsPages.tsx](../../frontend/src/pages/OperationsPages.tsx)
- [backend/tests/test_data_semantics.py](../../backend/tests/test_data_semantics.py)
- [backend/tests/test_replay.py](../../backend/tests/test_replay.py)
- [backend/tests/test_recovery_permissions.py](../../backend/tests/test_recovery_permissions.py)

- [test_pdf_replay.py](../../backend/tests/test_pdf_replay.py)
- [test_pdf_failures.py](../../backend/tests/test_pdf_failures.py)

## 本輪驗證條件

工程身份、合成小樣本與真實本地數據庫/組件共同驗證軟件行為。真實資料讀取、OCR、本地模型和原生語義工具另有實際收據，不與測試替身混稱。詳見[彙總報告](development-report.md)。本輪 `pass` 只表示臺賬聲明的工程範圍；不表示生產效果或醫院接受。

復現相關後端檢查（會重建獨立測試庫，不清理試用庫）：

```sh
backend/.venv/bin/python scripts/test_backend.py -q tests/test_data_semantics.py tests/test_replay.py tests/test_recovery_permissions.py
```

界面按 `frontend/e2e/` 與最終報告復現；原生組件檢查為 `npm --prefix frontend test`。一次有效結果複用於相關用例，不為每行重複運行整個套件。

## 逐用例臺賬

| 用例 | 本輪結果 | 已驗證範圍與限制 |
| --- | --- | --- |
| EV-F003-001 · 有效範圍讀取，失效授權和變化來源被阻斷 | pass | 由上述真實工程檢查和實現核對覆蓋“有效範圍讀取，失效授權和變化來源被阻斷”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-002 · 結構化值與邏輯記錄不變 | pass | 由上述真實工程檢查和實現核對覆蓋“結構化值與邏輯記錄不變”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-003 · Markdown 結構和受限原生能力可見 | pass | 由上述真實工程檢查和實現核對覆蓋“Markdown 結構和受限原生能力可見”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-004 · PDF 聲明頁覆蓋、表格與位置可核對 | pass | 真實組合解析為 3 頁、18 項證據、2 張表，包含數字頁、掃描表格與 90° 續頁；否定、<0.05、0007、125 保留。正式登記、Worker、原頁和定位框已實際核對；旋轉表的行列結構標為 partial/restricted，保留原矩陣與原圖；不擅自認定邏輯列正確或合併臨床事件。 |
| EV-F003-005 · 資產元數據不冒充解碼或診斷 | pass | 由上述真實工程檢查和實現核對覆蓋“資產元數據不冒充解碼或診斷”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-006 · 共同對象和不同來源身份不混並 | pass | 由上述真實工程檢查和實現核對覆蓋“共同對象和不同來源身份不混並”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-007 · 定位回放檢出錯位和過期引用 | pass | 由上述真實工程檢查和實現核對覆蓋“定位回放檢出錯位和過期引用”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-008 · 混合批次覆蓋保留空與未知 | pass | 五單元彙總保留 2 成功、1 部分/無定位、1 失敗、1 阻斷；另核對零範圍、未知總數、缺單元與非法範圍。來源 API 返回同一彙總，不把不同格式單元當病例數。 |
| EV-F003-009 · 中斷恢復與版本變化不破壞既有結果 | pass | 整個有界讀取任務是發佈單元：舊租約提交回滾、相同操作複用已完成 job，新範圍建立新 job/證據且舊結果保留。沒有聲稱在一個 job 內做無限流式分片提交。 |
| EV-F003-010 · 建模集合不讀取參照答案 | pass | 由上述真實工程檢查和實現核對覆蓋“建模集合不讀取參照答案”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-011 · 消費者理解範圍與合同版本 | pass | 由上述真實工程檢查和實現核對覆蓋“消費者理解範圍與合同版本”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-012 · 本地失敗不導致越域或全文日誌 | pass | 由上述真實工程檢查和實現核對覆蓋“本地失敗不導致越域或全文日誌”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-013 · 掃描頁真實 OCR 與關鍵字符/結構可查 | pass | 由上述真實工程檢查和實現核對覆蓋“掃描頁真實 OCR 與關鍵字符/結構可查”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |
| EV-F003-014 · 清洗保留標識、比較符與原文映射 | pass | 由上述真實工程檢查和實現核對覆蓋“清洗保留標識、比較符與原文映射”的軟件合同；數據/身份與專業限制沿本記錄，不擴大樣本結論。 |

## 交接與剩餘條件

直接消費者沿 Feature Map 接收同一版本/權限/證據合同。當前 PDF 實測為六頁規範和一頁純掃描合成夾具；複雜跨頁/旋轉/低質量掃描沒有專業驗收。 不讀取參考答案來補造金標準，不填寫默認臨床閾值。

本 Feature 的本輪工程用例和交接已完成；目標醫院的生產身份、數據和責任條件仍由產品准入另行核驗。原始驗收要求和專業邊界保持。
