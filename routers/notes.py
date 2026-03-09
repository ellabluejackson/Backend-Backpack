# notes - create read update delete

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteIn(BaseModel):
    title: str
    content: str = ""
    folder_id: int | None = None  # put note in a folder, null = no folder


@router.get("")
def list_notes(db=Depends(get_db)):
    # get all notes (each has folder_id, null = not in a folder)
    rows = db.execute("SELECT id, title, content, folder_id FROM notes ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/{note_id}")
def get_note(note_id: int, db=Depends(get_db)):
    row = db.execute("SELECT id, title, content, folder_id FROM notes WHERE id = ?", (note_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    return dict(row)


@router.post("")
def create_note(note: NoteIn, db=Depends(get_db)):
    # create a new note (optional folder_id to put it in a folder)
    if note.folder_id is not None:
        r = db.execute("SELECT id FROM folders WHERE id = ?", (note.folder_id,)).fetchone()
        if not r:
            db.close()
            raise HTTPException(status_code=404, detail="Folder not found")
    db.execute(
        "INSERT INTO notes (title, content, folder_id) VALUES (?, ?, ?)",
        (note.title, note.content, note.folder_id),
    )
    db.commit()
    row = db.execute(
        "SELECT id, title, content, folder_id FROM notes WHERE id = last_insert_rowid()"
    ).fetchone()
    db.close()
    return dict(row)


@router.put("/{note_id}")
def update_note(note_id: int, note: NoteIn, db=Depends(get_db)):
    # update title, content, and/or folder (send full note)
    if note.folder_id is not None:
        r = db.execute("SELECT id FROM folders WHERE id = ?", (note.folder_id,)).fetchone()
        if not r:
            db.close()
            raise HTTPException(status_code=404, detail="Folder not found")
    cur = db.execute(
        "UPDATE notes SET title = ?, content = ?, folder_id = ? WHERE id = ?",
        (note.title, note.content, note.folder_id, note_id),
    )
    db.commit()
    if cur.rowcount == 0:
        db.close()
        raise HTTPException(status_code=404, detail="Note not found")
    row = db.execute("SELECT id, title, content, folder_id FROM notes WHERE id = ?", (note_id,)).fetchone()
    db.close()
    return dict(row)


@router.delete("/{note_id}")
def delete_note(note_id: int, db=Depends(get_db)):
    # delete one note
    cur = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"ok": True}
