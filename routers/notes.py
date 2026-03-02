# notes API

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteIn(BaseModel):
    title: str
    content: str = ""


@router.get("")
def list_notes(db=Depends(get_db)):
    rows = db.execute("SELECT id, title, content FROM notes ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/{note_id}")
def get_note(note_id: int, db=Depends(get_db)):
    row = db.execute("SELECT id, title, content FROM notes WHERE id = ?", (note_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    return dict(row)


@router.post("")
def create_note(note: NoteIn, db=Depends(get_db)):
    db.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (note.title, note.content))
    db.commit()
    row = db.execute(
        "SELECT id, title, content FROM notes WHERE id = last_insert_rowid()"
    ).fetchone()
    db.close()
    return dict(row)


@router.put("/{note_id}")
def update_note(note_id: int, note: NoteIn, db=Depends(get_db)):
    cur = db.execute(
        "UPDATE notes SET title = ?, content = ? WHERE id = ?",
        (note.title, note.content, note_id),
    )
    db.commit()
    if cur.rowcount == 0:
        db.close()
        raise HTTPException(status_code=404, detail="Note not found")
    row = db.execute("SELECT id, title, content FROM notes WHERE id = ?", (note_id,)).fetchone()
    db.close()
    return dict(row)


@router.delete("/{note_id}")
def delete_note(note_id: int, db=Depends(get_db)):
    cur = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"ok": True}
