import React, { useState } from 'react';
import { 
  MessageSquare, 
  CheckSquare, 
  Layers, 
  BarChart3, 
  FlaskConical, 
  Sparkles, 
  ShieldAlert, 
  Lock, 
  User as UserIcon,
  LogOut,
  AlertOctagon
} from 'lucide-react';
import { api, setAuthToken } from '../services/api';

interface NavbarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  currentUser: any;
  killSwitchActive: boolean;
  onRefreshUser: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentPage,
  onNavigate,
  currentUser,
  killSwitchActive,
  onRefreshUser
}) => {
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const handleDemoLogin = async (username: string) => {
    try {
      const password = username === 'admin' ? 'admin123' : username === 'operator' ? 'operator123' : 'password123';
      try {
        await api.login({ email_or_username: username, password });
      } catch {
        // If user doesn't exist, create demo user
        await api.signup({
          email: `${username}@kalyan-demo.internal`,
          username,
          password,
          display_name: username.toUpperCase(),
        });
      }
      onRefreshUser();
      setShowRoleMenu(false);
    } catch (err) {
      console.error('Demo switch failed', err);
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    onRefreshUser();
  };

  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'approval', label: 'Approval Queue', icon: CheckSquare, badge: 'Ops' },
    { id: 'content', label: 'Content Library', icon: Layers },
    { id: 'analytics', label: 'Analytics & Cost', icon: BarChart3 },
    { id: 'experiments', label: 'A/B Tests', icon: FlaskConical },
    { id: 'pricing', label: 'VIP Pass', icon: Sparkles },
    { id: 'admin', label: 'Kill Switch & Lore', icon: Lock, adminOnly: true },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-[#0f1118]/80 backdrop-blur-md">
      {killSwitchActive && (
        <div className="bg-red-600/90 text-white text-xs font-bold py-1.5 px-4 text-center flex items-center justify-center gap-2 animate-pulse">
          <AlertOctagon className="w-4 h-4" />
          <span>EMERGENCY KILL SWITCH ACTIVE: ALL SOCIAL PUBLISHING AND AUTONOMOUS JOBS ARE HALTED.</span>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
        {/* Brand */}
        <div 
          onClick={() => onNavigate('landing')}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center shadow-lg shadow-orange-500/20 group-hover:scale-105 transition">
            <span className="text-xl">☕</span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-lg tracking-tight text-white group-hover:text-orange-400 transition">KALYAN</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-300 border border-orange-500/30">
                v1.0 Canon
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Brutally Honest Internet Dost</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition ${
                  isActive 
                    ? 'bg-orange-500/15 text-orange-400 border border-orange-500/30 shadow-sm'
                    : 'text-slate-300 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-orange-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User & Role Switcher */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setShowRoleMenu(!showRoleMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-orange-500/40 text-xs font-medium text-slate-200 transition"
            >
              <UserIcon className="w-3.5 h-3.5 text-orange-400" />
              <span>{currentUser ? `${currentUser.username} (${currentUser.role})` : 'Guest Mode'}</span>
            </button>

            {showRoleMenu && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl bg-[#161822] border border-white/10 shadow-2xl p-2 z-50">
                <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Switch Simulation Role
                </div>
                <button
                  onClick={() => handleDemoLogin('admin')}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-orange-500/20 text-slate-200 flex items-center justify-between"
                >
                  <span>Admin Operator</span>
                  <span className="text-[10px] text-orange-400">Full Access</span>
                </button>
                <button
                  onClick={() => handleDemoLogin('operator')}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-orange-500/20 text-slate-200 flex items-center justify-between"
                >
                  <span>Social Moderator</span>
                  <span className="text-[10px] text-amber-400">Approval Queue</span>
                </button>
                <button
                  onClick={() => handleDemoLogin('fan_user')}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-orange-500/20 text-slate-200 flex items-center justify-between"
                >
                  <span>Regular User</span>
                  <span className="text-[10px] text-slate-400">Standard Chat</span>
                </button>
                {currentUser && (
                  <div className="border-t border-white/10 mt-1 pt-1">
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 flex items-center gap-2"
                    >
                      <LogOut className="w-3 h-3" />
                      <span>Log Out to Guest</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
