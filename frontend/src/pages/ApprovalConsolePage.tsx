import React, { useEffect, useState } from 'react';
import { 
  CheckSquare, 
  Sparkles, 
  Send, 
  XCircle, 
  Edit3, 
  Check, 
  Filter, 
  RefreshCw, 
  AlertCircle,
  Clock,
  Share2
} from 'lucide-react';
import { api, CandidateItem } from '../services/api';

export const ApprovalConsolePage: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const data = await api.getCandidates(selectedStatus || undefined);
      setCandidates(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [selectedStatus]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      await api.generateCandidates(4, 'x');
      fetchCandidates();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    setActionLoading(id);
    try {
      await api.approveCandidate(id);
      fetchCandidates();
    } finally {
      setActionLoading(null);
    }
  };

  const handlePublish = async (id: string) => {
    setActionLoading(id);
    try {
      await api.publishCandidate(id);
      fetchCandidates();
    } catch (err: any) {
      alert(err.message || 'Publishing failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt("Reason for rejection:", "Does not fit current character tone");
    if (reason === null) return;
    setActionLoading(id);
    try {
      await api.rejectCandidate(id, reason);
      fetchCandidates();
    } finally {
      setActionLoading(null);
    }
  };

  const handleSaveEdit = async (id: string) => {
    try {
      await api.editCandidate(id, editText);
      setEditingId(null);
      fetchCandidates();
    } catch (err) {
      console.error(err);
    }
  };

  const getRiskBadge = (tier: string) => {
    switch (tier) {
      case 'tier_0':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Tier 0 (Safe)</span>;
      case 'tier_1':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">Tier 1 (Review)</span>;
      case 'tier_2':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">Tier 2 (Sensitive Claims)</span>;
      case 'tier_3':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30">Tier 3 (Hazard)</span>;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <CheckSquare className="w-6 h-6 text-orange-400" />
            <h1 className="text-2xl font-extrabold text-white">Human Approval Queue</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Human-in-the-Loop Governance: Inspect risk tiers, review tone, and approve before external social broadcasting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs shadow-lg shadow-orange-600/30 transition disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate New Candidates</span>
          </button>
          <button
            onClick={fetchCandidates}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300"
            title="Refresh list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {[
          { id: '', label: 'All Candidates' },
          { id: 'pending_approval', label: 'Pending Approval' },
          { id: 'approved', label: 'Approved & Ready' },
          { id: 'published', label: 'Published' },
          { id: 'rejected', label: 'Rejected' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedStatus(tab.id)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              selectedStatus === tab.id
                ? 'bg-orange-500 text-white'
                : 'bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Candidate Feed */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs">Loading candidates...</div>
      ) : candidates.length === 0 ? (
        <div className="py-16 text-center border border-dashed border-white/10 rounded-2xl text-slate-400 space-y-2">
          <CheckSquare className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold">No candidates match this filter.</p>
          <p className="text-xs text-slate-500">Click "Generate New Candidates" above to draft fresh posts across the 5 daily formats.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {candidates.map((c) => (
            <div
              key={c.id}
              className="p-5 rounded-2xl bg-[#12141c] border border-white/10 hover:border-white/20 transition space-y-4 shadow-xl"
            >
              {/* Top metadata */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase font-extrabold px-2 py-0.5 rounded bg-white/5 text-slate-300">
                    {c.source_channel.toUpperCase()}
                  </span>
                  <span className="text-xs font-semibold text-orange-400">{c.pillar}</span>
                  <span className="text-xs text-slate-500">• {c.format}</span>
                </div>
                <div className="flex items-center gap-2">
                  {getRiskBadge(c.risk_tier)}
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded uppercase ${
                    c.status === 'published' ? 'bg-purple-500/20 text-purple-400' :
                    c.status === 'approved' ? 'bg-emerald-500/20 text-emerald-400' :
                    c.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                    'bg-amber-500/20 text-amber-400'
                  }`}>
                    {c.status.replace('_', ' ')}
                  </span>
                </div>
              </div>

              {/* Text content or edit area */}
              {editingId === c.id ? (
                <div className="space-y-3">
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={3}
                    className="w-full bg-black/40 border border-orange-500/40 rounded-xl p-3 text-sm text-white focus:outline-none"
                  />
                  <div className="flex items-center gap-2 justify-end">
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSaveEdit(c.id)}
                      className="px-3 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-sm sm:text-base text-slate-100 font-medium leading-relaxed">
                  "{c.candidate_text}"
                </p>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <span className="text-[11px] text-slate-500 font-mono">
                  Created: {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>

                <div className="flex items-center gap-2">
                  {editingId !== c.id && c.status !== 'published' && (
                    <button
                      onClick={() => {
                        setEditingId(c.id);
                        setEditText(c.candidate_text);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Edit</span>
                    </button>
                  )}

                  {c.status === 'pending_approval' && (
                    <>
                      <button
                        onClick={() => handleReject(c.id)}
                        disabled={actionLoading === c.id}
                        className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold flex items-center gap-1.5 transition"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                      <button
                        onClick={() => handleApprove(c.id)}
                        disabled={actionLoading === c.id}
                        className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-md shadow-emerald-600/20"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve</span>
                      </button>
                    </>
                  )}

                  {c.status === 'approved' && (
                    <button
                      onClick={() => handlePublish(c.id)}
                      disabled={actionLoading === c.id}
                      className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-orange-600 to-amber-500 hover:from-orange-500 hover:to-amber-400 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-lg shadow-orange-600/30"
                    >
                      <Share2 className="w-3.5 h-3.5" />
                      <span>Publish Now</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
