# Backend-Backpack

backend for my digital backpack project FastAPI + SQLite

main.py has the app and CORS, database.py does get_db and init_db. routers folder has folders.

to run it:

cd Backend-Backpack
pip install -r files/requirements.txt  (or pip3)
uvicorn files.main:app --reload

then open http://127.0.0.1:8000/docs for the api docs


