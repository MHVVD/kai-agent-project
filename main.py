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