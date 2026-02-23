#fastapi  connects the routers and runs init_db on startup

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import notes, todos, folders

app = FastAPI(title="My Digital Backpack API")

# need this so the frontend can call the api from another port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router)
app.include_router(todos.router)
app.include_router(folders.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "My Digital Backpack API", "docs": "/docs"}
