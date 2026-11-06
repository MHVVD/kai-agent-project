import os
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
USER_EMAIL = os.getenv("KAI_USER_EMAIL", "")

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