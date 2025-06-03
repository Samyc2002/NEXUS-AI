import json
import os

log_file_path = "C:\\NEXUS_logs.json"


def _add_log(role: str, message: str):
    logs = {"messages": []}

    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            try:
                logs = json.load(log_file)
            except json.JSONDecodeError:
                logs = {"messages": []}

    logs["messages"].append({
        "role": role,
        "message": message
    })

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        json.dump(logs, log_file, indent=2, ensure_ascii=False)


def add_user_log(user_input: str):
    _add_log("User", user_input)


def add_nexus_log(nexus_response: str):
    _add_log("NEXUS", nexus_response)
