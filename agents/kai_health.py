# In: agents/kai_health.py

import re
from datetime import datetime
from uagents import Agent, Context
from services.calendar_service import schedule_event
from services.llm_service import generate_weekly_wellness_plan
from services.email_service import send_email
from models import LogActivity
from knowledge.user_model import atomspace, metta
from models import LogActivity, ScheduleMindfulness # <-- Add ScheduleMindfulness


kai_health = Agent(
    name="kai_health_agent",
    seed="kai_health_agent_secret_seed_phrase"
)

kai_health.storage.set("weekly_plan_generated", False)

@kai_health.on_interval(period=20.0)
async def generate_and_execute_plan(ctx: Context):
    if ctx.storage.get("weekly_plan_generated"):
        return

    # THE FIX: Get the address from storage, which was set in main.py
    kai_mind_address = ctx.storage.get("kai_mind_address")

    # (The rest of the function is the same as the last working version)
    ctx.logger.info("Kai-Health checking user state to generate weekly plan...")
    user_profile = {}
    queries = {
        'fitness_goal': ('(fitness-goal user $goal)', 'goal'),
        'current_state': ('(current-state user $state)', 'state'),
        'food_preferences': ('(food-preference user $pref)', 'pref'),
        'food_budget_status': ('(state user (food-budget $status))', 'status')
    }
    for key, (query_str, var_name) in queries.items():
        try:
            query = metta.parse_single(query_str)
            results = atomspace.query(query)
            if results:
                user_profile[key] = str(results[0][var_name]).strip('"')
        except Exception as e:
            ctx.logger.warning(f"Could not retrieve '{key}' from MeTTa brain. It may not be set yet. Error: {e}")

    ctx.logger.info(f"Generated user profile from brain: {user_profile}")
    plan_text = await generate_weekly_wellness_plan(user_profile)
    
    # ... (The rest of the function logic for parsing, scheduling, and emailing is the same)
    
    if kai_mind_address:
        await ctx.send(kai_mind_address, LogActivity(activity_type="Health", details="Generated and executed weekly wellness plan."))
    
    ctx.storage.set("weekly_plan_generated", True)
    ctx.logger.info("Weekly wellness plan successfully executed.")


@kai_health.on_interval(period=3600.0)
async def schedule_annual_checkup(ctx: Context):
    # ... (this function is unchanged)
    pass

@kai_health.on_message(model=ScheduleMindfulness)
async def handle_mindfulness_request(ctx: Context, sender: str, msg: ScheduleMindfulness):
    ctx.logger.info(f"Received request from {sender} to schedule: {msg.activity_title}")
    try:
        schedule_event(
            summary=f"Mindfulness: {msg.activity_title}",
            duration_hours=msg.duration_minutes / 60
        )
        # Log this new activity back to Kai-Mind
        await ctx.send(sender, LogActivity(
            activity_type="Mindfulness",
            details=f"Scheduled a {msg.duration_minutes}-minute {msg.activity_title} session."
        ))
    except Exception as e:
        ctx.logger.error(f"Failed to schedule mindfulness activity: {e}")