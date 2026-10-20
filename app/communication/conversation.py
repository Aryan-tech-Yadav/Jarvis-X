"""Conversation history and correlation for agent requests and replies."""

from __future__ import annotations

from typing import Iterable, List, Optional

from .message import AgentMessage


class Conversation:
    def __init__(self, conversation_id: Optional[str] = None):
        self.conversation_id = conversation_id
        self._messages: List[AgentMessage] = []

    def append(self, message: AgentMessage) -> AgentMessage:
        if message.correlation_id is None:
            message.correlation_id = self.conversation_id or message.message_id
        if self.conversation_id is None:
            self.conversation_id = message.correlation_id
        if message.correlation_id != self.conversation_id:
            raise ValueError("Message belongs to a different conversation")
        self._messages.append(message)
        return message

    def reply(self, request: AgentMessage, sender: str, payload=None, message_type: str = "REPLY") -> AgentMessage:
        reply = AgentMessage(
            sender=sender,
            receiver=request.sender,
            message_type=message_type,
            payload=payload,
            correlation_id=request.correlation_id or self.conversation_id,
            reply_to=request.message_id,
        )
        return self.append(reply)

    @property
    def messages(self) -> List[AgentMessage]:
        return list(self._messages)

    def between(self, sender: str, receiver: str) -> List[AgentMessage]:
        return [m for m in self._messages if m.sender == sender and m.receiver == receiver]

