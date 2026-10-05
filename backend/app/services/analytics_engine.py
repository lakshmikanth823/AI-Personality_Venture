from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from backend.app.models.analytics import UsageEvent, CostEvent, DailyMetric
from backend.app.models.conversation import Message, Conversation
from backend.app.models.user import User
from backend.app.models.subscription import PaymentTransaction
from backend.app.core.config import settings

class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db

    def record_usage(
        self,
        feature_name: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        user_id: str = None
    ) -> UsageEvent:
        cost_usd = (input_tokens / 1000.0) * settings.COST_PER_1K_INPUT_TOKENS_USD + \
                   (output_tokens / 1000.0) * settings.COST_PER_1K_OUTPUT_TOKENS_USD

        event = UsageEvent(
            id=f"use_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            feature_name=feature_name,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=round(cost_usd, 6),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(event)
        self.db.commit()
        return event

    def calculate_wmcr(self) -> int:
        """
        Weekly Meaningful Character Relationships (WMCR):
        Unique, non-deleted users with at least 3 interactions within the rolling 7-day
        window anchored to the IST midnight boundary.
        """
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist)
        seven_days_ago_ist_midnight = (now_ist - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago_utc = seven_days_ago_ist_midnight.astimezone(timezone.utc)

        # Count user messages grouped by user_id, strictly filtering for active users
        active_counts = (
            self.db.query(Conversation.user_id, func.count(Message.id).label("interaction_count"))
            .join(Message, Message.conversation_id == Conversation.id)
            .join(User, User.id == Conversation.user_id)
            .filter(
                Message.created_at >= seven_days_ago_utc.replace(tzinfo=None),
                Message.role == "user",
                User.is_active == True
            )
            .group_by(Conversation.user_id)
            .having(func.count(Message.id) >= 3)
            .all()
        )
        return len(active_counts)

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # DAU: Unique users with activity today
        dau = self.db.query(func.count(distinct(Conversation.user_id))).join(
            Message, Message.conversation_id == Conversation.id
        ).filter(Message.created_at >= today_start).scalar() or 0

        # WAU: Unique users with activity past 7 days
        wau = self.db.query(func.count(distinct(Conversation.user_id))).join(
            Message, Message.conversation_id == Conversation.id
        ).filter(Message.created_at >= seven_days_ago).scalar() or 0

        wmcr = self.calculate_wmcr()

        # Token usage & Cost summary
        total_tokens = self.db.query(
            func.sum(UsageEvent.input_tokens + UsageEvent.output_tokens)
        ).scalar() or 0

        total_cost_usd = self.db.query(func.sum(UsageEvent.cost_usd)).scalar() or 0.0
        total_cost_inr = total_cost_usd * settings.INR_PER_USD

        # Revenue summary
        total_revenue_inr = self.db.query(
            func.sum(PaymentTransaction.amount_inr)
        ).filter(PaymentTransaction.status == "completed").scalar() or 0.0

        # Contribution margin calculation
        # Revenue INR - (Inference Cost INR + Platform fees 2% + Infrastructure estimate)
        inference_cost_inr = total_cost_inr
        payment_fees_inr = total_revenue_inr * 0.02
        infrastructure_cost_inr = 250.0 # base cloud hosting
        contribution_margin_inr = total_revenue_inr - (inference_cost_inr + payment_fees_inr + infrastructure_cost_inr)

        # Feature level breakdown
        features = self.db.query(
            UsageEvent.feature_name,
            func.count(UsageEvent.id).label("calls"),
            func.sum(UsageEvent.cost_usd).label("cost")
        ).group_by(UsageEvent.feature_name).all()

        feature_breakdown = [
            {"feature": f[0], "calls": f[1], "cost_usd": round(f[2] or 0.0, 4)}
            for f in features
        ]

        # Strategic Decision Rules evaluation
        strategic_insights = self._evaluate_decision_rules(dau, wmcr, total_revenue_inr, total_cost_inr)

        return {
            "north_star_wmcr": wmcr,
            "dau": max(dau, 1),
            "wau": max(wau, 1),
            "total_tokens_processed": int(total_tokens),
            "total_cost_usd": round(total_cost_usd, 4),
            "total_cost_inr": round(total_cost_inr, 2),
            "total_revenue_inr": round(total_revenue_inr, 2),
            "contribution_margin_inr": round(contribution_margin_inr, 2),
            "feature_breakdown": feature_breakdown,
            "strategic_insights": strategic_insights
        }

    def _evaluate_decision_rules(self, dau: int, wmcr: int, revenue_inr: float, cost_inr: float) -> List[Dict[str, str]]:
        insights = []
        if dau > 10 and wmcr / max(dau, 1) < 0.2:
            insights.append({
                "rule": "High interaction + low retention",
                "diagnosis": "Memory/ritual problem",
                "recommended_action": "Strengthen durable memory callbacks and personalized inside jokes in character responses."
            })
        if wmcr > 5 and revenue_inr < 50:
            insights.append({
                "rule": "High retention + low revenue",
                "diagnosis": "Premium-value problem",
                "recommended_action": "Introduce contextual ₹49 single savage roasts and ₹149 monthly fan pass triggers."
            })
        if cost_inr > 0 and revenue_inr > 0 and (revenue_inr / cost_inr) < 1.5:
            insights.append({
                "rule": "High revenue + poor margin",
                "diagnosis": "Cost/routing problem",
                "recommended_action": "Route repetitive greetings to lighter models, enforce tighter memory compression."
            })

        if not insights:
            insights.append({
                "rule": "Healthy Foundation",
                "diagnosis": "Metrics aligned",
                "recommended_action": "Maintain daily content rhythm and test A/B humor intensity variants."
            })

        return insights
