# tool_registry.py
from agents.sql_agent import run_sql_agent
from agents.retrieval_agent import run_retrieval_agent

TOOL_REGISTRY = {
    "sql_agent": {
        "function": run_sql_agent,
        "schema": {
            "name": "sql_agent",
            "description": (
                "Query the relational database for structured data about clients, "
                "projects, consultants, and invoices. Use for counts, budgets, "
                "statuses, and billing questions."
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
                "Search indexed documents for policy, procedure, and case study "
                "information. Use for questions about processes, guidelines, or "
                "narrative content rather than structured data."
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

from tool_registry import call_tool, get_all_schemas

print("Registered tools:", [s["name"] for s in get_all_schemas()])

# Test each tool through the registry
result1 = call_tool("sql_agent", "How many active projects do we have?")
print(result1)

result2 = call_tool("retrieval_agent", "What is our onboarding process?")
print(result2)

# Test unknown tool handling
result3 = call_tool("nonexistent_tool", "test")
print(result3)