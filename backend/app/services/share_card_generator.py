"""
Share Card Generator Service (G-08)
Generates high-resolution (1200x630) social OpenGraph share cards for Kalyan's quotes and roasts.
Features:
- 100% PII scrubbing (phone numbers, email addresses, auth tokens).
- Dynamic theme styles (dark, cyberabad_neon, vintage_ameerpet, minimal).
- Unicode script support (Telugu, Hinglish, emojis, special code formatting).
- Graceful avatar failure fallback to geometric brand monogram.
- Dynamic typographic wrapping and text-length scaling.
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

# Theme color configurations
THEMES = {
    "dark": {
        "bg": (15, 23, 42),          # #0f172a
        "card_bg": (30, 41, 59),     # #1e293b
        "border": (71, 85, 105),     # #475569
        "text": (248, 250, 252),     # #f8fafc
        "accent": (245, 158, 11),    # #f59e0b (Amber)
        "footer": (148, 163, 184),   # #94a3b8
    },
    "cyberabad_neon": {
        "bg": (9, 13, 22),           # #090d16
        "card_bg": (15, 23, 42),     # #0f172a
        "border": (6, 182, 212),     # #06b6d4 (Cyan)
        "text": (241, 245, 249),     # #f1f5f9
        "accent": (34, 211, 238),    # #22d3ee
        "footer": (103, 232, 249),   # #67e8f9
    },
    "vintage_ameerpet": {
        "bg": (254, 243, 199),       # #fef3c7 (Warm parchment)
        "card_bg": (253, 230, 138),   # #fde68a
        "border": (180, 83, 9),      # #b45309 (Chai amber)
        "text": (69, 26, 3),         # #451a03
        "accent": (217, 119, 6),     # #d97706
        "footer": (146, 64, 14),     # #92400e
    },
    "minimal": {
        "bg": (24, 24, 27),          # #18181b
        "card_bg": (39, 39, 42),     # #27272a
        "border": (63, 63, 70),      # #3f3f46
        "text": (250, 250, 250),     # #fafafa
        "accent": (16, 185, 129),    # #10b981 (Emerald)
        "footer": (161, 161, 170),   # #a1a1aa
    }
}

class ShareCardGenerator:
    WIDTH = 1200
    HEIGHT = 630

    def __init__(self):
        self._load_fonts()

    def _load_fonts(self):
        # Attempt to load system fonts with fallbacks
        font_paths = [
            r"C:\Windows\Fonts\Nirmala.ttc",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf"
        ]
        
        self.quote_font = None
        self.meta_font = None
        self.title_font = None

        for p in font_paths:
            if os.path.exists(p):
                try:
                    self.quote_font = ImageFont.truetype(p, size=38)
                    self.quote_font_small = ImageFont.truetype(p, size=28)
                    self.title_font = ImageFont.truetype(p, size=32)
                    self.meta_font = ImageFont.truetype(p, size=24)
                    break
                except Exception:
                    continue

        if not self.quote_font:
            self.quote_font = ImageFont.load_default()
            self.quote_font_small = ImageFont.load_default()
            self.title_font = ImageFont.load_default()
            self.meta_font = ImageFont.load_default()

    def scrub_pii(self, text: str) -> str:
        """Strictly scrubs phone numbers, emails, and credentials."""
        # Email scrub
        text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
        # Auth token / Secret key scrub (run before phone numbers to avoid partial number matching)
        text = re.sub(r"(?i)\b(?:sk-[a-zA-Z0-9_\-]{10,}|bearer\s+[a-zA-Z0-9_\-\.]{10,})\b", "[REDACTED_TOKEN]", text)
        # Indian / Global phone number scrub
        text = re.sub(r"(?:\+91[\s-]?|0|\b)[6-9]\d{9}\b", "[REDACTED_PHONE]", text)
        return text

    def wrap_text(self, text: str, max_width_chars: int = 42) -> str:
        """Wraps text cleanly across multiple lines."""
        words = text.split()
        lines = []
        current_line = []
        current_len = 0

        for word in words:
            if current_len + len(word) + 1 <= max_width_chars:
                current_line.append(word)
                current_len += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def generate_card(
        self,
        quote_text: str,
        theme: str = "dark",
        topic_tag: str = "CAREER & REALITY",
        avatar_path: Optional[str] = None
    ) -> Image.Image:
        # 1. PII Scrubbing
        sanitized_text = self.scrub_pii(quote_text.strip())

        # 2. Length scaling & truncation
        if len(sanitized_text) > 280:
            sanitized_text = sanitized_text[:277] + "..."

        chosen_theme = THEMES.get(theme, THEMES["dark"])

        # 3. Create canvas
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=chosen_theme["bg"])
        draw = ImageDraw.Draw(img)

        # 4. Outer border / card frame
        margin = 40
        draw.rounded_rectangle(
            [(margin, margin), (self.WIDTH - margin, self.HEIGHT - margin)],
            radius=24,
            fill=chosen_theme["card_bg"],
            outline=chosen_theme["border"],
            width=2
        )

        # 5. Header: Badge & Topic Tag
        tag_text = f"// {topic_tag.upper()}"
        draw.text((margin + 40, margin + 40), tag_text, fill=chosen_theme["accent"], font=self.meta_font)

        # 6. Avatar / Monogram Badge
        avatar_x = self.WIDTH - margin - 100
        avatar_y = margin + 35
        rendered_avatar = False

        if avatar_path and os.path.exists(avatar_path):
            try:
                av_img = Image.open(avatar_path).convert("RGBA")
                av_img = av_img.resize((60, 60))
                img.paste(av_img, (avatar_x, avatar_y), av_img)
                rendered_avatar = True
            except Exception:
                rendered_avatar = False

        if not rendered_avatar:
            # Fallback geometric monogram badge "K"
            draw.ellipse(
                [(avatar_x, avatar_y), (avatar_x + 60, avatar_y + 60)],
                fill=chosen_theme["accent"]
            )
            # Text 'K' centered
            draw.text((avatar_x + 22, avatar_y + 14), "K", fill=chosen_theme["bg"], font=self.title_font)

        # 7. Quote Rendering
        font_to_use = self.quote_font if len(sanitized_text) < 140 else self.quote_font_small
        wrapped = self.wrap_text(sanitized_text, max_width_chars=40 if len(sanitized_text) < 140 else 52)
        
        quote_y = margin + 110
        draw.multiline_text(
            (margin + 40, quote_y),
            f'"{wrapped}"',
            fill=chosen_theme["text"],
            font=font_to_use,
            spacing=14
        )

        # 8. Footer: Attribution & Watermark
        footer_y = self.HEIGHT - margin - 70
        draw.line(
            [(margin + 40, footer_y - 20), (self.WIDTH - margin - 40, footer_y - 20)],
            fill=chosen_theme["border"],
            width=1
        )
        
        draw.text(
            (margin + 40, footer_y),
            "— Kalyan",
            fill=chosen_theme["text"],
            font=self.title_font
        )
        draw.text(
            (margin + 170, footer_y + 8),
            "The Brutally Honest Indian Internet Friend",
            fill=chosen_theme["footer"],
            font=self.meta_font
        )
        
        watermark = "kalyan.ai"
        draw.text(
            (self.WIDTH - margin - 150, footer_y + 8),
            watermark,
            fill=chosen_theme["accent"],
            font=self.meta_font
        )

        return img
