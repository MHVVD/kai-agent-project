import threading
from queue import Queue
from uagents import Agent, Context, Model

# We must define the ChatMessage model exactly the same way as the server
class ChatMessage(Model):
    text: str

message_queue: Queue = Queue()

user = Agent(
    name="user_agent",
    seed="a_very_secret_user_agent_seed_phrase",
    port=8003, # Using a different port
)

# This handler prints replies from the server agent
@user.on_message(model=ChatMessage)
async def on_agent_reply(ctx: Context, sender: str, msg: ChatMessage):
    print(f"\n[{sender[-6:]}]: {msg.text}")
    print(f"[{ctx.name}]: ", end="", flush=True)

# This is the agent's "outbox"
@user.on_interval(period=0.1)
async def send_message_from_queue(ctx: Context):
    if not message_queue.empty():
        destination, message_text = message_queue.get()
        if destination == "STOP":
            ctx.stop()
            return
        await ctx.send(destination, ChatMessage(text=message_text))

# This function runs in a separate thread for user input
def get_user_input(agent_address: str):
    print("\nChat session started. You can now send messages. Type 'exit' to quit.")
    while True:
        try:
            message = input(f"[{user.name}]: ")
            if message.lower() == 'exit':
                break
            message_queue.put((agent_address, message))
        except (EOFError, KeyboardInterrupt):
            break
    
    message_queue.put(("STOP", ""))
    print("\nChat session ended.")

if __name__ == "__main__":
    agent_address = input("Please enter the address of the Kai-Mind agent: ")
    
    input_thread = threading.Thread(target=get_user_input, args=(agent_address,))
    input_thread.start()
    
    user.run()
    
    input_thread.join()