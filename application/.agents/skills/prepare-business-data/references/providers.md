# 工具與官方 Skill 路由

用於縮小候選範圍，不是質量排名。官方 Skills 以同級目錄引入；複製到其他環境時帶上所需目錄或確認已有相應 Skill。固定提交見 [來源記錄](upstream-skills.json)。

## 已集成的官方 Skills

| 能力 | 入口與來源 | 選擇依據與邊界 |
| --- | --- | --- |
| Docling | [本地 Skill](../../docling/SKILL.md) · [官方倉庫](https://github.com/docling-project/docling) | 統一文檔對象、表格/圖片結構與來源位置；適合 PDF、Office、HTML 等。CLI/SDK 可本地運行，也有服務路線；核查所選管線依賴與模型。JSON 保留文檔模型，Markdown 供閱讀，不能承諾解析內容與原件完全一致。 |
| MinerU | [本地 Skill](../../mineru/SKILL.md) · [官方倉庫](https://github.com/opendatalab/MinerU) | 複雜 PDF、掃描件候選。引入的 Skill 面向 4.x，支持頁/塊定位；默認本地，遠程另選，不同質量檔位資源不同。不套用舊版 CLI，也不將預覽檔冒充正式解析質量。 |
| PaddleOCR 文檔解析 | [本地 Skill](../../paddleocr-doc-parsing/SKILL.md) · [官方說明](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/integrations/skills.en.md) | 此 Skill 使用 `paddleocr api` 和令牌，默認官方在線服務。本地 PP-StructureV3/PaddleOCR-VL 是另一條部署路線，按[本地文檔](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/quick_start.md)核查，不把 API Skill 稱為離線實現。 |
| LangExtract | [本地 Skill](../../langextract-usage/SKILL.md) · [官方倉庫](https://github.com/google/langextract) | 文本到候選實體、屬性與關係的可選後續環節；支持本地 Ollama 和雲端模型。示例應貼近業務，`char_interval` 可能缺失，有原文定位也不證明關係正確。不替代 PDF 解析或業務確認。 |

官方 Skill 原文與相對資源保留；描述可能較寬，跨工具選型時先決定路線再加載具體 Skill。不同時讀全部手冊，不為了一個 Skill 安裝全部工具。

## 按材料分流

| 材料特點 | 優先考慮 | 需核對 |
| --- | --- | --- |
| 文本 PDF、表格和圖文混排 | Docling 或 MinerU；已有合適解析器可先取樣 | 閱讀順序、跨頁表格、表頭/單元格、圖注、頁碼/座標，以實際樣本決定 |
| 掃描 PDF、文檔照片 | MinerU、Docling OCR/VLM 管線或 PaddleOCR | 旋轉、透視、模糊、文字和表格；手寫、印章、低清照片單獨驗證，不承諾效果 |
| CSV/TSV、規則表格 | 已有 pandas 或 Polars；按需加 Pandera | 編碼、記錄邊界、前導零、類型、空值和約束；不要求已有 pandas 項目遷移 |
| XLSX/XLS | 數據讀取用適配表格庫；需版面/嵌圖時再選文檔解析器 | 工作表、合併單元格、隱藏內容、公式和緩存值；不執行宏，不將緩存值說成已重算 |
| Markdown/TXT | 直接讀取；Markdown 按需用 markdown-it-py | 標題/列表/代碼/鏈接、段落、說話人和時間；只按依據規範化編碼、換行和空白 |
| JSON/JSONL/XML | 對應結構解析器與字段校驗 | 嵌套、類型、缺失/null、記錄邊界；保留 JSON 路徑等定位，避免先展平丟失關係 |
| DOCX/PPTX/HTML | Docling 等支持該格式的工具；簡單內容可直接讀取 | 標題、表格、頁/幻燈片、備註、鏈接與嵌圖；HTML 作為數據，不執行腳本 |
| 其他格式、壓縮包、API 來源 | 明確用途後補查對應能力 | 不假裝覆蓋所有格式；壓縮包先看目錄和體積，不自動遞歸解壓。接口文檔/導出文件不等於在線調用授權 |

圖片分離與圖表/流程圖的含義理解是兩件事。需要視覺模型讀出關係時，另評估準確性、運行位置與費用，並保留圖片證據。

## 可按需組合的組件

- [Polars](https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html)：支持按字符串讀取或指定類型。樣本推斷不能替代全量驗證。
- [Pandera](https://pandera.readthedocs.io/en/stable/)：表達已明確的字段/類型/數據約束，報告錯誤；不猜業務規則，不默認刪異常行。
- [OpenRefine](https://openrefine.org/docs/manual/cellediting)：人工檢查名稱聚類、別名和批量轉換。基礎功能可本地運行；外部 reconciliation 服務有獨立外發邊界，相似不等於實體相同。
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py)：按 Markdown 語法處理；TXT 不必經過文檔模型。

以上組件是候選，不代表已安裝或具有官方 Skill。庫、模型與 Skill 的可用性分別核查。

## 環境與成本

本地區分“命令存在”“當前 Python 有包”“模型已下載”“服務可連接”“樣本跑通”，僅報告已驗證的層級。CPU、Apple Silicon/MPS、CUDA 支持取決於版本、模型與引擎。

在線區分官方託管、自建服務和第三方兼容 API；兼容不意味著接口、數據政策或能力完全相同。核查端點、認證、文件/頁數限制。費用和免費額度會變化，調用前查當時官方說明；未知時標明，不以歷史額度承諾免費。

有樣本證據時優先使用；只有文檔聲明時標“候選，待驗證”。重試、併發、多輪抽取、大模型都可能增加費用，不默認最大配置。
