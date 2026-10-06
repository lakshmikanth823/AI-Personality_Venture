"""
backend/scripts/simulate_closed_beta_cohort.py
Closed Beta Cohort Simulation & Retention Analysis (50 Users, 30 Days)
Models organic user engagement, memory build-up, viral share-card generation,
and commercial conversion metrics for Kalyan AI.
"""

import sys
import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

def simulate_closed_beta_cohort(cohort_size: int = 50):
    print("=" * 75)
    print(f"  👥 KALYAN AI: CLOSED BETA COHORT & RETENTION SIMULATION ({cohort_size} USERS)")
    print("=" * 75)
    
    random.seed(42)
    
    users = []
    daily_active_users = {day: 0 for day in range(1, 31)}
    total_messages_generated = 0
    total_share_cards_created = 0
    total_memories_extracted = 0
    conversions_single_roast = 0
    conversions_fan_pass = 0
    
    # Archetypes in closed beta cohort
    archetypes = [
        {"type": "Ameerpet Dev / Fresher", "weight": 0.40, "base_engagement": 5, "retention_bias": 0.65},
        {"type": "Startup Founder / PM", "weight": 0.25, "base_engagement": 4, "retention_bias": 0.55},
        {"type": "College Student", "weight": 0.20, "base_engagement": 6, "retention_bias": 0.60},
        {"type": "Curious Tech Enthusiast", "weight": 0.15, "base_engagement": 3, "retention_bias": 0.40}
    ]
    
    user_id_counter = 1
    for arch in archetypes:
        count = int(cohort_size * arch["weight"])
        for _ in range(count):
            users.append({
                "id": f"beta_user_{user_id_counter:03d}",
                "archetype": arch["type"],
                "base_eng": arch["base_engagement"],
                "retention_bias": arch["retention_bias"],
                "active_days": [],
                "total_msgs": 0,
                "share_cards": 0,
                "memories": 0,
                "subscribed": False
            })
            user_id_counter += 1
            
    while len(users) < cohort_size:
        users.append({
            "id": f"beta_user_{len(users)+1:03d}",
            "archetype": "Ameerpet Dev / Fresher",
            "base_eng": 5,
            "retention_bias": 0.65,
            "active_days": [],
            "total_msgs": 0,
            "share_cards": 0,
            "memories": 0,
            "subscribed": False
        })
        
    # Simulate 30 days of activity
    for day in range(1, 31):
        for u in users:
            # Day 1: 100% onboarded
            if day == 1:
                is_active = True
            elif day in [2, 3]:
                is_active = random.random() < (u["retention_bias"] * 0.95)
            elif day <= 7:
                is_active = random.random() < (u["retention_bias"] * 0.80)
            elif day <= 14:
                is_active = random.random() < (u["retention_bias"] * 0.70)
            elif day <= 21:
                is_active = random.random() < (u["retention_bias"] * 0.65)
            else:
                is_active = random.random() < (u["retention_bias"] * 0.60)
                
            if is_active:
                daily_active_users[day] += 1
                u["active_days"].append(day)
                msgs = max(1, int(random.gauss(u["base_eng"], 2)))
                u["total_msgs"] += msgs
                total_messages_generated += msgs
                
                # Viral share card creation (approx 1 per 8 messages)
                if random.random() < 0.15:
                    u["share_cards"] += 1
                    total_share_cards_created += 1
                    
                # L3 Memory extraction (approx 1 per 5 messages up to 8 max)
                if u["memories"] < 8 and random.random() < 0.25:
                    u["memories"] += 1
                    total_memories_extracted += 1
                    
                # Monetization conversion events
                if not u["subscribed"] and day >= 7 and u["total_msgs"] >= 20:
                    if random.random() < 0.12:
                        u["subscribed"] = True
                        conversions_fan_pass += 1
                    elif random.random() < 0.20:
                        conversions_single_roast += 1

    # Retention Calculations
    d1_active = sum(1 for u in users if 1 in u["active_days"])
    d7_active = sum(1 for u in users if 7 in u["active_days"])
    d14_active = sum(1 for u in users if 14 in u["active_days"])
    d28_active = sum(1 for u in users if 28 in u["active_days"])
    
    ret_d1 = (d1_active / cohort_size) * 100
    ret_d7 = (d7_active / cohort_size) * 100
    ret_d14 = (d14_active / cohort_size) * 100
    ret_d28 = (d28_active / cohort_size) * 100
    
    # Financial metrics
    # LLM cost: ₹0.063 per turn (from real Gemini 3.5 Flash-Lite benchmark)
    total_llm_cost_inr = total_messages_generated * 0.063
    total_revenue_inr = (conversions_single_roast * 49.0) + (conversions_fan_pass * 149.0)
    net_profit_inr = total_revenue_inr - total_llm_cost_inr - (total_revenue_inr * 0.02) # minus payment gateway
    
    print(f"Cohort Size:                {cohort_size} users")
    print(f"Total Messages Exchanged:   {total_messages_generated:,}")
    print(f"Viral Share Cards Created:  {total_share_cards_created}")
    print(f"Durable Memories Stored:    {total_memories_extracted}")
    print()
    print("📈 RETENTION CURVE:")
    print(f"   - Day 1  Retention:       {ret_d1:.1f}% ({d1_active}/{cohort_size})")
    print(f"   - Day 7  Retention:       {ret_d7:.1f}% ({d7_active}/{cohort_size})")
    print(f"   - Day 14 Retention:       {ret_d14:.1f}% ({d14_active}/{cohort_size})")
    print(f"   - Day 28 Retention:       {ret_d28:.1f}% ({d28_active}/{cohort_size})")
    print()
    print("💵 30-DAY FINANCIAL SUMMARY:")
    print(f"   - ₹49 Single Roast Sales: {conversions_single_roast} (₹{conversions_single_roast * 49:.2f})")
    print(f"   - ₹149 Fan Pass Subscriptions: {conversions_fan_pass} (₹{conversions_fan_pass * 149:.2f})")
    print(f"   - Total Gross Revenue:    ₹{total_revenue_inr:,.2f} INR")
    print(f"   - Total Gemini LLM Cost:  ₹{total_llm_cost_inr:,.2f} INR")
    print(f"   - Net Operational Profit: ₹{net_profit_inr:,.2f} INR ({(net_profit_inr/max(1,total_revenue_inr))*100:.1f}% net margin)")
    print("=" * 75)
    
    # Save cohort report
    out_path = repo_root / "docs" / "EVIDENCE" / "E49_closed_beta_cohort_simulation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "cohort_size": cohort_size,
            "simulation_days": 30,
            "total_messages": total_messages_generated,
            "total_share_cards": total_share_cards_created,
            "total_memories": total_memories_extracted,
            "retention": {
                "day_1_pct": ret_d1,
                "day_7_pct": ret_d7,
                "day_14_pct": ret_d14,
                "day_28_pct": ret_d28
            },
            "financials": {
                "single_roast_count": conversions_single_roast,
                "fan_pass_count": conversions_fan_pass,
                "gross_revenue_inr": round(total_revenue_inr, 2),
                "total_llm_cost_inr": round(total_llm_cost_inr, 2),
                "net_profit_inr": round(net_profit_inr, 2)
            }
        }, f, indent=2)
    print(f"[+] Cohort simulation written to: {out_path.name}\n")

if __name__ == "__main__":
    simulate_closed_beta_cohort()
