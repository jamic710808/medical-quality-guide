# 這一筆，先別急著蓋章

FF - 醫療病歷質控工作檯｜手繪墨線＋淡彩紙感成人敘事動畫。

- 使用者已選畫風 A，腳本已通過。
- 片長 217.867 秒（3 分 37.9 秒），1920×1080，30fps，6536 幀。
- 旁白：實際呼叫 Gemini 3.8 Flash TTS / Kore，12 段。
- 音樂／提示音：本片程式原創，依旁白降低配樂音量；無外部音樂取樣。
- `review.html`：可直接開啟的 MP4 審片頁。
- `index.html`：可編輯 Canvas 工程預覽，需要本機 HTTP 伺服器。
- `script.md`、`storyboard.md`、`style-choice.md`：核准內容與實際分鏡。
- `film.json`：內容設定；`timeline.json`：實際配音鎖定時間軸。
- `subtitles.srt`：與畫面相同的近似句級字幕，非逐字強制對齊。
- `review.md`、`delivery-check.json`：驗收證據與限制。

## 重建

Python 3、Node、FFmpeg/FFprobe 與 Playwright/Chrome；字型與 Logo 已保存在 assets。

```powershell
python -m http.server 8765 --bind 127.0.0.1
# 瀏覽 http://127.0.0.1:8765/index.html
```

已交付音訊可直接重建，不必重新呼叫 Gemini：

```powershell
python tools/pipeline.py timeline . --lock
python tools/pipeline.py mix .
node tools/render.cjs . --preview
node tools/render.cjs . --render
python tools/pipeline.py finish .
```

設置 `PLAYWRIGHT_MODULE`、`CHROME_PATH`、`PYTHON` 為本機實際路徑；或在工程安裝 Playwright。`render.cjs` 保留技能管線的時間軸、資源指紋與亂序重畫檢查，並以 Canvas 原生 PNG 取代螢幕截圖，避免等待畫面合成。

重新配音需在執行環境設置 GEMINI_API_KEY，然後 `python tools/gemini_tts.py .`；不將金鑰寫入工程。工具只送出合成教學旁白，沒有真實病歷。配音更動後重新鎖時、混音及渲染。

`tools/make_soundtrack.py` 需要 NumPy；保留已生成配樂時不需執行。`tools/audio_review.py` 是另用 Gemini 3.8 Flash 盲轉錄的自動檢查，並非 TTS 引擎替代，也不等於人類聽感驗收。

字型：Noto Sans TC，SIL OFL 見 assets/NotoSansTC-OFL.txt。Logo 取自原專案，保持原圖與比例；品牌與作品使用仍依使用者及原專案權利範圍。
