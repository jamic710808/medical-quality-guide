# Ontology-Playground 原生來源與醫療適配

來源：https://github.com/microsoft/Ontology-Playground

固定提交：`defb487b133786c826eab60b99fcef9b8d3c6fbd`。本目錄保留原生圖譜、fCoSE 佈局、搜索、檢查器、路徑、統計、查詢、命令面板和完整可視化 Designer 及其依賴。沒有換成另一套渲染引擎或簡版 embed。UPSTREAM-LICENSE 為原 MIT 全文，upstream-manifest.json 保存引入時逐文件摘要。

## 明確的醫療適配

- 原生渲染器增加可選授權回調、醫療佈局參數、業務圖例、路徑聚焦、較大標籤與選中居中/容器尺寸適配；默認參數仍保留上游行為，>=1000 元素的 grid 策略保留。
- 檢查器補充類型/實例標籤和未知基數；原生字段/屬性/綁定/方向仍可查看。
- 設計器保留實體、屬性、關係、配色、撤銷重做、圖/RDF 預覽；醫療調用方將保存和提交接到受控候選/審核服務。
- 醫療模式不裝配公共 GitHub/Fabric 提交；原生代碼保留為來源，產品中不使用其遠程身份/令牌表單。原生格式序列化仍復用。
- RDF 的可選醫療解析模式保留原始 IRI（包括 URN）、中文名和未聲明基數；默認模式與上游測試相容。完整 OWL/SHACL 包由後端固定版本提供，顯示投影不冒充完整本體。
- 搜索行補齊鍵盤按鈕語義，醫療模式加大搜索與輔助文字，主面板可選中文標籤；醫療幫助替換教學/積分說明，默認幫助保留。
- 醫療查詢隔離 Fourth Coffee 示例回答，僅導航當前加載對象。
- themeTokens 測試路徑調整到本目錄；原生圖譜相關用例保留，教學構建/題庫目錄測試不計入醫療應用驗收。

## 本輪修改的原生路徑

- `src/a11y/themeTokens.ts`
- `src/components/HelpModal.tsx`
- `src/components/InspectorPanel.tsx`
- `src/components/OntologyDesigner.tsx`
- `src/components/OntologyGraph.tsx`
- `src/components/OntologyStatsPanel.tsx`
- `src/components/PathFinderPanel.tsx`
- `src/components/QueryPlayground.tsx`
- `src/components/SearchFilter.tsx`
- `src/components/designer/DesignerActions.tsx`
- `src/components/designer/DesignerPreview.tsx`
- `src/components/designer/RelationshipForm.tsx`
- `src/data/ontology.ts`
- `src/data/queryEngine.ts`
- `src/lib/rdf/parser.ts`
- `src/lib/rdf/serializer.ts`

實際產品接入在 frontend/src/pages/GraphPage.tsx；詳細合同位於 docs/architecture/ontology-playground-integration.md。所有實現/醫學資格邊界以本項目規格與實際驗證記錄為準。

醫療端默認淺色及瀏覽器偏好由 GraphPage.tsx 管理，原生 store 的默認行為未修改。2026-10-14 字號/主題核對見 docs/verification/readability-theme.md。
