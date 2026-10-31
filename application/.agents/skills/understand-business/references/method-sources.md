# 參考方法與融合取捨

以下是本次已核對的開源方法，用於說明設計依據。它們不是運行時依賴；本技能不要求安裝或調用這些外部 Skills。

| 參考 | 吸收的做法 | 本技能的取捨 |
| --- | --- | --- |
| [Superpowers / brainstorming](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md) | 具體情境、逐步提問、複述理解 | 對話用於幫助 FDE 理解業務，交付停在資料包 |
| [Matt Pocock / grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) | 問題依賴、先查可獲得的事實 | 優先解決上游缺口，不要求窮盡所有分支 |
| [Matt Pocock / domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md) | 澄清術語與關係 | 術語進入業務正文，不默認新建架構決策文檔 |
| [Dean Peters / problem-framing-canvas](https://github.com/deanpeters/Product-Manager-Skills/blob/main/skills/problem-framing-canvas/SKILL.md) | 檢查假設、參與角色與問題後果 | FDE 初步分析不冒充客戶驗證 |
| [Dean Peters / workshop-facilitation](https://github.com/deanpeters/Product-Manager-Skills/blob/main/skills/workshop-facilitation/SKILL.md) | 利用已有上下文、引導及中斷恢復 | 不強制選模式或固定數量的問題 |
| [PM Skills / interview-script](https://github.com/phuryn/pm-skills/blob/main/pm-product-discovery/skills/interview-script/SKILL.md) | 關注實際工作、避免誘導 | 用於輔導 FDE 和發現資料缺口，不模擬真實客戶回答 |
| [BMad / advanced-elicitation](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/skills/bmad-advanced-elicitation/SKILL.md) | 換角度檢查草案的假設與遺漏 | 按需覆盤，不帶入整套方法菜單或開發流程 |
| [Oh My Codex / deep-interview](https://github.com/Yeachan-Heo/oh-my-codex/blob/main/plugins/oh-my-codex/skills/deep-interview/SKILL.md) | 優先處理關鍵未知、適時收斂 | 以業務內容與證據判斷，不引入模型評分門檻 |
| [GitHub Spec Kit / clarify](https://github.com/github/spec-kit/blob/main/templates/commands/clarify.md) | 按影響選擇問題、說明追問意義 | 適配業務摸底，不要求預先存在軟件規格 |

輸出結構依據本項目已經存在的“資料索引 → 客戶需求／業務約定／溝通記錄 → 來源與條目”的讀取約定獨立整理，已內置於 `output-contract.md`。沒有複製 Playground 模板、渲染器或它的運行流程。

上游主分支會變化。以後迭代圍繞實際偏差核對必要原文，不能僅因上游變化而自動替換本地已經適配的工作流。
