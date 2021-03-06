#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import logging

import falcon
from falcon.media.validators import jsonschema

from datetime import datetime
import calendar

import messages
from db.models import User, UserToken, GenreEnum, RolEnum
from hooks import requires_auth
from resources.base_resources import DAMCoreResource
from resources.schemas import SchemaUserToken

mylogger = logging.getLogger(__name__)

@falcon.before(requires_auth)
class ResourceAccountUpdateUserProfile(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):

        super(ResourceAccountUpdateUserProfile, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        if req.media["name"] is not None:
            current_user.name = req.media["name"]
        if req.media["surname"] is not None:
            current_user.surname = req.media["surname"]
        if req.media["expirience"] is not None:
            current_user.gen_exp = req.media["expirience"]
        if req.media["description"] is not None:
            current_user.description = req.media["description"]

        if req.media["birthdate"] is not None:
            str_birthdate = req.media["birthdate"]
            aux_birthdate = datetime.strptime(str_birthdate, "%Y-%m-%d")

            current_user.birthdate = aux_birthdate

        if req.media["gender"] is not None:
            aux_gender = req.media["gender"]
            if aux_gender == "MALE":
                current_user.genere = GenreEnum.male
            elif aux_gender == "FEMALE":
                current_user.genere = GenreEnum.female

        self.db_session.add(current_user)
        self.db_session.commit()

        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceAccountSetUserRole(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):

        super(ResourceAccountSetUserRole, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        if "rol" in kwargs:
            aux_rol = kwargs["rol"]

            current_user.rol = aux_rol
            print("ROl " + format(current_user.rol))

        self.db_session.add(current_user)
        self.db_session.commit()
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceAccountSetUsername(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):

        super(ResourceAccountSetUsername, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        if "username" in kwargs:
            current_user.username = kwargs["username"]

        self.db_session.add(current_user)
        self.db_session.commit()
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceAccountShowUserProfile(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceAccountShowUserProfile, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        resp.media = current_user.private_profile
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceCompletedFirstSetUp(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):

        super(ResourceCompletedFirstSetUp, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        current_user.firstTime = False

        self.db_session.add(current_user)
        self.db_session.commit()
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceGetFirstSetUp(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetFirstSetUp, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        resp.media = current_user.firstTime
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceAccountUserProfile(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceAccountUserProfile, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        resp.media = current_user.json_model
        resp.status = falcon.HTTP_200





