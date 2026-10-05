import React, { useEffect, useState } from 'react';
import { X, Brain, Trash2, Shield, Download, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface MemoryManagerModalProps {
  onClose: () => void;
  currentUser: any;
  onRefreshUser: () => void;
}

export const MemoryManagerModal: React.FC<MemoryManagerModalProps> = ({ onClose, currentUser, onRefreshUser }) => {
  const [memories, setMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [personalization, setPersonalization] = useState(currentUser?.personalization_enabled ?? true);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const data = await api.getMemories();
      setMemories(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleDelete = async (id: string) => {
    await api.deleteMemory(id);
    setMemories(memories.filter(m => m.id !== id));
  };

  const handleClearAll = async () => {
    if (window.confirm("Are you sure you want Kalyan to forget everything about you?")) {
      await api.clearMemories();
      setMemories([]);
    }
  };

  const handleTogglePersonalization = async (val: boolean) => {
    setPersonalization(val);
    await api.togglePersonalization(val);
    onRefreshUser();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-xl rounded-2xl bg-[#14161f] border border-white/10 shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-orange-400" />
            <div>
              <h3 className="font-bold text-white text-base">Kalyan's Memory of You</h3>
              <p className="text-[11px] text-slate-400">Level 3 Durable User Memory & Privacy Controls</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Privacy Switch */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-sm font-semibold text-white">Enable Long-Term Personalization</span>
              <p className="text-xs text-slate-400">Allow Kalyan to remember your career, preferences, and goals</p>
            </div>
            <button
              onClick={() => handleTogglePersonalization(!personalization)}
              className={`w-12 h-6 rounded-full transition relative ${personalization ? 'bg-orange-600' : 'bg-white/10'}`}
            >
              <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition ${personalization ? 'right-1' : 'left-1'}`} />
            </button>
          </div>

          {/* Stored Memories List */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Durable Facts ({memories.length})
              </span>
              {memories.length > 0 && (
                <button
                  onClick={handleClearAll}
                  className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 font-semibold"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Wipe All Memories</span>
                </button>
              )}
            </div>

            {loading ? (
              <div className="py-8 text-center text-slate-400 text-xs">Loading memories...</div>
            ) : memories.length === 0 ? (
              <div className="py-8 text-center border border-dashed border-white/10 rounded-xl text-slate-400 space-y-1">
                <Brain className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="text-xs font-medium">No durable facts stored yet.</p>
                <p className="text-[11px] text-slate-500">Mention your job, favorite cricket team, or goals in chat.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {memories.map((m) => (
                  <div
                    key={m.id}
                    className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start justify-between gap-3 group hover:border-orange-500/30 transition"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-orange-500/20 text-orange-400">
                          {m.category || 'fact'}
                        </span>
                        <span className="text-xs font-semibold text-slate-200">{m.key}</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{m.value}</p>
                    </div>
                    <button
                      onClick={() => handleDelete(m.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-white/10 transition"
                      title="Delete this memory"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-400 bg-black/20">
          <span className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>Anti-poisoning & Indian DPDP Act compliant</span>
          </span>
          <button
            onClick={() => {
              const blob = new Blob([JSON.stringify(memories, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `kalyan_memories_export.json`;
              a.click();
            }}
            className="flex items-center gap-1 hover:text-white"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>
    </div>
  );
};
