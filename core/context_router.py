"""
Context Router for AYITI AI
Automatically detects which sector expertise to apply
"""

from typing import List, Dict, Optional, Tuple
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


class SectorRouter:
    """
    Automatically detects which sector expertise to apply
    Supports multi-sector queries
    """

    # Sector keywords in multiple languages
    SECTOR_KEYWORDS = {
        "agriculture": {
            "ht": [
                "agrikilti", "jaden", "plante", "rekòt", "fèm", "tè", "angrè",
                "manyòk", "bannann", "mayi", "pwa", "kafe", "mango", "sereyal",
                "bèt", "kodenn", "poul", "kabrit", "bèf", "chwal",
                "zouti", "machèt", "rajo", "dlo", "lapli", "sechrès",
                "vann", "mache", "pwodwi", "kilti", "semans"
            ],
            "fr": [
                "agriculture", "jardin", "plante", "récolte", "ferme", "terre", "engrais",
                "manioc", "banane", "maïs", "haricot", "café", "mangue", "céréale",
                "bétail", "dinde", "poulet", "chèvre", "bSuf", "cheval",
                "outil", "machette", "houe", "eau", "pluie", "sécheresse",
                "vendre", "marché", "produit", "culture", "semence"
            ],
            "en": [
                "agriculture", "farming", "garden", "plant", "harvest", "farm", "soil", "fertilizer",
                "cassava", "plantain", "corn", "bean", "coffee", "mango", "cereal",
                "livestock", "turkey", "chicken", "goat", "cattle", "horse",
                "tool", "machete", "hoe", "water", "rain", "drought",
                "sell", "market", "crop", "cultivation", "seed"
            ]
        },
        "education": {
            "ht": [
                "edikasyon", "lekòl", "etidyan", "elèv", "pwofesè", "ansèyman",
                "aprann", "liv", "kaye", "ekzamen", "kou", "klas", "pwogram",
                "alfabetizasyon", "konpetans", "fòmasyon", "diplòm",
                "matematik", "syans", "istwa", "lang", "kreyòl"
            ],
            "fr": [
                "éducation", "école", "étudiant", "élève", "professeur", "enseignement",
                "apprendre", "livre", "cahier", "examen", "cours", "classe", "programme",
                "alphabétisation", "compétence", "formation", "diplôme",
                "mathématiques", "science", "histoire", "langue", "créole"
            ],
            "en": [
                "education", "school", "student", "pupil", "teacher", "teaching",
                "learn", "book", "notebook", "exam", "course", "class", "curriculum",
                "literacy", "skill", "training", "degree", "diploma",
                "mathematics", "science", "history", "language", "creole"
            ]
        },
        "fishing": {
            "ht": [
                "lapèch", "pwason", "lanmè", "bato", "filè", "zen", "krab",
                "lanbi", "reken", "kòt", "plaj", "alevaj", "akwakiltri",
                "sal", "glase", "konsève", "mache"
            ],
            "fr": [
                "pêche", "poisson", "mer", "bateau", "filet", "hameçon", "crabe",
                "conque", "requin", "côte", "plage", "alevin", "aquaculture",
                "sel", "glace", "conserver", "marché"
            ],
            "en": [
                "fishing", "fish", "sea", "ocean", "boat", "net", "hook", "crab",
                "conch", "shark", "coast", "beach", "fry", "aquaculture",
                "salt", "ice", "preserve", "market"
            ]
        },
        "infrastructure": {
            "ht": [
                "konstriksyon", "batiman", "wout", "pon", "dlo", "elektrisite",
                "enèji", "solè", "van", "sanitasyon", "latrin", "twalet",
                "beton", "blòk", "bwa", "materyèl", "zouti"
            ],
            "fr": [
                "construction", "bâtiment", "route", "pont", "eau", "électricité",
                "énergie", "solaire", "vent", "assainissement", "latrine", "toilette",
                "béton", "bloc", "bois", "matériel", "outil"
            ],
            "en": [
                "construction", "building", "road", "bridge", "water", "electricity",
                "energy", "solar", "wind", "sanitation", "latrine", "toilet",
                "concrete", "block", "wood", "material", "tool"
            ]
        },
        "health": {
            "ht": [
                "sante", "malad", "doktè", "lopital", "klinik", "medikaman",
                "remèd", "trete", "vaksen", "prevention", "ijyèn", "dlo pwòp",
                "manje", "nitrisyon", "fanm ansent", "timoun", "maladi"
            ],
            "fr": [
                "santé", "malade", "docteur", "hôpital", "clinique", "médicament",
                "remède", "traiter", "vaccin", "prévention", "hygiène", "eau propre",
                "nourriture", "nutrition", "femme enceinte", "enfant", "maladie"
            ],
            "en": [
                "health", "sick", "doctor", "hospital", "clinic", "medicine",
                "remedy", "treat", "vaccine", "prevention", "hygiene", "clean water",
                "food", "nutrition", "pregnant", "child", "disease"
            ]
        },
        "governance": {
            "ht": [
                "gouvènman", "lwa", "règleman", "dwa", "jistis", "tribinal",
                "majistra", "elektoral", "vòt", "sitwayen", "kominote",
                "òganizasyon", "asosyasyon", "sèvis piblik"
            ],
            "fr": [
                "gouvernement", "loi", "règlement", "droit", "justice", "tribunal",
                "magistrat", "électoral", "vote", "citoyen", "communauté",
                "organisation", "association", "service public"
            ],
            "en": [
                "government", "law", "regulation", "right", "justice", "court",
                "magistrate", "electoral", "vote", "citizen", "community",
                "organization", "association", "public service"
            ]
        }
    }

    def __init__(self):
        """Initialize sector router"""
        self.sectors = list(self.SECTOR_KEYWORDS.keys())

    def analyze_query_intent(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Tuple[str, float]]:
        """
        Use keyword analysis + semantic understanding
        Returns sectors ranked by relevance

        Args:
            query: User query text
            conversation_history: Previous messages for context

        Returns:
            List of (sector, confidence_score) tuples, sorted by confidence
        """
        if not query:
            return []

        query_lower = query.lower()
        sector_scores = Counter()

        # Score based on keyword matches
        for sector, languages in self.SECTOR_KEYWORDS.items():
            score = 0
            for lang, keywords in languages.items():
                for keyword in keywords:
                    # Count occurrences of keyword
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', query_lower))
                    score += count

            if score > 0:
                sector_scores[sector] = score

        # Normalize scores to 0-1 range
        if sector_scores:
            max_score = max(sector_scores.values())
            normalized_scores = [
                (sector, score / max_score)
                for sector, score in sector_scores.most_common()
            ]

            # Filter out very low confidence matches
            filtered_scores = [
                (sector, conf) for sector, conf in normalized_scores
                if conf >= 0.3
            ]

            if filtered_scores:
                logger.info(f"Detected sectors: {filtered_scores}")
                return filtered_scores

        # Default to general if no clear sector
        logger.info("No specific sector detected, using general")
        return [("general", 0.5)]

    def get_relevant_knowledge_sources(
        self,
        sectors: List[Tuple[str, float]]
    ) -> List[str]:
        """
        Combine multiple knowledge bases for cross-sector queries

        Args:
            sectors: List of (sector, confidence) tuples

        Returns:
            List of knowledge base paths to query
        """
        knowledge_sources = []

        for sector, confidence in sectors:
            if confidence >= 0.3:  # Only include confident matches
                knowledge_sources.append(sector)

        return knowledge_sources

    def get_primary_sector(
        self,
        sectors: List[Tuple[str, float]]
    ) -> Optional[str]:
        """
        Get the primary (highest confidence) sector

        Args:
            sectors: List of (sector, confidence) tuples

        Returns:
            Primary sector name or None
        """
        if not sectors:
            return None

        return sectors[0][0]

    def is_multi_sector_query(
        self,
        sectors: List[Tuple[str, float]],
        threshold: float = 0.6
    ) -> bool:
        """
        Determine if query spans multiple sectors

        Args:
            sectors: List of (sector, confidence) tuples
            threshold: Confidence threshold for secondary sectors

        Returns:
            True if multiple sectors are relevant
        """
        high_confidence_sectors = [
            sector for sector, conf in sectors
            if conf >= threshold
        ]

        return len(high_confidence_sectors) > 1

    def suggest_related_sectors(
        self,
        primary_sector: str
    ) -> List[str]:
        """
        Suggest sectors that often relate to the primary sector

        Args:
            primary_sector: Primary sector name

        Returns:
            List of related sector names
        """
        # Common sector relationships
        relationships = {
            "agriculture": ["infrastructure", "education", "health"],
            "education": ["agriculture", "health", "governance"],
            "fishing": ["infrastructure", "health", "education"],
            "infrastructure": ["agriculture", "health", "governance"],
            "health": ["education", "infrastructure", "agriculture"],
            "governance": ["education", "infrastructure", "health"]
        }

        return relationships.get(primary_sector, [])


# Global instance
router = SectorRouter()
