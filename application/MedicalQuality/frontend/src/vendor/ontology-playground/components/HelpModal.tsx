import { motion } from 'framer-motion';
import { X, MousePointer, Target, MessageSquare, Link2, Lightbulb, Command } from 'lucide-react';

interface HelpModalProps {
  onClose: () => void;
  medical?: boolean;
}

export function HelpModal({ onClose, medical = false }: HelpModalProps) {
  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="modal-content"
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ type: 'spring', damping: 20 }}
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 700 }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontSize: 24, fontWeight: 600 }}>{medical ? '知識圖譜 · 使用幫助' : 'How to Use Ontology Playground (Preview)'}</h2>
          <button className="icon-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
{medical ? <>
          <div className="feature-card"><div className="feature-title">探索原生圖譜</div><p className="feature-text">拖動節點、平移和縮放畫布；點擊節點或關係查看定義、屬性與依據。雙擊節點聚焦鄰域，點擊空白處退出。佈局、搜索、路徑高亮和主題保留原生行為。</p></div>
          <div className="feature-card"><div className="feature-title">回到醫療證據</div><p className="feature-text">病例證據視圖區分文書、來源斷言、規則判斷、模型推斷和責任意見。選擇證據後可並列查看同版本原文，再返回原任務；圖中位置與有向路徑不表示臨床因果。</p></div>
          <div className="feature-card"><div className="feature-title">範圍、版本與候選</div><p className="feature-text">路徑只在當前已加載範圍內查找。原生設計器的保存與驗證產生候選，不直接發佈本體或改寫病歷。導出格式區分顯示投影、原生子集和完整本體包。</p></div>
          <div className="feature-card"><div className="feature-title">數據綁定與查詢</div><p className="feature-text">檢查器展示已登記的數據綁定、來源與語義版本。圖譜查詢用於對象與關係定位，不是臨床診斷問答。未知、未覆蓋和不適用的條件保持可見。</p></div>
          </> : <>
          <div className="feature-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <MousePointer size={20} color="var(--ms-blue)" />
              <span className="feature-title" style={{ marginBottom: 0 }}>Explore the Graph</span>
            </div>
            <p className="feature-text">
              Click on any <strong>entity type</strong> (colored node) to see its properties, relationships, and data bindings. 
              Click on <strong>relationship lines</strong> to see how entities connect. Use the controls in the bottom-left to zoom and reset the layout.
            </p>
          </div>

          <div className="feature-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <Target size={20} color="var(--ms-purple)" />
              <span className="feature-title" style={{ marginBottom: 0 }}>Complete Quests</span>
            </div>
            <p className="feature-text">
              Select a quest from the left panel to start a guided journey. Follow the instructions to click on specific entities 
              or relationships. Complete all steps to earn <strong>badges</strong> and <strong>points</strong>!
            </p>
          </div>

          <div className="feature-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <MessageSquare size={20} color="var(--ms-yellow)" />
              <span className="feature-title" style={{ marginBottom: 0 }}>Ask Natural Language Questions</span>
            </div>
            <p className="feature-text">
              Use the query playground in the bottom-right to ask questions like "Show me Gold tier customers" or 
              "Which products come from Ethiopia?". The graph will highlight relevant entities and relationships.
            </p>
          </div>

          <div className="feature-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <Link2 size={20} color="var(--ms-green)" />
              <span className="feature-title" style={{ marginBottom: 0 }}>View Data Bindings</span>
            </div>
            <p className="feature-text">
              When you select an entity type, the inspector shows how ontology properties map to real data sources in a data lakehouse, 
              including lakehouse tables and semantic models.
            </p>
          </div>

          <div style={{ 
            padding: 16, 
            background: 'rgba(0, 120, 212, 0.1)', 
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12
          }}>
            <Lightbulb size={20} color="var(--ms-blue)" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <strong style={{ color: 'var(--ms-blue)' }}>About Microsoft Fabric IQ Ontology</strong>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
                An ontology is a shared, machine-understandable vocabulary of your business. It defines entity types (like Customer, Product), 
                their properties, and relationships. This demo uses a fictional "Fourth Coffee" to illustrate these concepts.
              </p>
            </div>
          </div>

          </>}
          <div className="feature-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <Command size={20} color="var(--ms-blue)" />
              <span className="feature-title" style={{ marginBottom: 0 }}>{medical ? '鍵盤操作' : 'Keyboard Shortcuts'}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 16px', fontSize: 13, color: 'var(--text-secondary)' }}>
              <kbd className="help-kbd">⌘K</kbd><span>{medical ? '打開命令面板' : 'Open command palette'}</span>
              <kbd className="help-kbd">?</kbd><span>{medical ? '打開使用幫助' : 'Open this help dialog'}</span>
              <kbd className="help-kbd">Esc</kbd><span>{medical ? '關閉對話框' : 'Close any dialog'}</span>
              <kbd className="help-kbd">↑ ↓</kbd><span>{medical ? '選擇命令結果' : 'Navigate palette results'}</span>
              <kbd className="help-kbd">↵</kbd><span>{medical ? '執行選中命令' : 'Select palette command'}</span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <button className="btn btn-primary" onClick={onClose}>
            {medical ? '開始使用' : 'Got it!'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
