# 基礎架構研究與一致性核對

日期：2026-10-13。完成用戶明確描述的第一項：基於現有數據、業務需求、論文和通用方案，詳細確定基礎架構及技術承接。第二項內容尚未收到，未自行補造另一個任務。

## 交付與結論

- [總體架構](../architecture/architecture.md)：FA-01～12，模塊化單體、React/TypeScript/Vite、FastAPI、PostgreSQL/pgvector、獨立 Worker、LangGraph 與域內模型邊界；數據/進程流、選型原因、實施順序和仍需驗證的條件明確。
- [TP-13～16](../architecture/technical-points/platform-and-clinical-contracts.md)：內部接口、持久任務租約/併發、數據庫/權限/事務、臨床斷言/完整性、證據包、評測與運維。
- [研究依據](../research/medical-quality-architecture-evidence.md)：20 項代表性論文/研究及成熟項目，區分原研究任務、本項目推論和不能外推的效果；訪問/閱讀深度限制如實保留。
- 已同步當前檢索/Agent 決定、直接受影響 TP-01～12 和 F003～F007 Plan；F004/F006 的既有 AC 細化主體/否定/條件與截斷，編號和產品範圍不變。

正式業務存儲從此前的輕量應用 SQLite/文件向量/SQLite saver 設想收斂到 PostgreSQL/pgvector/PG checkpoint；原始 SQLite 輸入仍只讀，沒有實際庫遷移或雙後端實現。Qwen 4B 明確為工程基線，不冒稱臨床模型已定型。

## 觀察範圍

複用已核對的數據 README、資料目錄及此前四表結構觀察，未重掃大數據或讀取參考標註/驗證答案。論文檢索與官方工程文檔用於設計，沒有運行論文代碼或製造指標。

本輪只讀環境發現 macOS arm64、默認 Python 3.9.6，PATH 存在 Docker、psql（Postgres.app 17 目錄）、Node/npm/uv；當前磁盤約餘 8.26 GiB。未連接數據庫、查詢 Docker daemon、讀取憑據或測試模型。解釋器/命令存在不證明服務已準備好。

## 結構與追溯驗證

下列結構校驗通過，無錯誤/警告；未執行行為用例：

```bash
python3 -B .agents/skills/product-prd/scripts/validate_prd.py MedicalQuality --require-confirmed
python3 -B .agents/skills/product-spec/scripts/validate_product_spec.py MedicalQuality --require-confirmed
python3 -B .agents/skills/feature-spec-planning/scripts/validate_feature_specs.py MedicalQuality --feature F003 --feature F004 --feature F005 --feature F006 --feature F007
python3 -B .agents/skills/project-evals/scripts/validate_evals.py MedicalQuality --suite evals/F003.json --suite evals/F004.json --suite evals/F005.json --suite evals/F006.json --suite evals/F007.json --suite evals/product.json
```

產品仍為 19 REQ、6 NFR、26 PRD AC、13 PSC、10 個 planned Feature。局部用例仍 48 條；product 新增正式事務/租約與臨床語境/覆蓋兩條，當前 8 條，共 56 條。全部 check_ref=null，behavior=not_evaluated。

當次核對 23 份直接相關文檔的 248 處本地引用、38 處技術錨點，無失效；研究條目編號 L01～20 完整。本記錄新增鏈接另行核對。對存儲/框架的當前陳述進行了直接一致性檢查，歷史驗證記錄仍保留當時事實，未改寫成新架構已跑通。

## 完成與停止邊界

架構設計方向明確，整體及各 Plan 保持 draft，因為樣本適配、實際接口/依賴、臨床模型資格、併發恢復與生產責任配置仍需驗證。沒有新增 Feature、安裝依賴、啟動服務、下載模型、運行 RAG/Agent、處理醫療正文或改動原型。

選型、格式校驗、真實軟件運行、專業評測和生產放權分別成立；本輪完成前兩類設計交付，不將其表述為後幾類通過。
