import uuid
from datetime import datetime

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
    user_id = 0
    for item in tokens:
        if item['token'] == token:
            is_auth = True
            user_id = item['id']
            break
    return is_auth, user_id


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user_info = db.query(User).filter(User.id == user_id).first()
    if user_info is None:
        raise JSONResponse({'message': 'no user'}, status_code=NOT_FOUND)
    groups = [group.id for group in user_info.groups]
    categories = [cat.id for cat in user_info.user_to_categories]
    user_data = User(
        id=user_info.id,
        tag=user_info.tag,
        balance=user_info.balance,
        username=user_info.username,
        image=user_info.image,
        user_data=user_info.user_data,
        created_at=user_info.created_at,
        groups=groups,
        user_to_categories=categories
    )
    json_data = jsonable_encoder(user_data)
    return JSONResponse(content=json_data, status_code=OK)


@app.post("/users/{user_id}/add_category")
async def add_category(token: str,
                       category_name: str,
                       db: Session = Depends(get_db)):
    is_auth, user_id = auth(token)
    if is_auth:
        user_info = db.query(User).filter(User.id == user_id).first()
        if user_info is None:
            return JSONResponse({'message': 'no user'}, status_code=NOT_FOUND)
        existing_categories = db.query(UserToCategory).filter(UserToCategory.user_id == user_id).all()
        for user_category in existing_categories:
            cat = db.query(Category).filter(Category.id == user_category.category_id).first()
            if cat and cat.name == category_name:
                return JSONResponse({'message': 'already existing category'}, status_code=BAD_REQUEST)
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
async def add_action(token: str,
                     action_name: str,
                     action_type: int,
                     value: int,
                     date: str,
                     category_id: int,
                     description: str,
                     group_id: int = None,
                     db: Session = Depends(get_db)):
    is_auth, user_id = auth(token)
    if is_auth:
        user_info = db.query(User).filter(User.id == user_id).first()
        if user_info is None:
            return JSONResponse({'message': 'no user'}, status_code=NOT_FOUND)
        new_action = Action(
            name=action_name,
            type=action_type,
            value=value,
            date=date,
            category_id=category_id,
            description=description,
            group_id=group_id,
            created_at=datetime.utcnow()
        )
        user_info.actions.append(new_action)
        if group_id:
            group_info = db.query(Group).filter(Group.id == group_id).first()
            if group_info is not None:
                group_info.actions.append(new_action)
        db.add(new_action)
        db.commit()
        db.refresh(new_action)
        return JSONResponse({'id': new_action.id}, status_code=OK)
    return JSONResponse({'message': 'unauthorized'}, status_code=UNAUTHORIZED)


@app.post("/groups/create")
async def create_group(token: str,
                       group_name: str,
                       group_data: str = None,
                       image: str = None,
                       db: Session = Depends(get_db)):
    is_auth, user_id = auth(token)
    if not is_auth:
        return JSONResponse({'message': 'unauthorized'}, status_code=UNAUTHORIZED)
    user_info = db.query(User).filter(User.id == user_id).first()
    if user_info is None:
        return JSONResponse({'message': 'user not found'}, status_code=NOT_FOUND)
    new_group = Group(
        owner_id=user_id,
        name=group_name,
        group_data=group_data,
        image=image,
        created_at=datetime.utcnow()
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    user_info.groups.append(new_group)
    db.commit()
    return JSONResponse({'group_id': new_group.id}, status_code=OK)


@app.post("/groups/{group_id}/add_user")
async def add_user_to_group(group_id: int,
                            token: str,
                            new_user_id: int,
                            db: Session = Depends(get_db)):
    is_auth, current_user_id = auth(token)
    if not is_auth:
        return JSONResponse({'message': 'unauthorized'}, status_code=UNAUTHORIZED)
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        return JSONResponse({'message': 'group not found'}, status_code=NOT_FOUND)
    if group.owner_id != current_user_id:
        return JSONResponse({'message': 'only group owner can add users'}, status_code=UNAUTHORIZED)
    new_user = db.query(User).filter(User.id == new_user_id).first()
    if new_user is None:
        return JSONResponse({'message': 'user to add not found'}, status_code=NOT_FOUND)
    if new_user in group.users:
        return JSONResponse({'message': 'user already in group'}, status_code=BAD_REQUEST)
    group.users.append(new_user)
    db.commit()
    return JSONResponse({'message': 'user added to group successfully'}, status_code=OK)


@app.post("/register")
async def register(username: str,
                   password: str,
                   tag: str,
                   image: str = None,
                   user_data: str = None,
                   db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.tag == tag).first()
    if existing_user:
        return JSONResponse({'message': 'user with this tag already exists'}, status_code=BAD_REQUEST)
    new_user = User(
        tag=tag,
        balance=0,
        password=password,
        username=username,
        image=image,
        user_data=user_data,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = str(uuid.uuid4())
    tokens.append({'token': token, 'id': new_user.id})
    return JSONResponse({'user_id': new_user.id, 'token': token}, status_code=OK)
