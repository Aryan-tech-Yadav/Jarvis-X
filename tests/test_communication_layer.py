import unittest

from app.communication import (
    AgentMessage,
    Channel,
    Conversation,
    Mailbox,
    MessagePriority,
)


class TestCommunicationLayer(unittest.TestCase):
    def test_mailbox_delivers_high_priority_first(self):
        mailbox = Mailbox("backend")
        mailbox.deliver(AgentMessage("qa", "backend", "note", "normal"))
        mailbox.deliver(AgentMessage("repair", "backend", "urgent", "critical", MessagePriority.CRITICAL))
        self.assertEqual(mailbox.receive().message_type, "urgent")
        self.assertEqual(mailbox.receive().message_type, "note")

    def test_channel_routes_and_broadcasts(self):
        channel = Channel()
        channel.register(Mailbox("backend"))
        channel.register(Mailbox("database"))
        channel.send(AgentMessage("backend", "database", "schema"))
        sent = channel.broadcast("backend", ["database"], "status", {"ready": True})
        self.assertEqual(channel.mailbox("database").pending, 2)
        self.assertEqual(sent[0].receiver, "database")

    def test_conversation_correlates_reply(self):
        conversation = Conversation()
        request = conversation.append(AgentMessage("backend", "database", "schema"))
        reply = conversation.reply(request, "database", {"tables": ["users"]})
        self.assertEqual(reply.reply_to, request.message_id)
        self.assertEqual(len(conversation.messages), 2)

    def test_message_round_trip(self):
        message = AgentMessage("a", "b", "work", {"x": 1}, metadata={"trace": "t"})
        restored = AgentMessage.from_dict(message.to_dict())
        self.assertEqual(restored.message_id, message.message_id)
        self.assertEqual(restored.metadata, {"trace": "t"})


if __name__ == "__main__":
    unittest.main()
