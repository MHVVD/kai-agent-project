# In: services/llm_service.py

import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# --- API Configuration ---
client = OpenAI(
    base_url='https://api.asi1.ai/v1',
    api_key=os.getenv("ASI_ONE_API_KEY")
)

# --- Private Helper Function ---
async def _generate_text(prompt: str) -> str:
    """A helper function to call the ASI:One API."""
    if not client.api_key:
        return "ERROR: ASI_ONE_API_KEY is not set."
    try:
        response = client.chat.completions.create(
            model="asi1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return str(response.choices[0].message.content)
    except Exception as e:
        return f"ERROR: Could not generate text. API call failed: {e}"

# --- Public Service Functions ---

async def generate_motivational_quote(context: str) -> str:
    """Uses an LLM to generate a contextual motivational quote."""
    print(f"Generating motivational quote for context: {context}")
    prompt = f"Write a short, powerful motivational quote related to: {context}."
    return await _generate_text(prompt)

async def generate_diet_plan(prompt: str) -> str:
    """Uses an LLM to generate a diet plan based on a prompt."""
    print("Generating diet plan via ASI:One API...")
    return await _generate_text(prompt)

async def generate_tailored_cv(base_cv: str, job_description: str) -> str:
    """Uses an LLM to tailor a CV for a specific job."""
    print("Generating tailored CV via ASI:One API...")
    full_prompt = (
        f"Here is my base CV:\n---{base_cv}---\n\n"
        f"Here is the job description:\n---{job_description}---\n\n"
        f"Please rewrite my CV to be perfectly tailored for this job. "
        f"The output should be just the rewritten CV text, with no extra commentary."
    )
    return await _generate_text(full_prompt)

async def generate_cover_letter(base_cv: str, job_description: str) -> str:
    """Uses an LLM to generate a cover letter for a specific job."""
    print("Generating cover letter via ASI:One API...")
    prompt = (
        f"Based on my CV below, please write a compelling and professional cover letter "
        f"for the job described. The tone should be confident but not arrogant. "
        f"The output should be just the cover letter text, with no extra commentary.\n\n"
        f"--- MY CV ---\n{base_cv}\n\n"
        f"--- JOB DESCRIPTION ---\n{job_description}"
    )
    return await _generate_text(prompt)
    
async def get_book_suggestions(topic: str) -> str:
    """Uses an LLM to get book suggestions on a specific topic."""
    print(f"Getting book suggestions for topic: {topic}")
    prompt = (
        f"Please recommend one highly-rated and influential book on the topic of '{topic}'. "
        f"Provide the title, author, and a brief one-sentence summary of why it's a must-read. "
        f"Format your response as: 'Title: [Book Title], Author: [Author Name] - [One-sentence summary]'"
    )
    return await _generate_text(prompt)

async def generate_investment_analysis(risk_profile: str, market_data: dict) -> str:
    """Uses an LLM to generate an investment suggestion."""
    print("Generating investment analysis via ASI:One API...")
    prompt = (
        f"You are a conservative financial analyst. My personal investment risk profile is '{risk_profile}'.\n"
        f"Based on the following market data for an asset:\n"
        f"{market_data}\n\n"
        f"Please provide a brief, one-paragraph analysis. "
        f"Should I consider this investment based on my risk profile? "
        f"Explain your reasoning in simple terms."
    )
    return await _generate_text(prompt)

async def generate_weekly_wellness_plan(user_profile: dict) -> str:
    """Uses an LLM to generate a complete, adaptive wellness plan."""
    print("Generating adaptive weekly wellness plan via ASI:One API...")
    prompt = f"""
    Based on the following user profile:
    - Fitness Goal: {user_profile.get('fitness_goal', 'general wellness')}
    - Current State: {user_profile.get('current_state', 'normal')}
    - Food Budget Status: {user_profile.get('food_budget_status', 'healthy')}
    - Food Preferences: {user_profile.get('food_preferences', 'none')}

    Please generate a 3-day wellness plan.
    If the user is 'stressed', the workouts should be light (e.g., yoga, walking).
    If the food budget is 'tight', the diet plan must use affordable, common Nigerian ingredients.

    Format the response EXACTLY as follows, using these section headers:

    ### WORKOUT PLAN
    - Day 1: [Workout Title], [Duration in minutes]
    - Day 2: [Workout Title], [Duration in minutes]
    - Day 3: [Workout Title], [Duration in minutes]

    ### DIET PLAN
    - Day 1: [Meal description]
    - Day 2: [Meal description]
    - Day 3: [Meal description]

    ### SHOPPING LIST
    - [Item 1]
    - [Item 2]
    - [Item 3]
    """
    return await _generate_text(prompt)

async def find_job_opportunities(role: str) -> list[str]:
    """Finds job opportunities by scraping a simple job site."""
    url = f"https://realpython.github.io/fake-jobs/"
    # This part of the function is unchanged and remains for testing
    # ...
    return []
async def generate_holistic_summary(user_data: dict) -> str:
    """Uses an LLM to analyze a user's data and provide a summary."""
    print("Generating holistic summary via ASI:One API...")
    
    # Build a detailed prompt that gives the LLM the role of a life coach
    prompt = f"""
    You are KAI, a holistic AI personal assistant. Your role is to act as an encouraging life coach.
    Analyze the following data summary from my other agents and provide a short, insightful, and motivational paragraph about my progress.
    Conclude with one piece of actionable advice for the upcoming week.

    Here is my data:
    {user_data}
    """
    return await _generate_text(prompt)