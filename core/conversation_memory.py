"""
Conversation Memory System for AYITI AI
Manages conversation history and context
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history for context-aware responses
    Stores recent messages and provides conversation context
    """

    def __init__(self, max_messages_per_conversation: int = 10, ttl_hours: int = 24):
        """
        Initialize conversation memory

        Args:
            max_messages_per_conversation: Maximum messages to keep per conversation
            ttl_hours: Time-to-live for conversations in hours
        """
        self.conversations = defaultdict(list)
        self.metadata = {}  # Conversation metadata (created_at, last_updated, etc.)
        self.max_messages = max_messages_per_conversation
        self.ttl = timedelta(hours=ttl_hours)

    def create_conversation_id(self) -> str:
        """
        Create a new unique conversation ID

        Returns:
            Conversation ID string
        """
        conv_id = str(uuid.uuid4())
        self.metadata[conv_id] = {
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "message_count": 0
        }
        logger.info(f"Created new conversation: {conv_id}")
        return conv_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a message to conversation history

        Args:
            conversation_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata
        """
        if conversation_id not in self.metadata:
            self.metadata[conversation_id] = {
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "message_count": 0
            }

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[conversation_id].append(message)

        # Update metadata
        self.metadata[conversation_id]["last_updated"] = datetime.now()
        self.metadata[conversation_id]["message_count"] += 1

        # Trim if exceeds max messages
        if len(self.conversations[conversation_id]) > self.max_messages:
            self.conversations[conversation_id] = \
                self.conversations[conversation_id][-self.max_messages:]

        logger.debug(
            f"Added {role} message to conversation {conversation_id} "
            f"(total: {len(self.conversations[conversation_id])} messages)"
        )

    def get_conversation_history(
        self,
        conversation_id: str,
        include_metadata: bool = False
    ) -> List[Dict]:
        """
        Get conversation history

        Args:
            conversation_id: Conversation ID
            include_metadata: Whether to include message metadata

        Returns:
            List of message dicts
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return []

        messages = self.conversations[conversation_id]

        if not include_metadata:
            # Return only role and content
            return [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]

        return messages

    def get_recent_messages(
        self,
        conversation_id: str,
        n: int = 5
    ) -> List[Dict]:
        """
        Get recent N messages from conversation

        Args:
            conversation_id: Conversation ID
            n: Number of recent messages

        Returns:
            List of recent message dicts
        """
        messages = self.get_conversation_history(conversation_id)
        return messages[-n:] if messages else []

    def get_conversation_context(
        self,
        conversation_id: str,
        max_tokens: int = 500
    ) -> str:
        """
        Get formatted conversation context for LLM

        Args:
            conversation_id: Conversation ID
            max_tokens: Approximate max tokens (chars/4)

        Returns:
            Formatted context string
        """
        messages = self.get_conversation_history(conversation_id)

        if not messages:
            return ""

        # Build context from most recent messages
        context_parts = []
        current_length = 0
        max_chars = max_tokens * 4  # Rough approximation

        for message in reversed(messages):
            msg_text = f"{message['role']}: {message['content']}\n"
            msg_length = len(msg_text)

            if current_length + msg_length > max_chars:
                break

            context_parts.insert(0, msg_text)
            current_length += msg_length

        return "".join(context_parts)

    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear a conversation's history

        Args:
            conversation_id: Conversation ID
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

        if conversation_id in self.metadata:
            del self.metadata[conversation_id]

        logger.info(f"Cleared conversation: {conversation_id}")

    def cleanup_expired(self) -> int:
        """
        Remove expired conversations based on TTL

        Returns:
            Number of conversations removed
        """
        now = datetime.now()
        expired = []

        for conv_id, meta in self.metadata.items():
            if now - meta["last_updated"] > self.ttl:
                expired.append(conv_id)

        for conv_id in expired:
            self.clear_conversation(conv_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired conversations")

        return len(expired)

    def get_conversation_stats(self, conversation_id: str) -> Optional[Dict]:
        """
        Get statistics about a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            Dict with conversation statistics or None
        """
        if conversation_id not in self.metadata:
            return None

        meta = self.metadata[conversation_id]
        messages = self.conversations[conversation_id]

        return {
            "conversation_id": conversation_id,
            "created_at": meta["created_at"].isoformat(),
            "last_updated": meta["last_updated"].isoformat(),
            "message_count": len(messages),
            "user_messages": sum(1 for m in messages if m["role"] == "user"),
            "assistant_messages": sum(1 for m in messages if m["role"] == "assistant"),
            "age_hours": (datetime.now() - meta["created_at"]).total_seconds() / 3600
        }

    def list_active_conversations(self) -> List[str]:
        """
        List all active conversation IDs

        Returns:
            List of conversation IDs
        """
        return list(self.conversations.keys())

    def get_all_stats(self) -> Dict:
        """
        Get statistics about all conversations

        Returns:
            Dict with overall statistics
        """
        total_conversations = len(self.conversations)
        total_messages = sum(len(msgs) for msgs in self.conversations.values())

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": (
                total_messages / total_conversations if total_conversations > 0 else 0
            ),
            "active_conversations": self.list_active_conversations()
        }


# Global instance
conversation_memory = ConversationMemory()
