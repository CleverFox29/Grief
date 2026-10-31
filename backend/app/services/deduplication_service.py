"""Intelligent deduplication engine for campus grievances (F6, F7, NFR 4.1)."""

import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from app.models import Ticket, TicketStatus

class DeduplicationEngine:
    """
    Real-time duplicate grievance detector (F6).
    Evaluates category, location similarity, and tokenized description text
    against currently open/in-progress tickets within $< 2$ seconds.
    """

    DUPLICATE_THRESHOLD = 50.0  # Percentage similarity threshold to trigger duplicate warning

    @classmethod
    def check_duplicates(
        cls,
        db: Session,
        category_id: int,
        location: str,
        description: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scan open tickets and return ranked potential duplicates.
        Meets NFR 4.1 performance criteria (< 2s latency).
        """
        start_time = time.perf_counter()
        
        # Candidate pool: only open/unresolved tickets of the same category (SRS 3.2.3 Notes)
        unresolved_statuses = [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]
        candidates = db.query(Ticket).filter(
            Ticket.category_id == category_id,
            Ticket.status.in_(unresolved_statuses),
            Ticket.parent_ticket_id.is_(None)  # Only compare against parent/primary tickets
        ).all()

        if not candidates:
            return []

        clean_location = location.strip().lower()
        clean_description = description.strip().lower()
        matches = []

        for ticket in candidates:
            cand_location = ticket.location.strip().lower()
            cand_description = ticket.description.strip().lower()

            # Location similarity (0 - 100)
            loc_score = fuzz.token_set_ratio(clean_location, cand_location)

            # Description text similarity (0 - 100)
            desc_score = fuzz.token_set_ratio(clean_description, cand_description)
            desc_partial = fuzz.partial_ratio(clean_description, cand_description)
            combined_desc_score = (desc_score * 0.7) + (desc_partial * 0.3)

            # Location match weighs 35%, description weighs 65%
            overall_score = (loc_score * 0.35) + (combined_desc_score * 0.65)

            # If location is high match (> 70) and description has relevant similarity (> 40)
            if loc_score >= 70 and combined_desc_score >= 40:
                overall_score = max(overall_score, 60.0)

            if overall_score >= cls.DUPLICATE_THRESHOLD:
                matches.append({
                    "id": ticket.id,
                    "ticket_id": ticket.ticket_id,
                    "category_id": ticket.category_id,
                    "category_name": ticket.category.name if ticket.category else "",
                    "location": ticket.location,
                    "description": ticket.description,
                    "status": ticket.status,
                    "similarity_score": round(overall_score, 1),
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else None
                })

        # Rank matches by highest similarity score
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_matches = matches[:limit]

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        # Benchmark logging
        # print(f"Deduplication completed in {elapsed_ms:.2f} ms for {len(candidates)} candidates.")

        return top_matches
