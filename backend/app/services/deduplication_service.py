"""Hybrid, location-aware grievance matching with Gemini text embeddings."""

import re
import threading
import logging
from typing import Any, Dict, List, Optional

from rapidfuzz import fuzz
from app.config import settings

from app.models import Ticket, TicketStatus


class EmbeddingProvider:
    """Calls Gemini embeddings when configured; lexical matching is the fallback."""
    _client = None
    _lock = threading.Lock()

    @classmethod
    def suggest_category(cls, description: str, categories: List[Any]) -> Optional[Dict[str, Any]]:
        """Ask Gemini to choose the best existing category; never invent a category."""
        if len(categories) < 2:
            return None
        def lexical_fallback() -> Optional[Dict[str, Any]]:
            ranked = sorted(
                ((fuzz.token_set_ratio(description, f"{c.name} {c.description or ''}"), c) for c in categories),
                key=lambda item: item[0], reverse=True,
            )
            if ranked and ranked[0][0] >= 25:
                return {"id": ranked[0][1].id, "name": ranked[0][1].name}
            return None
        if not settings.GEMINI_API_KEY:
            return lexical_fallback()
        try:
            if cls._client is None:
                with cls._lock:
                    if cls._client is None:
                        from google import genai
                        cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            options = "\n".join(
                f"{category.id}: {category.name} — {category.description or 'No details provided'}"
                for category in categories
            )
            response = cls._client.models.generate_content(
                model=settings.GEMINI_CLASSIFICATION_MODEL,
                contents=(
                    "Choose the single best matching category for this campus issue. "
                    "Return only its numeric ID, or 0 if unclear.\n"
                    f"Categories:\n{options}\nIssue: {description[:1200]}"
                ),
            )
            category_id = int((response.text or "").strip())
            chosen = next((c for c in categories if c.id == category_id), None)
            return {"id": chosen.id, "name": chosen.name} if chosen else None
        except Exception:
            logging.warning("Gemini category suggestion failed; using local category matching")
            return lexical_fallback()

    @classmethod
    def encode(cls, text: str) -> Optional[List[float]]:
        if not settings.GEMINI_API_KEY:
            return None
        try:
            if cls._client is None:
                with cls._lock:
                    if cls._client is None:
                        from google import genai
                        cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            from google.genai import types
            result = cls._client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                    output_dimensionality=settings.GEMINI_EMBEDDING_DIMENSIONS,
                ),
            )
            return list(result.embeddings[0].values)
        except Exception:
            # Suggestions remain available through lexical/location matching during outages.
            logging.exception("Gemini embedding request failed; using lexical matching fallback")
            return None

    @classmethod
    def backfill_missing(cls, limit: int = 100) -> Dict[str, int]:
        """Populate missing vectors in bounded batches; safe to rerun after partial failure."""
        updated = failed = 0
        tickets = [
            t for t in Ticket.objects(status__in=[TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value])
            if not (getattr(t, "description_embedding", None) or [])
        ][:limit]
        for ticket in tickets:
            vector = cls.encode(ticket.description)
            if vector:
                ticket.description_embedding = vector
                ticket.save()
                updated += 1
            else:
                failed += 1
                # Provider outage or missing API key: stop rather than making repeated calls.
                break
        return {"updated": updated, "failed": failed}


class DeduplicationEngine:
    """Rank unresolved tickets by category, location, lexical, and semantic similarity."""

    DUPLICATE_THRESHOLD = 52.0
    LIVE_SUGGESTION_THRESHOLD = 65.0

    @staticmethod
    def _location_parts(location: str) -> Dict[str, Optional[str]]:
        text = re.sub(r"\s+", " ", location.lower().strip())
        room = re.search(r"\b(?:room|rm)\s*[-:#]?\s*([a-z0-9-]+)|\b([a-z]\d[- ]?\d{2,4})\b", text)
        floor = re.search(r"\b(\d+)(?:st|nd|rd|th)?\s*floor\b|\bfloor\s*(\d+)\b", text)
        block = re.search(r"\b(?:block|hostel|building|bldg)\s*[-#]?\s*([a-z0-9-]+)", text)
        return {
            "room": next((g for g in room.groups() if g), None) if room else None,
            "floor": next((g for g in floor.groups() if g), None) if floor else None,
            "block": next((g for g in block.groups() if g), None) if block else None,
        }

    @classmethod
    def _score(cls, location: str, description: str, ticket: Ticket, query_vector: Optional[List[float]]) -> Dict[str, float]:
        location_score = float(fuzz.token_set_ratio(location.lower(), ticket.location.lower()))
        lexical_score = float(fuzz.token_set_ratio(description.lower(), ticket.description.lower()))
        lexical_score = 0.7 * lexical_score + 0.3 * float(fuzz.partial_ratio(description.lower(), ticket.description.lower()))

        left, right = cls._location_parts(location), cls._location_parts(ticket.location)
        room_conflict = left["room"] and right["room"] and left["room"].replace(" ", "") != right["room"].replace(" ", "")
        block_conflict = left["block"] and right["block"] and left["block"] != right["block"]
        if room_conflict:
            location_score *= 0.3
        elif block_conflict:
            location_score *= 0.55

        semantic_score = lexical_score
        stored = getattr(ticket, "description_embedding", None) or []
        if query_vector and len(stored) == len(query_vector):
            cosine = sum(a * b for a, b in zip(query_vector, stored))
            semantic_score = max(0.0, min(100.0, cosine * 100.0))

        if query_vector and stored:
            overall = location_score * 0.35 + lexical_score * 0.25 + semantic_score * 0.40
        else:
            overall = location_score * 0.45 + lexical_score * 0.55
        if room_conflict:
            overall *= 0.30
        return {"location": location_score, "lexical": lexical_score, "semantic": semantic_score, "overall": overall}

    @classmethod
    def check_duplicates(
        cls, db, category_id: int, location: str, description: str,
        limit: int = 5, threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        statuses = [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]
        candidates = list(Ticket.objects(category_id=category_id, status__in=statuses, parent_ticket_id=None))
        if not candidates:
            return []

        minimum_score = cls.DUPLICATE_THRESHOLD if threshold is None else threshold
        query_vector = EmbeddingProvider.encode(description)
        matches = []
        for ticket in candidates:
            score = cls._score(location, description, ticket, query_vector)
            if score["overall"] < minimum_score:
                continue
            # Student suggestions must not disclose confidential grievances filed by others.
            if ticket.is_confidential:
                continue
            matches.append({
                "id": ticket.id,
                "ticket_id": ticket.ticket_id,
                "category_id": ticket.category_id,
                "category_name": ticket.category.name if ticket.category else "",
                "location": ticket.location,
                "description": ticket.description,
                "description_snippet": ticket.description[:180],
                "status": ticket.status,
                "similarity_score": round(score["overall"], 1),
                "location_match": round(score["location"], 1),
                "supporter_count": len(ticket.duplicate_tickets),
                "assigned_staff_name": ticket.assigned_staff.name if ticket.assigned_staff else None,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            })
        matches.sort(key=lambda item: item["similarity_score"], reverse=True)
        return matches[:limit]

