# 第三方來源與必要許可

本項目知識圖譜實際複用 Microsoft Ontology-Playground 原生源碼，固定提交為 `defb487b133786c826eab60b99fcef9b8d3c6fbd`。版權與 MIT 全文保留在 vendor 和 public/licenses，打包時隨靜態文件分發。以下是直接前端運行依賴；完整依賴版本以 package-lock.json 為準。

| 項目 | 固定版本 | 聲明許可 | 文件 |
| --- | --- | --- | --- |
| Microsoft Ontology-Playground | 固定提交 defb487 | MIT | [完整許可](public/licenses/Ontology-Playground.txt) |
| react | 19.2.4 | MIT | [完整許可](public/licenses/react.txt) |
| react-dom | 19.2.4 | MIT | [完整許可](public/licenses/react-dom.txt) |
| cytoscape | 3.33.1 | MIT | [完整許可](public/licenses/cytoscape.txt) |
| cytoscape-fcose | 2.2.0 | MIT | [完整許可](public/licenses/cytoscape-fcose.txt) |
| framer-motion | 12.29.2 | MIT | [完整許可](public/licenses/framer-motion.txt) |
| lucide-react | 0.563.0 | ISC | [完整許可](public/licenses/lucide-react.txt) |
| zustand | 5.0.10 | MIT | [完整許可](public/licenses/zustand.txt) |
| sanitize-html | 2.17.7 | MIT | [完整許可](public/licenses/sanitize-html.txt) |

原生源碼基線與摘要見 src/vendor/ontology-playground/upstream-manifest.json；醫療適配差異另列在該目錄 README.md。軟件許可不擴展到患者資料、外部醫學詞表或模型權重；原數據許可繼續以工作區 Data/醫療病歷質控/README.md 為準。模型來源與權重摘要存於本地 artifacts/models/manifest.json。
