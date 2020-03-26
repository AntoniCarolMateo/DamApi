#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import re

import falcon
from falcon.media.validators import jsonschema
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import phonenumbers

import messages
from db.models import User
from hooks import requires_auth
from resources.base_resources import DAMCoreResource
from resources.schemas import SchemaRegisterUser

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
        print("chivato")
        aux_user = User()
        print("password: " + req.media["password"] + " username" + req.media["username"])

        try:
            aux_user.password = req.media["password"]
            aux_user.username = req.media["username"]

            
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
