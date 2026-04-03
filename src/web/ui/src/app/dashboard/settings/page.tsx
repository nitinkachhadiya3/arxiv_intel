"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Shield, 
  Key, 
  Instagram, 
  Linkedin, 
  Facebook,
  CheckCircle2,
  Lock,
  Database,
  Cpu,
  Fingerprint,
  Zap,
  ChevronRight,
  Save
} from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("meta");
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSave = () => {
    setIsSaving(true);
    setErrorMsg("");
    setTimeout(() => {
       setIsSaving(false);
       setErrorMsg("ERROR: Node Authorization Missing. Check API Keys.");
       setTimeout(() => setErrorMsg(""), 5000);
    }, 1200);
  };

  return (
    <div className="settings-root-3">
      <header className="s-header-3">
        <div className="s-titles-3">
           <div className="s-badge-3 glass-premium">
              <Shield size={12} className="vibrant-blue" />
              <span>ENCRYPTION_LAYER: AES_256_ACTIVE</span>
           </div>
           <h1 className="s-text-3">Secure <span className="vibrant-gradient">Configurations</span></h1>
           <p className="s-sub-3">MANAGE PARTNER CREDENTIALS & NEURAL SYNC</p>
        </div>
        <button 
          className="s-save-btn-3 vibrant-bg magnetic-trigger hover-glow"
          onClick={handleSave}
          disabled={isSaving}
        >
           <Save size={18} /> {isSaving ? "SYNCING..." : "SAVE_SYNERGY"}
        </button>
      </header>

      <div className="s-grid-3">
        <aside className="s-nav-3">
           {[
             { id: "meta", label: "Meta Ecosystem", icon: Facebook },
             { id: "linkedin", label: "Professional Node", icon: Linkedin },
             { id: "vault", label: "Vault Security", icon: Database },
             { id: "compute", label: "Compute Nodes", icon: Cpu },
           ].map((tab) => (
             <motion.div 
               key={tab.id}
               whileHover={{ x: 4 }}
               onClick={() => setActiveTab(tab.id)}
               className={`sn-item-3 ${activeTab === tab.id ? "active" : ""}`}
             >
                <tab.icon size={18} className={activeTab === tab.id ? "vibrant-blue" : ""} />
                <span>{tab.label}</span>
                {activeTab === tab.id && <motion.div layoutId="sn-active" className="sn-active-dot" />}
             </motion.div>
           ))}
        </aside>

        <main className="s-content-3 glass-premium">
           <div className="sc-head-3">
              <div className="sc-icon-3 vibrant-bg">
                 <Key size={20} />
              </div>
              <div className="sc-meta-3">
                 <h3>CREDENTIAL_ORCHESTRATOR</h3>
                 <p>Configure neural access tokens for automated publishing via {activeTab.toUpperCase()}</p>
              </div>
           </div>

           <div className="sc-form-3">
              <div className="sc-group-3">
                 <label>NODE_IDENTIFIER</label>
                 <div className="sc-input-wrapper-3 glass-premium">
                    <Fingerprint size={16} className="sc-i-icon" />
                    <input type="text" placeholder="e.g. SOCIAL_AGENTS_PRIMARY" />
                 </div>
              </div>

              <div className="sc-split-3">
                 <div className="sc-group-3">
                    <label>ACCESS_TOKEN</label>
                    <div className="sc-input-wrapper-3 glass-premium">
                       <Lock size={16} className="sc-i-icon" />
                       <input type="password" placeholder="••••••••••••••••••••••••" />
                    </div>
                 </div>
                 <div className="sc-group-3">
                    <label>SYNC_ID</label>
                    <div className="sc-input-wrapper-3 glass-premium">
                       <Zap size={16} className="sc-i-icon" />
                       <input type="text" placeholder="10239102" />
                    </div>
                 </div>
              </div>

              <div className="sc-group-3">
                 <label>ENVIRONMENT_STAGING</label>
                 <div className="sc-toggle-bar-3 glass-premium">
                    <div className="sc-toggle-item active">PRODUCTION</div>
                    <div className="sc-toggle-item">STAGING</div>
                 </div>
              </div>
           </div>

           <div className="sc-footer-3">
              <div className="sc-status-3 glass-premium">
                 <div className="sc-status-indicator vibrant-blue" />
                 <div className="sc-status-text">
                    <span className="sc-st-main">NEURAL_SYNC_OPTIMAL</span>
                    <span className="sc-st-sub">LAST_VERIFIED: 2m AGORE</span>
                 </div>
              </div>
               <p className="sc-warning-3">
                 Security Alert: All credentials are hashed and stored within the Social Agents local node boundaries.
               </p>
               <AnimatePresence>
                 {errorMsg && (
                   <motion.div 
                     initial={{ opacity: 0, y: 10 }}
                     animate={{ opacity: 1, y: 0 }}
                     exit={{ opacity: 0, y: -10 }}
                     className="error-banner-3"
                   >
                     {errorMsg}
                   </motion.div>
                 )}
               </AnimatePresence>
            </div>
         </main>
      </div>

      <style jsx global>{`
        .settings-root-3 {
          display: flex;
          flex-direction: column;
          gap: 60px;
          padding-bottom: 80px;
        }

        .s-header-3 {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          padding-bottom: 40px;
          border-bottom: 2px solid rgba(255, 255, 255, 0.03);
        }

        .s-badge-3 {
           display: inline-flex;
           align-items: center;
           gap: 10px;
           padding: 6px 14px;
           border-radius: 100px;
           font-family: var(--font-mono);
           font-size: 0.6rem;
           font-weight: 800;
           letter-spacing: 1px;
           margin-bottom: 15px;
        }

        .s-text-3 {
          font-size: 2.8rem;
          font-weight: 900;
          letter-spacing: -1.5px;
          margin: 0;
        }

        .s-sub-3 {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.3);
          letter-spacing: 4px;
          font-family: var(--font-mono);
          margin-top: 10px;
        }

        .s-save-btn-3 {
          padding: 18px 32px;
          border-radius: 16px;
          border: none;
          background: var(--accent-primary, #6366f1);
          color: #fff;
          font-weight: 900;
          font-family: var(--font-mono);
          font-size: 0.85rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 12px;
          letter-spacing: 1px;
          box-shadow: 0 10px 20px rgba(99, 102, 241, 0.2);
          transition: all 0.3s;
        }

        .s-save-btn-3:hover {
          transform: translateY(-2px);
          box-shadow: 0 15px 30px rgba(99, 102, 241, 0.4);
        }

        .s-grid-3 {
          display: grid;
          grid-template-columns: 320px 1fr;
          gap: 40px;
        }

        .s-nav-3 {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .sn-item-3 {
          padding: 16px 24px;
          border-radius: 16px;
          display: flex;
          align-items: center;
          gap: 16px;
          color: rgba(255, 255, 255, 0.4);
          background: rgba(255, 255, 255, 0.01);
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .sn-item-3 span {
          font-weight: 500;
          font-size: 0.9rem;
        }

        .sn-item-3:hover {
          background: rgba(255, 255, 255, 0.04);
          color: rgba(255, 255, 255, 0.9);
          border-color: rgba(255, 255, 255, 0.1);
        }

        .sn-item-3.active {
          background: rgba(99, 102, 241, 0.08);
          color: #fff;
          border-color: rgba(255, 255, 255, 0.08);
        }

        .sn-active-dot {
           position: absolute;
           left: 0;
           width: 3px;
           height: 16px;
           background: var(--accent-primary);
           border-radius: 2px;
           box-shadow: 0 0 10px var(--accent-primary);
        }

        .s-content-3 {
          padding: 60px;
          border-radius: 40px;
        }

        .sc-head-3 {
          display: flex;
          align-items: center;
          gap: 25px;
          margin-bottom: 60px;
        }

        .sc-icon-3 {
          width: 54px;
          height: 54px;
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-primary, #6366f1);
          box-shadow: 0 0 15px rgba(99, 102, 241, 0.3);
        }

        .sc-meta-3 h3 {
          font-size: 1.2rem;
          font-weight: 800;
          margin-bottom: 6px;
          letter-spacing: 1px;
        }

        .sc-meta-3 p {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.3);
          font-weight: 500;
        }

        .sc-form-3 {
           display: flex;
           flex-direction: column;
           gap: 32px;
           max-width: 800px;
        }

        .sc-split-3 {
           display: grid;
           grid-template-columns: 1fr 1fr;
           gap: 24px;
        }

        .sc-group-3 label {
           display: block;
           font-size: 0.65rem;
           font-weight: 900;
           color: rgba(255, 255, 255, 0.3);
           letter-spacing: 2px;
           font-family: var(--font-mono);
           margin-bottom: 12px;
        }

        .sc-input-wrapper-3 {
           display: flex;
           align-items: center;
           gap: 15px;
           padding: 0 24px;
           height: 64px;
           border-radius: 16px;
           transition: border-color 0.3s;
        }

        .sc-input-wrapper-3:focus-within {
           border-color: var(--accent-primary);
        }

        .sc-input-wrapper-3 input {
           flex: 1;
           background: transparent;
           border: none;
           outline: none;
           color: #fff;
           font-size: 0.95rem;
        }

        .sc-i-icon { color: rgba(255, 255, 255, 0.2); }

        .sc-toggle-bar-3 {
           display: flex;
           padding: 6px;
           border-radius: 12px;
           width: fit-content;
        }

        .sc-toggle-item {
           padding: 10px 24px;
           border-radius: 8px;
           font-size: 0.65rem;
           font-weight: 900;
           font-family: var(--font-mono);
           letter-spacing: 1px;
           color: rgba(255, 255, 255, 0.3);
           cursor: pointer;
        }

        .sc-toggle-item.active {
           background: rgba(255, 255, 255, 0.05);
           color: var(--accent-primary);
        }

        .sc-footer-3 {
           margin-top: 80px;
           display: flex;
           flex-direction: column;
           gap: 24px;
        }

        .sc-status-3 {
           display: flex;
           align-items: center;
           gap: 20px;
           padding: 24px 32px;
           border-radius: 20px;
           width: fit-content;
        }

        .sc-status-indicator {
           width: 8px;
           height: 8px;
           border-radius: 50%;
           animation: statusPulse 2s infinite;
        }

        @keyframes statusPulse {
           0% { opacity: 0.4; transform: scale(1); }
           50% { opacity: 1; transform: scale(1.2); }
           100% { opacity: 0.4; transform: scale(1); }
        }

        .sc-status-text {
           display: flex;
           flex-direction: column;
        }

        .sc-st-main {
           font-size: 0.8rem;
           font-weight: 800;
           letter-spacing: 1px;
           font-family: var(--font-mono);
        }

        .sc-st-sub {
           font-size: 0.6rem;
           color: rgba(255, 255, 255, 0.3);
           font-family: var(--font-mono);
           font-weight: 700;
        }

        .sc-warning-3 {
           font-size: 0.75rem;
           color: rgba(255, 255, 255, 0.2);
           font-weight: 500;
        }

        .error-banner-3 {
           background: rgba(244, 63, 94, 0.1);
           border: 1px solid rgba(244, 63, 94, 0.2);
           color: #f43f5e;
           padding: 16px 24px;
           border-radius: 12px;
           font-family: var(--font-mono);
           font-size: 0.75rem;
           font-weight: 800;
           letter-spacing: 1px;
           margin-top: 10px;
        }

        .vibrant-blue { background: #3b82f6; box-shadow: 0 0 10px #3b82f6; }
      `}</style>
    </div>
  );
}
