# main.py
from fastapi import FastAPI, HTTPException, Header, Query, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# ------------- Config -------------
API_KEY = "Jan"
DATABASE_URL = "sqlite:///./app.db"  # local sqlite file

# ------------- DB setup -------------
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class TodoDB(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    task = Column(String, nullable=False)
    status = Column(String, default="pending")

Base.metadata.create_all(bind=engine)

# ------------- FastAPI / Models -------------
app = FastAPI(title="Janani's To-Do API (SQLite + Docker)")

class TodoCreate(BaseModel):
    task: str
    status: Optional[str] = "pending"

class TodoOut(BaseModel):
    id: int
    task: str
    status: str

# ------------- Utils -------------
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_token(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ------------- Routes -------------
@app.get("/")
def home():
    return {"message": "Welcome to Janani's To-Do API (SQLite)!"}

@app.get("/todos", response_model=List[TodoOut])
def list_todos(status: Optional[str] = Query(None), x_api_key: str = Header(...), db: Session = Depends(get_db)):
    verify_token(x_api_key)
    if status:
        items = db.query(TodoDB).filter(TodoDB.status == status).all()
    else:
        items = db.query(TodoDB).all()
    return items

@app.post("/todos", response_model=TodoOut)
def create_todo(item: TodoCreate, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    verify_token(x_api_key)
    todo = TodoDB(task=item.task, status=item.status)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@app.put("/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, item: TodoCreate, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    verify_token(x_api_key)
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Task not found")
    todo.task = item.task
    todo.status = item.status
    db.commit()
    db.refresh(todo)
    return todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    verify_token(x_api_key)
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(todo)
    db.commit()
    return {"message": "Deleted", "id": todo_id}
