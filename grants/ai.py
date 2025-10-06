"""Lightweight AI helper for grant insights.

Attempts to use sentence-transformers (all-MiniLM-L6-v2) to produce an
extractive-style summary and a simple score. If the library or model is not
available, returns a graceful fallback message.
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

def analyze_text(text: str) -> Dict[str, Optional[str]]:
    """Return a dict: {'summary': str, 'score': float or None, 'note': str}

    - summary: short extractive summary or fallback explanation
    - score: a float between 0-1 estimating 'impact' (higher is better) or None
    - note: explanation about model used or fallback
    """
    if not text:
        return {'summary': '', 'score': None, 'note': 'No text provided.'}

    # Try to use sentence-transformers for encoding and a simple centroid heuristic
    try:
        from sentence_transformers import SentenceTransformer, util

        model = SentenceTransformer('all-MiniLM-L6-v2')
        # split into sentences (naive split)
        sents = [s.strip() for s in text.split('.') if s.strip()]
        if not sents:
            return {'summary': text[:280], 'score': None, 'note': 'Used raw text; no sentences found.'}

        embeddings = model.encode(sents, convert_to_tensor=True)
        centroid = embeddings.mean(dim=0)
        scores = util.cos_sim(embeddings, centroid).squeeze().tolist()
        # pick top 2 sentences by similarity to centroid
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        top_idx = [i for i, _ in ranked[:2]]
        summary = '. '.join([sents[i] for i in sorted(top_idx)])
        # normalize score to 0..1
        avg_score = float(sum(scores) / len(scores))
        # clamp
        import math
        norm = 1 / (1 + math.exp(-12 * (avg_score - 0.5)))  # sigmoid-ish to spread
        return {
            'summary': summary if summary else text[:280],
            'score': round(norm, 3),
            'note': 'Model: sentence-transformers all-MiniLM-L6-v2 (local)',
        }

    except Exception as e:
        logger.debug('sentence-transformers not available or failed: %s', e)
        # Fallback: return first 280 chars and no score
        return {
            'summary': (text[:280] + '...') if len(text) > 280 else text,
            'score': None,
            'note': 'Fallback: sentence-transformers unavailable; install sentence-transformers for richer insights.',
        }
