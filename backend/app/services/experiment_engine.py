import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.experiment import Experiment, ExperimentVariant

SEED_EXPERIMENTS = [
    {
        "name": "H2_Cultural_Fluency",
        "hypothesis": "H2: Cultural specificity (Hinglish/Telugu infusion) beats generic English humor in engagement and shares.",
        "variable_tested": "language_flavor",
        "variants": [
            {
                "key": "control_standard_english",
                "name": "Standard Indian English",
                "prompt_modifier": "Maintain clean, witty Indian English with zero colloquial slang.",
                "allocation": 33.3
            },
            {
                "key": "treatment_hinglish",
                "name": "Punchy Hinglish Banter",
                "prompt_modifier": "Naturally weave selective Hinglish idioms (arre, yaar, scene off, jugaad, pakka) into punchlines.",
                "allocation": 33.3
            },
            {
                "key": "treatment_telugu_infused",
                "name": "Telugu-Infused Street Smarts",
                "prompt_modifier": "Infuse expressive Telugu slang (arre babu, chudu, emititi scenes, sorted boss) with filter coffee energy.",
                "allocation": 33.4
            }
        ]
    },
    {
        "name": "H5_Memory_Retention",
        "hypothesis": "H5: Active callback to user's biographical memories improves D7 retention and WMCR.",
        "variable_tested": "memory_callback_density",
        "variants": [
            {
                "key": "control_minimal_context",
                "name": "Zero L3 Memory",
                "prompt_modifier": "Respond strictly based on current conversation without referencing stored user history.",
                "allocation": 50.0
            },
            {
                "key": "treatment_proactive_memory",
                "name": "Proactive Personal Memory Callback",
                "prompt_modifier": "Proactively and wittily reference the user's career or cricket allegiance if relevant.",
                "allocation": 50.0
            }
        ]
    }
]

class ExperimentEngine:
    def __init__(self, db: Session):
        self.db = db
        self._ensure_seed_experiments()

    def _ensure_seed_experiments(self):
        for exp_data in SEED_EXPERIMENTS:
            existing = self.db.query(Experiment).filter(Experiment.name == exp_data["name"]).first()
            if not existing:
                exp = Experiment(
                    id=str(uuid.uuid4()),
                    name=exp_data["name"],
                    hypothesis=exp_data["hypothesis"],
                    variable_tested=exp_data["variable_tested"],
                    status="active"
                )
                self.db.add(exp)
                for v in exp_data["variants"]:
                    variant = ExperimentVariant(
                        id=str(uuid.uuid4()),
                        experiment_id=exp.id,
                        variant_key=v["key"],
                        name=v["name"],
                        prompt_modifier=v["prompt_modifier"],
                        allocation_percent=v["allocation"]
                    )
                    self.db.add(variant)
                self.db.commit()

    def get_active_experiments(self) -> List[Dict[str, Any]]:
        experiments = self.db.query(Experiment).all()
        result = []
        for exp in experiments:
            variants = [
                {
                    "key": v.variant_key,
                    "name": v.name,
                    "samples": v.samples_count,
                    "conversions": v.conversions_count,
                    "conversion_rate": round((v.conversions_count / max(v.samples_count, 1)) * 100, 1),
                    "shares": v.shares_count
                }
                for v in exp.variants
            ]
            result.append({
                "id": exp.id,
                "name": exp.name,
                "hypothesis": exp.hypothesis,
                "status": exp.status,
                "variants": variants
            })
        return result

    def get_assigned_variant(self, experiment_name: str, user_id: str) -> Optional[Dict[str, Any]]:
        exp = self.db.query(Experiment).filter(Experiment.name == experiment_name, Experiment.status == "active").first()
        if not exp or not exp.variants:
            return None

        # Deterministic hash allocation based on user_id
        import hashlib
        hash_val = int(hashlib.md5(f"{experiment_name}_{user_id}".encode()).hexdigest(), 16) % 100
        cumulative = 0.0
        for variant in exp.variants:
            cumulative += variant.allocation_percent
            if hash_val < cumulative:
                variant.samples_count += 1
                self.db.commit()
                return {
                    "variant_key": variant.variant_key,
                    "prompt_modifier": variant.prompt_modifier
                }

        # Fallback to first variant
        chosen = exp.variants[0]
        chosen.samples_count += 1
        self.db.commit()
        return {"variant_key": chosen.variant_key, "prompt_modifier": chosen.prompt_modifier}

    def record_conversion(self, experiment_name: str, variant_key: str, action: str = "conversion"):
        variant = (
            self.db.query(ExperimentVariant)
            .join(Experiment, Experiment.id == ExperimentVariant.experiment_id)
            .filter(Experiment.name == experiment_name, ExperimentVariant.variant_key == variant_key)
            .first()
        )
        if variant:
            if action == "share":
                variant.shares_count += 1
            else:
                variant.conversions_count += 1
            self.db.commit()
