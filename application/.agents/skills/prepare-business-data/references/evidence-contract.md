# EvidenceItem 與統一交付契約

## 定位

這是本 Skill 的默認技術封裝，承接項目已有的“身份、來源、位置、內容類型、原值、解析過程、質量狀態”語義。優先映射已有項目合同；不憑此文件變更產品範圍、醫學規則或建模模式。

機器結構見 [evidence-item.schema.json](evidence-item.schema.json)，使用 JSON Schema 2020-12；[evidence-examples.jsonl](evidence-examples.jsonl)是合成的契約示例，不是實際數據解析成果。結構示例不能替代真實來源驗證。

## 對象與字段

| 字段 | 約定 |
| --- | --- |
| schema_version | 當前 1.0；不兼容語義變化須明示，不能只改版本號遷移舊對象 |
| id / kind | 穩定對象身份；schema、record、table、text、image、waveform 六種內容分型 |
| source | 來源身份、URI、版本、格式、data_role、data_kind 與授權用途；文件宜記錄內容 SHA-256，數據庫另保留實際快照/一致性條件 |
| locator | 按原格式定位，不將所有格式都表示成“第幾頁”；見下表 |
| content | 文本用 text；記錄保留原 JSON 值 value；結構用 columns；表格用 rows 或 payload_ref；圖像/波形用 metadata。允許保留原生特有字段，規範化值放 normalized 並說明轉換 |
| native_refs | 原始或原生解析結果關聯；圖像/波形必需，WFDB 須能回到頭與信號兩部分 |
| provenance | 工具、版本、運行身份、必要配置與實際變換；配置必須去除憑據 |
| quality | success / partial / failed / blocked，問題代碼，建模訪問邊界；partial 明確 usable_scope |

成功只說明當前聲明的解析/讀取範圍成立，不證明臨床正確性。規則文件的讀取成功不代表規則已通過專業審核。只讀頭元數據的波形對象需顯式記錄 values_decoded=false，不能把元數據成功當作信號解碼完成。

## 位置語義

| locator.type | 必需表達 |
| --- | --- |
| database | 表；記錄/字段使用已聲明非空 row_key + declared_key，或快照內 row_ordinal + query_id + snapshot。不同快照的序號不能用於身份合併 |
| csv | record_number 從 1 開始，指源文件邏輯記錄（包含首行）；表頭身份另行說明。帶換行字段不能用物理行號代替 |
| json | RFC 6901 風格 pointer；JSONL/GZ 另保留解壓後的邏輯 record_number，原壓縮來源版本不丟失 |
| xml | 帶位置的 XPath 與需要的命名空間映射；mixed content 與段落屬性保留 |
| text | 從 1 開始的包含式行範圍；可選字符範圍按左閉右開、從 0 開始，且綁定該文字版本 |
| pdf | 頁碼從 1 開始；bbox 若有，按 [x_min,y_min,x_max,y_max] 並聲明單位、原點與頁面尺寸。從不同解析器適配時顯式轉化原生座標，不猜座標 |
| spreadsheet | 工作表名及 A1 單元格範圍；公式、緩存、合併關係和原單元格類型保持可查 |
| image | 原圖幀號，從 0 開始；尺寸/位深/色彩在 metadata；如經旋轉縮放需保留回投變換 |
| waveform | 記錄、通道、採樣率及左閉右開的採樣區間；單位、增益/基線、數字/物理模式在 metadata |
| unavailable | 不能可靠定位時寫原因；不得標 success 或直接進入可用建模輸入 |

PDF 原生 y 軸方向、頁號起點各不相同。只有實際得到座標才填 bbox；頁級定位可以保留，但不得冒充行級精確定位。清洗後文字偏移和原文偏移需要轉換映射。

## 來源角色與建模訪問

source.data_role 區分 business_evidence、schema_reference、rule_reference、terminology、reference_label、validation、heldout。source.data_kind 區分公開、公開脫敏、文獻、合成、生產和未知來源；不能因為標準化改變性質。

quality.modeling_access 為 allowed、evaluator_only 或 restricted：
- 參考標註、驗證/留出數據只能為 evaluator_only 或 restricted，不能進入建模構造輸入。
- failed、blocked 及 unavailable 定位為 restricted。
- partial 除問題原因外還要說明哪些部分可用；即便 allowed，也只能消費已聲明可用範圍。
- allowed 是在已有授權和數據分工下的交接標記，不授予新的訪問、外發、臨床使用或跨患者關聯權限。

## 文件組織與大數據

實際處理時可在來源之外維護一份運行交付：
- 來源清單：各來源版本/用途/授權、輸入範圍、成功/失敗/未讀覆蓋和重建依據。
- evidence.jsonl 或按來源分片：共同封裝；數據庫大表/數值數組通過 payload_ref 指向類型化產物，避免逐行都變成長篇自然語言。
- native/ 與 assets/：確實需要的解析器結構結果和派生資源；原始來源優先引用，不再複製一套大庫。
- 未通過項與路線評測結果：不能混在可用結果中不加標記。
- 建模交接說明：見 [modeling-handoff.md](modeling-handoff.md)。

這是產物職責，不要求選型任務預先創建全部目錄。派生大文件、模型、緩存和運行快照先加入忽略規則；清理前確認仍有來源、版本和重建路徑。保留跨文件引用和分片範圍，不把部分分片的成功稱為全庫成功。

## 校驗與質量的關係

validate_evidence.py 校驗對象結構、單項位置語義、評測隔離及本次受限批次內 ID 重複。它不讀取引用、不證明 source.version 對應實際內容，也不檢查關鍵字/圖文/通道是否被正確識別。多分片需另核對跨片身份及 manifest 覆蓋；來源定位重放與內容對照是 [quality-gates.md](quality-gates.md)的獨立職責。
