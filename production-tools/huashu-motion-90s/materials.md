# 素材與聲音來源

- Logo：D:/CODEX/MedicalQualityCase-Windows/MedicalQuality/frontend/public/brand/ff-logo.png，沿用原圖與比例。
- 產品色彩：同工程 frontend/src/styles.css 的背景 #f5f6f8、文字 #20252d、灰 #687487、產品藍 #087df1、線條 #e9ecf0 與白底；小字使用較深的 #596577、#0666c8 提高對比。
- 八條規則：同工程 backend/fixtures/prototype-synthetic.json，保留在 materials/rules.json；畫面名稱取自實際定義。
- 原文定位風格參考：materials/case-detail.png，來自既有工程合成病例截圖；這支片不把圖解冒充操作錄影。
- 過敏記載與流程：本聊天選定的 90 秒腳本；為合成教學故事，無真實患者資料。
- 字型：Noto Sans TC Variable，既有本機資產，SIL OFL 見 assets/NotoSansTC-OFL.txt。
- 程式：本機 huashu-motion 0.3.1，GSAP＋om runtime；工具源碼未因本片而修改。
- 旁白：實際呼叫 Gemini 3.8 Flash-Lite TTS／Kore，七段 WAV；回執與 SHA256 在 assets/narration-full/*-receipt.json。僅送出教學旁白。
- 音樂與音效：huashu-motion 本機合成的 pulse 配樂與 53 個低音量落點音，原文閱讀段降低能量，人聲下自動 duck。
- 無外部音樂取樣，無人物照片或生成醫療影像。
