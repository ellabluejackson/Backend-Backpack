# folders - can put a folder inside another (parent_id)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/folders", tags=["folders"])

NAME_MAX = 200


def _validate_folder_name(name: str | None) -> str:
    if name is None:
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
    if len(name) > NAME_MAX:
        raise HTTPException(status_code=400, detail=f"Folder name must be at most {NAME_MAX} characters")
    return name


class FolderIn(BaseModel):
    name: str
    parent_id: int | None = None  # leave null for top level
    is_flashcard_set: bool = False  # true when created via "Add Flashcards"


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None


def _descendant_ids(conn, folder_id: int) -> set[int]:
    # get all ids of folders inside this one 
    out = set()
    stack = [folder_id]
    while stack:
        pid = stack.pop()
        rows = conn.execute("SELECT id FROM folders WHERE parent_id = ?", (pid,)).fetchall()
        for r in rows:
            out.add(r["id"])
            stack.append(r["id"])
    return out


def _delete_folder_and_contents(conn, folder_id: int):
    # delete notes, todos, flashcards in this folder, then subfolders, then the folder
    conn.execute("DELETE FROM notes WHERE folder_id = ?", (folder_id,))
    conn.execute("DELETE FROM todos WHERE folder_id = ?", (folder_id,))
    conn.execute("DELETE FROM flashcards WHERE folder_id = ?", (folder_id,))
    rows = conn.execute("SELECT id FROM folders WHERE parent_id = ?", (folder_id,)).fetchall()
    for r in rows:
        _delete_folder_and_contents(conn, r["id"])
    conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))


@router.get("")
def list_folders(db=Depends(get_db)):
    # get all folders, each has parent_id (null = top level), is_flashcard_set (0/1)
    rows = db.execute(
        "SELECT id, name, parent_id, COALESCE(is_flashcard_set, 0) AS is_flashcard_set FROM folders ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("")
def create_folder(folder: FolderIn, db=Depends(get_db)):
    name = _validate_folder_name(folder.name)
    if folder.parent_id is not None:
        r = db.execute("SELECT id FROM folders WHERE id = ?", (folder.parent_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Parent folder not found")
    is_fc = 1 if folder.is_flashcard_set else 0
    db.execute(
        "INSERT INTO folders (name, parent_id, is_flashcard_set) VALUES (?, ?, ?)",
        (name, folder.parent_id, is_fc),
    )
    db.commit()
    row = db.execute(
        "SELECT id, name, parent_id, COALESCE(is_flashcard_set, 0) AS is_flashcard_set FROM folders WHERE id = last_insert_rowid()"
    ).fetchone()
    return dict(row)


@router.get("/{folder_id}")
def get_folder(folder_id: int, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Folder not found")
    return dict(row)


@router.put("/{folder_id}")
def update_folder(folder_id: int, body: FolderUpdate, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Folder not found")
    name = _validate_folder_name(body.name) if body.name is not None else row["name"]
    parent_id = body.parent_id if body.parent_id is not None else row["parent_id"] if body.parent_id is not None else row["parent_id"]
    if parent_id is not None:
        if parent_id == folder_id:
            raise HTTPException(status_code=400, detail="Folder cannot be its own parent")
        if parent_id in _descendant_ids(db, folder_id):
            raise HTTPException(status_code=400, detail="Would create a loop")
        r = db.execute("SELECT id FROM folders WHERE id = ?", (parent_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Parent folder not found")
    db.execute("UPDATE folders SET name = ?, parent_id = ? WHERE id = ?", (name, parent_id, folder_id))
    db.commit()
    row = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    return dict(row)


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, db=Depends(get_db)):
    # delete folder and everything in it (notes, todos, subfolders and their contents)
    row = db.execute("SELECT id FROM folders WHERE id = ?", (folder_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Folder not found")
    _delete_folder_and_contents(db, folder_id)
    db.commit()
    return {"ok": True}
