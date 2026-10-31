---
document: feature-tasks
feature: F007
status: in-progress
updated: "2026-10-14"
---

# F007 · 複核整改與責任簽字閉環任務

## 任務規則

- 本輪僅規劃，全部未執行；Plan 的實施前置關閉後再開始正式實現。
- 每項產出可單獨驗證，任務依賴是建設依賴，不把不同業務分支強行串成必須先後發生。
- 來源回到 [Spec](spec.md)，技術點見 [Plan](plan.md)；真實檢查建立後綁定 [Evals](../../../evals/F007.json)，有有效證據才勾選。

## 任務清單

- [x] T001 實現質控複核與有理由終態
  - 來源：REQ-009, NFR-004, PSC-006, PSC-009, AC-F007-001
  - 依賴：無
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：確認/駁回前後狀態、待辦和審計引用；當前無執行證據。
  - 驗證：EV-F007-001；複核分支及責任記錄測試，實現後綁定真實入口。

- [x] T002 交付醫生整改與新版本接入
  - 來源：REQ-010, NFR-004, NFR-005, PSC-001, PSC-006, PSC-007, AC-F007-002
  - 依賴：T001
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：父子版本、原件不變與拒絕記錄；當前無執行證據。
  - 驗證：EV-F007-002；新版本提交與權限/衝突測試，實現後綁定真實入口。

- [x] T003 實現申訴與專業爭議出口
  - 來源：REQ-010, REQ-011, NFR-003, NFR-004, PSC-005, PSC-006, PSC-009, AC-F007-003
  - 依賴：T001
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：原判/裁決關係、責任節點與阻斷；當前無執行證據。
  - 驗證：EV-F007-003；申訴三類出口與高風險未決測試，實現後綁定真實入口。

- [x] T004 貫通重核、退回與人工確認
  - 來源：REQ-012, NFR-003, NFR-005, PSC-005, PSC-006, PSC-007, AC-F007-004
  - 依賴：T002, T003
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：F006 運行引用、退回/阻斷與確認記錄；當前無執行證據。
  - 驗證：EV-F007-004；再核驗結果與人工門檻合同測試，實現後綁定真實入口。

- [ ] T005 實現範圍固定的分崗位簽字
  - 來源：REQ-013, NFR-003, NFR-004, PSC-007, PSC-008, PSC-009, AC-F007-005
  - 依賴：T004
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：獨立崗位/版本記錄及拒絕結果；當前無執行證據。
  - 驗證：EV-F007-005；雙崗位和缺前置簽字測試，實現後綁定真實入口。

- [x] T006 維護簽字歷史與版本失效
  - 來源：REQ-012, REQ-013, NFR-005, PSC-001, PSC-007, AC-F007-006
  - 依賴：T005
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：新舊鏈路、簽字綁定與當前受限狀態；當前無執行證據。
  - 驗證：EV-F007-006；版本更替與歷史回放測試，實現後綁定真實入口。

- [x] T007 實現責任接續與期限變更
  - 來源：REQ-014, NFR-004, NFR-006, PSC-006, PSC-009, PSC-013, AC-F007-007
  - 依賴：T001, T003
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：改派/延期記錄、逾期反饋和工作臺狀態；當前無執行證據。
  - 驗證：EV-F007-007；責任/期限轉換與待辦投影測試，實現後綁定真實入口。

- [x] T008 實現業務冪等與版本併發控制
  - 來源：REQ-009, REQ-012, REQ-013, NFR-004, NFR-005, PSC-009, AC-F007-008
  - 依賴：T002, T003, T005, T007
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：決定 ID、任務版本、審計與結果去重；當前無執行證據。
  - 驗證：EV-F007-008；重複/併發與提交後故障注入測試，實現後綁定真實入口。

- [x] T009 實現持久人工等待與安全恢復
  - 來源：REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, NFR-003, NFR-005, PSC-006, PSC-007, PSC-009, AC-F007-009
  - 依賴：T004, T006, T008
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：業務決定與執行遊標對照、拒絕及去重結果；當前無執行證據。
  - 驗證：EV-F007-009；跨進程暫停/恢復與提交邊界故障測試，實現後綁定真實入口。

- [x] T010 交付可連續處理的崗位界面
  - 來源：REQ-009, REQ-010, REQ-014, NFR-006, PSC-006, PSC-013, AC-F007-010
  - 依賴：T007, T009
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：雙視口、前後狀態與返回上下文操作記錄；當前無執行證據。
  - 驗證：EV-F007-010；一次多崗位代表旅程瀏覽器走查，實現後綁定真實入口。

- [x] T011 驗證業務授權與審計不可繞過
  - 來源：REQ-009, REQ-010, REQ-011, REQ-013, NFR-001, NFR-003, NFR-004, PSC-005, PSC-008, PSC-009, AC-F007-011
  - 依賴：T008, T009
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：真實主體、拒絕/回滾與未外發探針；當前無執行證據。
  - 驗證：EV-F007-011；授權/審計故障與模型越權負例測試，實現後綁定真實入口。

- [ ] T012 完成責任閉環局部驗收與交接
  - 來源：REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, NFR-001, NFR-003, NFR-004, NFR-005, NFR-006, AC-F007-001, AC-F007-002, AC-F007-003, AC-F007-004, AC-F007-005, AC-F007-006, AC-F007-007, AC-F007-008, AC-F007-009, AC-F007-010, AC-F007-011
  - 依賴：T001, T002, T003, T004, T005, T006, T007, T008, T009, T010, T011
  - 修改：`backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py` 及對應正式頁面/測試；細分職責已合併，不另建重複服務。
  - 完成證據：固定輸入/真實操作/結果與覆蓋，專業與生產條件未滿足的範圍明確；當前未運行。
  - 驗證：EV-F007-001, EV-F007-002, EV-F007-003, EV-F007-004, EV-F007-005, EV-F007-006, EV-F007-007, EV-F007-008, EV-F007-009, EV-F007-010, EV-F007-011、EV-F007-012；一次選定套件驗收，複用仍有效證據，僅對缺失/變化項執行檢查。

## Task 數量複核

- 任務總數：12。
- 原因：分別形成複核、版本、爭議、重核、簽字、責任、冪等、恢復、界面與權限結果，最後交接；保持同一責任閉環，不按頁面或技術車道拆散。上游依賴沿 Map，不新增循環。

## 執行記錄

| 日期 | 狀態變化 | 完成證據 | 偏差/剩餘項 |
| --- | --- | --- | --- |
| 2026-10-13 | planned | 只形成文檔與用例定義 | 真實接口、框架恢復和生產身份/簽署條件待落實；未開發 |

## 當前交接狀態

複核/誤報、醫生新文書、申訴/升級、改派/截止時間、重核/人工確認、雙崗位簽字和跨進程人工等待。 代表性實現/檢查已完成。未勾選的任務包括正式責任/專業核對（若適用）與整組最終驗收；詳情見[實現記錄](../../verification/F007-implementation.md)，不能據軟件可運行把 133 條正式用例全部寫成通過。
