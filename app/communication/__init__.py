"""Message-passing primitives for collaborating Jarvis-X agents."""

from .message import AgentMessage, MessagePriority
from .mailbox import Mailbox
from .channel import Channel
from .conversation import Conversation
from .event import CommunicationEvent
from .event_bus import CommunicationEventBus

__all__ = [
    "AgentMessage",
    "MessagePriority",
    "Mailbox",
    "Channel",
    "Conversation",
    "CommunicationEvent",
    "CommunicationEventBus",
]

