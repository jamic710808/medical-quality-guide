# 三版影片互動頁維護來源

根目錄 index.html 為可離線開啟的單一 HTML，內嵌 90 秒精華版、一般介面路演與手繪故事版，以及圖片／腳本。

共 32 個章節，三版各自記住播放位置。勾選播放跟隨後，依各版實際時間軸切換相關演示步驟；90 秒短片未涵蓋的四項功能停用跳轉。原架構、證據、熱點與放大互動仍保留。

tour-data.json 保存影片、步驟與各版同步映射。驗證摘要見 integration-validation.json。build_guide.py 等為本機維護來源快照，依賴原教材架構底稿、歷史媒體與本機路徑；觀看公開網站不依賴這些路徑。

若僅需要取得內嵌媒體，可執行：

```sh
python production-tools/interactive-guide-three-films/extract_assets.py --html index.html --out extracted-assets
```

這會讀取已公開單檔中的三支影片與圖片，不讀取任何憑據或存取外部服務。
