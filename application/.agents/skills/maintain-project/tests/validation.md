# maintain-project 實測記錄

2026-09-28。結論：在用戶提供的訂單履約原型上，調用獨立 `maintain-project` Skill 後，Agent 完成了新增需求的實現，並主動同步現有設計、使用說明和驗看記錄。本次場景通過；不能據此承諾所有未來變更均不遺漏文檔。

## 測試來源和輸入

用戶授權：基於 `<HISTORICAL_TEST_WORKSPACE>/docs/04_frontend-prototype` 測試“一旦有新的需求更改，對應的文檔也會進行更改”。具體篩選需求由 Agent 構造，不是客戶批准，也沒有應用到原項目。

獨立測試執行者沒有繼承開發會話，只讀取隔離項目的 AGENTS、Skill 和按需定位的現有文件。產品需求輸入如下，沒有額外提醒要修改哪份文檔：

> 在現有訂單列表增加“跟進崗位”篩選，以列表當前顯示的跟進崗位為準。它要能與已有搜索、關注分類、履約口徑和排序組合使用；從訂單詳情返回後保留篩選。保留協同跟進頁已有的崗位篩選及原來的重置行為。按本輪需求完成實現和必要驗證。

隔離副本僅複製 AGENTS、01/02 業務資料、03 設計、04 原型和新 Skill。沒有複製 Raw、TeachingWorkbench、依賴樹或整個產品工程；這些未複製目錄未納入副本內容校驗。瀏覽器自動化按本輪測試授權執行，原交付“不運行瀏覽器自動化”的約定保留為歷史條件。

## 實現與文檔同步

| 文件 | 實際變化 |
| --- | --- |
| `docs/04_frontend-prototype/assets/app.js` | 新增獨立 `orderOwner`，按訂單當前派生崗位完整匹配；組合原有條件，保留返回狀態，納入清除和重置 |
| `docs/04_frontend-prototype/assets/styles.css` | 訂單工具欄允許換行，承接新增篩選控件 |
| `docs/03_prototype-design/design.md` | 更新頁面職責表和當前交互規則，解釋動態崗位、獨立狀態、返回、空結果與重置 |
| `docs/04_frontend-prototype/README.md` | 更新實際操作、組合篩選、恢復方式和檢查範圍 |
| `docs/03_prototype-design/verification.md` | 保留原交付狀態，加入本輪變更來源、真實命令、觀察結果及未驗證項 |
| `.gitignore` | 忽略 `/.codex/maintenance/` 臨時運行記錄 |

AGENTS、HTML 入口、模擬數據和已複製的 01/02 資料無需變化，並驗證未變。沒有新建 PRD/Spec，也沒有修改已有原型生成 Skills。

審閱發現測試文檔把模擬需求寫成“本輪用戶明確的測試需求”，已收窄為“Agent 根據用戶授權構造的測試場景”；實現、測試腳本和業務規則未變。當前正文與實現一致，舊的未驗證記錄按歷史條件保留，沒有僅追加完成標記而保留衝突規則。

## 真實瀏覽器結果

運行時間：2026-09-28 19:25:20–19:25:23（Asia/Shanghai）。複用項目局部 Playwright，獨立 Chromium `151.0.7922.34`，本地隨機端口 `49354`。只訪問本地原型，未安裝依賴，未使用系統 Chrome 用戶配置。

執行命令（在隔離項目根目錄）：

```sh
python3 .agents/skills/maintain-project/scripts/maintenance.py run-check --project . --id order-owner-filter-forward-test --name prototype-browser --input .codex/maintenance/prototype-browser.cjs --input docs/04_frontend-prototype/assets/mock-data.js --input docs/04_frontend-prototype/index.html --input docs/04_frontend-prototype/order.html --input docs/04_frontend-prototype/followups.html -- node .codex/maintenance/prototype-browser.cjs
```

實際輸出末尾：

```text
PASS 47 assertions; browser 151.0.7922.34
Browser and local server stopped.
```

| 驗證路徑 | 結果 |
| --- | --- |
| 默認與組合條件 | 初始18條、每頁8行；交付崗位10條；搜索“模塊”+跟進中+到貨+交付可按客戶或交期排序 |
| 詳情返回與刷新 | 保留搜索、分類、口徑、崗位、排序、頁碼和滾動位置；刷新仍保留崗位 |
| 分頁與清除 | 第2頁結果正確；變更崗位返回第1頁、滾動清零；空結果清除條件並保留原排序 |
| 直接受影響的舊路徑 | 協同頁採購崗位和北辰搜索仍有效，返回保留隊列；兩頁崗位條件互不覆蓋 |
| 動態崗位 | 通過真實辦理按鈕使北辰計劃→倉儲→生產→生產 / 質量；篩選始終按當前展示崗位匹配 |
| 全局重置 | 從訂單和協同兩頁發起，均恢復業務數據與兩頁瀏覽默認值 |
| 桌面呈現 | 1280×800、1440×900的控件邊界檢查通過；實際查看1280初始列表及組合崗位截圖 |

47項斷言全部通過，瀏覽器無腳本異常。業務變化由頁面操作觸發，沒有向 sessionStorage 注入結果。`finish --review` 返回 `pass`；審閱後使用最終版檢查腳本重新讀取同一證據，`check` 返回 `pass`，未重複運行瀏覽器測試。

可追溯指紋：

| 對象 | SHA-256 |
| --- | --- |
| 輸入原型 `app.js` | `e15b4c6f2ffdc850d7c4dd4cd013cb2562f7baff196094f4aae484e33cb38534` |
| 已驗證的變更後 `app.js` | `0f10bfbf49bdb90f0e68a89183ff7d242c6fdb31ba4431b03a6806cf5405af00` |
| 實際瀏覽器腳本 | `b354f945c30081782617766f29f5189e210b62b969aa2de261d8d8a048c426fd` |
| 原始檢查輸出 | `a3745008aa8719557debe4791228123ebd8d1dd950956f3a437acf98af451e99` |

## 確定性檢查與能力邊界

最終檢查腳本的9項單元測試全部通過，涵蓋：非課程目錄適配、漏改應更新文檔、源碼變化使證據過期、授權刪除源碼、保護路徑和應保留文檔、未運行與執行錯誤、真實退出狀態、Hook 會話與目錄範圍及防循環、重複記錄與越界路徑。

其中“代碼檢查成功但應更新文檔未變”的用例返回 `fail`。這是防遺漏檢查；文件變化不等於語義正確，當前 Agent 仍須對照需求審閱內容。

```sh
python3 -B -m unittest discover -s .agents/skills/maintain-project/tests -p 'test_*.py' -v
```

Skill 的格式檢查已通過。前向測試使用創建時的腳本副本；最終版隨後調整了授權源碼刪除、項目外 Hook 事件忽略及未綁定會話恢復的邊界處理，其中前兩項有對應單元斷言，未綁定會話恢復沒有單獨實測。這些變動未改變本次新增篩選流程；最終版已讀取並通過同一原型證據。

本次沒有配置宿主原生 Hooks，也沒有觀察到真實 Stop 事件觸發；已驗證的是腳本協議、隔離前向流程與手動收尾檢查。沒有驗證移動端、其他瀏覽器、完整鍵盤無障礙或所有歷史業務路徑。不把本次測試寫成客戶業務驗收。

## 交付與清理

保留可審閱的文本產物：本記錄、[實際改動補丁](order-prototype-change.patch)、[實際瀏覽器測試腳本](order-prototype.browser.cjs)及[檢查腳本單元測試](test_maintenance.py)。補丁包含測試來源與臨時證據說明，是審閱材料，不作為向原項目自動應用新功能的指令。瀏覽器腳本保留當時使用的 Playwright 絕對路徑；復現時需該現有環境，或將其指向本機已有的兼容安裝。

重現瀏覽器路徑時，在原型隔離副本應用補丁，並將 `order-prototype.browser.cjs` 複製為 `.codex/maintenance/prototype-browser.cjs`，創建 `.codex/maintenance/tmp` 後執行 `node .codex/maintenance/prototype-browser.cjs`。腳本自行啟動和停止隨機端口服務及瀏覽器；不需要保留本次臨時副本。

測試結束後核對原項目22個輸入文件的 SHA-256 與測試前一致。臨時副本、截圖和運行輸出在整理上述文本證據後清理；沒有遺留測試服務器、瀏覽器或依賴安裝。原項目與已有服務未改動。
