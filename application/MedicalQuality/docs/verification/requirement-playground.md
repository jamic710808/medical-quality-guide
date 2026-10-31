# 一期需求 Playground 驗看記錄

日期：2026-10-13。

## 交付入口與生成依據

- 頁面：[index.html](../02_requirement-playground/index.html)。
- 標準數據：[board-data.json](../02_requirement-playground/board-data.json)，14 組痛點、對應功能與預期效果。
- 項目生成腳本：[build.py](../02_requirement-playground/build.py)，使用 Python 標準庫，複用外層本地 review-project-requirements Skill 的模板與數據校驗。
- FF Logo 使用項目已有 PNG 原始字節，並在生成時按工程約定檢查 SHA-256。Logo、原模板裝飾圖像、CSS 與閱讀控件均內嵌；項目腳本添加署名和窄屏閱讀控件換行修正，未改寫共享 Skill。

從外層工作區運行：

```bash
<USER_HOME>/.local/bin/python3.12 -B MedicalQuality/docs/02_requirement-playground/build.py
<USER_HOME>/.local/bin/python3.12 -B -u -m http.server 5198 --bind 127.0.0.1 --directory MedicalQualityCase/MedicalQuality/docs/02_requirement-playground
```

生成退出狀態為 0。本地預覽為 http://127.0.0.1:5198/，僅服務看板所在目錄；服務器保留供當前驗看，也可停止後直接打開 HTML 文件。

## 頁面與交互驗證

內置 Browser 和 Node REPL 均報告運行時啟動失敗（No such file or directory）。因此使用已有 npm 緩存中的 Playwright 與臨時下載的獨立 Chrome Headless Shell 155.0.8059.12 驗證；沒有調用系統 Chrome 或使用用戶登錄資料。

- 桌面 1440×1000：保留淺色三列、紅/綠/藍層級、編號、圖標、玻璃卡片與綠植；逐行三個欄目同高對齊，頁面無橫向溢出。截圖已人工查看。
- 14 組內容逐項與 JSON 對照：痛點標題/正文、功能標題/動作列表、效果標題/正文均一致。
- 字號“大字”、行距“緊湊”和“恢復默認”實際操作通過；字號比例達到 1.3，恢復後回到標準字號與舒展設置。
- 窄屏 390×844：每組按痛點→功能→效果縱向排列。初查發現閱讀欄橫向溢出，已通過項目生成腳本補充可換行的 flex 規則；修復後標準與大字模式的頁面寬度均為 390，3 個控件可見，42 張內容卡片均無橫向溢出。修復後的首屏、大字模式和頁尾截圖已查看。
- 頁首顯示原始 300×300 FF Logo，完整產品名在右側；頁尾包含業務邊界、效果說明和“@賦範空間 獨家研發”。
- HTTP 預覽返回 200；另以 file:// 離線打開頁面成功，14 組內容與署名可讀。沒有域外資源請求，沒有瀏覽器腳本錯誤。

桌面內容、交互和離線結果在窄屏 CSS 修復後繼續有效；僅針對受影響的窄屏佈局複查，沒有重複無關檢查。

## 文件與清理

HTML 是可再生產物，已加入外層 .gitignore。board-data.json、build.py、本地 Skill 模板和原始 Logo 是生成依據，不直接修改輸出文件。臨時瀏覽器、FFmpeg、測試報告和截圖已清理，未創建項目運行依賴樹或虛擬環境。

頁面僅呈現需求與預期效果，不表示醫療業務功能、專業評測或上線驗收已經完成。
