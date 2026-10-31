# Agent 選型 Skill 與 F006/F007 規劃驗證

日期：2026-10-13。完成範圍：讀取用戶指定材料、核對官方資料、創建通用 Agent 選型 Skill、落盤醫療項目編排路線、更新 F006 並展開 F007。沒有實施產品代碼或運行所比較的 Agent。

## 來源與範圍

三份 Excalidraw 的有效文本和鏈接直接從 JSON 讀取，原件未修改，業務文檔不把材料說明當生產驗收：

| 文件 | 有效文本元素數 | 本次讀取內容 SHA-256 |
| --- | ---: | --- |
| 52-選型-LangGraph與AgentScope業務編排.excalidraw | 22 | c683b9fb77576a93d0cab4bf4502811cfae12e61b01066bf46f68d25a384c0d2 |
| 53-選型-Pi與DeepSeekHarness定製運行.excalidraw | 22 | 32eadf0e0687c57302be2e31e259a40d2b3ece60559b92263727273813c3a902 |
| 54-選型-Hermes與Codex應用接入.excalidraw | 23 | a489a84bc896cc9b11c8e4b66b9cb2a3feedb2d5b429de5d7a7fb0b84a35b467 |

原路徑與官方來源集中在[Agent 技術決定](../architecture/agent-runtime.md)。核查了 LangGraph 的恢復/重放、AgentScope 2.0 TeamPipeline 的實驗狀態、Pi 進程與擴展邊界、DeepSeek Harness developer preview、Hermes 記憶與 Codex SDK/app-server 差異。

本機只讀執行 `codex --version` 和 `codex app-server --help`：版本 0.153.4，幫助標識實驗邊界；結合官方文檔，不據此聲稱模型可用、賬號有權限或協議集成已驗證。沒有讀取憑據、配置秘密、會話歷史或啟動 Codex 任務。

## Skill 與獨立前向試用

新增 [select-agent-architecture](../../../.agents/skills/select-agent-architecture/SKILL.md)，6 個文件：入口、界面元數據、業務選擇、官方能力邊界、合同/驗證及決定模板。當前工作區有 24 個 Skills，未創建全局副本或安裝運行依賴。

按 skill-creator 的複雜 Skill 驗證指引安排獨立只讀試用。只提供新 Skill 和合成的採購/研發場景，不提供醫療方案或預期框架；禁止寫文件、安裝、網絡及調用服務。

合成輸入：已有 Python 採購系統和審批/支付數據庫；真人可能兩天後回覆、服務重啟、付款已成功但頁面未更新；付款工具接受 operation_id 並能查詢結果。另有隻讀日誌/代碼建議 CLI。用戶只要求選型，不執行。

實際輸出：

- 採購主選顯式 LangGraph 編排並保留業務數據庫/服務作為事實源，同時指出既有持久狀態機若已滿足要求則無需遷移。
- 區分付款意圖/operation_id、檢查點和已提交業務結果；明確“接受 operation_id”不等於已保證冪等，未知結果先對賬而非換 ID 重付。
- 拒絕多 Agent 投票、Hermes 記憶或 Codex 工具批准代替真人財務簽字。
- 只讀研發 CLI 選擇 Codex 非交互入口，Pi 為需要自有運行控制的備選；工具權限與採購付款分離。
- 給出重啟、提交/恢復間隙、重複/過期回調、取消和版本兼容的驗證；沒有假裝安裝、運行或產生指標。

該試用實際加載 Skill 入口與三份參考；證明的是這組諮詢型場景的決策和範圍控制，不能證明框架運行、醫療正確性或所有業務自動選型都已驗證。本輪未發現需要據此修正的具體 Skill 行為錯誤。

## 項目交付與結構校驗

[TP-10～12](../architecture/technical-points/agent-orchestration.md)明確執行圖、業務狀態/責任事務、人工等待和可重放邊界。[F006 Plan](../specs/F006-quality-evidence-review/plan.md)保留編號增補恢復；[F007 Plan](../specs/F007-remediation-accountability/plan.md)配套 Spec/Tasks，共 11 條 AC、12 項待執行任務。

下列命令從工作區根執行並通過，均為結構驗證：

```bash
python3 -B <USER_HOME>/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/select-agent-architecture
python3 -B .agents/skills/product-prd/scripts/validate_prd.py MedicalQuality --require-confirmed
python3 -B .agents/skills/product-spec/scripts/validate_product_spec.py MedicalQuality --require-confirmed
python3 -B .agents/skills/feature-spec-planning/scripts/validate_feature_specs.py MedicalQuality --feature F006 --feature F007
python3 -B .agents/skills/project-evals/scripts/validate_evals.py MedicalQuality --suite evals/F006.json --suite evals/F007.json --suite evals/product.json
```

PRD 仍為 19 REQ / 6 NFR / 26 AC，Product Spec 仍為 13 PSC；Map 仍 10 個 planned Feature，無新增平臺 Feature 或依賴循環。本輪校驗的 F006 / F007 / product 為 9 / 11 / 6 條用例，全部未綁定，behavior=not_evaluated；全項目已設計 48 條局部和 6 條組合用例。

核對當次 22 份相關文檔的 207 處本地鏈接及 20 處技術錨點，無失效；界面描述長度、默認提示與自動選擇設置有效。本記錄新增鏈接另行核對。狀態/工具/事務語義已對照原 PSC 審閱，沒有把 runtime 成功升級為專業批准。

## 未執行與停止點

本次沒有運行 LangGraph/AgentScope/Pi/DeepSeek Harness/Hermes 或 Codex 工作任務，沒有下載模型、構建索引、改原型或業務源數據。未改變已選 Qwen、BGE-M3 或當前助手模型設置。

F003～F007 的 Spec ready、Plan draft、Tasks planned。實際依賴版本、接口、持久故障行為、真實簽署/留存與生產條件繼續按 Plan 核查；Skill 和文檔校驗不能替代這些證據。
