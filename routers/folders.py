from fastapi import APIRouter, Depends, HTTPException
from database import get_db

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("")
def list_folders(db=Depends(get_db)):
    rows = db.execute("SELECT id, name FROM folders ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.post("")
def create_folder(name: str, db=Depends(get_db)):
    cur = db.execute("INSERT INTO folders (name) VALUES (?)", (name,))
    db.commit()
    row = db.execute("SELECT id, name FROM folders WHERE id = ?", (cur.lastrowid,)).fetchone()
    db.close()
    return dict(row)


@router.get("/{folder_id}")
def get_folder(folder_id: int, db=Depends(get_db)):
    row = db.execute("SELECT id, name FROM folders WHERE id = ?", (folder_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Folder not found")
    return dict(row)


@router.put("/{folder_id}")
def update_folder(folder_id: int, name: str, db=Depends(get_db)):
    cur = db.execute("UPDATE folders SET name = ? WHERE id = ?", (name, folder_id))
    db.commit()
    if cur.rowcount == 0:
        db.close()
        raise HTTPException(status_code=404, detail="Folder not found")
    row = db.execute("SELECT id, name FROM folders WHERE id = ?", (folder_id,)).fetchone()
    db.close()
    return dict(row)


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, db=Depends(get_db)):
    cur = db.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"ok": True}
