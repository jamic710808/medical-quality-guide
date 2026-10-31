# 醫療項目 Skills 索引

本目錄保存項目本地 Skills 及原生語義運行包。先按任務選擇入口，再讀取對應 `SKILL.md` 和必要資源；安裝文件不代表已經執行工作流、啟動服務或取得業務批准。

## 按任務選擇

| 用途 | 入口 |
| --- | --- |
| 項目骨架 | [build-fde-project](skills/build-fde-project/SKILL.md) |
| 業務理解與追問 | [understand-business](skills/understand-business/SKILL.md) |
| 需求材料準備 | [prepare-requirement-materials](skills/prepare-requirement-materials/SKILL.md) |
| 需求資料整理 | [normalize-project-requirements](skills/normalize-project-requirements/SKILL.md) |
| 需求看板與審閱 | [review-project-requirements](skills/review-project-requirements/SKILL.md) |
| 交互演示 | [playground](skills/playground/SKILL.md) |
| 前端原型 | [build-frontend-prototype](skills/build-frontend-prototype/SKILL.md) |
| 業務數據準備 | [prepare-business-data](skills/prepare-business-data/SKILL.md) |
| 知識檢索選型與構建 | [select-rag-architecture](skills/select-rag-architecture/SKILL.md) |
| Agent 選型與業務編排 | [select-agent-architecture](skills/select-agent-architecture/SKILL.md) |
| 業務數據分類 | [classify-project-data](skills/classify-project-data/SKILL.md) |
| 文檔解析 | [docling](skills/docling/SKILL.md)、[mineru](skills/mineru/SKILL.md)、[paddleocr-doc-parsing](skills/paddleocr-doc-parsing/SKILL.md) |
| 文本信息抽取 | [langextract-usage](skills/langextract-usage/SKILL.md) |
| 本體構建、探索與演化 | [build-ontology](skills/build-ontology/SKILL.md)、[explore-ontology](skills/explore-ontology/SKILL.md)、[evolve-ontology](skills/evolve-ontology/SKILL.md) |
| 產品需求與規格 | [product-prd](skills/product-prd/SKILL.md)、[product-spec](skills/product-spec/SKILL.md) |
| 功能拆分與計劃 | [feature-spec-planning](skills/feature-spec-planning/SKILL.md) |
| 評測與驗證 | [project-evals](skills/project-evals/SKILL.md) |
| 項目維護 | [maintain-project](skills/maintain-project/SKILL.md) |
| 項目交付 | [deliver-project](skills/deliver-project/SKILL.md) |
| 歷史會話回查 | [read-session-context](skills/read-session-context/SKILL.md) |


## 資源與調用邊界

- 每個 Skill 的 references、scripts、assets、agents、templates、examples、測試與許可按來源完整保留；資源路徑依正文約定、引用文件位置或 Skill 根目錄解釋。
- `build-fde-project` 依賴同級 product-prd、product-spec、feature-spec-planning 的模板；`playground` 提及的看板模板與構建腳本屬於同級 review-project-requirements。不要拆散同級結構。
- select-rag-architecture 與 select-agent-architecture 承接檢索/知識表示及執行編排選型。實際醫療技術決定以[產品架構](../MedicalQuality/docs/architecture/architecture.md)及對應 Feature 為準。
- 醫療數據準備以[項目工作流](../MedicalQuality/docs/data-preparation/workflow.md)為入口；保留的[治理參考](skills/prepare-business-data/references/data-governance.md)、[證據契約](skills/prepare-business-data/references/evidence-contract.md)、[質量核對](skills/prepare-business-data/references/quality-gates.md)和[建模交接](skills/prepare-business-data/references/modeling-handoff.md)繼續適用。
- 來源版 `inspect_inputs.py` 是通用初篩，不支持舊 `--no-preview` 或此前的醫療格式擴展，可能輸出正文預覽。使用項目工作流中的當前命令與合成示例；正式醫療資料按來源角色和授權範圍交給產品讀取適配器。
- 原生本體運行包位於 `vendor/evoontology/`；項目 stdio 調用、來源、許可及恢復見[安裝說明](evoontology-installation.md)。Skill 可發現與當前會話已暴露 MCP 工具分別核對。
- maintain-project 中的訂單測試及補丁屬於來源歷史材料，不作為醫療項目運行或驗收入口。正式檢查採用本項目[運行手冊](../MedicalQuality/docs/development-runbook.md)與受影響工程中的用例。
- 文件來源、初始化資源核對及本地保留項見[同步記錄](../MedicalQuality/docs/verification/agents-sync.md)。項目業務約定與需求資料入口由[工作區 AGENTS.md](../AGENTS.md)管理。
