import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """
    Registered user profile is stored in db
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))


class Restaurant(Base):
    """
    Restaurant names along with creator ids stored in db
    """
    __tablename__ = 'restaurant'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    picture = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="restaurant")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'user_id': self.user_id
        }


class MenuItem(Base):
    """
    Restaurant menu item information along with creator id stored in db
    """
    __tablename__ = 'menu_item'

    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    description = Column(String(250))
    price = Column(String(8))
    course = Column(String(250))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(Restaurant, backref=backref('menu_item', cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="menu_item")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return{
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'price': self.price,
            'course': self.course,
            'restaurant_id': self.restaurant_id,
            'user_id': self.user_id
        }


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.create_all(engine)
