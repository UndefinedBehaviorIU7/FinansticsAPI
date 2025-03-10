from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker
import random
from models import (
    Base,
    User,
    Group,
    GroupToUser,
    Friend,
    Admin,
    Category,
    UserToCategory,
)

engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

faker = Faker()

users = []
for _ in range(20):
    user = User(
        tag=faker.unique.user_name(),
        balance=random.randint(0, 1000),
        password=faker.password(),
        username=faker.name(),
        image=faker.image_url(),
        user_data=faker.text(max_nb_chars=200),
        created_at=faker.date_time_between(start_date='-2y', end_date='now')
    )
    session.add(user)
    users.append(user)
session.commit()

groups = []
for _ in range(5):
    owner = random.choice(users)
    group = Group(
        owner_id=owner.id,
        name=faker.word(),
        group_data=faker.text(max_nb_chars=200),
        image=faker.image_url(),
        created_at=faker.date_time_between(start_date='-2y', end_date='now')
    )
    session.add(group)
    groups.append(group)
session.commit()

categories = []
for _ in range(5):
    category = Category(name=faker.word())
    session.add(category)
    categories.append(category)
session.commit()

group_to_users = []
for group in groups:
    num_users = random.randint(3, 10)
    group_users = random.sample(users, num_users)
    for user in group_users:
        gtu = GroupToUser(
            group_id=group.id,
            user_id=user.id
        )
        session.add(gtu)
        group_to_users.append(gtu)
session.commit()

admins = []
for group in groups:
    group_user_ids = [gtu.user_id for gtu in group_to_users if gtu.group_id == group.id]
    if group_user_ids:
        admin_user_id = random.choice(group_user_ids)
        admin = Admin(
            group_id=group.id,
            user_id=admin_user_id
        )
        session.add(admin)
        admins.append(admin)
session.commit()

friends_list = []
for user in users:
    potential_friends = [u for u in users if u.id != user.id]
    num_friends = random.randint(2, min(5, len(potential_friends)))
    selected_friends = random.sample(potential_friends, num_friends)
    for friend in selected_friends:
        if not any(f.user_id == user.id and f.friend_id == friend.id for f in friends_list):
            fr = Friend(
                user_id=user.id,
                friend_id=friend.id
            )
            session.add(fr)
            friends_list.append(fr)
session.commit()

user_to_categories_list = []
for user in users:
    num_categories = random.randint(1, 3)
    selected_categories = random.sample(categories, num_categories)
    for category in selected_categories:
        utc = UserToCategory(
            user_id=user.id,
            category_id=category.id
        )
        session.add(utc)
        user_to_categories_list.append(utc)
session.commit()

print("Генерация случайных данных завершена.")
