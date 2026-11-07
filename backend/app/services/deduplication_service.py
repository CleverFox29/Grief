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
    _category_vectors: Dict[str, List[float]] = {}

    @classmethod
    def suggest_category(cls, description: str, categories: List[Any]) -> Optional[Dict[str, Any]]:
        """Choose the closest category using cached Gemini semantic embeddings."""
        if len(categories) < 2:
            return None
        if not settings.GEMINI_API_KEY:
            return None
        try:
            examples = {
                "plumbing": "water cooler, drinking water dispenser, tap, pipe, leak, drain, flush",
                "electrical": "fan, light, power, switch, socket, wiring, motor, appliance not turning on",
                "carpentry": "chair, table, door, cupboard, bed, wood, broken furniture",
                "masonry": "wall, floor, tile, ceiling, plaster, crack, seepage",
                "administrative": "ID card, allotment, fee, records, office, paperwork",
                "security": "theft, safety, lost item, harassment, gate, guard",
            }
            category_texts = {}
            for category in categories:
                key = category.name.lower()
                hints = next((value for name, value in examples.items() if name in key), "")
                profile = f"{category.name}. {category.description or ''} Related issues include: {hints}."
                category_texts[f"{category.id}:{profile}"] = category
            missing = [text for text in category_texts if text not in cls._category_vectors]
            if missing:
                vectors = cls.encode_many(missing)
                if not vectors:
                    return None
                cls._category_vectors.update(dict(zip(missing, vectors)))
            query_vector = cls.encode(description[:1200])
            if not query_vector:
                return None
            ranked = []
            for text, category in category_texts.items():
                vector = cls._category_vectors.get(text)
                if vector and len(vector) == len(query_vector):
                    ranked.append((sum(a * b for a, b in zip(query_vector, vector)), category))
            if not ranked:
                return None
            _, selected = max(ranked, key=lambda item: item[0])
            return {"id": selected.id, "name": selected.name}
        except Exception:
            logging.warning("Gemini embedding category match failed", exc_info=True)
            return None

    @classmethod
    def encode_many(cls, texts: List[str]) -> Optional[List[List[float]]]:
        if not texts or not settings.GEMINI_API_KEY:
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
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                    output_dimensionality=settings.GEMINI_EMBEDDING_DIMENSIONS,
                ),
            )
            return [list(item.values) for item in result.embeddings]
        except Exception:
            logging.warning("Gemini category embedding request failed", exc_info=True)
            return None

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

    DUPLICATE_THRESHOLD = 30.0
    LIVE_SUGGESTION_THRESHOLD = 30.0

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
        has_location = bool(location and location.strip())
        location_score = float(fuzz.token_set_ratio(location.lower(), ticket.location.lower())) if has_location else 0.0
        lexical_score = float(fuzz.token_set_ratio(description.lower(), ticket.description.lower()))
        lexical_score = 0.7 * lexical_score + 0.3 * float(fuzz.partial_ratio(description.lower(), ticket.description.lower()))

        left, right = cls._location_parts(location), cls._location_parts(ticket.location)
        room_conflict = left["room"] and right["room"] and left["room"].replace(" ", "") != right["room"].replace(" ", "")
        block_conflict = left["block"] and right["block"] and left["block"] != right["block"]
        if has_location and room_conflict:
            location_score *= 0.3
        elif has_location and block_conflict:
            location_score *= 0.55

        semantic_score = lexical_score
        stored = getattr(ticket, "description_embedding", None) or []
        if query_vector and len(stored) == len(query_vector):
            cosine = sum(a * b for a, b in zip(query_vector, stored))
            semantic_score = max(0.0, min(100.0, cosine * 100.0))

        if not has_location:
            overall = semantic_score * 0.65 + lexical_score * 0.35 if query_vector and stored else lexical_score
        elif query_vector and stored:
            overall = location_score * 0.35 + lexical_score * 0.25 + semantic_score * 0.40
        else:
            overall = location_score * 0.45 + lexical_score * 0.55
        if has_location and room_conflict:
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

