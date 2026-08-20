from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_history: dict
    risk_score: float      # Required for metrics
    reasoning: List[str]   # Required for the trace
    final_verdict: str     # Required for the Green/Red boxes