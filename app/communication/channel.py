"""Direct and broadcast message routing between agent mailboxes."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .mailbox import Mailbox
from .message import AgentMessage


class Channel:
    def __init__(self):
        self._mailboxes: Dict[str, Mailbox] = {}

    def register(self, mailbox: Mailbox) -> None:
        if mailbox.owner in self._mailboxes:
            raise ValueError(f"Mailbox already registered: {mailbox.owner}")
        self._mailboxes[mailbox.owner] = mailbox

    def unregister(self, owner: str) -> Mailbox:
        try:
            return self._mailboxes.pop(owner)
        except KeyError as exc:
            raise KeyError(f"Mailbox not registered: {owner}") from exc

    def mailbox(self, owner: str) -> Mailbox:
        try:
            return self._mailboxes[owner]
        except KeyError as exc:
            raise KeyError(f"Mailbox not registered: {owner}") from exc

    def send(self, message: AgentMessage) -> AgentMessage:
        self.mailbox(message.receiver).deliver(message)
        return message

    def broadcast(
        self,
        sender: str,
        receivers: Iterable[str],
        message_type: str,
        payload=None,
        priority: int = 2,
        metadata=None,
    ) -> List[AgentMessage]:
        messages = [
            AgentMessage(sender, receiver, message_type, payload, priority, metadata=dict(metadata or {}))
            for receiver in receivers
        ]
        for message in messages:
            self.send(message)
        return messages

