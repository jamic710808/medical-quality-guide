# 醫療項目 EvoOntology 安裝與調用

本說明隨 2026-10-14 `.agents` 同步引入，並按醫療項目實際目錄與調用方式調整。來源項目的訂單運行目錄、Codex 配置及用戶級信任記錄不適用於此工作區。

## 本地入口

| 內容 | 位置與使用方式 |
| --- | --- |
| 初次構建 | [build-ontology](skills/build-ontology/SKILL.md) |
| 只讀探索 | [explore-ontology](skills/explore-ontology/SKILL.md) |
| 基於使用記錄迭代 | [evolve-ontology](skills/evolve-ontology/SKILL.md) |
| 原生運行包 | `vendor/evoontology/`，包含 Python 包及 macOS/Linux、Windows 啟動腳本 |
| 應用調用 | [native_semantic.py](../MedicalQuality/backend/medical_quality/native_semantic.py) 通過 JSON-RPC stdio 啟動本項目 launcher，以當前 Python 解釋器設置 `EVO_ONTOLOGY_PYTHON` |
| 業務語義工作區 | `MedicalQualityCase/MedicalQuality/.evoontology/`；與安裝目錄分開 |

產品使用項目 Python 環境。模型消費僅開放規定的只讀語義工具；構建、演化與發佈遵循產品授權及版本流程。原生 active 不自動成為正式 SemanticRelease，不能回寫病歷或代簽。當前工程入口、依賴及恢復命令見[運行手冊](../MedicalQuality/docs/development-runbook.md)。

本次沒有創建 `.codex/config.toml`、改變用戶級插件或設置工作區信任；產品的 stdio 調用不依賴來源項目的這些配置。Skill 文件可用與當前會話是否暴露 `evo-semantic` 工具是兩件事，不能僅據文件存在宣稱會話已接入 MCP。

## 來源、許可與恢復

- 上游固定為 `ruc-datalab/EvoOntology` 提交 `f64413dae88d88645b1f2c069cf4e17308ad0f89` 的 `plugins/evoontology-codex/`；來源安裝記錄標註插件版本 `1.1.1+codex.20260928144739`。
- 三個 Skill 的正文、資源及獨立調用名稱採用來源項目現有文件。MIT 許可保留在運行包 `LICENSE` 與各 Skill 的 `UPSTREAM-LICENSE`。
- 本次比較表明運行包與來源相同，未替換運行環境或下載依賴。安裝目錄不存放病例、模型發佈、評測答案或軌跡。
- 需要恢復時，從上述固定上游版本或經比較的來源項目複製對應 Skill、Python 包、啟動腳本及許可，保留完整相對結構；不復制來源項目的虛擬環境、訂單數據或配置。
- 文件隨醫療項目保留。只有在產品不再調用且相關工作流已遷移後，才可移除安裝文件；業務語義與版本歷史按運行手冊另行處理。

## 本輪驗證範圍

同步核對文件內容、權限與配套資源。沒有重新構建本體或執行模型推理；既有工程運行證據見[開發報告](../MedicalQuality/docs/verification/development-report.md)，本次結果見[同步記錄](../MedicalQuality/docs/verification/agents-sync.md)。
