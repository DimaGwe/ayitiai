"""
DeepSeek LLM Integration for AYITI AI
Provides cost-efficient LLM foundation with request optimization
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import openai
from openai import AsyncOpenAI
import logging
from dataclasses import dataclass
from collections import defaultdict

from core.config_manager import settings

logger = logging.getLogger(__name__)


@dataclass
class CostTracker:
    """Track API costs per request and daily totals"""
    daily_cost: float = 0.0
    request_count: int = 0
    last_reset: datetime = None
    cost_by_sector: Dict[str, float] = None

    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = datetime.now()
        if self.cost_by_sector is None:
            self.cost_by_sector = defaultdict(float)

    def reset_if_needed(self):
        """Reset daily costs if it's a new day"""
        if datetime.now() - self.last_reset > timedelta(days=1):
            self.daily_cost = 0.0
            self.request_count = 0
            self.cost_by_sector = defaultdict(float)
            self.last_reset = datetime.now()

    def add_cost(self, cost: float, sector: str):
        """Add cost to tracker"""
        self.reset_if_needed()
        self.daily_cost += cost
        self.cost_by_sector[sector] += cost
        self.request_count += 1

    def can_proceed(self) -> bool:
        """Check if we're within cost limits"""
        self.reset_if_needed()
        return self.daily_cost < settings.cost_limit_daily


class DeepSeekIntegration:
    """
    Cost-efficient LLM foundation using DeepSeek API
    Features:
    - Request batching for cost optimization
    - Fallback mechanisms
    - Rate limiting
    - Token usage tracking
    - Context window management
    """

    # DeepSeek pricing (approximate - verify current rates)
    INPUT_COST_PER_1K = 0.0001  # $0.0001 per 1K input tokens
    OUTPUT_COST_PER_1K = 0.0002  # $0.0002 per 1K output tokens

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_api_base
        )
        self.cost_tracker = CostTracker()
        self.response_cache = {}  # Simple in-memory cache

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        sector_context: Optional[str] = None,
        language: str = "ht",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """
        Generate a response using DeepSeek API with sector awareness

        Args:
            messages: List of message dicts with 'role' and 'content'
            sector_context: Sector-specific context to include
            language: Target language code
            temperature: Model temperature (default from settings)
            max_tokens: Max tokens to generate (default from settings)

        Returns:
            Dict with response, cost, and metadata
        """
        # Check cost limits
        if not self.cost_tracker.can_proceed():
            logger.warning("Daily cost limit reached")
            return {
                "response": "Cost limit reached for today. Please try again tomorrow.",
                "error": "COST_LIMIT_EXCEEDED",
                "cost": 0.0
            }

        # Prepare system message with sector context
        system_message = self._build_system_message(sector_context, language)
        full_messages = [{"role": "system", "content": system_message}] + messages

        try:
            # Call DeepSeek API
            response = await self.client.chat.completions.create(
                model=settings.model_name,
                messages=full_messages,
                temperature=temperature or settings.temperature,
                max_tokens=max_tokens or settings.max_tokens
            )

            # Calculate cost
            cost = self._calculate_cost(response.usage)

            # Track cost
            sector = sector_context or "general"
            self.cost_tracker.add_cost(cost, sector)

            # Log metrics
            logger.info(
                f"LLM request completed - Sector: {sector}, "
                f"Cost: ${cost:.4f}, Tokens: {response.usage.total_tokens}"
            )

            return {
                "response": response.choices[0].message.content,
                "cost": cost,
                "tokens_used": response.usage.total_tokens,
                "sector": sector,
                "language": language,
                "model": settings.model_name
            }

        except Exception as e:
            logger.error(f"LLM API error: {str(e)}")
            return {
                "response": "An error occurred processing your request.",
                "error": str(e),
                "cost": 0.0
            }

    def _build_system_message(self, sector: Optional[str], language: str) -> str:
        """Build sector-aware system message with language preference"""

        language_names = {
            "ht": "Haitian Creole (Kreyòl)",
            "fr": "French (Français)",
            "en": "English",
            "es": "Spanish (Español)"
        }

        base_prompt = f"""You are AYITI AI, a helpful assistant designed to support Haiti's development
across multiple sectors. You provide practical, culturally-appropriate advice for Haitian communities.

Language: Respond in {language_names.get(language, language)}.

"""

        sector_prompts = {
            "agriculture": """Sector Focus: AGRICULTURE
You specialize in Haitian agricultural practices, including:
- Sustainable farming for local soil types
- Climate-resilient crops (cassava, plantain, mango, coffee)
- Water conservation and soil enrichment
- Organic pest control
- Post-harvest techniques
- Market access strategies

Provide practical advice suitable for small-scale farmers.""",

            "education": """Sector Focus: EDUCATION
You specialize in Haitian education, including:
- Kreyòl-language teaching materials
- STEM education adaptations
- Vocational training
- Low-resource teaching techniques
- Digital literacy
- Community-based learning

Focus on practical solutions for resource-limited environments.""",

            "fishing": """Sector Focus: FISHING & MARINE RESOURCES
You specialize in Haitian fishing and aquaculture, including:
- Sustainable fishing practices
- Coastal resource management
- Fish processing and preservation
- Aquaculture methods
- Market preparation

Provide advice suitable for coastal communities.""",

            "infrastructure": """Sector Focus: INFRASTRUCTURE
You specialize in Haitian infrastructure development, including:
- Sustainable building practices
- Water and sanitation systems
- Renewable energy solutions
- Road and transportation
- Climate-resilient construction

Focus on practical, locally-appropriate solutions.""",

            "health": """Sector Focus: HEALTH
You specialize in Haitian health and wellness, including:
- Primary healthcare
- Disease prevention
- Nutrition and sanitation
- Traditional and modern medicine integration
- Community health education

Provide culturally-sensitive health guidance.""",

            "governance": """Sector Focus: GOVERNANCE & REGULATIONS
You specialize in Haitian governance, including:
- Local government processes
- Community organization
- Legal rights and regulations
- Civic participation
- Public services access

Provide clear, accessible information."""
        }

        if sector and sector in sector_prompts:
            return base_prompt + sector_prompts[sector]

        return base_prompt + "Provide helpful information across all sectors as needed."

    def _calculate_cost(self, usage) -> float:
        """Calculate cost based on token usage"""
        input_cost = (usage.prompt_tokens / 1000) * self.INPUT_COST_PER_1K
        output_cost = (usage.completion_tokens / 1000) * self.OUTPUT_COST_PER_1K
        return input_cost + output_cost

    async def batch_generate(
        self,
        requests: List[Dict],
        delay_between: float = 0.5
    ) -> List[Dict]:
        """
        Process multiple requests with rate limiting

        Args:
            requests: List of request dicts with 'messages', 'sector_context', 'language'
            delay_between: Delay between requests in seconds

        Returns:
            List of response dicts
        """
        responses = []

        for req in requests:
            response = await self.generate_response(
                messages=req.get("messages", []),
                sector_context=req.get("sector_context"),
                language=req.get("language", "ht")
            )
            responses.append(response)

            # Rate limiting
            if delay_between > 0:
                await asyncio.sleep(delay_between)

        return responses

    def get_cost_stats(self) -> Dict:
        """Get current cost statistics"""
        self.cost_tracker.reset_if_needed()

        return {
            "daily_cost": self.cost_tracker.daily_cost,
            "request_count": self.cost_tracker.request_count,
            "cost_by_sector": dict(self.cost_tracker.cost_by_sector),
            "remaining_budget": settings.cost_limit_daily - self.cost_tracker.daily_cost,
            "limit": settings.cost_limit_daily
        }


# Global instance
llm = DeepSeekIntegration()
