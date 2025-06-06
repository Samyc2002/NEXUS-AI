import json
import os
from datetime import datetime

default_log_file_path = "C:\\NEXUS_logs.json"


def get_log_file_path():
    """
    The function `get_log_file_path` retrieves the log file path from the environment variable or uses a
    default path.
    """
    log_file_path = default_log_file_path
    if os.environ.get("log_file_path"):
        log_file_path = os.environ.get("log_file_path")
    return log_file_path


def _add_log(role: str, message: str):
    """
    The function `_add_log` appends a new log entry with role and message to a JSON log file.
    
    :param role: The `role` parameter in the `_add_log` function is a string that represents the role
    associated with the log message being added. It could be a user role, system role, or any other
    identifier that helps categorize the log message
    :type role: str
    :param message: The `message` parameter is a string that represents the log message to be added to
    the log file. It contains information or details that you want to log for a specific role
    :type message: str
    """
    logs = {"messages": []}

    if os.path.exists(get_log_file_path()):
        with open(get_log_file_path(), "r", encoding="utf-8") as log_file:
            try:
                logs = json.load(log_file)
            except json.JSONDecodeError:
                logs = {"messages": []}

    logs["messages"].append({
        "role": role,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })

    with open(get_log_file_path(), "w", encoding="utf-8") as log_file:
        json.dump(logs, log_file, indent=2, ensure_ascii=False)


def add_user_log(user_input: str):
    """
    The function `add_user_log` takes a user input as a string and logs it with the tag "User".

    :param user_input: A string representing the input provided by the user
    :type user_input: str
    """
    _add_log("user", user_input)


def add_nexus_log(nexus_response: str):
    """
    The function `add_nexus_log` logs a Nexus response with a specified tag.

    :param nexus_response: A string containing the response received from a Nexus API call
    :type nexus_response: str
    """
    _add_log("assistant", nexus_response)


def get_previous_logs():
    if os.path.exists(get_log_file_path()):
        with open(get_log_file_path(), "r", encoding="utf-8") as log_file:
            try:
                logs = json.load(log_file)
                return [{"role": msg["role"], "content": msg["message"]} for msg in logs.get("messages", [])]
            except json.JSONDecodeError:
                return []
    return []
