import React, { useEffect, useState } from 'react';
import { FlaskConical, TrendingUp, CheckCircle2, RefreshCw, Sparkles, BarChart2 } from 'lucide-react';
import { api } from '../services/api';

export const ExperimentsPage: React.FC = () => {
  const [experiments, setExperiments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchExperiments = async () => {
    setLoading(true);
    try {
      const data = await api.getExperiments();
      setExperiments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-orange-400" />
            <h1 className="text-2xl font-extrabold text-white">A/B Experiments & Hypotheses</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Empirical validation of personality stickiness, cultural fluency (Hinglish vs Telugu vs English), and memory retention.
          </p>
        </div>
        <button
          onClick={fetchExperiments}
          className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs">Loading experiment telemetry...</div>
      ) : (
        <div className="space-y-6">
          {experiments.map((exp) => (
            <div
              key={exp.id}
              className="p-6 rounded-2xl bg-[#12141c] border border-white/10 space-y-5 shadow-xl"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-orange-500/20 text-orange-400 uppercase">
                      {exp.name}
                    </span>
                    <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{exp.status.toUpperCase()}</span>
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-white mt-1.5">{exp.hypothesis}</h3>
                </div>
              </div>

              {/* Variants Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {exp.variants.map((v: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3 flex flex-col justify-between"
                  >
                    <div>
                      <span className="text-[11px] font-mono text-slate-400 block">{v.key}</span>
                      <h4 className="text-sm font-bold text-white mt-0.5">{v.name}</h4>
                    </div>

                    <div className="space-y-2 pt-2 border-t border-white/5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Sample Allocations:</span>
                        <span className="font-mono text-white font-bold">{v.samples}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Shares & Referrals:</span>
                        <span className="font-mono text-orange-400 font-bold">{v.shares}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Conversion Rate:</span>
                        <span className="font-mono text-emerald-400 font-bold">{v.conversion_rate}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
