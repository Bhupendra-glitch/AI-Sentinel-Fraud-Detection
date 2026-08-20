import json
import os
from datetime import datetime

def save_to_ledger(user_id, transaction_data, agent_output):
    file_path = "transaction_ledger.json"
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "verdict": agent_output.get("verdict", "N/A"),
        "risk_score": agent_output.get("risk_score", 0.0),
        "reasoning": agent_output.get("reasoning", "N/A")
    }
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try: history = json.load(f)
            except: history = []
    else:
        history = []
    history.append(new_entry)
    with open(file_path, "w") as f:
        json.dump(history, f, indent=4)