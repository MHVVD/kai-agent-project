# In: protocols/chat.py
from uagents import Protocol, Model

class ChatMessage(Model):
    text: str

# Let's give our protocol a name and version
chat_protocol = Protocol("UserChat", version="1.0")