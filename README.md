# FF－醫療病歷質控｜三版影片互動導覽

- [GitHub Pages](https://jamic710808.github.io/medical-quality-guide/)
- [Vercel 正式網站](https://medical-quality-guide-site.vercel.app)
- [應用程式碼與運行說明](application/MedicalQuality/README.md)
- [Windows 啟動與驗證說明](application/MedicalQuality/Windows啟動與驗證說明.md)
- [架構設計](application/MedicalQuality/docs/architecture/architecture.md)
- [90 秒影片來源與分鏡](production-tools/huashu-motion-90s/)
- [三版互動頁同步與驗證來源](production-tools/interactive-guide-three-films/)
- [原手繪動畫製作來源](production-tools/)

## 2026-10-31 更新

新增《每個疑點，都有來處》90 秒完整版，使用 Kore 女聲、繁體中文字幕與配樂，作為預設入口。保留一般版（137.15 秒）及手繪故事版（217.867 秒）。共 32 個章節，支援影片切換位置記憶、相關演示跳轉、三版自選播放跟隨、原圖熱點放大與鍵盤操作。

單一 index.html 內嵌三支影片與 13 張圖片，可下載後離線開啟。精華版為 1080p，另外兩版為 720p 觀看副本。影片中的病例、文書差異、修訂與簽署均為合成教學示意。

本輪靜態與實際 Chrome 驗證涵蓋 32 章節、128 項前後同步查核、快速切換、10 個截圖熱點步驟與 1440／390／360px 版面；無 JavaScript 錯誤或外部資源依賴。這些是教材網站驗證，未進行新增的完整人工聽音或臨床驗收。

## 原始碼與部署範圍

應用程式碼來自 Windows 工程副本，保留前後端、測試、遷移、依賴鎖檔、配套 Skills 與許可。需求材料使用學員包脫敏副本。未包含憑據、原始醫療資料、資料庫、模型權重、node_modules 或 venv。

GitHub Pages 與 Vercel 提供靜態導覽；Python 後端及資料庫需依運行手冊另行準備，不因網站發布而視為已部署。原始碼同步歷史見 source-sync-manifest.json；本次網站與新增影片來源清單見 site-release-manifest.json。

動畫來源可供檢視；大型可編輯音訊、字型與工具依賴保留於本機完整媒體包。公開單檔內的觀看影片與圖片可使用 extract_assets.py 取出。
