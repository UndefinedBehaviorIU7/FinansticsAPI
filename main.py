from fastapi import FastAPI
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from fastapi.responses import JSONResponse
from models import *

tokens = []


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def auth(token):
    is_auth = False
    id = 0
    for item in tokens:
        if item['token'] == token:
            is_auth = True
            id = item['id']
            break

    return is_auth, id



