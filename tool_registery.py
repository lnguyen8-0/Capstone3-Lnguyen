# tool_registry.py
from agents.sql_agent import run_sql_agent
from agents.retrieval_agent import run_retrieval_agent

TOOL_REGISTRY = {
    "sql_agent": {
        "function": run_sql_agent,
        "schema": {
            "name": "sql_agent",
            "description": (
                "Use for questions that require querying the relational database: "
                "counts, totals, filters, aggregations, and lookups against the "
                "clients, projects, consultants, and invoices tables (e.g. 'How many "
                "active projects?', 'What is the total budget for client X?'). "
                "Do NOT use for policy questions, process descriptions, guidelines, "
                "or any question whose answer lives in a document rather than a "
                "database row."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"]
            }
        }
    },
    "retrieval_agent": {
        "function": run_retrieval_agent,
        "schema": {
            "name": "retrieval_agent",
            "description": (
                "Use for questions answered by searching indexed documents: policies, "
                "procedures, onboarding guides, case studies, and narrative content "
                "(e.g. 'What is our escalation policy?', 'How do we onboard new "
                "clients?'). "
                "Do NOT use for questions about specific records, numbers, counts, "
                "budgets, statuses, or anything retrievable from the relational "
                "database tables (clients, projects, consultants, invoices)."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"]
            }
        }
    }
}

def get_all_schemas() -> list:
    return [tool["schema"] for tool in TOOL_REGISTRY.values()]

def call_tool(tool_name: str, question: str) -> dict:
    if tool_name not in TOOL_REGISTRY:
        return {"success": False, "answer": f"Unknown tool: {tool_name}", "sources": [], "metadata": {}}
    return TOOL_REGISTRY[tool_name]["function"](question)

