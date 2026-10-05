import React, { useEffect, useState } from 'react';
import { Sparkles, Check, Zap, Crown, Flame, ShieldCheck, Heart } from 'lucide-react';
import { api } from '../services/api';

interface MonetizationPageProps {
  currentUser: any;
  onRefreshUser: () => void;
}

export const MonetizationPage: React.FC<MonetizationPageProps> = ({ currentUser, onRefreshUser }) => {
  const [plans, setPlans] = useState<any[]>([]);
  const [entitlement, setEntitlement] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const p = await api.getPlans();
      setPlans(p);
      if (currentUser) {
        const ent = await api.getMyEntitlement();
        setEntitlement(ent);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [currentUser]);

  const handleCheckout = async (planKey: string) => {
    if (!currentUser) {
      alert("Please log in or switch to a demo user first via the top right menu.");
      return;
    }
    setPurchasing(planKey);
    try {
      const res = await api.checkout(planKey);
      alert(`Success! ${res.message} (Reference: ${res.payment_reference})`);
      fetchData();
      onRefreshUser();
    } catch (err: any) {
      alert(err.message || 'Payment simulation failed');
    } finally {
      setPurchasing(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2 pb-6 border-b border-white/10">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-bold uppercase">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Monetization Ladder (Blueprint §6)</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">Upgrade Your Dost Level</h1>
        <p className="text-xs sm:text-sm text-slate-400">
          Support independent character IP. Get unlimited reality checks, voice messages, and official canonical lore features.
        </p>

        {entitlement && (
          <div className="pt-2">
            <span className="text-xs font-semibold px-3 py-1 rounded-full bg-white/5 border border-white/10 text-slate-200">
              Current Plan: <span className="text-orange-400 font-bold">{entitlement.plan_name}</span> (Limit: {entitlement.daily_message_limit} msgs/day)
            </span>
          </div>
        )}
      </div>

      {/* Pricing Cards Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs">Loading plans...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {plans.map((p) => {
            const isCurrent = entitlement?.tier === p.tier_key;
            return (
              <div
                key={p.tier_key}
                className={`p-6 rounded-2xl bg-[#12141c] border flex flex-col justify-between transition relative shadow-xl ${
                  p.tier_key === 'fan_pass_149'
                    ? 'border-orange-500 shadow-orange-500/10'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                {p.tier_key === 'fan_pass_149' && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-gradient-to-r from-orange-600 to-amber-500 text-white text-[10px] font-extrabold uppercase tracking-wider shadow-md">
                    Most Popular
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <h3 className="text-base font-bold text-white">{p.name}</h3>
                    <div className="mt-3 flex items-baseline gap-1">
                      <span className="text-3xl font-extrabold text-white">₹{p.price_inr}</span>
                      {p.price_inr > 0 && <span className="text-xs text-slate-400">/mo</span>}
                    </div>
                  </div>

                  <ul className="space-y-2 pt-2 border-t border-white/5 text-xs text-slate-300">
                    <li className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{p.daily_limit} messages per day</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{p.has_priority_memory ? 'Priority L3 Durable Memory' : 'Standard Session Memory'}</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className={`w-3.5 h-3.5 ${p.has_voice ? 'text-emerald-400' : 'text-slate-600'}`} />
                      <span className={p.has_voice ? 'text-white font-medium' : 'text-slate-500'}>
                        {p.has_voice ? 'Voice Notes Simulation' : 'Text Only'}
                      </span>
                    </li>
                  </ul>
                </div>

                <div className="mt-6 pt-4 border-t border-white/5">
                  <button
                    onClick={() => handleCheckout(p.tier_key)}
                    disabled={isCurrent || purchasing === p.tier_key}
                    className={`w-full py-2.5 rounded-xl font-bold text-xs transition ${
                      isCurrent
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 cursor-default'
                        : p.tier_key === 'fan_pass_149'
                        ? 'bg-gradient-to-r from-orange-600 to-amber-500 hover:from-orange-500 hover:to-amber-400 text-white shadow-lg shadow-orange-600/30'
                        : 'bg-white/10 hover:bg-white/15 text-white'
                    }`}
                  >
                    {isCurrent ? 'Active Plan' : purchasing === p.tier_key ? 'Processing...' : `Upgrade for ₹${p.price_inr}`}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Safety & Value Warning Note */}
      <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400" />
        <span>All transactions simulate Razorpay / UPI test workflows with instant idempotent entitlement grants.</span>
      </div>
    </div>
  );
};
