from hyperon import MeTTa

metta = MeTTa()
atomspace = metta.space()

# --- Detailed User Profile ---
# Budgets
atomspace.add_atom(metta.parse_single('(budget food 50000)'))
atomspace.add_atom(metta.parse_single('(budget leisure 10000)'))

# Budget Thresholds
atomspace.add_atom(metta.parse_single('(threshold food (tight 80))'))

# Initial Spending
atomspace.add_atom(metta.parse_single('(spent food 0)'))
atomspace.add_atom(metta.parse_single('(spent leisure 0)'))

# User Profile & State
atomspace.add_atom(metta.parse_single('(risk-profile user conservative)'))
atomspace.add_atom(metta.parse_single('(interest user "Artificial Intelligence")'))
atomspace.add_atom(metta.parse_single('(fitness-goal user "weight-loss")'))
atomspace.add_atom(metta.parse_single('(food-preference user "no-pork")'))
atomspace.add_atom(metta.parse_single('(mood user negative)')) # New state for adaptive planning
atomspace.add_atom(metta.parse_single('(savings-goal user (target 100000) (current 15000) (deadline "2025-12-31"))'))

print("MeTTa Atomspace initialized with detailed user profile.")