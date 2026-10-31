---
document: implementation-contracts
status: draft
updated: "2026-10-13"
---

# 一期模塊實施合同與交付順序

本文固定既有 Feature 之間需要共同實現的技術語義，承接 [FA 基線](architecture.md)、[產品總規格](../specs/product-spec.md)和各 Feature Plan。它給出字段、版本、失敗及事務約定，正式 Pydantic/OpenAPI/SQLAlchemy/Alembic 文件在開發時按這裡實現並驗證；不冒充已有運行代碼或醫院配置。

## 1. 共同請求、響應和事務

| 合同 | 必需字段/語義 | 執行要求 |
| --- | --- | --- |
| CommandEnvelope | request_id、action、target_id/scope、purpose、expected_version、idempotency_key、payload；理由按動作必需 | actor/崗位/允許集合由可信服務端解析，不來自客戶端或模型 |
| VersionManifest | source/document/evidence/context、ontology/mapping/shape/value-set、rule/knowledge/index、model/prompt/解析配置及 app/graph/schema 版本 | 實際依賴全部固定；未使用的能力明確 not_used，不以 latest 或虛構版本填充 |
| ResultEnvelope | request/operation_id、對象 ID/version、status、result_ref、coverage、reason_codes、blocking_conditions、required_next_action | 受理、運行、業務提交、人工確認分別表達；錯誤返回最小化，不復制正文 |
| Coverage | declared_scope、unit、expected_total/known、completed/partial/failed/blocked/not_run、每單元狀態或可回查 manifest | 同粒度分母對賬，未知總數不填 0；部分可用範圍明確 |
| ResponsibilityEvent | actor/role、action、resource/scope、before/after_version、reason、operation/decision/run、time、result | 關鍵業務變化＋必要責任記錄＋outbox 同庫事務 |
| DurableJob | job/run/attempt、input_manifest、purpose/scope、lease_owner/until、fencing_token、heartbeat、result/failure、budget | 短事務領取與提交，不持鎖等模型/人工；遲到嘗試不能覆寫當前結果 |

冪等鍵作用域包含實際主體/業務操作類別與目標範圍，持久化規範化請求摘要。同鍵同請求返回已成立結果，同鍵不同請求衝突；expected_version 比較更新是事務條件，不先查後無條件寫。業務已提交但 HTTP 響應丟失先按操作查詢，不盲目重做。

API 內部統一使用成功/受理與明確錯誤語義：202 僅表示作業受理；401 為身份失敗；403/404 按一致對象存在性策略拒絕；409 為狀態/版本/冪等衝突；422 為輸入合同錯誤；依賴不可用/超時等採用明確技術原因與實際部分覆蓋。具體狀態碼不能把業務 unknown、不適用、棄答和執行失敗壓成一個 success=false；消費方按 reason/coverage 判斷能否繼續。

對象主鍵建議使用獨立穩定 ID，來源自然鍵/namespace 另存；版本行不可因新輸入更新而覆蓋。數據庫約束至少包括有效操作唯一鍵、父子版本引用、獨立原判主體/樣本唯一性、同範圍同崗位有效簽署、發佈清單與資源摘要關聯。允許保留 JSONB 原生詳情，但授權/狀態/版本/唯一性關鍵字段必須可約束。

<a id="contracts-access"></a>
## 2. F001 授權與審計接口

| 內部操作/擬議入口 | 輸入 | 輸出/拒絕 | 調用方 |
| --- | --- | --- | --- |
| 身份會話建立與當前主體查詢 | 已核對 OIDC 回調/會話，不包含任意自報角色 | actor_id、崗位映射、會話狀態；無效拒絕 | 工作臺/API |
| authorize（內部服務） | actor context、action、resource、purpose、now、對象/策略版本 | decision_id、allow/deny、effective_scope、policy_version、expires_at、reason | 全部敏感入口/Worker |
| append_audit（同事務內部） | 當前 transaction、已驗證主體/動作、前後版本、理由/結果引用 | audit_id；失敗拋出使關鍵變更回滾 | 各 Feature 命令 |
| GET /api/v1/audit-events | 獲准篩選/範圍、時間/關聯 ID、穩定分頁 | 最小責任軌跡；無權範圍拒絕 | 質控/信息科等實際獲准崗位 |
| 更新授權/用途（受限管理命令） | 當前權限、目標範圍/期限、expected_version、理由 | 新 policy version、審計/失效事件 | 目標醫院授權管理職責 |

AuthorizationDecision 是當前一次決定/範圍引用，不是長期訪問令牌。數據庫 SET LOCAL 等上下文由服務端賦值，連接池歸還後不留舊身份；RLS 運行角色不能繞過策略。授權策略變化、長任務恢復、下載/原文取回和結果發佈都重驗，不僅在登錄時驗一次。

## 3. 原件、版本化資源與發佈

文件/模型/OCR/導出和數據庫寫入沒有天然跨系統事務。統一採用未發佈資源→摘要/範圍核對→短事務提交 manifest/result/outbox→消費者只讀已提交 manifest；崩潰後以 operation/input/config 對賬。原始 Data 只讀，派生物放 MedicalQuality/artifacts 下並忽略 Git。清理條件分別處理可重建緩存、必要歷史證據及不可再生責任記錄。

模型、外部詞表、解析器和本體導入不允許在處理真實病例時隱式從網絡下載；準備期固定批准來源/版本/許可，執行期缺依賴就給明確不可用。資料中的命令/HTML/宏/外部實體不獲得工具權。

<a id="contracts-source"></a>
## 4. F002 → F003 來源與讀取合同

SourceRegistrationRequest：connector_id/data_root_id、source_reference、namespace、format_hint、data_role/data_kind、purpose、license_refs、declared_scope、expected_source_version、operation_key。reference 只在批准 connector 下解釋，客戶端不交任意服務器路徑/URL。

SourceVersion：source_id/version、content_digest 或 snapshot_contract、schema_digest、format、namespace、role/kind、authorized_use、license/authority_refs、path_base、predecessor、created_operation、registration_status/coverage。只登記邊界的受限評測源使用可信登記版本及明確未讀狀態，不為生成摘要讀取禁止正文。

ReadScope/ReadHandle：source_id/version、允許表/列/查詢目錄與參數或頁/邏輯記錄範圍、purpose、授權引用/有效期、consistency_mode、budget、opaque_handle、locator_convention。服務端解句柄後重驗權限/版本，不能當永久 bearer token。

| 擬議操作 | 結果 |
| --- | --- |
| POST /api/v1/sources | 創建或查重來源登記，返回 source/version 或有限作業受理；不表示解析成功 |
| GET /api/v1/sources/{id}/versions/{version} | 當前授權下的元數據、範圍/失敗與定位基準 |
| POST /api/v1/source-versions/{id}/parse-runs | 按固定範圍受理 F003 作業，返回 job/run ID |
| 內部 open_read_handle | 得到受限同版本讀取資源，權限過期/內容變化/版本不兼容明確拒絕 |

F003 交付 EvidenceItem 1.0、native refs、parse_manifest、transforms/quality/coverage 與 permitted_consumer_scope；驗證語法、原值、定位回放和業務適用性分別負責。掃描主備和模型固定見[PDF 定案](../data-preparation/governance-cleaning-handoff.md#pdf-scan-decision)。

## 5. F004～F007 的語義、運行與責任合同

| 合同 | 關鍵字段/版本 | 生產者 → 消費者 |
| --- | --- | --- |
| SemanticRelease | native origin/version（如使用）、core/imports/terms/mapping/shapes/value-set/bindings 摘要、審核/適用/許可、projection_version | F004 構建/發佈 → F004/F005/F006 |
| SemanticResolution | requested/actual_release、operation、concept/關係/映射、result_kind、support_refs、coverage、ambiguous/unsupported 等原因 | F004 只讀服務 → 圖節點/檢索 |
| CaseContext | case/encounter namespace、固定文書/證據、raw/normalized、斷言主體/極性/時間/條件、關係、unknown/conflicts/unlinked、coverage、SemanticRelease | F004 → F006/工作臺 |
| RetrievalResult | query/route、原 query/擴展語義、固定知識/規則/index/model/semantic 版本、命中 evidence/parent/locator、原生 rank/score、資格與缺口 | F005 → F006/依據查看 |
| QualityRun / CheckResult | run/attempt、scope、完整版本清單、逐規則 eligibility/execution/condition、候選、coverage/blockers、支持/反證及資源記錄 | F006 → F007/F008/F004 |
| BusinessDecision | 真實 actor/role、task/action、expected_version、scope/document/rule/run/semantic 版本、理由、operation key/digest | F007 → 業務庫及 outbox/圖恢復 |
| SignatureScope | 本輪文書/問題/處理意見/運行/規則/語義清單、兩崗位各自身份/時間、簽署方式/審計引用 | F007 → 當前/歷史責任查看 |

原生本體 active 與產品 release 分離。缺本體版本/映射能力會限制依賴的自動判斷，合法原文與人工路徑仍可用。語義響應不是病例真值、SHACL 不是臨床裁決、checkpoint 不是責任狀態源。詳見[Agent/semantic 合同](../data-preparation/governance-cleaning-handoff.md#agent-semantic)。

F007 寫入先完成業務/審計/outbox 事務，圖只接受 decision_id 並從庫中取得已提交事實；恢復重驗當前權限/條件。舊語義/文書的歷史結果不因新版本重算而漂移，新範圍需新核驗鏈。

<a id="contracts-evaluation"></a>
## 6. F008 評測接口與報告

| 對象/操作 | 固定字段/行為 |
| --- | --- |
| EvaluationBatch | batch_id/version、scope、樣本/分組/來源 manifest、construction/evaluation 邊界、規則與完整配置版本、protocol_id/version、凍結狀態 |
| Judgment | judgment_id、batch/sample/rule、rater actor、decision/severity、evidence/理由、unable_reason、提交版本/時間、audit |
| Arbitration | 原判兩 ID、實際仲裁主體、判定/風險/依據、未決原因、追加關係；不覆蓋原判 |
| MetricReport | report/version、batch/run/ref、unit、counts/denominators、分層 metrics、NA/reason、coverage/abstention/failures、原始一致性/仲裁、配置/證據引用 |
| GateEvidence | scope/versions、high_risk_fn_refs、unresolved_high_risk_refs、threshold_protocol、缺項與實際專業/運行資格 |
| POST /api/v1/evaluation-batches | 建立/凍結批次；不讀取未獲準標籤或自行選留出 |
| POST /api/v1/evaluation-batches/{id}/judgments | 實際獲派專家提交自己的原判，冪等/版本/審計 |
| POST /api/v1/evaluation-batches/{id}/arbitrations | 具資格責任人追加裁決，保留原判 |
| GET /api/v1/evaluation-batches/{id}/report | 獲准查看固定報告，區分未運行/部分/完成 |

指標和責任簽字都不是 LLM 回答中的可自由生成字段。具體公式、rubric 與樣本設計以[評估計劃](../evaluation-plan.md)為準；缺 gold/閾值/實際執行時保留未評估，不製造成績。

<a id="contracts-release"></a>
## 7. F009 准入與能力控制

GateRequest 固定 target_stage、scope、baseline_version_manifest、evaluation_report_ids、workflow_verification_refs、required_role_acceptance 與目標環境證據；expected_version/operation_key 沿共同命令。

GateCondition：key、required、scope、status（滿足/不滿足/未知/有依據不適用）、source/version、evidence_refs、checked_at/validity、reason/owner。required=true 時未知不能被跳過；不適用必須有符合當前協議的依據，不是規避條件的複選框。

GateDecision：decision_id/version、request/baseline、approve/reject/stop、allowed_capabilities、scope/期限、condition_digest、真實 actor/責任接受/審計與生效信息。新事務提交前複核依賴的當前版本和授權，不能在頁面判斷後無條件寫 enable=true。

擬議內部入口：POST /api/v1/release-requests、GET /api/v1/release-requests/{id}、POST /api/v1/release-requests/{id}/decisions；運行服務通過受限 capability 查詢核對當前允許範圍。API/SDK 這裡是工作臺內部接口，不新增醫院外部接入產品形態。

失效事件包含受影響基線/能力/原因/責任與重驗要求；收到舊/重複事件按版本/操作對賬。生產入口即使事件未及時消費也不能繼續使用當前已知失效資格。歷史決定不刪除，臨床動作仍要求實際人工責任。

<a id="contracts-delivery"></a>
## 8. F010 資產與導出合同

ExportRequest：baseline_id/version、asset_selectors、target_purpose/recipient_scope、desired_format、expected_version/operation_key。F009 的 approve/reject/unreleased 等事實都可在合法說明性導出中保留，不因導出變更其資格。

ExportManifest：export_id/version、baseline、items（producer/id/version/schema/digest/type、scope、origin/license、review/verification/gate_status、dependencies）、included/excluded/restricted 原因、輸入配置、合法生成狀態、交接說明和 audit。生產內容清單由服務端計算，不打包調用方任意路徑。

擬議 POST /api/v1/exports、GET /api/v1/exports/{id}、GET /api/v1/exports/{id}/download；大資源經受控服務，下載再次授權。生成資源與 manifest 摘要一致後才發佈，無完整提交就無 ready download。

接收檢查只讀驗證摘要、Schema、依賴/許可範圍與狀態；不自動導入激活對方醫院的規則、本體、權限和真人身份。來源不可分發時給合法引用/說明並聲明無法完整重現，不造虛假完整包。

## 9. 分階段交付與恢復

1. F001/F002 提供實際授權/事務與來源合同；F003 在有明確範圍的源上驗證原生/OCR/統一證據。
2. F004 建本體基線/語義及病例上下文；F005 先可做候選來源治理，完整檢索消費需要 F004 已批准語義。
3. F006 固定規則/語義/證據執行，F007 承接真人閉環。F008 可按固定 QualityRun 獨立評測，不反向要求全部病例先簽字。
4. F009 組合真實評測、責任/環境證據控制階段；F010 交付固定資產與資格說明。
5. 每層先獨立合同再真實組合，測試替身必須標識；應用代碼存在後綁定檢查與生成實際運行文檔，不能在本輪填假啟動命令。

所有模塊沿既有 Feature 內部實現，不增加跨服務事務系統或通用數據平臺。本體包/專業規則/閾值/醫院配置都在各自權威來源維護，消費方通過固定 ID/版本引用。未獲真實條件的生產前置保持阻斷，不因全部規劃文檔已齊而解除。


<a id="contracts-graph"></a>
## 10. F011 原生圖譜消費合同

[TP-17/18](ontology-playground-integration.md)是新增 GraphViewEnvelope v1、圖查詢/元素/候選/導出接口及格式適配的唯一詳細合同。F004 提供固定語義/病例上下文與候選審核，F005 提供規則知識，F006 提供問題/實際引用，F003 提供原文定位；F001 先過濾授權再返回圖。畫布、Inspector、原文和規則固定同一版本集合，保留語義分型/未知/覆蓋/損失。

F011 不把實例寫成類，不將上游 parser 默認基數視為事實，不將原生 Validate 或 Playground 預覽發佈視為正式 SemanticRelease；域內候選、樂觀鎖與審計沿既有事實源。渲染/路徑只是顯示和導航，不改變 LangGraph 的只讀語義權限。F009 交付准入需 PG-006 證據；既有原文/人工恢復路徑繼續有效。
