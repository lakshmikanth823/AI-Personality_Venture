import React, { useEffect, useState } from 'react';
import { Layers, Send, ExternalLink, RefreshCw, CheckCircle2, Flame, Globe } from 'lucide-react';
import { api } from '../services/api';

export const ContentLibraryPage: React.FC = () => {
  const [published, setPublished] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getPublishedHistory();
      setPublished(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const contentMix = [
    { format: "Reactive Replies", pct: "30%", color: "bg-blue-500", desc: "Quoting & answering trending tech & culture tweets" },
    { format: "Original Observations", pct: "25%", color: "bg-orange-500", desc: "Unfiltered reality checks on Indian jobs, college & startups" },
    { format: "User Situations", pct: "20%", color: "bg-amber-500", desc: "Real dilemnas submitted by followers ('My boss did X')" },
    { format: "Recurring Series", pct: "15%", color: "bg-purple-500", desc: "Monday Reality Check, Startup Red Flag of the Day" },
    { format: "Character Lore / Community", pct: "10%", color: "bg-emerald-500", desc: "Bunty misadventures, Ameerpet institute survival lore" },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-6 h-6 text-orange-400" />
            <h1 className="text-2xl font-extrabold text-white">Content Library & Publishing</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            GTM Content Distribution Engine — Strategic 5-Format Mix & Social Adapters (X, Instagram, YouTube, WhatsApp).
          </p>
        </div>
        <button
          onClick={fetchHistory}
          className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Strategic Mix Distribution Card */}
      <div className="p-6 rounded-2xl bg-[#12141c] border border-white/10 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Flame className="w-4 h-4 text-orange-400" />
          <span>Strategic Daily Content Mix (GTM Blueprint §5)</span>
        </h3>

        {/* Visual Progress Bar */}
        <div className="w-full h-3 rounded-full bg-white/5 flex overflow-hidden">
          <div style={{ width: '30%' }} className="bg-blue-500" title="30% Reactive Replies" />
          <div style={{ width: '25%' }} className="bg-orange-500" title="25% Original Observations" />
          <div style={{ width: '20%' }} className="bg-amber-500" title="20% User Situations" />
          <div style={{ width: '15%' }} className="bg-purple-500" title="15% Recurring Series" />
          <div style={{ width: '10%' }} className="bg-emerald-500" title="10% Lore & Community" />
        </div>

        {/* Legend */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-2">
          {contentMix.map((item, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-white/5 border border-white/5 space-y-1">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                <span className="text-xs font-bold text-white">{item.format}</span>
                <span className="text-xs font-mono text-slate-400 ml-auto">{item.pct}</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Published Feeds */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Globe className="w-4 h-4 text-orange-400" />
          <span>Recently Published Across Social Channels ({published.length})</span>
        </h3>

        {loading ? (
          <div className="py-12 text-center text-slate-400 text-xs">Loading published history...</div>
        ) : published.length === 0 ? (
          <div className="py-12 text-center border border-dashed border-white/10 rounded-2xl text-slate-400">
            No published posts yet. Approve and publish candidates in the Approval Queue!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {published.map((p) => (
              <div
                key={p.id}
                className="p-5 rounded-2xl bg-[#141622] border border-white/10 flex flex-col justify-between gap-3 shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-orange-500/20 text-orange-400">
                      {p.channel.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      ID: {p.external_post_id}
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{p.status}</span>
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-white/5 text-[11px] text-slate-400">
                  <span>{new Date(p.published_at).toLocaleString()}</span>
                  <a
                    href={`https://${p.channel}.com/kalyan_unfiltered`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-orange-400 hover:text-orange-300 font-semibold flex items-center gap-1"
                  >
                    <span>View Post</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
