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

# In: agents/kai_career.py

import hashlib
from datetime import datetime, timedelta
from uagents import Agent, Context
from services.llm_service import find_job_opportunities, generate_tailored_cv, generate_cover_letter
from services.email_service import send_email
from services.calendar_service import schedule_event
from knowledge.user_model import atomspace, metta
from models import SetLearningGoal

# --- Agent Definition ---
kai_career = Agent(
    name="kai_career_agent",
    seed="kai_career_agent_secret_seed_phrase"
)

# --- Configuration ---
USER_BASE_CV = """
Mahmud Lawal - Python Developer
Experience: Built a multi-agent system with uAgents.
Skills: Python, AI, uAgents, MeTTa, APIs.
"""
USER_EMAIL = "your_email@gmail.com" # Replace with your email

# --- Event Handlers ---

@kai_career.on_interval(period=60.0) # Runs every minute for demo purposes
async def perform_job_search_cycle(ctx: Context):
    """
    Periodically searches for jobs, generates documents, and logs them.
    Includes special logic for demo mode to be repeatable.
    """
    
    # Cooldown logic is commented out for the demo to ensure it runs every time.
    # last_sent_time = ctx.storage.get("last_career_email_sent")
    # if last_sent_time and datetime.now() < datetime.fromisoformat(last_sent_time) + timedelta(days=3):
    #     ctx.logger.info("Kai-Career is in 3-day cooldown period. Skipping job search.")
    #     return

    ctx.logger.info("Starting new job search cycle for demo...")
    
    # 1. Find all available job opportunities
    job_postings = await find_job_opportunities(role="Developer")
    if not job_postings:
        ctx.logger.info("No jobs found in this cycle.")
        return

    # 2. Filter out jobs that have already been processed and stored in the "brain"
    new_jobs_to_process = []
    ctx.logger.info(f"Found {len(job_postings)} total jobs. Filtering out previously sent ones...")
    
    for job_desc in job_postings:
        job_hash = hashlib.sha256(job_desc.encode()).hexdigest()
        query = metta.parse_single(f'(processed-job {job_hash})')
        if not atomspace.query(query):
            new_jobs_to_process.append((job_desc, job_hash))

    if not new_jobs_to_process:
        ctx.logger.info("No *new* jobs found. Resetting job memory for next demo run...")
        
        # DEMO MODE FIX: Correctly query for all old jobs and remove them from the "brain"
        old_jobs_query = metta.parse_single('(processed-job $hash)')
        old_jobs = atomspace.query(old_jobs_query)
        
        for job_binding in old_jobs:
            full_atom_to_remove = metta.parse_single(f"(processed-job {str(job_binding['hash'])})")
            atomspace.remove_atom(full_atom_to_remove)
            
        ctx.logger.info("Job memory has been reset.")
        return

    # 3. Process up to 3 new jobs for the demo
    jobs_for_email = new_jobs_to_process[:3]
    email_content_parts = []
    
    for i, (job_desc, job_hash) in enumerate(jobs_for_email):
        ctx.logger.info(f"Processing new job {i+1}/{len(jobs_for_email)}...")
        
        # Generate tailored documents using the ASI:One LLM
        tailored_cv = await generate_tailored_cv(USER_BASE_CV, job_desc)
        cover_letter = await generate_cover_letter(USER_BASE_CV, job_desc)
        
        content_part = f"""
--------------------------------------------------
JOB #{i+1}
--------------------------------------------------

JOB DESCRIPTION:
{job_desc}

================== TAILORED CV ==================
{tailored_cv}

============== TAILORED COVER LETTER ==============
{cover_letter}
        """
        email_content_parts.append(content_part)

        # Add the job's fingerprint to the "brain" so it's not processed again in this run
        fact = metta.parse_single(f'(processed-job {job_hash})')
        atomspace.add_atom(fact)

    # 4. Log the consolidated content instead of emailing for the demo
    if email_content_parts:
        full_email_body = "\n".join(email_content_parts)
        ctx.logger.info(f"--- DEMO: Would send the following email to {USER_EMAIL} ---")
        ctx.logger.info(full_email_body)
        
        ctx.logger.info("Job cycle complete.")

@kai_career.on_message(model=SetLearningGoal)
async def handle_set_goal(ctx: Context, sender: str, msg: SetLearningGoal):
    """Handles requests to set a new learning goal and schedules it."""
    ctx.logger.info(f"Received request to set learning goal: {msg.goal_description}")
    
    # Add the goal to the MeTTa knowledge graph
    goal_fact = metta.parse_single(f'(goal user (learn "{msg.goal_description}"))')
    atomspace.add_atom(goal_fact)
    ctx.logger.info(f"New goal added to knowledge graph: {goal_fact}")
    
    # Schedule the first study block in the calendar
    try:
        schedule_event(summary=f"Study Block: {msg.goal_description}", duration_hours=1)
        ctx.logger.info("Scheduled first study block in Google Calendar.")
    except Exception as e:
        ctx.logger.error(f"Failed to schedule study block: {e}")

# In: agents/kai_finance.py

from uagents import Agent, Context
from services.finance_service import get_market_data
from services.llm_service import generate_investment_analysis
from models import LogExpense
from knowledge.user_model import atomspace, metta
from datetime import datetime

kai_finance = Agent(
    name="kai_finance_agent",
    seed="kai_finance_agent_secret_seed_phrase",
)

@kai_finance.on_message(model=LogExpense)
async def log_expense_handler(ctx: Context, sender: str, msg: LogExpense):
    ctx.logger.info(f"Received expense log for '{msg.category}': ₦{msg.amount}")
    
    query = metta.parse_single(f'(spent {msg.category} $amount)')
    results = atomspace.query(query)

    if not results:
        ctx.logger.error(f"Could not find 'spent' record for category '{msg.category}'")
        return

    # Correctly access the binding by the variable name
    current_spent_atom = results[0]['amount']
    current_spent_amount = current_spent_atom.get_object().value
    new_spent_amount = current_spent_amount + msg.amount
    
    # To replace, we must build the full original and new atoms
    old_atom = metta.parse_single(f'(spent {msg.category} {current_spent_amount})')
    new_atom = metta.parse_single(f'(spent {msg.category} {new_spent_amount})')

    atomspace.replace_atom(old_atom, new_atom)
    ctx.logger.info(f"Updated '{msg.category}' spending to: ₦{new_spent_amount}")


@kai_finance.on_interval(period=300.0)
async def check_investments(ctx: Context):
    ctx.logger.info("Checking for investment insights...")

    profile_query = metta.parse_single('(risk-profile user $profile)')
    profile_results = atomspace.query(profile_query)
    risk_profile = str(profile_results[0]['profile']) if profile_results else 'moderate'
    
    ctx.logger.info(f"User risk profile is: {risk_profile}")

    # Use a reliable global stock for the demo
    market_data = await get_market_data(ticker="MSFT")
    if not market_data:
        return

    suggestion = await generate_investment_analysis(risk_profile, market_data)
    
    ctx.logger.info(f"AI-POWERED INVESTMENT INSIGHT:\n{suggestion}")


@kai_finance.on_interval(period=20.0)
async def check_budget_status(ctx: Context):
    ctx.logger.info("Checking budget status using MeTTa rules...")

    try:
        # 1. FETCH the data from the Atomspace
        budget_query = metta.parse_single('(budget food $b)')
        budget_results = atomspace.query(budget_query)
        budget_amount = budget_results[0]['b'].get_object().value

        spent_query = metta.parse_single('(spent food $s)')
        spent_results = atomspace.query(spent_query)
        spent_amount = spent_results[0]['s'].get_object().value
        
        # 2. ASK MeTTa to do the calculation
        if budget_amount == 0:
            percentage_spent = 0.0
        else:
            calc_expr = f'!(/ (* {spent_amount} 100) {budget_amount})'
            results = metta.run(calc_expr)
            percentage_spent = results[0][0].get_object().value

        ctx.logger.info(f"Food budget is {percentage_spent:.2f}% used.")
        
        # 3. Get the threshold and compare
        threshold_query = metta.parse_single('(threshold food (tight $val))')
        threshold_results = atomspace.query(threshold_query)
        tight_threshold = threshold_results[0]['val'].get_object().value

        if percentage_spent > tight_threshold:
            ctx.logger.warning(f"Food budget is over the {tight_threshold}% threshold!")
            status_fact = metta.parse_single('(state user (food-budget tight))')
            atomspace.add_atom(status_fact)
            ctx.logger.info(f"Updated user state in knowledge graph: {status_fact}")
    except Exception as e:
        ctx.logger.error(f"Error checking budget with MeTTa: {e}")

# --- NEW HANDLER FOR GOAL TRACKING ---
@kai_finance.on_interval(period=60.0) # Checks once per minute for testing
async def check_savings_goal(ctx: Context):
    ctx.logger.info("Checking progress on savings goal...")
    
    # Query the brain for the savings goal details
    query = metta.parse_single('(savings-goal user (target $target) (current $current) (deadline $deadline))')
    results = atomspace.query(query)

    if not results:
        return

    try:
        goal = results[0]
        target = goal['target'].get_object().value
        current = goal['current'].get_object().value
        deadline_str = str(goal['deadline']).strip('"')
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")

        # Calculate progress
        progress_percent = (current / target) * 100
        days_left = (deadline - datetime.now()).days

        if days_left <= 0:
            ctx.logger.info(f"Savings goal deadline has passed. Progress: {progress_percent:.2f}%")
            return

        # Calculate required savings rate
        amount_to_save = target - current
        required_per_day = amount_to_save / days_left

        ctx.logger.info(f"SAVINGS GOAL UPDATE: You are {progress_percent:.2f}% towards your goal of ₦{target}.")
        ctx.logger.info(f"You have {days_left} days left to save ₦{amount_to_save}.")
        ctx.logger.info(f"To stay on track, you need to save approximately ₦{required_per_day:.2f} per day.")

    except Exception as e:
        ctx.logger.error(f"Error processing savings goal: {e}")

# In: main.py

from uagents import Bureau
from agents.kai_health import kai_health
from agents.kai_career import kai_career
from agents.kai_mind import kai_mind
from agents.kai_finance import kai_finance

if __name__ == "__main__":
    bureau = Bureau(port=8000, endpoint=["http://localhost:8000/submit"], log_level="INFO")

    # Add all agents to the bureau
    bureau.add(kai_health)
    bureau.add(kai_career)
    bureau.add(kai_mind)
    bureau.add(kai_finance)
    
    # --- Address Exchange for internal communication ---
    kai_health.storage.set("kai_mind_address", kai_mind.address)

    # --- Print Addresses for Inspector UI ---
    print("\n" + "="*60)
    print("AGENT ADDRESSES FOR INSPECTOR UI:")
    print(f"COPY THIS ONE FOR CHAT -> {kai_mind.name}: {kai_mind.address}")
    print("="*60 + "\n")
    
    # Run the entire multi-agent system
    print("Starting Bureau...")
    bureau.run()