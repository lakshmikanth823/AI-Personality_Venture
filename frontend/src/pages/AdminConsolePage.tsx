import React, { useEffect, useState } from 'react';
import { 
  Lock, 
  AlertOctagon, 
  ShieldAlert, 
  CheckCircle2, 
  RefreshCw, 
  BookOpen, 
  Plus, 
  Terminal,
  Clock,
  UserCheck
} from 'lucide-react';
import { api } from '../services/api';

interface AdminConsolePageProps {
  currentUser: any;
  killSwitchActive: boolean;
  onRefreshKillSwitch: () => void;
}

export const AdminConsolePage: React.FC<AdminConsolePageProps> = ({
  currentUser,
  killSwitchActive,
  onRefreshKillSwitch
}) => {
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [lores, setLores] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [killReason, setKillReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // New Lore Form
  const [showAddLore, setShowAddLore] = useState(false);
  const [loreTitle, setLoreTitle] = useState('');
  const [loreContent, setLoreContent] = useState('');
  const [loreCategory, setLoreCategory] = useState('origin');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [logs, l] = await Promise.all([
        api.getAuditLogs(),
        api.getLore()
      ]);
      setAuditLogs(logs);
      setLores(l);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleKillSwitch = async () => {
    if (!currentUser || currentUser.role !== 'admin') {
      alert("Only users with Admin role can trigger the Emergency Kill Switch.");
      return;
    }

    const reason = killReason.trim() || prompt("Enter reason for emergency stop action:", "Operational safety intervention");
    if (!reason) return;

    setActionLoading(true);
    try {
      if (killSwitchActive) {
        await api.deactivateKillSwitch(reason);
      } else {
        await api.activateKillSwitch(reason);
      }
      onRefreshKillSwitch();
      setKillReason('');
      fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to update kill switch state");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateLore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loreTitle || !loreContent) return;
    try {
      await api.createLore(loreTitle, loreContent, loreCategory, 'canon');
      setLoreTitle('');
      setLoreContent('');
      setShowAddLore(false);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-10">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <Lock className="w-6 h-6 text-orange-400" />
            <h1 className="text-2xl font-extrabold text-white">Operations & Governance Center</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Global emergency controls, immutable audit logging, and canonical character lore governance.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Emergency Kill Switch Section */}
      <div className={`p-6 sm:p-8 rounded-3xl border transition shadow-2xl ${
        killSwitchActive 
          ? 'bg-red-950/30 border-red-500/50' 
          : 'bg-[#12141c] border-white/10'
      }`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <AlertOctagon className={`w-6 h-6 ${killSwitchActive ? 'text-red-500 animate-pulse' : 'text-slate-400'}`} />
              <h2 className="text-xl font-extrabold text-white">Global Emergency Kill Switch</h2>
            </div>
            <p className="text-xs text-slate-300 max-w-xl leading-relaxed">
              Instantly halts all social media publishing, autonomous background jobs, and channel adapters across X, Instagram, YouTube, and WhatsApp. Normal web chat and audit trails remain accessible.
            </p>
            <div className="flex items-center gap-2 text-xs pt-1">
              <span className="text-slate-400 font-mono">Current Status:</span>
              <span className={`font-extrabold px-2 py-0.5 rounded text-[11px] uppercase ${
                killSwitchActive 
                  ? 'bg-red-500 text-white animate-pulse' 
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              }`}>
                {killSwitchActive ? 'EMERGENCY STOP ENGAGED' : 'NORMAL OPERATIONAL STATE'}
              </span>
            </div>
          </div>

          <div className="w-full sm:w-auto flex flex-col gap-2">
            <button
              onClick={handleToggleKillSwitch}
              disabled={actionLoading}
              className={`px-6 py-3.5 rounded-2xl font-extrabold text-xs uppercase tracking-wider transition shadow-2xl flex items-center justify-center gap-2 ${
                killSwitchActive
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  : 'bg-red-600 hover:bg-red-500 text-white shadow-red-600/30'
              }`}
            >
              <AlertOctagon className="w-4 h-4" />
              <span>{killSwitchActive ? 'Disengage Kill Switch' : 'ENGAGE EMERGENCY STOP'}</span>
            </button>
            <span className="text-[10px] text-center text-slate-500">Requires Admin Role</span>
          </div>
        </div>
      </div>

      {/* Character Lore Manager */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-orange-400" />
            <h3 className="text-base font-bold text-white">Canonical Character Lore (L4 Memory)</h3>
          </div>
          <button
            onClick={() => setShowAddLore(!showAddLore)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-orange-600 hover:bg-orange-500 text-white text-xs font-bold transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Canonical Fact</span>
          </button>
        </div>

        {/* Add Lore Modal / Form */}
        {showAddLore && (
          <form onSubmit={handleCreateLore} className="p-5 rounded-2xl bg-white/5 border border-white/10 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Lore Title</label>
                <input
                  type="text"
                  value={loreTitle}
                  onChange={(e) => setLoreTitle(e.target.value)}
                  placeholder="e.g. Bunty's Notice Period"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Category</label>
                <select
                  value={loreCategory}
                  onChange={(e) => setLoreCategory(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white"
                >
                  <option value="origin">Origin</option>
                  <option value="friends">Friends & Rivals</option>
                  <option value="habits">Habits & Tastes</option>
                  <option value="opinions">Strong Opinions</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Lore Narrative Fact</label>
              <textarea
                value={loreContent}
                onChange={(e) => setLoreContent(e.target.value)}
                placeholder="Detailed backstory fact that will be permanently injected into Kalyan's canonical memory."
                rows={3}
                className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-white"
                required
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAddLore(false)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-500 font-bold text-xs text-white"
              >
                Save Canonical Fact
              </button>
            </div>
          </form>
        )}

        {/* Lore Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {lores.map((l) => (
            <div key={l.id} className="p-4 rounded-xl bg-[#141622] border border-white/10 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-orange-500/20 text-orange-400">
                  {l.category}
                </span>
                <span className="text-[10px] text-emerald-400 font-bold">✓ VERIFIED CANON</span>
              </div>
              <h4 className="text-sm font-bold text-white">{l.title}</h4>
              <p className="text-xs text-slate-300 leading-relaxed">{l.content}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Immutable System Audit Logs */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-orange-400" />
          <h3 className="text-base font-bold text-white">System & Operator Audit Logs ({auditLogs.length})</h3>
        </div>

        <div className="rounded-2xl bg-[#12141c] border border-white/10 overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-white/5 border-b border-white/10 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="p-4">Action</th>
                <th className="p-4">Actor</th>
                <th className="p-4">Target Type</th>
                <th className="p-4">Timestamp</th>
                <th className="p-4">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-white/5 transition">
                  <td className="p-4 font-bold text-white">{log.action}</td>
                  <td className="p-4 text-orange-400">{log.actor_role} ({log.actor_id})</td>
                  <td className="p-4 text-slate-400">{log.target_type || 'system'}</td>
                  <td className="p-4 text-slate-400">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td className="p-4 text-[11px] text-slate-400 truncate max-w-xs">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
