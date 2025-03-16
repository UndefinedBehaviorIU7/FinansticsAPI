from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from fastapi.responses import JSONResponse

from codes import *
from models import *

tokens = []
Base.metadata.create_all(bind=engine)
app = FastAPI()


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


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user_info = db.query(User).filter(User.id == user_id).first()

    if user_info is None:
        raise JSONResponse({'message': 'no user'}, status_code=NOT_FOUND)

    groups = [group.id for group in user.groups]
    categories = [cat.id for cat in user.user_to_categories]

    return User(
        id=user.id,
        tag=user.tag,
        balance=user.balance,
        username=user.username,
        image=user.image,
        user_data=user.user_data,
        created_at=user.created_at,
        groups=groups,
        user_to_categories = categories
    )


@app.post("/users/{user_id}/add_category")
async def add_category(token,
                       category_name: str,
                       db: Session = Depends(get_db)):
    is_auth, user_id = auth(token)
    if is_auth:
        user_info = db.query(User).filter(User.id == user_id).first()
        if user_info is None:
            raise JSONResponse({'message': 'no user'}, status_code=NOT_FOUND)

        existing_categories = db.query(UserToCategory).filter(UserToCategory.user_id == user_id).all()
        for user_category in existing_categories:
            cat = db.query(Category).filter(Category.id == user_category.category_id).first()
            if cat and cat.name == category_name:
                raise JSONResponse({'message': 'already existing category'}, status_code=BAD_REQUEST)

        new_category = Category(name=category_name)
        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        new_user_category = UserToCategory(user_id=user_id, category_id=new_category.id)
        db.add(new_user_category)
        db.commit()
        return JSONResponse({'id': new_category.id}, status_code=OK)
    return JSONResponse({'message': 'unauthorized'}, status_code=UNAUTHORIZED)


@app.post("/users/{user_id}/add_action")
async def add_action(token,
                     action_name: str,
                     action_type: int,
                     value: int,
                     date: Date,
                     category_id: int,
                     description: str,
                     group_id,
                     db: Session = Depends(get_db)):
    is_auth, user_id = auth(token)
    if is_auth:
        user_info = db.query(User).filter(User.id == user_id).first()
        if user_info is None:
            raise JSONResponse({'message': 'no user'}, status_code=NOT_FOUND)

        new_action = Action(name=action_name,
                            type=action_type,
                            value=value,
                            date=date,
                            category_id=category_id,
                            description=description,
                            group_id=group_id)

        user_info.actions.append(new_action)
        if group_id:
            group_info = db.query(Group).filter(Group.id == group_id).first()
            if not group_info is None:
                group_info.actions.append(new_action)
        db.add(new_action)
        db.commit()
        db.refresh(new_action)

        return JSONResponse({'id': new_action.id}, status_code=OK)
    return JSONResponse({'message': 'unauthorized'}, status_code=UNAUTHORIZED)
