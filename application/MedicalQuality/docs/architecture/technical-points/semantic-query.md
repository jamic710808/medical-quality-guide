# 病例語義與受控查詢技術點

承接[技術決定 KD-02/03](../knowledge-retrieval.md)，主責 F004。下面是擬實現合同，不是已經生成的患者關係或可直接運行的查詢服務。

<a id="tp-01"></a>
## TP-01 · 精確範圍與只讀結構化查詢

### 已核對的源結構

2026-10-13 通過只讀 PRAGMA 檢查以下四表，沒有讀取業務記錄。四表聲明的主鍵均為內部 `_source_record_number`，業務字段為 TEXT，未聲明外鍵。

| 來源表 | 相關字段 | 可提出的業務映射 | 尚需實際核查 |
| --- | --- | --- | --- |
| mimic_iv_demo__patients | subject_id、anchor_age、anchor_year | MIMIC 命名空間的患者標識與脫敏錨定信息 | subject_id 唯一/缺失；不能把 anchor_age 直接當任意就診時的精確年齡 |
| mimic_iv_demo__admissions | subject_id、hadm_id、admittime、dischtime | 住院標識及源時間 | hadm_id 唯一性、患者關聯和時間含義；脫敏偏移不還原真實日曆 |
| mimic_iv_demo__labevents | labevent_id、subject_id、hadm_id、itemid、charttime、storetime、value、valuenum、valueuom | 檢驗事件與原值/單位 | 重複、缺少 hadm_id、兩種時間的語義、單位/數值解析 |
| mimic_iv_demo__d_labitems | itemid、label、fluid、category | 檢驗項目字典候選 | itemid 關聯覆蓋、標籤同義與語境；列名不證明實際數據庫外鍵 |

上述映射只是核對入口，激活前查樣本與數據字典，不先發布已確認語義。eICU、CMQCIC、PMC、Open-i 的標識各自命名空間；不因相同 ID 或相似描述合併。ECG 的 subject_id 只支持有來源的患者級關聯，不補造住院事件歸屬。

### 查詢執行

擬由 `clinical_context/query_catalog.py` 定義固定 operation（如 `list_cases`、`get_case_context`、`get_encounter_evidence`），關聯允許表/列、輸入類型、結果粒度與必要過濾。不是面向用戶的任意自然語言 SQL 產品。

1. 消費 F001 的有效授權及 F002/F003 的來源版本；將來源命名空間、允許病例集合、用途與版本作為服務器端條件，不能由前端覆蓋。
2. 來源連接使用只讀 URI 與 query_only；參數值綁定，表/列/排序項僅來自固定白名單，不用字符串拼接用戶內容。不啟用可加載擴展或任意 ATTACH。
3. 通過 SQLite authorizer 拒絕不需要的操作，並以 progress handler/受控讀取限制時間與結果規模。只讀模式不代替行範圍過濾，SELECT 前綴也不構成安全查詢驗證。
4. 身份/粒度校驗先於 JOIN。只在已核對關係上連接；缺失關聯保留單列，不能內連接後靜默丟失病例/事件。
5. 列表、總數、分頁共用授權篩選與一致快照；穩定排序以業務允許字段加穩定身份，不依賴偶然讀行順序。統計按實際業務對象去重，不把檢驗事件行數當患者數。
6. 只表達來源時間/相對時間；時區、偏移或單位不足時標 unknown。數值顯式轉換並記錄失敗，不把空白、未知與 0 合併。

工作臺的任務狀態/風險/責任由 F006/F007 提供到應用讀模型；公開原庫沒有的真實待辦、簽字記錄不能推導生成。F007 尚無實現時固定夾具只能驗證界面合同，不能作為真實業務操作證據。

### 輸出與驗證

響應固定 source/context 版本、允許範圍、實際結果/總數、排序遊標及異常記錄；未知或截斷明確說明。用一人多住院、一住院多事件、無就診檢驗、相同外部編號和權限撤銷夾具對照獨立預期集合。進一步讀取真實行時保留查詢與選擇範圍，不將整庫探測作為每次必要步驟。

<a id="tp-02"></a>
## TP-02 · 必需的醫療質控應用本體與病例上下文

### 設計與表示

按用戶明確要求，一期必須建設並接入限定醫療質控應用本體。採用 OWL 2 EL 定義模塊、術語/映射/值集、數據綁定與 SHACL 形狀；用 ROBOT/ELK 與 RDFLib/pySHACL 離線檢查，發佈後生成 PostgreSQL 只讀語義投影。原值/臨床斷言/實例繼續位於業務層，查詢模板留代碼；原 SQLite 只讀，事務/權限沿 [TP-14](platform-and-clinical-contracts.md#tp-14)。

詳細策略唯一維護於[醫療本體專項](../../data-preparation/governance-cleaning-handoff.md#ontology)：12 項決定、28 個核心概念、18 組關係、14 項約束、14 個 CQ；包括外部詞表許可/中文映射、版本發佈和原生五類 Skill 對象適配。當前是設計，未構建本體包或服務。

| 對象 | 技術必需信息 | 約束 |
| --- | --- | --- |
| 本體/映射版本 | ontology_release、mapping/shape/value_set 版本、概念定義/關係、公理、源綁定/證據、粒度及審核依據 | 沒有有效基線則限制依賴能力；無據定義/映射不激活，舊解釋不漂移 |
| 病例 / 就診 | namespace、原業務標識、context_version、來源關聯與證據 | 業務身份與 `_source_record_number` / EvidenceItem.id 分開 |
| 文書 / 字段 / 事件 | 文書版本、字段路徑、raw_value、normalized_value、轉換說明、原時間/單位、evidence_refs | normalized 值不能覆蓋 raw；無法可靠解析就保留未知 |
| 關係與衝突 | 起止對象、關係含義、支持證據、狀態、受影響範圍 | 已關聯、待核實、未關聯和矛盾分開；相似度只能形成候選 |
| 上下文快照 | 輸入證據 manifest、映射版本、覆蓋/缺口、規則消費所需限制 | F006 固定使用該快照，不從當前“最新”視圖偷偷換輸入 |

XML 報告段落、術語工作簿關係、病例正文各有來源性質。規則/知識不是患者已發生事件；參考答案不是醫學事實。應用本體不運行無證據實體對齊或跨源自動患者歸併。OWL 定義與 SHACL 數據約束分開，專業規則/授權/簽字仍由原責任模塊承擔。

臨床文字還須表達主體/experiencer、否定/不確定/假設、事件與記錄時間、段落和原文 span。家屬、既往、計劃與當前患者不能只按關鍵詞合併；這些字段是有來源的解釋，自動抽取仍為候選。完整細節見 [TP-15](platform-and-clinical-contracts.md#tp-15)，不另建原始證據 Schema。

### 工作臺消費

正式前端按同一查詢結果展示病例、文書和事件詳情；返回保留篩選、排序、位置，記錄不再符合條件時說明退出結果集。F007 的改派/延期/整改狀態以已保存版本為準，不通過修改 F004 本地狀態模擬處理成功。

1280×800 / 1440×1000 下原文與規範化值可對照，未知/衝突/定位失效有文字；原型每頁 6 條與 sessionStorage 不是實現合同。正式前端已選 React/TypeScript/Vite，服務端為 FastAPI；路徑和共享狀態見 [TP-13](platform-and-clinical-contracts.md#tp-13)，實現與用戶驗看尚未執行。

### 版本與驗收

映射修改產生新 context_version 並列出受影響對象，舊上下文用於舊運行回查；不使舊簽字或規則判斷漂移。驗收使用身份衝突、相對時間、單位缺失及跨段矛盾，檢查源回放、未知保留、授權集合、詳情返回和 F007 狀態投影。F004 通過不代表 F006 醫學候選或 F007 簽字通過。
