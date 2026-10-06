"""
backend/scripts/run_real_gemini_100_benchmark.py
Real Google Gemini Live End-to-End Evaluation & Unit Economics Analysis
Evaluates authentic character quality, token consumption, latency, and margin economics.
"""

import sys
import os
import time
import asyncio
import json
import statistics
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.core.config import settings
from backend.app.services.model_provider import LiveGeminiProvider
from backend.app.services.persona_engine import KALYAN_CONSTITUTION

# Representative benchmark test prompts covering core character pillars
BENCHMARK_PROMPTS = [
    # Career & Resume Reality Checks
    {"id": "C-01", "pillar": "career", "prompt": "I have 6 months of experience and I am demanding a 30 LPA package. Am I right?"},
    {"id": "C-02", "pillar": "career", "prompt": "My manager asked me to work this Saturday for a release. Should I quit?"},
    {"id": "C-03", "pillar": "career", "prompt": "Is doing 500 LeetCode problems enough to get into Google?"},
    {"id": "C-04", "pillar": "career", "prompt": "I got rejected by TCS, Infosys, and Wipro. Is my tech career over?"},
    {"id": "C-05", "pillar": "career", "prompt": "Should I pay 50k for an Ameerpet Full Stack Java certification?"},
    
    # Startup & Venture Reality Checks
    {"id": "S-01", "pillar": "startup", "prompt": "I am building an AI app that generates LinkedIn appreciation posts. Will VCs fund it?"},
    {"id": "S-02", "pillar": "startup", "prompt": "My startup has 10 users and ₹0 revenue. When should I buy the fancy office beanbags?"},
    {"id": "S-03", "pillar": "startup", "prompt": "We are pivoting our tea shop into a Web3 blockchain chai subscription platform."},
    
    # Dating, Society & Life Dilemmas
    {"id": "D-01", "pillar": "dating_life", "prompt": "She replied after 14 hours with 'k'. Should I send a 3-paragraph explanation?"},
    {"id": "D-02", "pillar": "dating_life", "prompt": "My parents want me to marry an NRI engineer who lives in New Jersey. What to do?"},
    {"id": "D-03", "pillar": "dating_life", "prompt": "Sharma ji ka beta just bought a 3BHK in Gachibowli and my mom is giving me the look."},
    
    # Tech & Indian Internet Banter
    {"id": "T-01", "pillar": "tech_humor", "prompt": "Why does every startup CEO claim they work 100 hours a week on Twitter?"},
    {"id": "T-02", "pillar": "tech_humor", "prompt": "RCB will definitely win the trophy this season, right?"},
    {"id": "T-03", "pillar": "tech_humor", "prompt": "Is prompt engineering a real 50 LPA engineering discipline?"}
]

async def run_gemini_quality_and_economics_benchmark(sample_size: int = 14):
    print("=" * 75)
    print("  🚀 KALYAN AI: REAL GEMINI QUALITY & UNIT ECONOMICS BENCHMARK")
    print("=" * 75)
    
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not configured in .env or settings.")
        return
    
    provider = LiveGeminiProvider(api_key=api_key)
    
    results = []
    latencies = []
    costs_usd = []
    input_tokens = []
    output_tokens = []
    
    prompts_to_run = BENCHMARK_PROMPTS[:sample_size]
    print(f"Executing {len(prompts_to_run)} live Gemini conversations...\n")
    
    for idx, item in enumerate(prompts_to_run, start=1):
        print(f"[{idx:02d}/{len(prompts_to_run):02d}] Evaluating [{item['pillar'].upper()}]: \"{item['prompt']}\"")
        messages = [{"role": "user", "content": item["prompt"]}]
        
        t0 = time.time()
        try:
            resp = await provider.generate(
                messages=messages,
                system_prompt=KALYAN_CONSTITUTION,
                temperature=0.7,
                max_tokens=350
            )
            dt = time.time() - t0
            
            latencies.append(resp.latency_ms)
            costs_usd.append(resp.cost_usd)
            input_tokens.append(resp.tokens_input)
            output_tokens.append(resp.tokens_output)
            
            # Authenticity check: presence of character idioms
            text_lower = resp.content.lower()
            has_character_flavor = any(w in text_lower for w in ["boss", "guru", "bhai", "babu", "dost", "sharma", "chai", "ameerpet", "package", "resume", "startup", "arre", "dekho"])
            
            results.append({
                "id": item["id"],
                "pillar": item["pillar"],
                "prompt": item["prompt"],
                "latency_ms": resp.latency_ms,
                "input_tokens": resp.tokens_input,
                "output_tokens": resp.tokens_output,
                "cost_usd": resp.cost_usd,
                "cost_inr": resp.cost_usd * 86.5,
                "character_flavor": has_character_flavor,
                "snippet": resp.content.replace("\n", " ")[:120] + "..."
            })
            print(f"    ✓ Latency: {resp.latency_ms:.0f}ms | Tokens: In={resp.tokens_input}, Out={resp.tokens_output} | Cost: ₹{resp.cost_usd * 86.5:.4f}")
            print(f"    Sample: \"{resp.content.strip()[:90]}...\"\n")
            
            # Gentle pacing between live API requests
            await asyncio.sleep(1.0)
            
        except Exception as e:
            print(f"    ✗ API Error: {type(e).__name__}: {e}\n")
    
    if not results:
        print("[!] No benchmark results collected.")
        return
        
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    avg_in_tok = statistics.mean(input_tokens)
    avg_out_tok = statistics.mean(output_tokens)
    avg_cost_usd = statistics.mean(costs_usd)
    avg_cost_inr = avg_cost_usd * 86.5
    total_cost_usd = sum(costs_usd)
    total_cost_inr = total_cost_usd * 86.5
    flavor_pass_rate = (sum(1 for r in results if r["character_flavor"]) / len(results)) * 100
    
    # -------------------------------------------------------------
    # UNIT ECONOMICS MODELING
    # -------------------------------------------------------------
    # Tier 1: Single Roast Plan (₹49) -> ~3 conversational turns
    cost_single_roast_inr = avg_cost_inr * 3
    gross_margin_single_roast = ((49.0 - cost_single_roast_inr) / 49.0) * 100
    
    # Tier 2: Fan Pass Monthly Plan (₹149) -> Active user ~150 messages/month
    cost_fan_pass_monthly_inr = avg_cost_inr * 150
    gross_margin_fan_pass = ((149.0 - cost_fan_pass_monthly_inr) / 149.0) * 100
    
    print("\n" + "=" * 75)
    print("  📊 BENCHMARK SUMMARY & REAL PERFORMANCE TELEMETRY")
    print("=" * 75)
    print(f"Total Live Turns Evaluated:  {len(results)}")
    print(f"Average Turn Latency:       {avg_latency:.1f} ms (p95: {p95_latency:.1f} ms)")
    print(f"Average Input Tokens:       {avg_in_tok:.1f} tokens")
    print(f"Average Output Tokens:      {avg_out_tok:.1f} tokens")
    print(f"Average Cost Per Turn:      ${avg_cost_usd:.6f} USD (~₹{avg_cost_inr:.4f} INR)")
    print(f"Character Authenticity:     {flavor_pass_rate:.1f}% on-brand")
    
    print("\n" + "-" * 75)
    print("  💰 REAL-WORLD COMMERCIAL UNIT ECONOMICS")
    print("-" * 75)
    print(f"1. ₹49 Single Roast (3 turns):")
    print(f"   - LLM Inference Cost:    ₹{cost_single_roast_inr:.3f} INR")
    print(f"   - Payment Gateway Fee:   ~₹1.00 INR (2%)")
    print(f"   - Gross Profit:          ₹{49.0 - cost_single_roast_inr - 1.00:.2f} INR")
    print(f"   - Gross Margin:          {gross_margin_single_roast:.1f}%")
    print()
    print(f"2. ₹149 Fan Pass (150 turns/month):")
    print(f"   - LLM Inference Cost:    ₹{cost_fan_pass_monthly_inr:.3f} INR")
    print(f"   - Payment Gateway Fee:   ~₹3.00 INR (2%)")
    print(f"   - Gross Profit:          ₹{149.0 - cost_fan_pass_monthly_inr - 3.00:.2f} INR")
    print(f"   - Gross Margin:          {gross_margin_fan_pass:.1f}%")
    print("=" * 75)
    
    # Write summary artifact to docs/EVIDENCE
    evidence_path = repo_root / "docs" / "EVIDENCE" / "E48_real_gemini_benchmark_and_economics.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": "gemini-3.5-flash-lite",
            "evaluated_turns": len(results),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_cost_usd": round(avg_cost_usd, 6),
            "avg_cost_inr": round(avg_cost_inr, 4),
            "single_roast_gross_margin_pct": round(gross_margin_single_roast, 1),
            "fan_pass_gross_margin_pct": round(gross_margin_fan_pass, 1),
            "character_authenticity_pct": round(flavor_pass_rate, 1),
            "sample_turns": results
        }, f, indent=2)
    print(f"\n[+] Benchmark evidence and economics record written to: {evidence_path.name}\n")

if __name__ == "__main__":
    asyncio.run(run_gemini_quality_and_economics_benchmark())
