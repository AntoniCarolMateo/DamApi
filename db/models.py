#!/usr/bin/python
# -*- coding: utf-8 -*-

import binascii
import datetime
import enum
import logging
import os
from _operator import and_
from builtins import getattr
from urllib.parse import urljoin

import falcon
from passlib.hash import pbkdf2_sha256
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, Unicode, UnicodeText, Boolean, Table, Float

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy_i18n import make_translatable

import messages
from db.json_model import JSONModel
import settings

mylogger = logging.getLogger(__name__)

SQLAlchemyBase = declarative_base()
make_translatable(options={"locales": settings.get_accepted_languages()})


def _generate_media_url(class_instance, class_attibute_name, default_image=False):
    class_base_url = urljoin(urljoin(urljoin("http://{}".format(settings.STATIC_HOSTNAME), settings.STATIC_URL),
                                     settings.MEDIA_PREFIX),
                             class_instance.__tablename__ + "/")
    class_attribute = getattr(class_instance, class_attibute_name)
    if class_attribute is not None:
        return urljoin(urljoin(urljoin(urljoin(class_base_url, class_attribute), str(class_instance.id) + "/"),
                               class_attibute_name + "/"), class_attribute)
    else:
        if default_image:
            return urljoin(urljoin(class_base_url, class_attibute_name + "/"), settings.DEFAULT_IMAGE_NAME)
        else:
            return class_attribute


class GenreEnum(enum.Enum):
    male = "M"
    female = "F"


class RolEnum(enum.Enum):
    user = "user"
    band = "band"
    sponsor = "sponsor"


class UserToken(SQLAlchemyBase):
    __tablename__ = "users_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(Unicode(50), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="tokens")

    @hybrid_property
    def json_model(self):
        return {
            "id_instrument": self.id_instrument,
            "name": self.name
        }


class AssociationUserInstruments(SQLAlchemyBase, JSONModel):
    __tablename__ = "user-instruments-association"

    id_user = Column(Integer, ForeignKey("users.id",
                                         onupdate="CASCADE", ondelete="CASCADE"),
                     nullable=False, primary_key=True)
    id_instrument = Column(Integer, ForeignKey("instruments.id_instrument",
                                               onupdate="CASCADE", ondelete="CASCADE"),
                           nullable=False, primary_key=True)
    expirience = Column(Integer, nullable=False)

    assoc_instruments = relationship("Instruments")





class Instruments(SQLAlchemyBase, JSONModel):
    __tablename__ = "instruments"

    id_instrument = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)


AssociationUserMusicalGenre = Table('user-musicalgeneres-association', SQLAlchemyBase.metadata,
                                    Column('id_user', Integer, ForeignKey('users.id',
                                                                           onupdate="CASCADE", ondelete="CASCADE"),
                                            nullable=False),
                                    Column('id_genre', Integer, ForeignKey('musicalgeneres.id',
                                                                             onupdate="CASCADE", ondelete="CASCADE"),
                                            nullable=False))


seguidores = Table("seguimientos", SQLAlchemyBase.metadata,
    Column("seguidor", Integer, ForeignKey("users.id"), primary_key=True),
    Column("seguido", Integer, ForeignKey("users.id"), primary_key=True))


class User(SQLAlchemyBase, JSONModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.now, nullable=False)
    username = Column(Unicode(50), unique=True, nullable=False)
    password = Column(UnicodeText, nullable=False)
    firstTime = Column(Boolean, default=True)
    email = Column(Unicode(255), )
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    rol = Column(Enum(RolEnum))
    name = Column(Unicode(50))
    surname = Column(Unicode(50))
    birthdate = Column(Date)
    genere = Column(Enum(GenreEnum))
    phone = Column(Unicode(50))
    photo = Column(Unicode(255))
    gps = Column(UnicodeText, nullable=False)
    description = Column(Unicode(255))
    gen_exp = Column(Float)


    user_instruments = relationship("AssociationUserInstruments")
    user_musicalgeneres = relationship("MusicalGenere", secondary=AssociationUserMusicalGenre)

    subscribed_to = relationship("User",secondary=seguidores,primaryjoin=id==seguidores.c.seguidor,secondaryjoin=id==seguidores.c.seguido,backref="left_nodes")


    @hybrid_property
    def public_profile(self):
        mgenere = self.genere
        if mgenere is None:
            mgenere = ""
        else:
            mgenere = self.genere.value
        return {
            "created_at": self.created_at.strftime(settings.DATETIME_DEFAULT_FORMAT),
            "username": self.username,
            "genere": mgenere,
            "photo": self.photo,
            "gps": self.gps,
            "description": self.description

        }

    @hybrid_property
    def private_profile(self):
        mgenere = self.genere
        if mgenere is None:
            mgenere = ""
        else:
            mgenere = self.genere.value
        return {
            "username": self.username,
            "name": self.name,
            "surname": self.surname,
            "genere": mgenere,
            "birthdate": self.birthdate.strftime(
                settings.DATE_DEFAULT_FORMAT) if self.birthdate is not None else self.birthdate,
            "gen_exp": self.gen_exp,
            "description": self.description

        }

    @hybrid_method
    def set_password(self, password_string):
        self.password = pbkdf2_sha256.hash(password_string)

    @hybrid_method
    def check_password(self, password_string):
        return pbkdf2_sha256.verify(password_string, self.password)

    @hybrid_method
    def create_token(self):
        if len(self.tokens) < settings.MAX_USER_TOKENS:
            token_string = binascii.hexlify(os.urandom(25)).decode("utf-8")
            aux_token = UserToken(token=token_string, user=self)
            return aux_token
        else:
            raise falcon.HTTPBadRequest(title=messages.quota_exceded, description=messages.maximum_tokens_exceded)

    @hybrid_property
    def json_model(self):
        mgenere = self.genere
        if mgenere is None:
            mgenere = ""
        else:
            mgenere = self.genere.value
        return {
            "created_at": self.created_at.strftime(settings.DATETIME_DEFAULT_FORMAT),
            "username": self.username,
            "email": self.email,
            "name": self.name,
            "surname": self.surname,
            "birthdate": self.birthdate.strftime(
                settings.DATE_DEFAULT_FORMAT) if self.birthdate is not None else self.birthdate,
            "genere": mgenere,
            "phone": self.phone,
            "photo": self.photo,
            "gps": self.gps,

        }



# ------------------- MODELOS INSTRUMENTOS ------------------------


# ------------------- MODELOS Generes ------------------------

class MusicalGenere(SQLAlchemyBase, JSONModel):
    __tablename__ = "musicalgeneres"

    id = Column(Integer, primary_key="true")
    name = Column(Unicode(50))

    @hybrid_property
    def json_model(self):
        return {
            "id": self.id,
            "name": self.name
        }
