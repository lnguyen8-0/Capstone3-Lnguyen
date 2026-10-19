from dotenv import load_dotenv
load_dotenv()

from orchestrator import orchestrator
from tokenomics_logger import run_traced_query, print_cost_summary

questions = [
    "How many active projects do we have?",
    "What is the total budget across all projects?",
    "Which consultant has the most billable hours?",
    "List all clients in the technology industry.",
    "What invoices are currently unpaid?",
    "What is our onboarding process?",
    "What is the company escalation policy?",
    "How many active projects do we have, and what is our project delivery methodology?",
    "What is the total contract value for all clients, and what are our client success guidelines?",
    "How many consultants do we have and what is our consultant performance review process?",
]

for q in questions:
    run_traced_query(orchestrator, q)

print_cost_summary()
