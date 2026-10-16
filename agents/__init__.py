from typing import TypedDict


class TokenUsage(TypedDict):
    input: int
    output: int


class AgentResult(TypedDict):
    success: bool
    answer: str
    sources: list[str]
    metadata: dict  # always contains "token_usage: TokenUsage"
