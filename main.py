from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
import json
import os

app = FastAPI()
DATA_FILE = "todos.json"

# -----------------------------
# API Key (simple token-based security)
# -----------------------------
API_KEY = "Jan"

def verify_token(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -----------------------------
# Todo Model
# -----------------------------
class TodoItem(BaseModel):
    task: str
    status: str = "pending"  # default status

# -----------------------------
# Load todos from file if exists
# -----------------------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        todos = json.load(f)
else:
    todos = []

# -----------------------------
# Save todos to file
# -----------------------------
def save_todos():
    with open(DATA_FILE, "w") as f:
        json.dump(todos, f)

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Janani's Enhanced To-Do API!"}

@app.get("/todos")
def get_todos(status: str = Query(None, description="Filter by task status"), x_api_key: str = Header()):
    verify_token(x_api_key)
    if status:
        filtered = [task for task in todos if task["status"] == status]
        return {"todos": filtered}
    return {"todos": todos}

@app.post("/todos")
def add_todo(item: TodoItem, x_api_key: str = Header(...)):
    verify_token(x_api_key)
    task_id = todos[-1]["id"] + 1 if todos else 0
    task = {"id": task_id, "task": item.task, "status": item.status}
    todos.append(task)
    save_todos()
    return {"message": "Task added successfully", "todos": todos}

@app.put("/todos/{task_id}")
def update_todo(task_id: int, item: TodoItem, x_api_key: str = Header(...)):
    verify_token(x_api_key)
    for task in todos:
        if task["id"] == task_id:
            task["task"] = item.task
            task["status"] = item.status
            save_todos()
            return {"message": "Task updated successfully", "todos": todos}
    return {"error": "Invalid task ID"}

@app.delete("/todos/{task_id}")
def delete_todo(task_id: int, x_api_key: str = Header(...)):
    verify_token(x_api_key)
    for i, task in enumerate(todos):
        if task["id"] == task_id:
            deleted = todos.pop(i)
            save_todos()
            return {"message": f"Deleted: {deleted}", "todos": todos}
    return {"error": "Invalid task ID"}
