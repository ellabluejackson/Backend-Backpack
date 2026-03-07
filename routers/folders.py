# folders - can put a folder inside another (parent_id)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/folders", tags=["folders"])


class FolderIn(BaseModel):
    name: str
    parent_id: int | None = None  # leave null for top level


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None


def _descendant_ids(conn, folder_id: int) -> set[int]:
    # get all ids of folders inside this one (so we dont create a loop when moving)
    out = set()
    stack = [folder_id]
    while stack:
        pid = stack.pop()
        rows = conn.execute("SELECT id FROM folders WHERE parent_id = ?", (pid,)).fetchall()
        for r in rows:
            out.add(r["id"])
            stack.append(r["id"])
    return out


@router.get("")
def list_folders(db=Depends(get_db)):
    # get all folders, each has parent_id (null = top level)
    rows = db.execute("SELECT id, name, parent_id FROM folders ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.post("")
def create_folder(folder: FolderIn, db=Depends(get_db)):
    # create folder, optional parent_id to put it inside another
    if folder.parent_id is not None:
        r = db.execute("SELECT id FROM folders WHERE id = ?", (folder.parent_id,)).fetchone()
        if not r:
            db.close()
            raise HTTPException(status_code=404, detail="Parent folder not found")
    db.execute(
        "INSERT INTO folders (name, parent_id) VALUES (?, ?)",
        (folder.name, folder.parent_id),
    )
    db.commit()
    row = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE id = last_insert_rowid()"
    ).fetchone()
    db.close()
    return dict(row)


@router.get("/{folder_id}")
def get_folder(folder_id: int, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Folder not found")
    return dict(row)


@router.put("/{folder_id}")
def update_folder(folder_id: int, body: FolderUpdate, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Folder not found")
    name = body.name if body.name is not None else row["name"]
    parent_id = body.parent_id if body.parent_id is not None else row["parent_id"]
    if parent_id is not None:
        if parent_id == folder_id:
            db.close()
            raise HTTPException(status_code=400, detail="Folder cannot be its own parent")
        if parent_id in _descendant_ids(db, folder_id):
            db.close()
            raise HTTPException(status_code=400, detail="Would create a loop")
        r = db.execute("SELECT id FROM folders WHERE id = ?", (parent_id,)).fetchone()
        if not r:
            db.close()
            raise HTTPException(status_code=404, detail="Parent folder not found")
    db.execute("UPDATE folders SET name = ?, parent_id = ? WHERE id = ?", (name, parent_id, folder_id))
    db.commit()
    row = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    db.close()
    return dict(row)


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, db=Depends(get_db)):
    # only delete if it has no subfolders
    has_child = db.execute(
        "SELECT id FROM folders WHERE parent_id = ? LIMIT 1", (folder_id,)
    ).fetchone()
    if has_child:
        db.close()
        raise HTTPException(
            status_code=409,
            detail="Folder has subfolders – delete or move them first",
        )
    cur = db.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"ok": True}
