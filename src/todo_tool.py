import json
import os
from langchain.tools import tool
from typing import List, Dict

NEXUS_FILES = os.environ.get("nexus_files")
TODO_FILE = f"{NEXUS_FILES}/todo.json"


def load_todo_list() -> List[Dict]:
    """
    The function `load_todo_list` reads and returns a list of dictionaries representing a todo list from
    a file if it exists, otherwise returns an empty list.
    :return: A list of dictionaries representing the todo list items is being returned. If the TODO_FILE
    exists and can be successfully loaded as JSON, the function returns the loaded data. If there is an
    error decoding the JSON data, an empty list is returned. If the TODO_FILE does not exist, an empty
    list is also returned.
    """
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    else:
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
    return []


def save_todo_list(todo_list: List[Dict]):
    """
    The function `save_todo_list` saves a list of dictionaries representing todo items to a file in JSON
    format.

    :param todo_list: A list of dictionaries representing a todo list. Each dictionary should contain
    information about a single task, such as the task name, description, due date, etc
    :type todo_list: List[Dict]
    """
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todo_list, f, indent=2, ensure_ascii=False)


@tool
def add_item(item: str) -> str:
    """
    The function `add_item` adds a new task to a to-do list and returns a confirmation message.

    :param item: The `item` parameter in the `add_item` function is a string that represents a task or
    item to be added to a todo list
    :type item: str
    :return: The function `add_item` is returning a string that says "Added: '{item}'", where `{item}`
    is the item that was added to the todo list.
    """
    task = item
    try:
        item_json = json.loads(item["input"])
        if hasattr(item_json, "item"):
            task = item["item"]
    except:
        task = item
    todo_list = load_todo_list()
    todo_list.append({"task": task, "done": False})
    save_todo_list(todo_list)
    return f"Added: '{task}'"


@tool
def check_item(index: int) -> str:
    """
    This Python function toggles the "done" status of an item in a todo list based on the provided
    index.

    :param index: The `index` parameter is an integer representing the position of an item in a to-do
    list that the user wants to check or uncheck
    :type index: int
    :return: The function `check_item` returns a message indicating whether an item in the todo list has
    been marked as checked or unchecked. If the index provided is valid and within the range of the todo
    list, it will update the status of the item and return a message confirming the change. If the index
    is invalid, it will return a message stating "Invalid index."
    """
    todo_list = load_todo_list()
    if 0 <= index < len(todo_list):
        todo_list[index]["done"] = not todo_list[index]["done"]
        save_todo_list(todo_list)
        status = "checked" if todo_list[index]["done"] else "unchecked"
        return f"Marked item {index + 1} as {status}."
    return "Invalid index."


@tool
def delete_item(index: int) -> str:
    """
    This Python function deletes an item from a todo list based on the provided index.

    :param index: The `index` parameter in the `delete_item` function is an integer that represents the
    position of the item to be deleted from the todo list. It is used to specify which item in the list
    should be removed
    :type index: int
    :return: The function `delete_item` returns a string message indicating whether the deletion was
    successful or not. If the index provided is valid and within the range of the todo list, it will
    delete the item at that index, save the updated todo list, and return a message stating that the
    task has been deleted. If the index is invalid (less than 0 or greater than or equal to the length
    of
    """
    todo_list = load_todo_list()
    if 0 <= index < len(todo_list):
        removed = todo_list.pop(index)
        save_todo_list(todo_list)
        return f"Deleted: '{removed['task']}'"
    return "Invalid index."


@tool
def modify_item(index: int, new_task: str) -> str:
    """
    This Python function modifies a task in a todo list at a specified index and returns a message
    indicating the change made.

    :param index: The `index` parameter in the `modify_item` function is an integer that represents the
    position of the item in the todo list that you want to modify. It is used to locate the specific
    item in the list that you want to update with a new task
    :type index: int
    :param new_task: The `new_task` parameter in the `modify_item` function is a string that represents
    the new task that will replace the existing task at the specified index in the todo list
    :type new_task: str
    :return: The function `modify_item` returns a message indicating whether the modification of the
    task at the specified index was successful or not. If the index is valid and within the range of the
    todo list, it will return a message showing the change made from the old task to the new task. If
    the index is invalid, it will return "Invalid index."
    """
    todo_list = load_todo_list()
    if 0 <= index < len(todo_list):
        old = todo_list[index]["task"]
        todo_list[index]["task"] = new_task
        save_todo_list(todo_list)
        return f"Changed: '{old}' → '{new_task}'"
    return "Invalid index."


@tool
def show_todo_list(_: str = "") -> str:
    """
    The function `show_todo_list` displays the to-do list with task numbers, status indicators, and task
    descriptions.

    :param _: The underscore (_) in the function parameter list is a convention in Python to indicate
    that the parameter is not going to be used within the function. It's a way to communicate to other
    developers that the parameter is intentionally ignored or not relevant to the function's logic. In
    this case, the underscore (_) is
    :type _: str
    :return: The function `show_todo_list` returns a formatted string representation of the to-do list
    tasks, including their status (done or not done) and task description. If the to-do list is empty,
    it returns the message "Your to-do list is empty."
    """
    todo_list = load_todo_list()
    if not todo_list:
        return "Your to-do list is empty."
    result = []
    for i, task in enumerate(todo_list):
        status = "[x]" if task["done"] else "[ ]"
        result.append(f"{i+1}. {status} {task['task']}")
    return "\n".join(result)
