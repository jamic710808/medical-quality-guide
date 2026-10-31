/* 原型專用合成資料；不讀取、修改或發送工作區醫療原始數據。 */
window.MQ_DATA = {
  rules: [
    {id:'MQC-DOC-001',name:'必要文書與段落完整性',group:'文書完整性',risk:'medium',method:'確定性規則',issue:'出院記錄缺少病情變化摘要',a:'病情變化與診療經過：未填寫。',b:'出院記錄已提交，病情變化摘要為空。',resolution:'已補充病情變化摘要',advice:'請責任醫生根據現有診療記錄補充病情變化摘要，並保留來源。'},
    {id:'MQC-DOC-002',name:'病例與就診身份一致性',group:'身份與時間',risk:'high',method:'確定性規則',issue:'兩份文書的就診標識不一致',a:'就診標識：ZY202610-0284。',b:'就診標識：ZY202610-0184。',resolution:'就診標識已核對一致',advice:'先核對文書歸屬與就診標識。身份未明確前，不繼續合併或核驗。'},
    {id:'MQC-DOC-003',name:'文書時間線一致性',group:'身份與時間',risk:'medium',method:'確定性規則',issue:'病程記錄與出院時間順序待核對',a:'出院時間：2026-10-12 09:00。',b:'病程記錄時間：2026-10-13 17:40。',resolution:'時間線已核對',advice:'請核對文書時間、事件時間及補記情況，說明存在差異的原因。'},
    {id:'MQC-DOC-004',name:'檢查結果引用可追溯性',group:'證據完整性',risk:'medium',method:'規則 + 知識檢索',issue:'檢查結果引用缺少原始報告',a:'相關檢查結果見胸部檢查報告。',b:'附件目錄中未找到對應檢查報告。',resolution:'已關聯檢查報告',advice:'補充或關聯被引用的檢查報告。當前材料缺失不代表臨床未實施檢查。'},
    {id:'MQC-DOC-005',name:'過敏記載跨段一致性',group:'語義一致性',risk:'high',method:'規則 + 語義分析',issue:'入院與出院記錄的過敏史記載衝突',a:'藥物過敏史：青黴素過敏。',b:'藥物過敏史：否認。',resolution:'青黴素過敏',advice:'請責任醫生核實過敏史，並統一相關文書記載；系統不判斷真實過敏狀態。'},
    {id:'MQC-DOC-006',name:'診斷描述跨段一致性',group:'語義一致性',risk:'medium',method:'語義分析 + 專家',issue:'入院與出院診斷描述存在差異',a:'入院診斷記錄：成人肺炎。',b:'出院診斷記錄：待補充。',resolution:'已核對診斷描述',advice:'請責任醫生結合病情演變解釋診斷描述差異，補足對應記錄。'},
    {id:'MQC-DOC-007',name:'用藥文本要素完整性',group:'文書完整性',risk:'high',method:'確定性規則',issue:'用藥記錄中的劑量單位缺失',a:'用藥記錄：劑量單位未記錄。',b:'出院帶藥記錄：見原醫囑。',resolution:'已核對用藥記錄要素',advice:'請對照原醫囑核對文書中的劑量單位與頻次；不由系統補造數值或給出治療建議。'},
    {id:'MQC-DOC-008',name:'作者、簽署與版本完整性',group:'證據完整性',risk:'medium',method:'確定性規則',issue:'文書責任作者與簽署版本待補充',a:'責任作者：未記錄。',b:'文書版本：v1.0；簽署信息未關聯。',resolution:'已補充責任作者與版本',advice:'請關聯責任作者和對應文書版本，核對簽署權限後完成責任確認。'}
  ],
  cases: [
    {id:'C001',record:'ZY202610-0281',name:'陳**',age:68,sex:'男',bed:'28',rule:4,status:'review',team:'A組',due:'2026-10-14T18:00',arrival:'09:12'},
    {id:'C002',record:'ZY202610-0282',name:'李**',age:56,sex:'女',bed:'12',rule:3,status:'blocked',team:'A組',blocked:'missing',due:'2026-10-14T12:00',arrival:'09:24'},
    {id:'C003',record:'ZY202610-0283',name:'王**',age:72,sex:'男',bed:'06',rule:6,status:'doctor',team:'A組',due:'2026-10-14T16:00',arrival:'09:35'},
    {id:'C004',record:'ZY202610-0284',name:'周**',age:61,sex:'女',bed:'19',rule:5,status:'appeal',team:'B組',due:'2026-10-14T18:00',arrival:'09:42',appeal:'病情隨住院過程發生變化，請結合後續病程複核描述差異。'},
    {id:'C005',record:'ZY202610-0285',name:'吳**',age:49,sex:'男',bed:'03',rule:0,status:'verify',team:'A組',due:'2026-10-14T18:00',arrival:'10:03',corrected:true},
    {id:'C006',record:'ZY202610-0286',name:'趙**',age:66,sex:'女',bed:'31',rule:7,status:'sign',team:'A組',due:'2026-10-14T18:00',arrival:'10:12',corrected:true},
    {id:'C007',record:'ZY202610-0287',name:'鄭**',age:54,sex:'男',bed:'17',rule:2,status:'review',team:'B組',due:'2026-10-15T12:00',arrival:'10:20'},
    {id:'C008',record:'ZY202610-0288',name:'孫**',age:70,sex:'女',bed:'22',rule:4,status:'doctor',team:'B組',due:'2026-10-15T18:00',arrival:'10:32'},
    {id:'C009',record:'ZY202610-0289',name:'徐**',age:63,sex:'男',bed:'10',rule:1,status:'blocked',team:'A組',blocked:'identity',due:'2026-10-14T12:00',arrival:'10:45'},
    {id:'C010',record:'ZY202610-0290',name:'林**',age:47,sex:'女',bed:'08',rule:0,status:'blocked',team:'B組',blocked:'scope',department:'外科病區',due:'2026-10-15T12:00',arrival:'11:02'},
    {id:'C011',record:'ZY202610-0291',name:'何**',age:58,sex:'男',bed:'16',rule:3,status:'review',team:'A組',due:'2026-10-15T18:00',arrival:'11:16'},
    {id:'C012',record:'ZY202610-0292',name:'許**',age:75,sex:'女',bed:'25',rule:6,status:'verify',team:'A組',due:'2026-10-15T18:00',arrival:'11:30',corrected:true}
  ],
  incoming: [
    {id:'C013',record:'ZY202610-0293',name:'馮**',age:64,sex:'男',bed:'09',rule:7,status:'review',team:'A組',due:'2026-10-15T18:00',arrival:'11:45'},
    {id:'C014',record:'ZY202610-0294',name:'蔣**',age:59,sex:'女',bed:'21',rule:2,status:'review',team:'B組',due:'2026-10-15T18:00',arrival:'11:48'}
  ]
};
