# PRD 至 Feature 拆分完成記錄

日期：2026-10-13。

## 本輪範圍與停止點

用戶明確要求按“原型與客戶討論、收斂反饋 → PRD → Product Spec → Feature 拆分 → 詳細設計與計劃 → 開發與驗證”的流程，直接完成到 Feature 拆分後停止。

使用項目內 product-prd、product-spec、feature-spec-planning Skills，沿用需求、業務約定和已驗看原型，納入前一輪用戶提出的數據庫結構/記錄、多格式讀取與統一對象能力。本輪委託作為當前一期產品基線與拆分判斷依據，不補造客戶討論、原型驗收、專業審核或生產簽字。

交付入口：

- [PRD](../PRD.md)：confirmed；19 項功能需求、6 項非功能要求、26 條 Given/When/Then 驗收。
- [Product Spec](../specs/product-spec.md)：confirmed；13 條 PSC，定義統一對象、狀態、不變量、責任與組合門檻。
- [Feature Map](../specs/feature-map.md)：confirmed；F001～F010 均為 planned，固定邊界、輸入輸出、消費方、獨立驗收與依賴。

未創建 Feature 目錄、spec.md、plan.md、tasks.md、evals 或開發任務。原架構文件保持 draft，只同步前置狀態；沒有技術選型、依賴安裝、數據處理或產品代碼修改。

## 內容收斂與審閱

- PRD 保留 DEC-001/002、OQ-001～004 和原有版本歷史，在同一文件補齊產品合同；新增正式穩定 ID，不改寫背景資料的 REQ-MED 編號。
- 對象統一限於共同身份、來源、定位、類型和質量狀態，保留數據庫/文檔原生結構；未把 Docling、MinerU 或研究建議寫成已確認實現。
- 原型只提供交互和分支依據。正式權限以實際身份/對象範圍為準；獨立評測要求兩個不同複核身份；簽字與版本、範圍綁定；無法判斷、高風險漏報與未解爭議不能通過准入。
- OQ-003～006 保留樣本適配、專業規則、工具部署、量化指標與目標環境的待辦。已明確這些條件缺失時的限制/阻斷，因此不妨礙本次合同與邊界凍結；必須在各自實施或啟用階段落實，不能由 confirmed 狀態替代。
- F001～F003 優先產出授權、接入和統一證據結果；F004/F005 到 F006 建立有依據的質控；F007/F008 分別承接責任閉環與評測；F009 管理准入，F010 固化複用資產。
- 保留一個閉環維護複核、整改、核驗與簽字一致性，同時把可獨立優化的解析、語義、規則治理和評測分開。運行中的整改反饋不被誤列為建設依賴環。

## 校驗方法與結果

從外層工作區執行：

```bash
<USER_HOME>/.local/bin/python3.12 -B .agents/skills/product-prd/scripts/validate_prd.py MedicalQuality --require-confirmed
<USER_HOME>/.local/bin/python3.12 -B .agents/skills/product-spec/scripts/validate_product_spec.py MedicalQuality --require-confirmed
```

兩項退出狀態均為 0，無 errors 或 warnings。PRD 檢查覆蓋 19 REQ、6 NFR、26 AC；Product Spec 檢查覆蓋全部 25 個需求/NFR 及 26 AC，共 13 PSC。

Feature Map 使用一次只針對 Map 的靜態核對：複用本地 validate_feature_specs.py 的 Feature 行解析、編號規則、開放問題檢查和依賴環檢查函數，並檢查八列非空、合法狀態、主責驗收映射和停止邊界。結果為 10 個合法且唯一的 Feature，25 項 REQ/NFR、13 項 PSC 全覆蓋，26 條 PRD AC 均有唯一主責，依賴無環，Feature 目錄及後續三件套/評測套件均未創建。

現有完整 Feature 校驗器會要求每個 Feature 已有 spec/plan/tasks，沒有僅 Map 的 CLI 選項。因此本輪未調用 require-ready/require-complete，也未為滿足完整校驗器而越界創建後續文件；Map 核對不冒充 Feature 已 ready 或已實現。

本次 9 個新建/修改文件的 139 處本地鏈接全部可定位，顯式錨點無重複；PRD 中引用的 26 處 S01/S02 穩定來源條目均存在。結構檢查不代表業務效果或客戶/醫院驗收通過。
