import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  Cpu, 
  HeartHandshake, 
  RefreshCw, 
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
  PieChart
} from 'lucide-react';
import { api, AnalyticsDashboard } from '../services/api';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-orange-400" />
            <h1 className="text-2xl font-extrabold text-white">Analytics, Unit Economics & Cost</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Tracking Weekly Meaningful Character Relationships (WMCR), token budgets, and contribution margins.
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading || !data ? (
        <div className="py-20 text-center text-slate-400 text-xs">Computing real-time telemetry metrics...</div>
      ) : (
        <>
          {/* Key Metric KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* North-Star WMCR */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-orange-950/60 to-[#12141c] border border-orange-500/30 space-y-2 shadow-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-extrabold text-orange-400 tracking-wider">North-Star Metric</span>
                <HeartHandshake className="w-4 h-4 text-orange-400" />
              </div>
              <div className="text-3xl font-extrabold text-white">{data.north_star_wmcr}</div>
              <p className="text-[11px] text-slate-300">
                Weekly Meaningful Character Relationships (≥3 interactions/7d)
              </p>
            </div>

            {/* Active Users */}
            <div className="p-5 rounded-2xl bg-[#12141c] border border-white/10 space-y-2 shadow-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-bold text-slate-400">DAU / WAU</span>
                <TrendingUp className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-3xl font-extrabold text-white">
                {data.dau} <span className="text-sm font-normal text-slate-400">/ {data.wau}</span>
              </div>
              <p className="text-[11px] text-slate-400">Daily Active Users / Weekly Active Users</p>
            </div>

            {/* Tokens Processed */}
            <div className="p-5 rounded-2xl bg-[#12141c] border border-white/10 space-y-2 shadow-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-bold text-slate-400">Tokens Processed</span>
                <Cpu className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-white">
                {data.total_tokens_processed.toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-400">
                Inference Cost: ${data.total_cost_usd} (₹{data.total_cost_inr})
              </p>
            </div>

            {/* Contribution Margin */}
            <div className="p-5 rounded-2xl bg-[#12141c] border border-white/10 space-y-2 shadow-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-bold text-slate-400">Contribution Margin</span>
                <DollarSign className="w-4 h-4 text-amber-400" />
              </div>
              <div className={`text-3xl font-extrabold ${data.contribution_margin_inr >= 0 ? 'text-emerald-400' : 'text-slate-300'}`}>
                ₹{data.contribution_margin_inr}
              </div>
              <p className="text-[11px] text-slate-400">
                Revenue ₹{data.total_revenue_inr} − Inference & Cloud fees
              </p>
            </div>
          </div>

          {/* Unit Economics Formula Banner */}
          <div className="p-5 rounded-2xl bg-black/40 border border-white/10 space-y-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Unit Economics Formula (PRD §6):</span>
            <div className="p-3 rounded-xl bg-white/5 font-mono text-xs text-orange-300 flex flex-wrap items-center gap-2">
              <span>Revenue/User</span>
              <span>−</span>
              <span>Inference (${data.total_cost_usd})</span>
              <span>−</span>
              <span>Platform/Payment Fees (2%)</span>
              <span>−</span>
              <span>Infrastructure</span>
              <span>=</span>
              <span className="font-bold text-white">Contribution Margin (₹{data.contribution_margin_inr})</span>
            </div>
          </div>

          {/* Strategic Decision Rules Evaluation */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-orange-400" />
              <span>Automated Business Decision Rules (Blueprint §8)</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.strategic_insights.map((insight, idx) => (
                <div key={idx} className="p-5 rounded-2xl bg-[#141622] border border-white/10 space-y-2 shadow-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-orange-400 uppercase tracking-wider">
                      {insight.rule}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white/10 text-slate-300">
                      {insight.diagnosis}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-medium">
                    {insight.recommended_action}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Feature-Level Cost Attribution Table */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <PieChart className="w-4 h-4 text-orange-400" />
              <span>Feature-Level Cost Attribution</span>
            </h3>

            <div className="rounded-2xl bg-[#12141c] border border-white/10 overflow-hidden shadow-xl">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-white/5 border-b border-white/10 text-slate-400 uppercase font-semibold">
                  <tr>
                    <th className="p-4">Feature Component</th>
                    <th className="p-4">Invocation Calls</th>
                    <th className="p-4">Attributed Cost (USD)</th>
                    <th className="p-4">Cost (INR)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.feature_breakdown.map((item, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition">
                      <td className="p-4 font-mono font-bold text-white">{item.feature}</td>
                      <td className="p-4">{item.calls}</td>
                      <td className="p-4 font-mono text-orange-400">${item.cost_usd}</td>
                      <td className="p-4 font-mono">₹{round(item.cost_usd * 86.0, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const round = (num: number, dec: number) => {
  return Number(Math.round(Number(num + 'e' + dec)) + 'e-' + dec);
};
