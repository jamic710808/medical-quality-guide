# 第三方來源與維護說明

## Emil 設計心法

- 作者：Emil Kowalski。
- 上游：[emilkowalski/skills](https://github.com/emilkowalski/skills)。
- 原文件：上游項目的 `skills/emil-design-eng/SKILL.md`。
- 本包位置：[emil-design-eng.md](emil-design-eng.md)。
- 取材版本：2026-09-28 從本機 MuYuProjectBuild 項目中正在使用的 `.agents/skills/emil-design-eng/SKILL.md` 原樣複製。只改變承載文件名，沒有重寫原文；未將其替換為上游最新版本。
- 原始文件 SHA-256：`e71de849347050c2c573c1cf24d742d5a13459557ecffa6e562f08006f46b5b7`。
- 此本地副本對應的上游提交未確認，不將查詢時的最新提交冒認為它的來源提交。
- 許可證：MIT；[許可證全文](LICENSE.emil-design-eng.txt)於 2026-09-28 從[上游 LICENSE](https://github.com/emilkowalski/skills/blob/main/LICENSE)獲取，保留作者版權聲明。此第三方聲明適用於附帶的 Emil 原文。

Emil 原文保留其原始語言、示例和表達。工作流新寫的設計記錄、安裝說明與驗證說明均使用簡體中文。

## 如何使用這份心法

主 Skill 先明確溝通目標，按應用產品設計方法決定頁面空間與交互，再讀取 Emil，將適用原則落實為組件反饋、動效和細節。產品流程與呈現意圖來自需求和本輪溝通，不由通用視覺心法代替。任務已明確時直接應用相關章節，不必執行原文中面向無具體請求場景的初始問候。

原文中的代碼示例不是已經驗證過的當前組件庫 API。實現時以當前工程的依賴版本、官方文檔與組件源碼為準；業務事實和用戶約束優先於通用設計建議。

## 應用產品設計方法的整合來源

2026-09-28，依據用戶對原型頁面的反饋，審閱本機全局 `~/.claude/skills/` 中以下材料，將適合當前體驗原型的思想重新組織為 [product-design.md](product-design.md)。這是本工作流的適配指引，不是這些 Skill 的原文副本或完整執行流程；下列路徑僅用於來源定位，分發後無需訪問它們。

| 全局材料 | 本輪採用的設計依據 |
| --- | --- |
| `product-form-from-backend/SKILL.md` 的信息架構與用戶路徑部分 | 從使用者、工作對象和實際任務組織入口，明確開始、處理和業務結果 |
| `frontend-design-layer/SKILL.md`、`templates/design-brief.md`、`templates/craft-checklist.md` | 將佈局作為獨立設計決定，說明空間主次、常駐內容與交互模型，按任務確定信息密度 |
| `gstack/plan-design-review/sections/review-sections.md` 的信息架構與 App UI 部分 | 區分應用與營銷頁面，圍繞主工作區、導航和輔助上下文組織頁面，檢查卡片堆疊是否取代了實際佈局 |
| `gstack/design-review/SKILL.md` 的頁面定位與設計檢查部分 | 檢查所在位置、搜索與操作入口，以及篩選、頁籤、分頁等工作狀態 |

列表規模與分頁選擇、滾動分工、返回位置和下一步承接的要求，結合當前實際反饋補充為可執行的原型設計與驗看方法，不冒稱均為上述來源的原文規則。

整合保留當前整體原型範圍、HTML 默認路線和用戶指定的驗看方式。沒有引入來源流程中的完整後端契約、真實網絡模擬、全量管理後臺、固定數量的競品研究、強制雙主題、逐項審批或特定動效依賴；也不要求安裝或運行這些全局 Skill。Emil 原文及其許可證保持不變。

## 更新與分發

分享時複製完整的 `build-frontend-prototype/` 目錄，並保留此說明和許可證，不依賴任何本機絕對路徑或外部符號鏈接。

需要更新 Emil 內容時，先比較上游變化與本包版本，明確採用版本後替換引用文件並更新校驗值和來源。不要在安裝時自動追蹤上游主分支。工作流本身與第三方心法分開維護，避免把客戶需求寫入通用心法。
