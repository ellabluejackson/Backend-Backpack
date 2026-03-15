# todos - list, get one, add, mark done, delete

from fastapi import APIRouter, Depends, HTTPException
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
def get_todos(db=Depends(get_db)):
    # get all todos (each has folder_id, null = not in a folder)
    rows = db.execute("SELECT id, text, done, folder_id FROM todos").fetchall()
    return [dict(r) for r in rows]


@router.get("/{todo_id}")
def get_todo(todo_id: int, db=Depends(get_db)):
    return _one(db, todo_id)


@router.post("")
def create_todo(todo: TodoIn, db=Depends(get_db)):
    # add a new todo (optional folder_id to put it in a folder)
    if todo.folder_id is not None:
        r = db.execute("SELECT id FROM folders WHERE id = ?", (todo.folder_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Folder not found")
    db.execute("INSERT INTO todos (text, folder_id) VALUES (?, ?)", (todo.text, todo.folder_id))
    db.commit()
    row = db.execute("SELECT id, text, done, folder_id FROM todos WHERE id = last_insert_rowid()").fetchone()
    return dict(row)


@router.patch("/{todo_id}")
def update_todo(todo_id: int, done: bool | None = None, folder_id: int | None = None, db=Depends(get_db)):
    # mark done or not (?done=true/false), or move to folder (?folder_id=1)
    _one(db, todo_id)
    if done is not None:
        db.execute("UPDATE todos SET done = ? WHERE id = ?", (1 if done else 0, todo_id))
    if folder_id is not None:
        r = db.execute("SELECT id FROM folders WHERE id = ?", (folder_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Folder not found")
        db.execute("UPDATE todos SET folder_id = ? WHERE id = ?", (folder_id, todo_id))
    if done is not None or folder_id is not None:
        db.commit()
    return _one(db, todo_id)


@router.delete("/{todo_id}")
def delete_todo(todo_id: int, db=Depends(get_db)):
    # delete a todo
    cur = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"ok": True}
