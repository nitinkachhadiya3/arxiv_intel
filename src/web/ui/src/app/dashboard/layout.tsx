"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import gsap from "gsap";
import { 
  LayoutDashboard, 
  Database, 
  Settings as SettingsIcon,
  LogOut,
  ChevronRight,
  Bell,
  Cpu,
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const sidebarRef = useRef<HTMLDivElement>(null);
  
  const navItems = [
    { id: "dashboard", icon: LayoutDashboard, label: "Studio", href: "/dashboard" },
    { id: "vault", icon: Database, label: "Post Vault", href: "/dashboard/vault" },
    { id: "settings", icon: SettingsIcon, label: "Settings", href: "/dashboard/settings" },
  ];

  return (
    <div className="layout-container-3 border-glow-3">
      {/* Neural Mesh Background */}
      <div className="neural-mesh" />

      {/* Futuristic Sidebar */}
      <aside ref={sidebarRef} className="sidebar-3 glass-premium">
        <div className="sidebar-header-3">
           <div className="logo-box-3 vibrant-bg">
             <Cpu size={24} />
           </div>
           <div className="logo-meta-3">
             <h2 className="logo-shimmer">SOCIAL_AGENTS</h2>
             <span className="v-label-3">V3.0_STABLE</span>
           </div>
        </div>

        <nav className="sidebar-nav-3">
          {navItems.map((item) => (
            <Link key={item.id} href={item.href} className="no-underline">
              <motion.div
                whileHover={{ x: 6 }}
                className={`nav-item-3 ${pathname === item.href ? "active" : ""}`}
              >
                <item.icon size={20} className="n-icon-3" />
                <span>{item.label}</span>
                {pathname === item.href && (
                  <motion.div layoutId="n-active-3" className="n-active-line-3" />
                )}
                {pathname === item.href && <ChevronRight size={14} className="n-arr-3" />}
              </motion.div>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer-3">
           <div className="user-pill-3 glass-premium">
              <div className="u-avatar-3 vibrant-bg">AI</div>
              <div className="u-meta-3">
                <span className="u-name-3">FOUNDER</span>
                <span className="u-status-3">PRIMARY NODE</span>
              </div>
           </div>
           <button className="logout-trigger-3">
             <LogOut size={18} />
           </button>
        </div>
      </aside>

      {/* Main Orchestration View */}
      <main className="main-content-3">
        <header className="main-header-3 glass-premium">
          <div className="telemetry-bar-3">
             <div className="t-item-3">
               <div className="t-dot-3 vibrant-green" />
               <span>SYSTEM: OPTIMAL</span>
             </div>
             <div className="t-item-3">
               <div className="t-dot-3 vibrant-blue" />
               <span>LATENCY: 42MS</span>
             </div>
          </div>

          <div className="header-actions-3">
             <button className="h-btn-3 glass-premium">
               <Bell size={18} />
               <div className="h-notif-3" />
             </button>
             <div className="h-sep-3" />
             <div className="h-profile-3">
                <span className="h-name-3">Founder Node</span>
                <div className="h-avatar-mini-3">AI</div>
             </div>
          </div>
        </header>

        <div className="content-viewport-3">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 10, filter: "blur(4px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, y: -10, filter: "blur(4px)" }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      <style jsx global>{`
        .layout-container-3 {
          display: grid;
          grid-template-columns: 320px 1fr;
          min-height: 100vh;
          background: #08080A;
          color: #fff;
          position: relative;
          overflow: hidden;
        }

        .sidebar-3 {
          margin: 20px;
          border-radius: 32px;
          display: flex;
          flex-direction: column;
          padding: 40px 30px;
          position: relative;
          z-index: 50;
        }

        .sidebar-header-3 {
          display: flex;
          align-items: center;
          gap: 15px;
          margin-bottom: 60px;
        }

        .logo-box-3 {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .logo-meta-3 h2 {
          font-size: 0.95rem;
          margin-bottom: 2px;
          letter-spacing: 1px;
        }

        .v-label-3 {
          font-size: 0.55rem;
          color: rgba(255, 255, 255, 0.3);
          letter-spacing: 2px;
          font-weight: 900;
        }

        .sidebar-nav-3 {
          display: flex;
          flex-direction: column;
          gap: 12px;
          flex: 1;
        }

        .nav-item-3 {
          display: flex;
          align-items: center;
          gap: 18px;
          padding: 18px 24px;
          border-radius: 16px;
          color: rgba(255, 255, 255, 0.4);
          transition: all 0.3s;
          position: relative;
          cursor: pointer;
        }

        .nav-item-3:hover {
          background: rgba(255, 255, 255, 0.03);
          color: rgba(255, 255, 255, 0.8);
        }

        .nav-item-3.active {
          background: rgba(99, 102, 241, 0.06);
          color: var(--accent-primary);
        }

        .n-icon-3 {
           transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .nav-item-3.active .n-icon-3 {
           transform: scale(1.1) rotate(-5deg);
        }

        .n-active-line-3 {
          position: absolute;
          left: 0;
          width: 4px;
          height: 20px;
          background: var(--accent-primary);
          border-radius: 4px;
          box-shadow: 0 0 10px var(--accent-primary);
        }

        .n-arr-3 {
          margin-left: auto;
          opacity: 0.5;
        }

        .sidebar-footer-3 {
           padding-top: 30px;
           border-top: 1px solid rgba(255, 255, 255, 0.05);
           display: flex;
           align-items: center;
           gap: 15px;
        }

        .user-pill-3 {
           flex: 1;
           display: flex;
           align-items: center;
           gap: 12px;
           padding: 12px 16px;
           border-radius: 16px;
        }

        .u-avatar-3 {
           width: 32px;
           height: 32px;
           border-radius: 50%;
           display: flex;
           align-items: center;
           justify-content: center;
           font-size: 10px;
           font-weight: 900;
        }

        .u-meta-3 {
           display: flex;
           flex-direction: column;
        }

        .u-name-3 {
           font-size: 0.75rem;
           font-weight: 800;
        }

        .u-status-3 {
           font-size: 0.55rem;
           color: rgba(255, 255, 255, 0.3);
           letter-spacing: 1px;
        }

        .logout-trigger-3 {
           width: 44px;
           height: 44px;
           border-radius: 12px;
           background: transparent;
           border: 1px solid rgba(255, 255, 255, 0.05);
           color: rgba(255, 255, 255, 0.3);
           display: flex;
           align-items: center;
           justify-content: center;
           cursor: pointer;
           transition: all 0.3s;
        }

        .logout-trigger-3:hover {
           background: rgba(244, 63, 94, 0.1);
           color: #f43f5e;
           border-color: rgba(244, 63, 94, 0.2);
        }

        .main-content-3 {
           padding: 20px;
           padding-left: 0;
           display: flex;
           flex-direction: column;
           gap: 20px;
        }

        .main-header-3 {
           height: 80px;
           border-radius: 20px;
           display: flex;
           align-items: center;
           justify-content: space-between;
           padding: 0 40px;
        }

        .telemetry-bar-3 {
           display: flex;
           gap: 24px;
        }

        .t-item-3 {
           display: flex;
           align-items: center;
           gap: 10px;
           font-size: 0.7rem;
           font-weight: 800;
           letter-spacing: 1px;
           color: rgba(255, 255, 255, 0.3);
        }

        .t-dot-3 {
           width: 6px;
           height: 6px;
           border-radius: 50%;
        }

        .vibrant-green { background: #10b981; box-shadow: 0 0 10px #10b981; }
        .vibrant-blue { background: #3b82f6; box-shadow: 0 0 10px #3b82f6; }

        .header-actions-3 {
           display: flex;
           align-items: center;
           gap: 30px;
        }

        .h-btn-3 {
           width: 40px;
           height: 40px;
           border-radius: 12px;
           display: flex;
           align-items: center;
           justify-content: center;
           cursor: pointer;
           position: relative;
        }

        .h-notif-3 {
           position: absolute;
           top: 10px;
           right: 10px;
           width: 6px;
           height: 6px;
           background: #f43f5e;
           border-radius: 50%;
           box-shadow: 0 0 8px #f43f5e;
        }

        .h-profile-3 {
           display: flex;
           align-items: center;
           gap: 15px;
        }

        .h-name-3 {
           font-size: 0.8rem;
           color: rgba(255, 255, 255, 0.4);
           font-weight: 600;
        }

        .h-avatar-mini-3 {
           width: 36px;
           height: 36px;
           background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
           border-radius: 10px;
           display: flex;
           align-items: center;
           justify-content: center;
           font-size: 10px;
           font-weight: 900;
        }

        .content-viewport-3 {
           flex: 1;
           overflow-y: auto;
           padding-right: 10px;
        }
      `}</style>
    </div>
  );
}
