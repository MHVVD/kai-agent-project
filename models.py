from uagents import Model

class LogActivity(Model):
    activity_type: str
    details: str

class LogExpense(Model):
    category: str
    amount: int

class SetLearningGoal(Model):
    goal_description: str

# New message for Kai-Mind to command Kai-Health
class ScheduleMindfulness(Model):
    activity_title: str # e.g., "Meditation" or "Journaling"
    duration_minutes: int