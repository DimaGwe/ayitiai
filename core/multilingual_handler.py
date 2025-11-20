"""
Multilingual Handler for AYITI AI
Native support for: Kreyòl, French, English, Spanish
Priority: Kreyòl-first approach
"""

from typing import Optional, Dict, Tuple
import logging
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator

from core.config_manager import settings

# Set seed for consistent language detection
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)


class MultilingualProcessor:
    """
    Native support for: Kreyòl, French, English, Spanish
    Priority: Kreyòl-first approach
    """

    # Language code mappings
    LANGUAGE_CODES = {
        "ht": "Haitian Creole",
        "fr": "French",
        "en": "English",
        "es": "Spanish"
    }

    # Common Kreyòl keywords for detection
    KREYOL_KEYWORDS = [
        "mwen", "ou", "li", "nou", "yo", "ki", "sa", "kijan", "poukisa",
        "konbyen", "kote", "kilè", "èske", "gen", "pa", "ak", "nan",
        "pou", "sou", "anba", "tou", "byen", "mal", "bon", "move"
    ]

    # Common French keywords
    FRENCH_KEYWORDS = [
        "je", "tu", "il", "nous", "vous", "ils", "qui", "que", "quoi",
        "comment", "pourquoi", "combien", "où", "quand", "avec", "dans"
    ]

    def __init__(self):
        """Initialize multilingual processor"""
        self.supported_languages = settings.supported_languages
        self.default_language = settings.default_language

    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Auto-detect language with confidence scoring

        Args:
            text: Input text to analyze

        Returns:
            Tuple of (language_code, confidence_score)
        """
        if not text or len(text.strip()) < 3:
            return (self.default_language, 1.0)

        try:
            # Check for Kreyòl keywords first (priority detection)
            kreyol_score = self._check_kreyol_keywords(text)
            if kreyol_score > 0.6:
                logger.info(f"Detected Kreyòl with keyword score: {kreyol_score}")
                return ("ht", kreyol_score)

            # Use langdetect for other languages
            detected = detect(text)

            # Map detected language to supported languages
            if detected in self.supported_languages:
                confidence = 0.8  # Baseline confidence
                logger.info(f"Detected language: {detected}")
                return (detected, confidence)

            # Default to Kreyòl if detection uncertain
            logger.warning(f"Uncertain detection: {detected}, defaulting to Kreyòl")
            return (self.default_language, 0.5)

        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return (self.default_language, 0.5)

    def _check_kreyol_keywords(self, text: str) -> float:
        """
        Check for Kreyòl-specific keywords

        Args:
            text: Input text

        Returns:
            Confidence score (0-1)
        """
        text_lower = text.lower()
        words = text_lower.split()

        if not words:
            return 0.0

        kreyol_count = sum(1 for word in words if word in self.KREYOL_KEYWORDS)
        french_count = sum(1 for word in words if word in self.FRENCH_KEYWORDS)

        # If more Kreyòl keywords than French, likely Kreyòl
        if kreyol_count > french_count:
            return min(kreyol_count / len(words) * 3, 1.0)

        return 0.0

    def translate_if_needed(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Only translate when necessary for accuracy

        Args:
            text: Text to potentially translate
            target_language: Target language code
            source_language: Source language (auto-detected if None)

        Returns:
            Translated text or original if not needed
        """
        if not text:
            return text

        # Auto-detect source if not provided
        if source_language is None:
            source_language, _ = self.detect_language(text)

        # No translation needed if same language
        if source_language == target_language:
            return text

        # Check if both languages are supported
        if source_language not in self.supported_languages:
            logger.warning(f"Unsupported source language: {source_language}")
            return text

        if target_language not in self.supported_languages:
            logger.warning(f"Unsupported target language: {target_language}")
            return text

        try:
            translator = GoogleTranslator(source=source_language, target=target_language)
            translated = translator.translate(text)

            logger.info(
                f"Translated from {source_language} to {target_language}: "
                f"{text[:50]}... -> {translated[:50]}..."
            )

            return translated

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text  # Return original on error

    def generate_cultural_context(self, language: str, sector: str) -> str:
        """
        Add cultural nuances to prompts based on language and sector

        Args:
            language: Language code
            sector: Sector name

        Returns:
            Cultural context string
        """
        contexts = {
            "ht": {
                "agriculture": "Konsidere pratik tradisyonèl ayisyen ak resous lokal disponib.",
                "education": "Konsidere kontèks edikasyon ayisyen ak enpòtans lang kreyòl.",
                "fishing": "Konsidere pratik pèch tradisyonèl ak rezève marin ayisyen yo.",
                "infrastructure": "Konsidere kondisyon lokal ak materyèl disponib nan Ayiti.",
                "health": "Konsidere medsin tradisyonèl ak aksè swen sante nan kominote ayisyen.",
                "governance": "Konsidere sistèm gouvènans lokal ak patisipasyon kominotè."
            },
            "fr": {
                "agriculture": "Considérez les pratiques agricoles traditionnelles haïtiennes et les ressources locales disponibles.",
                "education": "Considérez le contexte éducatif haïtien et l'importance de la langue créole.",
                "fishing": "Considérez les pratiques de pêche traditionnelles et les réserves marines haïtiennes.",
                "infrastructure": "Considérez les conditions locales et les matériaux disponibles en Haïti.",
                "health": "Considérez la médecine traditionnelle et l'accès aux soins de santé dans les communautés haïtiennes.",
                "governance": "Considérez les systèmes de gouvernance locale et la participation communautaire."
            },
            "en": {
                "agriculture": "Consider traditional Haitian farming practices and locally available resources.",
                "education": "Consider the Haitian educational context and the importance of Creole language.",
                "fishing": "Consider traditional fishing practices and Haitian marine resources.",
                "infrastructure": "Consider local conditions and materials available in Haiti.",
                "health": "Consider traditional medicine and healthcare access in Haitian communities.",
                "governance": "Consider local governance systems and community participation."
            },
            "es": {
                "agriculture": "Considere las prácticas agrícolas tradicionales haitianas y los recursos locales disponibles.",
                "education": "Considere el contexto educativo haitiano y la importancia del idioma criollo.",
                "fishing": "Considere las prácticas de pesca tradicionales y los recursos marinos haitianos.",
                "infrastructure": "Considere las condiciones locales y los materiales disponibles en Haití.",
                "health": "Considere la medicina tradicional y el acceso a la atención médica en las comunidades haitianas.",
                "governance": "Considere los sistemas de gobernanza local y la participación comunitaria."
            }
        }

        # Get cultural context or default
        lang_contexts = contexts.get(language, contexts["ht"])
        context = lang_contexts.get(sector, "")

        return context

    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        return self.LANGUAGE_CODES.get(code, code)

    def validate_language(self, code: str) -> bool:
        """Check if language code is supported"""
        return code in self.supported_languages

    def get_response_format_instructions(self, language: str) -> str:
        """Get language-specific response formatting instructions"""
        instructions = {
            "ht": "Reponn nan kreyòl ayisyen. Itilize yon langaj senp ak pratik.",
            "fr": "Répondez en français. Utilisez un langage simple et pratique.",
            "en": "Respond in English. Use simple and practical language.",
            "es": "Responda en español. Use un lenguaje simple y práctico."
        }

        return instructions.get(language, instructions["ht"])


# Global instance
multilingual = MultilingualProcessor()
