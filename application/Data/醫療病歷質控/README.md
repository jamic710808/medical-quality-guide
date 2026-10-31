> **學員資料包範圍**：本目錄僅交付數據說明、來源入口和許可文件，不包含原始醫療數據庫、病例正文、影像、波形或參考答案。下文的數量與約 2.24 GiB 存儲量描述的是教師原項目的數據，不是本資料包已附文件。各數據需按發佈方的訪問與使用條件自行獲取；部分來源存在非商業或額外分發限制。

# 醫療病歷質控項目實戰數據

本目錄只保留供後續項目開發直接讀取的數據、數據字典及必要許可。原始下載壓縮包、重複數據庫、網頁快照、下載腳本和過程報告已經移除。當前目錄是這套項目數據的正式入口，請不要再按“可再生成的臨時目錄”刪除。

## 數據總量

| 數據內容 | 實際數量 | 形式與語言 | 性質與用途 |
|---|---:|---|---|
| 醫院結構化數據 | 68張表，6,010,126行 | SQLite、CSV目錄；英文 | 真實脫敏醫院記錄，包含患者、住院、急診、診斷、檢驗、醫囑、護理、照護計劃和生命體徵 |
| 文獻病例患者敘述 | 250,294條，來自210,069篇文獻 | JSONL.GZ；英文 | 從已發表病例報告抽取，適合長文本解析、語義建模、檢索與證據定位；不是醫院直接導出的完整原始病歷 |
| 中文質控病例材料 | 785條任務記錄，644種不同文本 | JSONL.GZ；中文 | 網站病例材料，支持76項醫療質量指標任務；同一文本可能對應不同指標 |
| 中文參考規則 | 98個條目，其中76個有評測樣本 | JSON；中文 | 發佈方規則及加工字段，另22個條目沒有配套樣本 |
| 質控參考標註 | 785條，與病例doc_id關聯 | JSONL；中文 | 發佈方經GPT-4o輔助生成並由人工檢查，獨立於病例原文；不是本項目專家金標準 |
| 胸部影像報告 | 3,955份 | XML；英文 | 真實脫敏影像報告，保留原有段落、標籤和逐份許可 |
| 胸部影像 | 7,470張，7,470個圖文關聯 | PNG、CSV | 按發佈方ID與報告對應；一份報告可能有多張影像 |
| 心電圖 | 659份，覆蓋92名患者 | WFDB：659個DAT＋659個HEA；CSV與RECORDS索引 | 真實12導聯、10秒、500Hz波形；沒有對應的文字診斷報告 |
| 影像術語表 | 1份，3個工作表 | XLSX；英文 | synonyms、mappings、hierarchy；供術語和關係映射研究 |
| 病案首頁規範 | 1份，2016年版本 | PDF；中文 | 病歷質控規則設計的公開參考文件 |

表格行數不是患者數。6,010,126行中有346,030行字典、人員或機構參考記錄，其餘5,664,096行為其他醫院表格記錄。影像、報告、索引和相關文本屬於不同載體，不能相加當作獨立患者數量。

醫院數據的患者和就診規模：

- MIMIC-IV Demo：100名患者、275次住院、140次ICU停留。
- MIMIC-IV-ED Demo：64名患者、222次急診就診；64名均屬於上述100名患者。
- MIMIC-IV-ECG Demo：92名患者，均可與上述100名患者按subject_id關聯。
- eICU Demo：1,841個患者標識、2,520次ICU停留；不與MIMIC合併患者身份。

## 目錄與數據入口

```text
醫療病歷質控/
├── README.md
├── LICENSE-ODbL-1.0.txt
├── 01_醫院結構化數據/
│   ├── 醫院結構化數據.sqlite
│   ├── 表目錄.csv
│   └── 字段目錄.csv
├── 02_病例文本/
│   ├── PMC-Patients.jsonl.gz
│   └── CMQCIC-病例.jsonl.gz
├── 03_質控規則與參考標註/
│   ├── CMQCIC-規則.json
│   ├── CMQCIC-參考標註.jsonl
│   └── 住院病案首頁數據填寫質量規範-2016.pdf
├── 04_影像資料/
│   ├── 報告/                 # 3,955份XML
│   ├── 影像/                 # 7,470張PNG
│   ├── 圖文關聯.csv
│   └── 術語映射.xlsx
└── 05_心電圖/
    ├── files/                # 659組DAT/HEA
    ├── record_list.csv
    └── RECORDS
```

`.gitignore`用於避免大型數據進入普通Git歷史。僅保留一份醫院數據庫；病例文本使用流式JSONL.GZ；影像報告保留原生XML，不再保留同內容的SQLite和JSONL副本。

## 如何直接讀取

### 醫院表格

```python
from pathlib import Path
import sqlite3
root = Path("Data/醫療病歷質控")  # 從外層項目目錄運行
con = sqlite3.connect(root / "01_醫院結構化數據/醫院結構化數據.sqlite")
tables = con.execute("SELECT * FROM table_catalog").fetchall()
admissions = con.execute("SELECT * FROM mimic_iv_demo__admissions LIMIT 5").fetchall()
```

`table_catalog`列出68張業務與參考表。表名前綴區分`mimic_iv_demo__`、`mimic_iv_ed_demo__`、`eicu_crd_demo__`。所有源字段按TEXT保存，編號、前導零、空白及原始日期保持不變；計算前按源字段含義顯式轉換。

`_source_record_number`是原CSV的邏輯數據記錄號，從1開始，不含表頭，不等於帶換行CSV的物理行號。`table_catalog.source_file`現為發佈方原文件下載地址，`source_member`僅記錄原發布包內的歷史路徑，不是本地文件路徑。直接開發使用本地SQLite即可。

### 病例文本與參考標註

```python
import gzip, json
with gzip.open(root / "02_病例文本/CMQCIC-病例.jsonl.gz", "rt", encoding="utf-8") as f:
    record = json.loads(next(f))
    text = record["text"]
    doc_id = record["doc_id"]
```

每行是一條完整JSON記錄，含`doc_id`、`dataset_id`、`language`、`title`、`text`、`text_sha256`、`license`與`metadata`。`source_file`和`source_locator`指向當前保留文件和行號；`origin`保留上游固定版本URL及原記錄位置。PMC的`metadata.source_article_url`可定位來源文獻；其他由發佈方提供的`metadata.file_path`屬於上游元數據，不是本地文件入口。

中文參考標註以`doc_id`關聯病例，規則以`metadata.indicator_key`關聯規則JSON的鍵。應用讀取原文時使用`02_病例文本/`，需要研究參考答案時才讀獨立標註文件，避免將模型輔助解釋誤當作患者原始事實。

### 影像與心電圖

- `圖文關聯.csv`的`report_path`和`image_path`均相對於本目錄，7,470個關聯已核對文件存在。
- XML保留COMPARISON、INDICATION、FINDINGS、IMPRESSION等源段落；實際缺少某段時保持缺失。
- `record_list.csv`的`path`相對於`05_心電圖/`，添加`.hea`或`.dat`即可找到成對文件。可使用支持WFDB的工具讀取；本目錄不包含額外運行環境。
- 心電圖與MIMIC可按`subject_id`關聯，不能僅憑日期接近假定屬於同一住院事件；跨設備時間同步未驗證。

## 數據質量與已知邊界

**本次數據準備沒有調用生成模型，沒有新增虛構患者、診療記錄、整改、申訴或簽字記錄。** “真實來源”依據發佈方說明、文獻來源和格式核對，不代表逐條經過本項目臨床專家審查。

- 醫院表格已核對原發布文件的可用官方校驗和、導入數量及代表字段；已有住院/急診和eICU關鍵表關聯檢查通過。數據庫已通過SQLite完整性檢查。
- 本輪清理逐條核對兩份病例文本中的`text_sha256`，原文不變；只調整封裝和文件定位。影像及心電圖文件保持原內容。659份心電圖對應原包1,321項官方校驗和已通過。
- CMQCIC有141條重複文本任務記錄；Open-i有119條重複報告文本。重複可能來自不同任務或正常報告，均保留，不直接刪成更小的“唯一病例庫”。
- CMQCIC共有2,922項事實標註，其中192項`Original Text`可完整逐字匹配對應文本，另2,730項不能以整個字段逐字匹配。後者可能包含說明、改寫或缺失描述，不能直接當作精確證據片段或憑空生成偏移；這不等於已判定2,730項醫學結論錯誤。
- 中文參考規則和答案含發佈方AI輔助加工；規則版本、適用條件、專業正確性和漏誤報指標仍需項目複核。
- eICU發佈頁面稱演示子集來自20家醫院，當前patient表實際含186個不同hospitalid；這一來源描述差異尚未解釋，原標識保持不變。
- MIMIC日期已經脫敏偏移；eICU不少事件採用相對時間。沒有補造真實日曆日期、缺失值、單位或跨來源患者關係。
- 現有文本以英文為主，未批量翻譯為中文。病歷摘要、影像報告和醫院表格各有覆蓋範圍；原文缺少記錄不自動等於臨床未實施。
- PDF和術語XLSX保留為原生資料，未把全部內容轉換成已批准的自動質控規則。2016年文件的現行效力、地區及客戶適用性尚未凍結，中國規範不直接套用到美國病歷。

這些數據可支持數據接入、結構化、語義建模、規則與證據核查、圖文附件查詢及評測研究。當前沒有真實醫院的質控複核、醫生申訴、整改前後版本、責任簽字、生產賬號或上線驗收記錄；後續實戰需要建立流程並據實產生試用記錄，不能將其冒充現成真實業務閉環。

## 來源、版本與許可

以下內容是數據使用所需的出處和許可，已集中在本README；不再保留來源網頁快照和下載過程材料。

| 數據 | 發佈方與固定版本 | 許可/限制 |
|---|---|---|
| [MIMIC-IV Demo](https://physionet.org/content/mimic-iv-demo/2.2/) | Alistair Johnson等，PhysioNet，2.2 | ODbL-1.0，完整文本見根目錄LICENSE文件 |
| [MIMIC-IV-ED Demo](https://physionet.org/content/mimic-iv-ed-demo/2.2/) | Alistair Johnson等，PhysioNet，2.2 | ODbL-1.0 |
| [MIMIC-IV-ECG Demo](https://physionet.org/content/mimic-iv-ecg-demo/0.1/) | Brian Gow等，PhysioNet，0.1 | ODbL-1.0 |
| [eICU Demo](https://physionet.org/content/eicu-crd-demo/2.0.1/) | Alistair Johnson、Tom Pollard、Omar Badawi、Jesse Raffa，2.0.1 | ODbL-1.0 |
| [PMC-Patients](https://huggingface.co/datasets/zhengyun21/PMC-Patients) | Zhengyun Zhao等，V2；revision `28d8836518f86d4f1e6358ea8ec09977023e5766` | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |
| [CMQCIC](https://huggingface.co/datasets/YuY2001/CMQCIC) | Guangya Yu等；revision `a0b41eda54c68cea3598f93d38da605f2becd885` | [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)；代碼倉庫許可不替代數據許可 |
| [Open-i / Indiana](https://openi-vip.nlm.nih.gov/faq) | Indiana University / NLM，公開XML、PNG與術語表 | XML逐份標註[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)；發佈方另要求組織外使用者返回官方入口申請；術語表單獨使用範圍未另核實 |
| [住院病案首頁數據填寫質量規範](https://www.nhc.gov.cn/yzygj/c100068/201606/2e3b6393fcff4f0095a45a507a975f2f/files/1732862097149_84256.pdf) | 國家衛生健康委網站公開文件，2016年版本 | 保留文號、版本及來源，用作規則設計參考 |

**整理成本地可讀數據沒有改變原許可。** PMC、CMQCIC和Open-i存在非商業或分發限制，收費課程使用及向學員分發的授權仍未確認。相應數據保留用於本地參考研究，不因清理目錄而變成無限制商用數據。

MIMIC-IV-Note、n2c2和CDrugRed未取得，本目錄不包含這些受限正文或來源不明的替代副本。

## 存儲量

清理後的數據和說明約 **2.24 GiB**（不含任何運行環境），較清理前減少約 **3.29 GiB**。

| 目錄 | 大小 |
|---|---:|
| `01_醫院結構化數據` | 605.72 MiB |
| `02_病例文本` | 280.77 MiB |
| `03_質控規則與參考標註` | 2.54 MiB |
| `04_影像資料` | 1,327.10 MiB |
| `05_心電圖` | 75.90 MiB |

數量和質量說明更新於2026-10-10。下載包和重建腳本已移除；以上保留文件就是後續項目輸入，不應作為緩存清理。需要重新獲取時可按上方來源和固定版本訪問發佈方。
