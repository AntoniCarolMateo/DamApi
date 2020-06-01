#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import logging
import os

from sqlalchemy.sql import text

import db
import settings
from db.models import SQLAlchemyBase, User, GenreEnum, UserToken, RolEnum, AssociationUserInstruments
from db.models import Instruments, MusicalGenere
from settings import DEFAULT_LANGUAGE

# LOGGING
mylogger = logging.getLogger(__name__)
settings.configure_logging()


def execute_sql_file(sql_file):
    sql_folder_path = os.path.join(os.path.dirname(__file__), "sql")
    sql_file_path = open(os.path.join(sql_folder_path, sql_file), encoding="utf-8")
    sql_command = text(sql_file_path.read())
    db_session.execute(sql_command)
    db_session.commit()
    sql_file_path.close()


if __name__ == "__main__":
    settings.configure_logging()

    db_session = db.create_db_session()

    # -------------------- REMOVE AND CREATE TABLES --------------------
    mylogger.info("Removing database...")
    SQLAlchemyBase.metadata.drop_all(db.DB_ENGINE)
    mylogger.info("Creating database...")
    SQLAlchemyBase.metadata.create_all(db.DB_ENGINE)

    # -------------------- CREATE USERS --------------------
    mylogger.info("Creating default users...")
    # noinspection PyArgumentList
    user_admin = User(
        created_at=datetime.datetime(2020, 1, 1, 0, 1, 1),
        username="admin",
        email="admin@damcore.com",
        name="Administrator",
        surname="DamCore",
        genere=GenreEnum.male,
        gps="42.090205,1.1504",
        rol=RolEnum.sponsor,
        gen_exp=4.5,
        description="description admin"
    )
    user_admin.set_password("DAMCoure")

    # noinspection PyArgumentList
    user_1 = User(
        created_at=datetime.datetime(2020, 1, 1, 0, 1, 1),
        username="34938030161",
        email="usuari1@gmail.com",
        name="usuari",
        surname="1",
        rol=RolEnum.user,
        birthdate=datetime.datetime(1989, 1, 1),
        genere=GenreEnum.male,
        gps="42.390205,3.1504",
        description="description user1",
        firstTime=False,
        gen_exp=3.0,
    )
    user_1.set_password("1234")
    user_1.tokens.append(UserToken(token="656e50e154865a5dc469b80437ed2f963b8f58c8857b66c9bf"))

    # noinspection PyArgumentList
    user_2 = User(
        created_at=datetime.datetime(2020, 1, 1, 0, 1, 1),
        username="user2",
        email="user2@gmail.com",
        name="user",
        surname="2",
        birthdate=datetime.datetime(2017, 1, 1),
        genere=GenreEnum.male,
        gps="40.390205,2.5504",
        description="description user2",
        gen_exp=5.0,
    )
    user_2.set_password("r45tgt")
    user_2.tokens.append(UserToken(token="0a821f8ce58965eadc5ef884cf6f7ad99e0e7f58f429f584b2"))

    user_1.subscribed_to.append(user_2)
    user_admin.subscribed_to.append(user_1)

    # -------------------- CREATE Instruments --------------------
    mylogger.info("Creating instrumets data...")

    ins_path = os.path.join(os.path.dirname(__file__), "instrumentsdata.txt")
    file_ins = open(ins_path, "r")
    Lines = file_ins.readlines()
    for ins in Lines:
        instrument = Instruments(
            name=ins.strip()
        )

        db_session.add(instrument)
        if instrument.name == "Bajo":
            a1 = AssociationUserInstruments(
                expirience=3.0,
                assoc_instruments=instrument)
            user_1.user_instruments.append(a1)
        if instrument.name == "Voz":
            a2 = AssociationUserInstruments(
                expirience=4.0,
                assoc_instruments =instrument)
            user_2.user_instruments.append(a2)

        # if ins == "Batería" or "Guitarra Clássica":
        #
        # if ins == "Piano Électrico":


    # -------------------- CREATE Generes --------------------
    mylogger.info("Creating MusicalGenere data...")

    gen_path = os.path.join(os.path.dirname(__file__), "musicalgenresdata.txt")
    file_gen = open(gen_path, "r")
    Lines = file_gen.readlines()
    for gen in Lines:
        genre = MusicalGenere(
            name=gen.strip()
        )
        if gen == "Blues" or "Rock and Roll" or "Jazz":
            user_2.user_musicalgeneres.append(genre)
        if gen == "Disco" or "Pop" or "Trap":
            user_admin.user_musicalgeneres.append(genre)
        if gen == "Salsa" or "Bachata":
            user_1.user_musicalgeneres.append(genre)
        else:
            db_session.add(genre)

    # ----Adding Users----#
    db_session.add(user_admin)
    db_session.add(user_1)
    db_session.add(user_2)


    db_session.commit()
    db_session.close()
