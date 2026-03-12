# flashacrds list, get one, add, update, delete and always belong to a folder

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


class FlashcardIn(BaseModel):
    front: str
    back: str
    folder_id: int  # every flashcard must be in a folder


@router.get("")
def list_flashcards(db=Depends(get_db)):
    # get all flashcards (each has folder_id)
    rows = db.execute(
        "SELECT id, front, back, folder_id FROM flashcards ORDER BY id"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/{card_id}")
def get_flashcard(card_id: int, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, front, back, folder_id FROM flashcards WHERE id = ?",
        (card_id,),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return dict(row)


@router.post("")
def create_flashcard(card: FlashcardIn, db=Depends(get_db)):
    # add a card (folder_id is required)
    r = db.execute("SELECT id FROM folders WHERE id = ?", (card.folder_id,)).fetchone()
    if not r:
        db.close()
        raise HTTPException(status_code=404, detail="Folder not found")
    db.execute(
        "INSERT INTO flashcards (front, back, folder_id) VALUES (?, ?, ?)",
        (card.front, card.back, card.folder_id),
    )
    db.commit()
    row = db.execute(
        "SELECT id, front, back, folder_id FROM flashcards WHERE id = last_insert_rowid()"
    ).fetchone()
    db.close()
    return dict(row)


@router.put("/{card_id}")
def update_flashcard(card_id: int, card: FlashcardIn, db=Depends(get_db)):
    # update front, back, and folder 
    r = db.execute("SELECT id FROM folders WHERE id = ?", (card.folder_id,)).fetchone()
    if not r:
        db.close()
        raise HTTPException(status_code=404, detail="Folder not found")
    cur = db.execute(
        "UPDATE flashcards SET front = ?, back = ?, folder_id = ? WHERE id = ?",
        (card.front, card.back, card.folder_id, card_id),
    )
    db.commit()
    if cur.rowcount == 0:
        db.close()
        raise HTTPException(status_code=404, detail="Flashcard not found")
    row = db.execute(
        "SELECT id, front, back, folder_id FROM flashcards WHERE id = ?",
        (card_id,),
    ).fetchone()
    db.close()
    return dict(row)


@router.delete("/{card_id}")
def delete_flashcard(card_id: int, db=Depends(get_db)):
    # delete one card
    cur = db.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return {"ok": True}
