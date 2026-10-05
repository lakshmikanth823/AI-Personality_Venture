import React, { useState } from 'react';
import { 
  MessageSquare, 
  Sparkles, 
  ArrowRight, 
  Play, 
  Volume2, 
  Pause, 
  CheckCircle2, 
  Flame, 
  Brain, 
  ShieldCheck, 
  Share2,
  Users
} from 'lucide-react';

interface LandingPageProps {
  onNavigate: (page: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const toggleAudio = () => {
    setIsPlayingAudio(!isPlayingAudio);
  };

  const sampleRoasts = [
    {
      prompt: "I want to quit my job and do an MBA to switch fields.",
      reply: "Only if your dream in life is to build PowerPoint slides with arrows pointing in circles while charging ₹30 lakhs for the privilege. What are you actually building right now?"
    },
    {
      prompt: "They haven't texted me in 18 hours, should I send a follow-up?",
      reply: "If they took 18 hours to reply to 'hey', they didn't 'forget their phone,' boss. People check their phones at red lights and weddings. Have some self-respect and close WhatsApp."
    },
    {
      prompt: "My startup will 100x using autonomous reasoning agents.",
      reply: "Every Indian founder's pitch deck right now is 'Uber for laundry, powered by autonomous multi-agent reasoning on the edge.' Bhai, the OTP still doesn't arrive on time."
    }
  ];

  const pillars = [
    { icon: "☕", title: "Indian Internet Life", desc: "WhatsApp family groups, LinkedIn cringe, Ameerpet institute survival." },
    { icon: "💼", title: "College & Job Culture", desc: "Layoffs, notice periods, 90-hour work week myths, startup drama." },
    { icon: "💔", title: "Relationships & Dating", desc: "Filterless dating reality checks, texting etiquette, self-respect." },
    { icon: "🏏", title: "Cricket & Pop Culture", desc: "RCB loyalty coping, Super Over anxiety, Telugu cinema mass takes." },
    { icon: "🤖", title: "AI & Tech Reality", desc: "Calling out hype, practical shipping vs empty buzzwords." }
  ];

  return (
    <div className="min-h-screen bg-[#0b0c10] text-slate-100 flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-28 px-4 sm:px-6 max-w-6xl mx-auto w-full text-center">
        {/* Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-orange-600/15 rounded-full blur-[120px] pointer-events-none" />

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8 animate-in fade-in">
          <span className="text-orange-400 font-bold text-xs uppercase tracking-wider">Social-First Character Media Property</span>
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-ping" />
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6">
          Meet <span className="bg-gradient-to-r from-orange-400 via-amber-300 to-orange-500 bg-clip-text text-transparent">Kalyan</span>.
          <br />
          Your Brutally Honest Internet Dost.
        </h1>

        {/* Tagline */}
        <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
          Zero corporate sugarcoating. 100% filterless reality. Powered by Irani chai, Ameerpet grit, and sharp observational wit.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <button
            onClick={() => onNavigate('chat')}
            className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-orange-600 to-amber-500 hover:from-orange-500 hover:to-amber-400 text-white font-bold text-base shadow-xl shadow-orange-600/30 flex items-center justify-center gap-3 transition transform hover:-translate-y-0.5"
          >
            <MessageSquare className="w-5 h-5" />
            <span>Talk to Kalyan</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => onNavigate('approval')}
            className="w-full sm:w-auto px-6 py-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-200 font-semibold text-sm flex items-center justify-center gap-2 transition"
          >
            <span>Operator Approval Queue</span>
          </button>
        </div>

        {/* Voice Preview Module */}
        <div className="max-w-xl mx-auto p-4 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center justify-between gap-4 shadow-2xl">
          <div className="flex items-center gap-3">
            <button
              onClick={toggleAudio}
              className="w-12 h-12 rounded-xl bg-orange-600 hover:bg-orange-500 flex items-center justify-center text-white shadow-lg shadow-orange-600/30 transition"
            >
              {isPlayingAudio ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
            </button>
            <div className="text-left">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Volume2 className="w-3.5 h-3.5 text-orange-400" />
                <span>Voice Preview: Ameerpet Chai vs Coffee</span>
              </span>
              <p className="text-[11px] text-slate-400 font-mono">hyderabad_expressive_v1.mp3</p>
            </div>
          </div>

          {/* Animated Waveform */}
          <div className="flex items-center gap-1 h-6">
            {[40, 75, 90, 60, 30, 85, 95, 50, 70, 45, 80].map((h, i) => (
              <div
                key={i}
                style={{ height: isPlayingAudio ? `${h}%` : '20%' }}
                className={`w-1 rounded-full bg-orange-500 transition-all duration-300 ${isPlayingAudio ? 'animate-pulse' : 'opacity-40'}`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Sample Roasts Carousel */}
      <section className="py-16 px-4 sm:px-6 max-w-6xl mx-auto w-full border-t border-white/10">
        <div className="text-center mb-12">
          <span className="text-xs uppercase font-bold text-orange-400 tracking-wider">Unfiltered Reality Checks</span>
          <h2 className="text-3xl font-extrabold text-white mt-1">What Happens When You Ask Kalyan</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sampleRoasts.map((roast, idx) => (
            <div
              key={idx}
              className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between hover:border-orange-500/40 transition group"
            >
              <div className="space-y-4">
                <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs text-slate-300 italic">
                  "{roast.prompt}"
                </div>
                <div className="flex items-start gap-2.5">
                  <span className="text-xl">☕</span>
                  <p className="text-sm font-medium text-slate-100 leading-relaxed">
                    {roast.reply}
                  </p>
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-[11px] text-slate-400">
                <span className="font-mono">Kalyan Canon v1.0</span>
                <span className="text-orange-400 font-semibold group-hover:underline cursor-pointer" onClick={() => onNavigate('chat')}>
                  Ask your own →
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Content Pillars */}
      <section className="py-16 px-4 sm:px-6 max-w-6xl mx-auto w-full border-t border-white/10">
        <div className="text-center mb-12">
          <span className="text-xs uppercase font-bold text-orange-400 tracking-wider">Character Universe</span>
          <h2 className="text-3xl font-extrabold text-white mt-1">5 Core Cultural Pillars</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {pillars.map((p, idx) => (
            <div key={idx} className="p-6 rounded-2xl bg-[#13151f] border border-white/10 flex items-start gap-4">
              <span className="text-3xl">{p.icon}</span>
              <div>
                <h4 className="font-bold text-white text-base mb-1">{p.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{p.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Moat Ladder & Architectural Trust */}
      <section className="py-16 px-4 sm:px-6 max-w-6xl mx-auto w-full border-t border-white/10 mb-12">
        <div className="p-8 rounded-3xl bg-gradient-to-br from-orange-950/40 via-black to-[#0d0e14] border border-orange-500/20 text-center space-y-4">
          <h3 className="text-2xl font-extrabold text-white">The Long-Term Character Moat</h3>
          <p className="text-sm text-slate-300 max-w-xl mx-auto">
            Character → Audience → Lore/Community → Interaction Data → Creator Ecosystem → Licensable Character IP.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-xs font-semibold text-slate-300">
            <span className="flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-emerald-400" /> 4-Tier Risk Safety Engine</span>
            <span className="flex items-center gap-1.5"><Brain className="w-4 h-4 text-blue-400" /> 4-Level Memory + Anti-Poisoning</span>
            <span className="flex items-center gap-1.5"><Users className="w-4 h-4 text-orange-400" /> Weekly Meaningful Relationships (WMCR)</span>
          </div>
        </div>
      </section>
    </div>
  );
};
