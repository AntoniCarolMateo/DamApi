#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import re

import falcon
from falcon.media.validators import jsonschema
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import phonenumbers

import messages
from db.models import User, Instruments, MusicalGenere, AssociationUserInstruments, AssociationUserMusicalGenre
from hooks import requires_auth
from resources.base_resources import DAMCoreResource
from resources.schemas import SchemaRegisterUser
from math import sin, cos, sqrt, atan2, radians
mylogger = logging.getLogger(__name__)


@falcon.before(requires_auth)
class ResourceGetUserProfile(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetUserProfile, self).on_get(req, resp, *args, **kwargs)

        if "username" in kwargs:
            try:
                aux_user = self.db_session.query(User).filter(User.username == kwargs["username"]).one()

                resp.media = aux_user.public_profile
                resp.status = falcon.HTTP_200
            except NoResultFound:
                raise falcon.HTTPBadRequest(description=messages.user_not_found)


class ResourceRegisterUser(DAMCoreResource):
    @jsonschema.validate(SchemaRegisterUser)
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceRegisterUser, self).on_post(req, resp, *args, **kwargs)
        aux_user = User()

        try:
            aux_user.password = req.media["password"]
            aux_user.username = req.media["username"]
            aux_user.gps = req.media["gps"]

            email_validator = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'

            try:
                phone = phonenumbers.parse(aux_user.username, None)
            except:
                raise falcon.HTTPBadRequest(description=messages.invalid_phone)

            if phonenumbers.is_valid_number(phone):
                aux_user.phone = str(phone.country_code) + str(phone.national_number)
                aux_user.username = str(phone.country_code) + str(phone.national_number)
            elif re.search(email_validator, aux_user.username):
                aux_user.email = aux_user.username
            else:
                raise falcon.HTTPBadRequest(description=messages.invalid_username)

            self.db_session.add(aux_user)

            try:
                self.db_session.commit()
            except IntegrityError:
                raise falcon.HTTPBadRequest(description=messages.user_exists)

        except KeyError:
            raise falcon.HTTPBadRequest(description=messages.parameters_invalid)

        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceGetUsers(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetUsers, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        # Filtro OR &

        request_genres = req.get_param("genres", False)
        print(request_genres)

        request_genres_list = list()
        if request_genres is not None:
            request_genres_list = request_genres.split(",")


        request_instruments = req.get_param("instruments", False)

        request_instruments_list = list()
        print(format(request_instruments))

        if request_instruments is not None:
            request_instruments_list = request_instruments.split(",")
            print(format(request_instruments_list))



        data = []

        query = self.db_session.query(User).filter(
            User.id != current_user.id)

        genres_list_filtered = list()
        instruments_list_filtered = list()
        results = list()

        if request_genres is not None:
            genres_list_filtered = query.join(AssociationUserMusicalGenre, MusicalGenere ).filter(
                 MusicalGenere.name.in_(request_genres_list)).all()


        if request_instruments is not None:
            instruments_list_filtered = query.join(AssociationUserInstruments, Instruments).filter(
                 Instruments.name.in_(request_instruments_list)).all()


        if genres_list_filtered != []:
            results = genres_list_filtered

        if instruments_list_filtered != []:
            results += instruments_list_filtered

        results = set(results)

        if request_genres is None and request_instruments is None:
            results = query.all()

        for result in results:
            data.append(result.public_profile)

        resp.media = data

        resp.status = falcon.HTTP_200




