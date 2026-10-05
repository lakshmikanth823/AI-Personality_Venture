import React, { useState } from 'react';
import { X, Share2, Copy, Check, Download, Sparkles } from 'lucide-react';

interface ShareCardModalProps {
  quote: string;
  contextPrompt?: string;
  onClose: () => void;
}

export const ShareCardModal: React.FC<ShareCardModalProps> = ({ quote, contextPrompt, onClose }) => {
  const [copied, setCopied] = useState(false);
  const [theme, setTheme] = useState<'ameerpet' | 'cyberabad' | 'vintage'>('ameerpet');

  const themes = {
    ameerpet: 'from-orange-950 via-[#181216] to-[#0c0d12] border-orange-500/40 text-orange-400',
    cyberabad: 'from-cyan-950 via-[#101925] to-[#0c0d12] border-cyan-500/40 text-cyan-400',
    vintage: 'from-amber-950 via-[#1a1410] to-[#0c0d12] border-amber-500/40 text-amber-400'
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(`"${quote}" — Kalyan (@kalyan_unfiltered) #BrutallyHonest #KalyanAI`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-[#14161f] border border-white/10 shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-orange-400" />
            <h3 className="font-bold text-white text-base">Viral Quote Card</h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Card Preview Container */}
        <div className="p-6 flex flex-col items-center justify-center bg-black/40">
          <div 
            id="share-card"
            className={`w-full rounded-2xl p-6 bg-gradient-to-br border shadow-2xl flex flex-col justify-between min-h-[260px] ${themes[theme]}`}
          >
            {/* Top Bar of Card */}
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-orange-500 to-amber-400 flex items-center justify-center text-lg shadow-md">
                  ☕
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-white text-sm">Kalyan</span>
                    <span className="w-3.5 h-3.5 rounded-full bg-blue-500 text-white text-[9px] flex items-center justify-center font-bold">✓</span>
                  </div>
                  <span className="text-[11px] text-slate-400">@kalyan_unfiltered</span>
                </div>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-black/40 text-slate-300 border border-white/10">
                Reality Check
              </span>
            </div>

            {/* Prompt context if available */}
            {contextPrompt && (
              <p className="text-xs text-slate-400 italic line-clamp-1 my-2">
                Replying to: "{contextPrompt}"
              </p>
            )}

            {/* Quote Body */}
            <div className="my-4">
              <p className="text-base sm:text-lg font-medium text-slate-100 leading-relaxed tracking-tight">
                "{quote}"
              </p>
            </div>

            {/* Footer Watermark */}
            <div className="flex items-center justify-between pt-4 border-t border-white/10 text-[11px] text-slate-400">
              <span>Zero Corporate Sugarcoating</span>
              <span className="font-mono text-orange-400 font-bold">kalyan.ai</span>
            </div>
          </div>
        </div>

        {/* Theme Picker & Action Buttons */}
        <div className="p-6 border-t border-white/10 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Card Theme:</span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setTheme('ameerpet')}
                className={`px-3 py-1 rounded-md text-xs font-semibold ${theme === 'ameerpet' ? 'bg-orange-500 text-white' : 'bg-white/5 text-slate-300'}`}
              >
                Ameerpet Irani
              </button>
              <button
                onClick={() => setTheme('cyberabad')}
                className={`px-3 py-1 rounded-md text-xs font-semibold ${theme === 'cyberabad' ? 'bg-cyan-500 text-white' : 'bg-white/5 text-slate-300'}`}
              >
                Cyberabad Neon
              </button>
              <button
                onClick={() => setTheme('vintage')}
                className={`px-3 py-1 rounded-md text-xs font-semibold ${theme === 'vintage' ? 'bg-amber-600 text-white' : 'bg-white/5 text-slate-300'}`}
              >
                Filter Coffee
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleCopy}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-500 font-bold text-white text-xs transition shadow-lg shadow-orange-600/30"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              <span>{copied ? 'Copied to Clipboard!' : 'Copy Quote Text'}</span>
            </button>
            <button
              onClick={() => {
                const tweetUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(`"${quote}" — Kalyan (@kalyan_unfiltered)\n\nhttps://kalyan.ai`)}`;
                window.open(tweetUrl, '_blank');
              }}
              className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-bold text-xs flex items-center gap-2 transition"
            >
              <Share2 className="w-4 h-4" />
              <span>Share to X</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
