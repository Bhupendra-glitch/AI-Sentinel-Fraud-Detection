import os
import re
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage
# Ensure state.py defines AgentState with 'messages', 'user_history', and 'risk_score'
from state import AgentState 

# --- 1. Import your custom tool ---
try:
    from tools import check_transaction_history
except ImportError:
    def check_transaction_history(user_id):
        # Fallback to prevent crash if tools.py is missing
        return {"avg_spend": 100, "typical_location": "New York", "status": "Active"}

# --- 2. Setup LLM ---
# Using llama3.2 as specified in your setup
llm = ChatOllama(model="llama3.2", temperature=0)

# --- 3. Define the Nodes ---

def fetch_data_node(state: AgentState):
    """Node 1: Fetches background data."""
    # Logic to find a User ID if present (could be extracted from state['messages'])
    user_id = "USER_9921" 
    history = check_transaction_history(user_id)
    
    # Update the state with fetched history
    return {"user_history": history}

def investigator(state: AgentState):
    """Node 2: The AI Analyst."""
    # Safely get the last message content
    if not state['messages']:
        last_message = "No transaction details provided."
    else:
        last_message = state['messages'][-1].content

    history = state.get("user_history", {})
    
    prompt = (
        "You are a Fraud Detection Expert.\n"
        f"CUSTOMER HISTORY: Typical spend ${history.get('avg_spend', 'Unknown')}, "
        f"Location: {history.get('typical_location', 'Unknown')}.\n"
        f"NEW TRANSACTION: {last_message}\n\n"
        "Compare the new transaction to the history. "
        "Output ONLY a risk score between 0.0 and 1.0 (e.g., 0.85)."
    )
    
    response = llm.invoke(prompt)
    content = response.content.strip()

    # Extract score using regex
    try:
        match = re.search(r"[-+]?\d*\.\d+|\d+", content)
        score = float(match.group()) if match else 0.5
    except:
        score = 0.5
        
    # Return BOTH the AI's explanation and the numeric score for the router
    return {
        "messages": [AIMessage(content=f"Analysis complete. Risk Score: {score}")],
        "risk_score": score
    }

def approve_node(state: AgentState):
    return {"messages": [AIMessage(content="✅ APPROVED: Transaction matches user profile.")]}

def block_node(state: AgentState):
    return {"messages": [AIMessage(content="❌ BLOCKED: Significant deviation from user history.")]}

def review_node(state: AgentState):
    return {"messages": [AIMessage(content="⚠️ REVIEW: Unusual patterns, requires human verification.")]}

# --- 4. Routing Logic ---
def router(state: AgentState):
    # Ensure we are pulling the score correctly from the updated state
    score = state.get("risk_score", 0.5) 
    
    if score <= 0.35:
        return "approve"
    elif score > 0.70:
        return "block"
    else:
        return "review"

# --- 5. Construct the Graph ---
builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("fetcher", fetch_data_node)
builder.add_node("investigator", investigator)
builder.add_node("approve", approve_node)
builder.add_node("block", block_node)
builder.add_node("review", review_node)

# Define the Flow
builder.set_entry_point("fetcher")
builder.add_edge("fetcher", "investigator")

# Conditional routing
builder.add_conditional_edges(
    "investigator",
    router,
    {
        "approve": "approve",
        "block": "block",
        "review": "review"
    }
)

# Close the graph
builder.add_edge("approve", END)
builder.add_edge("block", END)
builder.add_edge("review", END)

graph = builder.compile()