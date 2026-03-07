# todos - list, get one, add, mark done, delete

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/todos", tags=["todos"])


class TodoIn(BaseModel):
    text: str


def _one(conn, todo_id):
    row = conn.execute("SELECT id, text, done FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    return dict(row)


@router.get("")
def get_todos():
    # get all todos
    conn = get_db()
    rows = conn.execute("SELECT id, text, done FROM todos").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{todo_id}")
def get_todo(todo_id: int):
    conn = get_db()
    try:
        return _one(conn, todo_id)
    finally:
        conn.close()


@router.post("")
def create_todo(todo: TodoIn):
    # add a new todo
    conn = get_db()
    conn.execute("INSERT INTO todos (text) VALUES (?)", (todo.text,))
    conn.commit()
    row = conn.execute("SELECT id, text, done FROM todos WHERE id = last_insert_rowid()").fetchone()
    conn.close()
    return dict(row)


@router.patch("/{todo_id}")
def update_todo(todo_id: int, done: bool | None = None):
    # mark done or not (pass ?done=true or ?done=false)
    conn = get_db()
    try:
        _one(conn, todo_id)
        if done is not None:
            conn.execute("UPDATE todos SET done = ? WHERE id = ?", (1 if done else 0, todo_id))
            conn.commit()
        return _one(conn, todo_id)
    finally:
        conn.close()


@router.delete("/{todo_id}")
def delete_todo(todo_id: int):
    # delete a todo
    conn = get_db()
    cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"ok": True}
