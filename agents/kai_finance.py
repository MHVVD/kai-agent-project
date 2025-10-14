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