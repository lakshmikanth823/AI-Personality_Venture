import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Brain, 
  Share2, 
  Sparkles, 
  Clock, 
  DollarSign, 
  AlertTriangle,
  RotateCcw,
  Coffee
} from 'lucide-react';
import { api, ChatMessage } from '../services/api';
import { ShareCardModal } from '../components/ShareCardModal';
import { MemoryManagerModal } from '../components/MemoryManagerModal';

interface ChatPageProps {
  currentUser: any;
  onRefreshUser: () => void;
}

interface DisplayMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  meta?: {
    latency_ms?: number;
    cost_usd?: number;
    tokens_out?: number;
    risk_tier?: string;
    memory_created?: string;
  };
}

export const ChatPage: React.FC<ChatPageProps> = ({ currentUser, onRefreshUser }) => {
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Chusa chusa! Kalyan here. Zero corporate sugarcoating, 100% filterless reality. Tell me what's going on—job stress, dating circus, or did someone try to sell you a 50x crypto token?",
      meta: { latency_ms: 15, cost_usd: 0.00001, tokens_out: 42, risk_tier: 'tier_0' }
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [convId, setConvId] = useState<string | undefined>(undefined);
  const [langPref, setLangPref] = useState('hinglish');
  const [shareQuote, setShareQuote] = useState<{ quote: string; prompt?: string } | null>(null);
  const [showMemoryModal, setShowMemoryModal] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const quickStarters = [
    "My manager scheduled a 1-on-1 on Friday 6 PM. Am I getting fired?",
    "Should I switch to management or stay in technical coding?",
    "Crush took 18 hours to reply to 'hey'. Should I double-text?",
    "Explain why Irani chai is better than fancy pour-over coffee."
  ];

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsgId = Date.now().toString();
    const newMessages: DisplayMessage[] = [
      ...messages,
      { id: userMsgId, role: 'user', content: text }
    ];
    setMessages(newMessages);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const resp = await api.sendMessage(text, convId, langPref);
      setConvId(resp.conversation_id);

      setMessages([
        ...newMessages,
        {
          id: resp.message_id,
          role: 'assistant',
          content: resp.content,
          meta: {
            latency_ms: resp.latency_ms,
            cost_usd: resp.cost_usd,
            tokens_out: resp.tokens_output,
            risk_tier: resp.risk_tier,
            memory_created: resp.memory_created
          }
        }
      ]);
    } catch (err) {
      console.error(err);
      setMessages([
        ...newMessages,
        {
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: "Arre babu, connection glitched for a second. The Ameerpet broadband cable must be loose. Try sending that again!"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-[#0b0c10]">
      {/* Top Bar Controls */}
      <div className="border-b border-white/10 bg-[#10121a] px-4 py-2.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Coffee className="w-4 h-4 text-orange-400" />
          <span className="text-xs font-bold text-white">Banter Tone:</span>
          <div className="flex items-center gap-1">
            {[
              { id: 'hinglish', label: 'Hinglish' },
              { id: 'telugu_hinglish', label: 'Telugu-Infused' },
              { id: 'english', label: 'Standard English' }
            ].map((lang) => (
              <button
                key={lang.id}
                onClick={() => setLangPref(lang.id)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
                  langPref === lang.id
                    ? 'bg-orange-500 text-white shadow-sm'
                    : 'bg-white/5 text-slate-400 hover:text-white'
                }`}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowMemoryModal(true)}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 border border-white/10 hover:border-orange-500/40 text-xs text-slate-200 transition"
          >
            <Brain className="w-3.5 h-3.5 text-orange-400" />
            <span className="hidden sm:inline">Kalyan's Memory of Me</span>
          </button>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-4xl mx-auto w-full">
        {messages.map((msg, idx) => (
          <div
            key={msg.id}
            className={`flex gap-3 sm:gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-orange-600 to-amber-500 flex-shrink-0 flex items-center justify-center text-sm shadow-md">
                ☕
              </div>
            )}

            <div className={`max-w-[85%] sm:max-w-[75%] space-y-2 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-orange-600 text-white rounded-br-none shadow-md shadow-orange-600/20'
                    : 'bg-[#151722] text-slate-100 border border-white/10 rounded-bl-none shadow-xl'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>

              {/* Telemetry & Action Bar for Assistant */}
              {msg.role === 'assistant' && msg.meta && (
                <div className="flex items-center gap-3 text-[10px] text-slate-400 px-1">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{msg.meta.latency_ms}ms</span>
                  </span>
                  <span className="flex items-center gap-0.5">
                    <DollarSign className="w-3 h-3 text-slate-500" />
                    <span>${msg.meta.cost_usd}</span>
                  </span>
                  {msg.meta.risk_tier && (
                    <span className="px-1.5 py-0.2 rounded bg-black/40 text-slate-400 border border-white/5 uppercase">
                      {msg.meta.risk_tier}
                    </span>
                  )}
                  {msg.meta.memory_created && (
                    <span className="text-orange-400 font-medium">
                      🧠 Learned: {msg.meta.memory_created.split(':')[0]}
                    </span>
                  )}
                  <button
                    onClick={() => {
                      const userPrompt = messages[idx - 1]?.content;
                      setShareQuote({ quote: msg.content, prompt: userPrompt });
                    }}
                    className="ml-auto text-orange-400 hover:text-orange-300 font-semibold flex items-center gap-1"
                  >
                    <Share2 className="w-3 h-3" />
                    <span>Share Card</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 items-center">
            <div className="w-8 h-8 rounded-xl bg-orange-600 flex items-center justify-center text-sm shadow-md animate-pulse">
              ☕
            </div>
            <div className="p-3.5 rounded-2xl bg-[#151722] border border-white/10 text-xs text-slate-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-orange-500 animate-ping" />
              <span>Kalyan is brewing a filterless reply...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Starters Carousel */}
      {messages.length <= 2 && (
        <div className="max-w-4xl mx-auto w-full px-4 pb-2">
          <div className="flex items-center gap-2 overflow-x-auto py-1 scrollbar-none">
            {quickStarters.map((starter, i) => (
              <button
                key={i}
                onClick={() => handleSend(starter)}
                className="whitespace-nowrap px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-300 transition"
              >
                "{starter}"
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Bar */}
      <div className="border-t border-white/10 bg-[#10121a] p-3 sm:p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="max-w-4xl mx-auto flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Kalyan anything (career, dating, startup, life reality-check)..."
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 transition"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-3 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 hover:from-orange-500 hover:to-amber-400 text-white font-bold transition disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-orange-600/30"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Modals */}
      {shareQuote && (
        <ShareCardModal
          quote={shareQuote.quote}
          contextPrompt={shareQuote.prompt}
          onClose={() => setShareQuote(null)}
        />
      )}

      {showMemoryModal && (
        <MemoryManagerModal
          onClose={() => setShowMemoryModal(false)}
          currentUser={currentUser}
          onRefreshUser={onRefreshUser}
        />
      )}
    </div>
  );
};
