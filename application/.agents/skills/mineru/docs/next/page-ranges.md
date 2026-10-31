# PDF 頁碼範圍規範

狀態: Implemented

CLI 的 `--pages`、Python/Doclib/API 的 `page_range` 和 Gradio 轉換事件的頁碼參數使用同一套語法；Gradio 界面通過雙滑塊生成連續選區。
頁碼錶示 PDF 文件內的頁面順序，從 1 開始，不使用正文印刷頁碼或 PDF page label。
內部 `page_idx` / `page_indices` 仍從 0 開始，抽頁後保留原始頁索引。

## 輸入語法

| 表達式 | 含義 |
|---|---|
| `5` | 第五頁 |
| `1-5` | 第一到第五頁，包含兩端 |
| `1-3,7,10-12` | 多個區間和單頁 |
| `all` | 全部頁面 |
| `r1` | 最後一頁 |
| `r5-r1` | 最後五頁 |
| `3-r1` | 第三頁到最後一頁 |

端點使用 ASCII 正整數（`[1-9][0-9]*`），或小寫 `r` 加該正整數。`all` 只能獨立使用。
允許首尾、逗號和連字符兩側空白，例如 ` 1 - 3 , r1 `。不接受前導零、正負號、中文分隔符、
大寫 `R` / `ALL`、空選項和缺失端點；`1:5` 不是受支持的切片語法。

先以文檔總頁數求值 `rN`，再檢查區間方向；任何倒序區間均報錯。
`5-3`、`r1-r5` 無效；五頁文檔的 `4-r3` 也無效，不能被其他有效選項掩蓋。

有效頁面取區間與文檔的交集，再去重、升序和合並相鄰頁：

- 十頁文檔的 `8-15` 得到 `8-10`。
- 十頁文檔的 `r20-r8` 得到 `1-3`。
- `3,1-3,2` 得到 `1-3`，不會重排或複製頁面。
- 整個表達式選不到頁面時，例如十頁文檔的 `20`，返回 `page_range_invalid`。

## 未指定與全部

空字符串、純空白和接口允許的 `null` 都表示未指定，默認策略由入口選擇：

| 入口 | 未指定 PDF 頁碼時 |
|---|---|
| `mineru parse` / Doclib 解析 | 首次前 10 頁，不足 10 頁則全部 |
| Doclib 內容讀取 | 首次前 10 頁；帶續讀遊標時保留現有窗口策略 |
| Doclib 內容導出 | 導出已有緩存內容 |
| Python `parse` / `parse_async` | 全部 |
| V1 Parse Jobs / `MinerUApiParser` | 全部 |
| `mineru-kit parse` | 全部 |
| Gradio PDF | 默認全部；配置 `--max-pages M` 後選擇前 M 頁，不足則全部 |

顯式 `all` 選擇全部 PDF 頁面；內容讀取/導出仍受實際緩存可用性約束。
非 PDF 的解析限制不變：不能顯式設置頁碼（包括 `all`）；Gradio 對非 PDF 自動清空並隱藏此控件。
Gradio 僅對已上傳的 PDF 顯示選頁控件，所有檔位（包括 Flash）一致；配置的頁數上限也適用於直接調用 Gradio 轉換事件，顯式超限選區報 `page_range_invalid`。

## 輸入與輸出

```bash
mineru parse report.pdf --pages "1-3,7,r2-r1"
mineru parse report.pdf --pages all
mineru-kit parse report.pdf -o result.md --pages "r5-r1"
```

```python
from mineru.parser import parse

result = parse("report.pdf", tier="flash", page_range="1,3,r1")
```

```json
{
  "tier": "flash",
  "files": [{"source": {"type": "file_id", "file_id": "file-example"}, "page_range": "1-3,r1"}],
  "output_formats": ["middle_json"]
}
```

已求值的 API/Doclib 範圍、覆蓋狀態、續讀命令、解析記錄及新緩存文件名使用正整數連字符格式。
例如十頁文檔的 `1-3,r1` 輸出為 `1-3,10`，`5-5` 輸出為 `5`，空覆蓋集合輸出空字符串。
parsing rules 和排隊中的 V1 請求尚未取得總頁數時允許保留 `rN` / `all`；實際解析時再求值。

## 錯誤與實現邊界

統一錯誤碼為 `page_range_invalid`，類型為 `invalid_request_error`。Python 拋出
`InvalidRequestError`；CLI 和 Gradio 保留該錯誤含義。V1 創建任務的語法錯誤返回 HTTP 400，
`error.param` 定位到 `files.<index>.page_range`。總頁數求值錯誤通過異步任務的文件級錯誤返回。

共享實現位於 `mineru/parser/page_range.py`，負責語法、求值、格式化和頁數統計。緩存內部的空範圍
表示空集合，不表示用戶輸入的“未指定”。總頁數未知的緩存內容導出可使用絕對頁碼或全部緩存，
不能用已有緩存的最大頁碼推測 `r1`。

## 歷史結果兼容

舊 Doclib 中使用半角 `~` 的正整數結果範圍（例如 `1~5,8`）可以直接讀取，
並可與新格式結果共存。內容讀取、緩存命中、覆蓋統計和 compaction 共用此兼容規則；
無需因頁碼分隔符變化而重建數據庫、重新解析或更換數據目錄。

讀取舊緩存文件時仍使用數據庫記錄中的原始範圍和原文件名，例如 `1~5_時間戳.json`。
對外返回的結果範圍、新解析記錄及正常 compaction 輸出統一使用連字符，例如 `1-5,8`。
讀取和結果展示不會原地修改舊記錄或重命名舊緩存文件。

兼容僅適用於已求值的歷史結果及元數據，不放寬新請求輸入，也不擴展舊 parsing rules 或舊待處理任務的執行兼容。
新請求仍使用 `1-5`、`r1`、`all`。全角 `～`、負號倒數頁碼 `-1` / `-5~-1` 不受支持；
已求值結果中也不能包含未經展開的 `rN` 或 `all`。
