---
document: feature-plan
feature: F007
status: ready
updated: "2026-10-14"
---

# F007 · 複核整改與責任簽字閉環實施計劃

## 2026-10-14 實施更新

用戶 U10 已授權持續開發。本 Feature 的軟件已落地：複核/誤報、醫生新文書、申訴/升級、改派/截止時間、重核/人工確認、雙崗位簽字和跨進程人工等待。 實際文件為 `backend/medical_quality/remediation.py`、`backend/medical_quality/quality.py`。為保持模塊化單體簡單，下文最初規劃的多個職責文件合併在這些模塊中；它們不是另有待創建的第二實現。Spec 的業務語義不變。工程前置已有實測，Plan ready 不等於專業或完整驗收通過。逐用例結果與剩餘組合見[當前實現記錄](../../verification/F007-implementation.md)。本地身份簽字標記 local_engineering；不是醫院員工的實際電子簽署。

下文“現有上下文/擬建模塊”保留原設計階段背景；當前工程狀態以本節和實際文件為準。

## 現有上下文與複用

- backend 尚無業務實現，原型僅作多崗位旅程輸入；不把 sessionStorage、固定前端核驗或模擬簽字搬成業務事實源。
- 複用 F001 身份/責任接口、F002～F004 版本證據、F006 固定運行結果和再次核驗，沿用 PSC-001, PSC-005, PSC-006, PSC-007, PSC-008, PSC-009, PSC-013。
- [Agent 技術決定](../../architecture/agent-runtime.md)選擇 LangGraph 顯式編排；[TP-10～12](../../architecture/technical-points/agent-orchestration.md)是執行、人工事務和恢復的技術事實源，原 TP-01～09 的模型/檢索選擇不變。
- 當前只落盤設計，用例均未綁定；Plan 保留真實身份/接口和框架故障驗證的前置，不將複製 Skill 或選框架稱為可運行。

## 影響範圍

以下為擬創建模塊，路徑相對 MedicalQuality。可按職責合併文件，不為每項任務另建服務。

| 路徑/模塊 | 當前職責 | 計劃變化 | 對應 AC |
| --- | --- | --- | --- |
| backend/medical_quality/remediation/ 內的 review.py、commands.py | 尚無正式實現 | 實現質控複核與有理由終態 | AC-F007-001 |
| backend/medical_quality/remediation/ 內的 revisions.py、commands.py | 尚無正式實現 | 交付醫生整改與新版本接入 | AC-F007-002 |
| backend/medical_quality/remediation/ 內的 appeals.py、decisions.py | 尚無正式實現 | 實現申訴與專業爭議出口 | AC-F007-003 |
| backend/medical_quality/remediation/ 內的 reverification.py、graph.py | 尚無正式實現 | 貫通重核、退回與人工確認 | AC-F007-004 |
| backend/medical_quality/remediation/ 內的 signatures.py、commands.py | 尚無正式實現 | 實現範圍固定的分崗位簽字 | AC-F007-005 |
| backend/medical_quality/remediation/ 內的 version_links.py、signatures.py | 尚無正式實現 | 維護簽字歷史與版本失效 | AC-F007-006 |
| backend/medical_quality/remediation/ 內的 assignment.py、deadlines.py | 尚無正式實現 | 實現責任接續與期限變更 | AC-F007-007 |
| backend/medical_quality/remediation/ 內的 commands.py、repository.py、outbox.py | 尚無正式實現 | 實現業務冪等與版本併發控制 | AC-F007-008 |
| backend/medical_quality/remediation/ 內的 graph.py、resume.py、outbox.py | 尚無正式實現 | 實現持久人工等待與安全恢復 | AC-F007-009 |
| backend/medical_quality/remediation/ 內的 projection.py；frontend/ 正式責任流程頁面 | 尚無正式實現 | 交付可連續處理的崗位界面 | AC-F007-010 |
| backend/medical_quality/remediation/ 內的 commands.py、access.py、repository.py | 尚無正式實現 | 驗證業務授權與審計不可繞過 | AC-F007-011 |

共享命令/結果放 backend/medical_quality/contracts/，模塊內僅適配；圖執行復用 orchestration/ 的 PostgreSQL checkpoint 和受限恢復。正式頁面已選 React/TypeScript/Vite，經 FastAPI 處理責任命令；事務、身份和持久任務見 [TP-13/14](../../architecture/technical-points/platform-and-clinical-contracts.md#tp-13)，對應檢查在 backend/tests/remediation/，代碼尚未創建。

## 實現方案

### 技術點歸屬

| 技術點 | 本 Feature 的實現 |
| --- | --- |
| [TP-10](../../architecture/technical-points/agent-orchestration.md#tp-10) | 消費 F006 固定運行與受影響重核，區分計算失敗與專業確認 |
| [TP-11](../../architecture/technical-points/agent-orchestration.md#tp-11) | LangGraph 等待/恢復 + PostgreSQL 業務命令、責任記錄和 outbox 同事務；checkpoint 獨立保存 |
| [TP-12](../../architecture/technical-points/agent-orchestration.md#tp-12) | 工具/角色邊界、真實待辦與運行事件、取消和版本兼容驗證 |

### 本體版本與 Agent 恢復的交接

消費 F006 的固定 SemanticRelease/mapping/shape/value-set 與證據/規則引用；詳細見[Agent 與本體專項](../../data-preparation/governance-cleaning-handoff.md#agent-semantic)。原生 ontology_vN/active 或演化 Accept 不改變本病例已保存決定/簽字。暫停期間授權/語義資格變化按當前前置處理；需要重核則新運行鏈，不能用新本體重解釋舊簽字。恢復仍只消費應用已提交 BusinessDecision，構建/推理工具不提供業務批准。

### 狀態與寫入邊界

業務狀態由應用庫決定，圖只消費已提交 BusinessDecision。actor 來自可信身份，校驗 task/scope/expected_version/action/reason/idempotency_key 後同事務提交業務變化、必要責任記錄和待投遞事件；失敗不給完整成功。圖恢復傳 decision_id，不接收客戶端或模型直接批准值作為責任事實。

checkpoint 與業務庫提交不假定原子。恢復執行器可重複消費事件，按決定/任務版本去重，已提交業務事實不可被模型重放覆蓋；業務寫操作不放在會因 interrupt 恢復而重複的等待節點。響應丟失先對賬，過期/亂序恢復拒絕或隔離。

### 前後路徑與消費

正常確認/駁回、整改/申訴、專家三類出口、重核/退回、雙崗簽字、改派/延期以及新版本重新核驗均沿 Spec/PSC 狀態。F007 請求新版本登記與重核只是消費既有上游能力，不改變 Map 的建設依賴。

F004 列表/詳情/統計從同一已保存結果投影；F008/F009 取得固定版本及實際責任/覆蓋證據。真實簽署方式與身份映射未配置時不得生產啟用，測試身份與合成記錄必須顯式標記。

## 實施順序

1. 核對 F001/F006 技術合同和本地 LangGraph/checkpointer 目標版本，以小型非業務故障夾具確認暫停/恢復語義；解決下表實施前置後更新 Plan ready。
2. 按任務建立業務命令、版本/責任事實與正常人工分支，再接圖等待/恢復；不先用聊天記錄或自動記憶模擬狀態源。
3. 接入工作臺、消息投影與直接受影響的返回路徑；圖事件不得製造假成功。
4. 綁定 [F007 用例](../../../evals/F007.json) 並完成必要檢查；相關真路徑具備後執行 [product 套件](../../../evals/product.json)。模擬身份或替身不替代專業/生產驗收。

## 依賴與風險

| 依賴/風險 | 影響 | 應對 | 驗證時機 |
| --- | --- | --- | --- |
| graph 與業務庫不是同一事務 | 寫後崩潰重複派單/簽字 | 同庫業務/審計/outbox 提交，圖只消費決定，操作查重/版本校驗 | AC-F007-008/009/011 |
| F001/F006 尚無實際接口 | 無法證明真實授權與重核 | 先固定合同及顯式夾具，真路徑另做組合 | 實施前與集成時 |
| 階段/對象版本更新 | 舊輸入或簽字誤用 | 固定範圍、拒絕過期、受影響重核 | AC-F007-006/008 |
| 工具審批與業務簽署混用 | 非責任主體代簽 | 應用身份驗證，不信模型/瀏覽器角色或裸 resume | AC-F007-005/011 |
| 記憶/日誌與病例混用 | 信息越域或歷史汙染 | 狀態/上下文分域，必要引用留痕，日誌最小化 | 邊界與生產配置核對 |

### 開放項與就緒條件

| ID | 問題/假設及影響 | 是否阻塞 | 負責人/驗證方式與時機 | 狀態 | 處理結論與依據 |
| --- | --- | --- | --- | --- | --- |
| OQ-001 | 工程實施前置核對：LangGraph/checkpoint 包版本與本地恢復/圖升級未實測 | 否 | 實施負責人用進程重啟和提交邊界故障固定版本/結果 | 已解決 | 2026-10-14 已固定本地依賴並運行對應工程鏈；見[實際證據](../../verification/F007-implementation.md)。只關閉進入工程實現的前置；臺賬中擴大組合和專業條件仍未驗收。 |
| OQ-002 | 工程實施前置核對：應用身份/審計/狀態及 F006 交接字段尚未在工程落實 | 否 | 與 F001/F006 固定決定、版本、錯誤和事務接口後綁定檢查 | 已解決 | 2026-10-14 已固定本地依賴並運行對應工程鏈；見[實際證據](../../verification/F007-implementation.md)。只關閉進入工程實現的前置；臺賬中擴大組合和專業條件仍未驗收。 |
| OQ-003 | 真實簽署方式、生產留存與關鍵崗位責任接受未配置 | 否 | 業務/信息科責任人在生產啟用前落實 PRD OQ-006 | 待確認 | 不阻塞局部離線驗證設計，缺失時不能使用真實生產簽字能力 |

阻塞指實施就緒，不阻塞本次文檔交付。所有正式寫入與恢復條件都有明確檢查，不用 Plan 狀態替代實際測試。

## 回退策略

暫停新的圖執行時保留業務待辦和歷史決定；舊狀態僅在當前授權/版本允許時繼續。新圖/Schema 不兼容則受控停止或顯式遷移，不能重放舊寫入。已提交決定不因回滾 checkpoint 被抹除，重複恢復先對賬。禁止清空任務庫、原件或簽字歷史恢復演示；靜態原型繼續獨立使用。

## 驗收映射

檢查尚無工程入口，eval 的 check_ref 均為 null。每項只執行最窄相關方法，已有效的結果不重複獲取；業務結果與結構校驗分別記錄。

| AC | Eval | 實現結果 | 最窄驗證方法 | 預期證據 |
| --- | --- | --- | --- | --- |
| AC-F007-001 | EV-F007-001 | 實現質控複核與有理由終態 | 複核分支及責任記錄測試（入口待綁定） | 確認/駁回前後狀態、待辦和審計引用 |
| AC-F007-002 | EV-F007-002 | 交付醫生整改與新版本接入 | 新版本提交與權限/衝突測試（入口待綁定） | 父子版本、原件不變與拒絕記錄 |
| AC-F007-003 | EV-F007-003 | 實現申訴與專業爭議出口 | 申訴三類出口與高風險未決測試（入口待綁定） | 原判/裁決關係、責任節點與阻斷 |
| AC-F007-004 | EV-F007-004 | 貫通重核、退回與人工確認 | 再核驗結果與人工門檻合同測試（入口待綁定） | F006 運行引用、退回/阻斷與確認記錄 |
| AC-F007-005 | EV-F007-005 | 實現範圍固定的分崗位簽字 | 雙崗位和缺前置簽字測試（入口待綁定） | 獨立崗位/版本記錄及拒絕結果 |
| AC-F007-006 |EV-F007-006、EV-F007-012 | 維護簽字歷史與版本失效 | 版本更替與歷史回放測試（入口待綁定） | 新舊鏈路、簽字綁定與當前受限狀態 |
| AC-F007-007 | EV-F007-007 | 實現責任接續與期限變更 | 責任/期限轉換與待辦投影測試（入口待綁定） | 改派/延期記錄、逾期反饋和工作臺狀態 |
| AC-F007-008 |EV-F007-008、EV-F007-012 | 實現業務冪等與版本併發控制 | 重複/併發與提交後故障注入測試（入口待綁定） | 決定 ID、任務版本、審計與結果去重 |
| AC-F007-009 |EV-F007-009、EV-F007-012 | 實現持久人工等待與安全恢復 | 跨進程暫停/恢復與提交邊界故障測試（入口待綁定） | 業務決定與執行遊標對照、拒絕及去重結果 |
| AC-F007-010 | EV-F007-010 | 交付可連續處理的崗位界面 | 一次多崗位代表旅程瀏覽器走查（入口待綁定） | 雙視口、前後狀態與返回上下文操作記錄 |
| AC-F007-011 |EV-F007-011、EV-F007-012 | 驗證業務授權與審計不可繞過 | 授權/審計故障與模型越權負例測試（入口待綁定） | 真實主體、拒絕/回滾與未外發探針 |
