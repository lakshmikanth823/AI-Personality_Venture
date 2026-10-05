"""
Generate 12 Share Card Edge Cases (G-08)
Validates rendering across:
1. Telugu Unicode script
2. Hinglish slang
3. 2000-character text truncation
4. Ultra-short 3 words
5. Emoji-rich text
6. Code & punctuation symbols (SQL / HTML tags)
7. Missing avatar / image failure graceful fallback
8. Dark OLED Charcoal & Amber theme
9. Cyberabad Neon Cyan theme
10. Ameerpet Vintage Parchment theme
11. Modern Minimalist Emerald theme
12. PII Scrubbing verification (Emails, Phone numbers, API tokens)
"""

import os
import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.services.share_card_generator import ShareCardGenerator

def generate_12_cases():
    generator = ShareCardGenerator()
    out_dir = Path("docs/EVIDENCE/assets")
    out_dir.mkdir(parents=True, exist_ok=True)

    test_cases = [
        {
            "id": "case_01",
            "name": "Telugu Unicode Script",
            "text": "మీ కెరీర్ మీ చేతుల్లో ఉంది. అమీర్‌పేట్ సర్టిఫికేట్ కాదు, మీ కోడింగ్ మాత్రమే మిమ్మల్ని కాపాడుతుంది.",
            "theme": "dark",
            "topic": "CAREER & REALITY",
            "avatar": None
        },
        {
            "id": "case_02",
            "name": "Hinglish Slang",
            "text": "Arey bhai, agar tumhara code first try mein run ho gaya, toh celebration mat karo. Tumne galat branch deploy ki hai.",
            "theme": "vintage_ameerpet",
            "topic": "AMEERPET WISDOM",
            "avatar": None
        },
        {
            "id": "case_03",
            "name": "2000-Character Long Text Truncation",
            "text": "Tech companies spend ₹20 lakhs on office beanbags, fancy barista stations, and artisanal cold brew taps, but will initiate a formal HR disciplinary enquiry if you expense a ₹45 auto ride from the station. " * 15,
            "theme": "dark",
            "topic": "CORPORATE REALITY",
            "avatar": None
        },
        {
            "id": "case_04",
            "name": "Ultra-Short 3 Words",
            "text": "Fix your code.",
            "theme": "minimal",
            "topic": "BRUTAL TRUTH",
            "avatar": None
        },
        {
            "id": "case_05",
            "name": "Emoji-Rich Text",
            "text": "Deploying directly to production on Friday evening? 😂💀 Bro wants weekend overtime and zero peace of mind 🚀🔥💯",
            "theme": "cyberabad_neon",
            "topic": "DEVOPS CHAOS",
            "avatar": None
        },
        {
            "id": "case_06",
            "name": "Special Characters & Code Formatting",
            "text": "SELECT * FROM resumes WHERE experience = 'Ameerpet' AND <script>alert('hired')</script> -- logic: 100% verified.",
            "theme": "dark",
            "topic": "DEV HUMOR",
            "avatar": None
        },
        {
            "id": "case_07",
            "name": "Missing Avatar Graceful Fallback",
            "text": "Your college degree is like a receipt for an expensive meal you didn't enjoy. Focus on building real projects.",
            "theme": "vintage_ameerpet",
            "topic": "EDUCATION",
            "avatar": "non_existent_avatar_file_path_12345.png"
        },
        {
            "id": "case_08",
            "name": "Dark OLED Charcoal Theme",
            "text": "The fastest way to get ₹30 LPA is not another certification. It is actually learning how to read the documentation.",
            "theme": "dark",
            "topic": "CAREER ACCELERATION",
            "avatar": None
        },
        {
            "id": "case_09",
            "name": "Cyberabad Neon Theme",
            "text": "In Hitec City, traffic moves slower than a junior engineer trying to explain why their PR has 4,000 lines of changes.",
            "theme": "cyberabad_neon",
            "topic": "HYDERABAD CULTURE",
            "avatar": None
        },
        {
            "id": "case_10",
            "name": "Ameerpet Vintage Parchment Theme",
            "text": "Chai at Niloufer Cafe solves 80% of architecture bugs. The remaining 20% require rewriting the entire microservice.",
            "theme": "vintage_ameerpet",
            "topic": "HYDERABAD LORE",
            "avatar": None
        },
        {
            "id": "case_11",
            "name": "Modern Minimalist Theme",
            "text": "Simplicity is not a lack of clutter, that's just a byproduct. True simplicity is knowing what to say NO to.",
            "theme": "minimal",
            "topic": "ARCHITECTURE",
            "avatar": None
        },
        {
            "id": "case_12",
            "name": "PII Scrubbing Verification",
            "text": "Send bug reports to founder@stealthai.io or call Kalyan directly at +919876543210 with secret sk-live-99228833774455.",
            "theme": "dark",
            "topic": "SECURITY SCRUBBING",
            "avatar": None
        }
    ]

    print(f"[*] Generating {len(test_cases)} Share Card Edge Cases...")
    generated_files = []

    for case in test_cases:
        c_id = case["id"]
        c_name = case["name"]
        
        # Scrub check assertion for case 12
        if c_id == "case_12":
            scrubbed = generator.scrub_pii(case["text"])
            assert "founder@stealthai.io" not in scrubbed, "Failed to scrub email!"
            assert "9876543210" not in scrubbed, "Failed to scrub phone!"
            assert "sk-live-99228833774455" not in scrubbed, "Failed to scrub API token!"
            assert "[REDACTED_EMAIL]" in scrubbed
            assert "[REDACTED_PHONE]" in scrubbed
            assert "[REDACTED_TOKEN]" in scrubbed
            print(f"[+] Case 12 PII Scrubbing Assertion: PASSED (Zero raw PII stamped)")

        img = generator.generate_card(
            quote_text=case["text"],
            theme=case["theme"],
            topic_tag=case["topic"],
            avatar_path=case["avatar"]
        )

        assert img.size == (1200, 630), f"Invalid dimensions: {img.size}"

        out_path = out_dir / f"share_card_{c_id}.png"
        img.save(str(out_path), "PNG")
        assert out_path.exists() and out_path.stat().st_size > 5000, f"File creation failed for {out_path}"
        
        generated_files.append((c_id, c_name, str(out_path), out_path.stat().st_size))
        print(f"[+] [{c_id}] {c_name} -> {out_path.name} ({out_path.stat().st_size} bytes)")

    print(f"[SUCCESS] All {len(generated_files)} Share Cards Generated & Assertions Verified 100%!")
    return generated_files

if __name__ == "__main__":
    generate_12_cases()
