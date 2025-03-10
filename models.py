from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class GroupToUser(Base):
    __tablename__ = 'group_to_user'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'))
    user_id = Column(Integer, ForeignKey('user.id'))


class UserToCategory(Base):
    __tablename__ = 'user_to_category'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    category_id = Column(Integer, ForeignKey('category.id'))


class Friend(Base):
    __tablename__ = 'friend'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    friend_id = Column(Integer, ForeignKey('user.id'))

    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friend_of")


class Admin(Base):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    group = relationship("Group", back_populates="admins")
    user = relationship("User", back_populates="admin_groups")


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    tag = Column(String, unique=True)
    balance = Column(Integer)
    password = Column(String)
    username = Column(String)
    image = Column(String)
    user_data = Column(String)
    created_at = Column(DateTime)

    actions = relationship("Action", back_populates="user")
    groups = relationship("Group", secondary=GroupToUser.__table__, back_populates="users")
    user_to_categories = relationship("UserToCategory", back_populates="user")
    friends = relationship("Friend", primaryjoin="User.id==Friend.user_id", back_populates="user")
    friend_of = relationship("Friend", primaryjoin="User.id==Friend.friend_id", back_populates="friend")
    owned_groups = relationship("Group", back_populates="owner", foreign_keys="[Group.owner_id]")
    admin_groups = relationship("Admin", back_populates="user")


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('user.id'))
    name = Column(String)
    group_data = Column(String)
    image = Column(String)
    created_at = Column(DateTime)

    owner = relationship("User", back_populates="owned_groups", foreign_keys=[owner_id])
    actions = relationship("Action", back_populates="group")
    users = relationship("User", secondary=GroupToUser.__table__, back_populates="groups")
    admins = relationship("Admin", back_populates="group")


class Action(Base):
    __tablename__ = 'action'
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('user.id'))
    type = Column(Integer)
    name = Column(String)
    value = Column(Integer)
    date = Column(Date)
    category_id = Column(Integer, ForeignKey('category.id'))
    description = Column(String)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=True)
    created_at = Column(DateTime)

    user = relationship("User", back_populates="actions")
    category = relationship("Category", back_populates="actions")
    group = relationship("Group", back_populates="actions")


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    actions = relationship("Action", back_populates="category")
    user_to_categories = relationship("UserToCategory", back_populates="category")


UserToCategory.user = relationship("User", back_populates="user_to_categories")
UserToCategory.category = relationship("Category", back_populates="user_to_categories")
