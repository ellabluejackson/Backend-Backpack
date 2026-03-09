# todos - list, get one, add, mark done, delete

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/todos", tags=["todos"])


class TodoIn(BaseModel):
    text: str
    folder_id: int | None = None  # put todo in a folder, null = no folder


def _one(conn, todo_id):
    # get one todo or 404
    row = conn.execute("SELECT id, text, done, folder_id FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    return dict(row)


@router.get("")
def get_todos():
    # get all todos (each has folder_id, null = not in a folder)
    conn = get_db()
    rows = conn.execute("SELECT id, text, done, folder_id FROM todos").fetchall()
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
    # add a new todo (optional folder_id to put it in a folder)
    conn = get_db()
    if todo.folder_id is not None:
        r = conn.execute("SELECT id FROM folders WHERE id = ?", (todo.folder_id,)).fetchone()
        if not r:
            conn.close()
            raise HTTPException(status_code=404, detail="Folder not found")
    conn.execute("INSERT INTO todos (text, folder_id) VALUES (?, ?)", (todo.text, todo.folder_id))
    conn.commit()
    row = conn.execute("SELECT id, text, done, folder_id FROM todos WHERE id = last_insert_rowid()").fetchone()
    conn.close()
    return dict(row)


@router.patch("/{todo_id}")
def update_todo(todo_id: int, done: bool | None = None, folder_id: int | None = None):
    # mark done or not (?done=true/false), or move to folder (?folder_id=1)
    conn = get_db()
    try:
        _one(conn, todo_id)
        if done is not None:
            conn.execute("UPDATE todos SET done = ? WHERE id = ?", (1 if done else 0, todo_id))
        if folder_id is not None:
            r = conn.execute("SELECT id FROM folders WHERE id = ?", (folder_id,)).fetchone()
            if not r:
                raise HTTPException(status_code=404, detail="Folder not found")
            conn.execute("UPDATE todos SET folder_id = ? WHERE id = ?", (folder_id, todo_id))
        if done is not None or folder_id is not None:
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
