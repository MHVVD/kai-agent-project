# In: agents/kai_mind.py

import matplotlib.pyplot as plt
from collections import Counter
from uagents import Agent, Context
from models import LogActivity, LogExpense, SetLearningGoal, ScheduleMindfulness
from knowledge.user_model import atomspace, metta
from services.email_service import send_email
from services.llm_service import get_book_suggestions, generate_motivational_quote, generate_holistic_summary
from protocols.chat import chat_protocol, ChatMessage

# --- Agent Definition ---
kai_mind = Agent(
    name="kai_mind_agent",
    seed="kai_mind_agent_secret_seed_phrase",
)

kai_mind.include(chat_protocol)
kai_mind.storage.set("book_suggestion_made", False)
kai_mind.storage.set("mindfulness_task_done", False)

# --- Message and Event Handlers ---

@kai_mind.on_message(model=LogActivity)
async def handle_activity_log(ctx: Context, sender: str, msg: LogActivity):
    """Handles activity logs from other agents."""
    ctx.logger.info(f"Received activity log from: {sender}")
    fact = metta.parse_single(f'(fact (user mahmud) (activity_type {msg.activity_type}) (details "{msg.details}"))')
    atomspace.add_atom(fact)
    ctx.logger.info(f"New fact added to knowledge graph: {fact}")

@chat_protocol.on_message(model=ChatMessage)
async def handle_user_chat(ctx: Context, sender: str, msg: ChatMessage):
    """Handles commands from the user and delegates to other agents."""
    ctx.logger.info(f"Received command from user: {msg.text}")
    command = msg.text.lower().split()
    reply = "Sorry, I don't understand. Try 'log expense <category> <amount>', 'set goal <description>', 'my mood is <mood>', 'quote', or 'report'."

    try:
        if command[0] == "log" and command[1] == "expense" and len(command) == 4:
            category, amount = command[2], int(command[3])
            finance_addr = ctx.storage.get("kai_finance_address")
            if finance_addr:
                await ctx.send(finance_addr, LogExpense(category=category, amount=amount))
                reply = f"Got it. Logged expense of ₦{amount} for {category}."
        elif command[0] == "set" and command[1] == "goal":
            goal = ' '.join(command[2:])
            career_addr = ctx.storage.get("kai_career_address")
            if career_addr:
                await ctx.send(career_addr, SetLearningGoal(goal_description=goal))
                reply = f"Okay, I've set a new learning goal: {goal}."
        elif command[0] == "my" and command[1] == "mood" and len(command) == 4:
            mood = command[3]
            old_fact_query = metta.parse_single('(mood user $mood)')
            old_facts = atomspace.query(old_fact_query)
            if old_facts:
                atomspace.remove_atom(old_facts[0]['mood'].get_parent())
            atomspace.add_atom(metta.parse_single(f'(mood user {mood})'))
            reply = f"Understood. Updated your mood to '{mood}'."
        elif "quote" in msg.text.lower():
            quote = await generate_motivational_quote("achieving their goals")
            reply = quote
        elif "report" in msg.text.lower():
            await generate_report(ctx)
            reply = "Okay, I'm generating your summary report now. It will be sent to your email."
    except (IndexError, ValueError) as e:
        reply = f"There was an error parsing your command. Error: {e}"

    await ctx.send(sender, ChatMessage(text=reply))

@kai_mind.on_interval(period=120.0)
async def generate_report(ctx: Context):
    """Periodically gathers all data and emails a holistic summary."""
    ctx.logger.info("Gathering data for holistic summary report...")
    user_data = {}
    
    # Query for various facts... (you can add more here)
    activity_query = metta.parse_single('!(match &self (fact (user mahmud) (activity_type $type) ($details)) $type)')
    activity_results = metta.run(str(activity_query))
    if activity_results and activity_results[0]:
        user_data['activity_counts'] = dict(Counter([str(atom) for sublist in activity_results for atom in sublist]))

    savings_query = metta.parse_single('(savings-goal user (target $t) (current $c) (deadline $d))')
    savings_results = atomspace.query(savings_query)
    if savings_results:
        user_data['savings_goal'] = {'target': savings_results[0]['t'].get_object().value, 'current': savings_results[0]['c'].get_object().value}

    if not user_data:
        ctx.logger.info("Not enough data for a report yet.")
        return

    summary_text = await generate_holistic_summary(user_data)
    user_email = "your_email@gmail.com" # Replace with your email
    send_email(user_email, "Your KAI Progress Summary & Insights", summary_text)
    ctx.logger.info(f"Holistic summary report sent to {user_email}.")

@kai_mind.on_interval(period=45.0)
async def mindfulness_and_book_suggester(ctx: Context):
    """Periodically checks mood to suggest mindfulness or books."""
    ctx.logger.info("Kai-Mind checking user state for proactive suggestions...")
    mood_query = metta.parse_single('(mood user $mood)')
    mood_results = atomspace.query(mood_query)

    if mood_results:
        mood = str(mood_results[0]['mood'])
        if mood == 'negative' and not ctx.storage.get("mindfulness_task_done"):
            quote = await generate_motivational_quote("for someone feeling down")
            ctx.logger.info(f"EMPATHETIC QUOTE: {quote}")
            health_address = ctx.storage.get("kai_health_address")
            if health_address:
                await ctx.send(health_address, ScheduleMindfulness(activity_title="Meditation", duration_minutes=15))
            ctx.storage.set("mindfulness_task_done", True)
            return
            
    if not ctx.storage.get("book_suggestion_made"):
        interest_query = metta.parse_single('(interest user $topic)')
        interest_results = atomspace.query(interest_query)
        if interest_results:
            topic = str(interest_results[0]['topic']).strip('"')
            suggestion = await get_book_suggestions(topic)
            ctx.logger.info(f"BOOK SUGGESTION: {suggestion}")
            ctx.storage.set("book_suggestion_made", True)