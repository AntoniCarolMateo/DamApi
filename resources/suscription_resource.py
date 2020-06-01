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


#  Da una info u otra del perfil, dependiendo de si current user esta subscrito a el user por parametro
@falcon.before(requires_auth)
class ResourceGetInfoSubscription(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetInfoSubscription, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        if "username" in kwargs:
            try:
                data = []
                is_subscribed = False
                aux_user = self.db_session.query(User).filter(User.username == kwargs["username"]).one()
                for user in current_user.subscribed_to:
                    if user.username == aux_user.username:
                        is_subscribed = True

                data.append(aux_user.public_profile)
                data.append({"subscribed": is_subscribed})
                resp.media = data

                resp.status = falcon.HTTP_200
            except NoResultFound:
                raise falcon.HTTPBadRequest(description='error en ResourceGetInfoSubscription')


# ------------------- Current user(auth) se convierte en seguidor de usuario por GET------------------------
@falcon.before(requires_auth)
class ResourceSubscribeUser(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceSubscribeUser, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        if "username" in kwargs:
            try:
                aux_user = self.db_session.query(User).filter(User.username == kwargs["username"]).one()
                current_user.subscribed_to.append(aux_user)
                resp.media = 1
                self.db_session.add(current_user)
                self.db_session.commit()
                resp.status = falcon.HTTP_200
            except NoResultFound:
                raise falcon.HTTPBadRequest(description=messages.user_not_found)


# Devuelve los usuarios a los que este subscrito el current_user
@falcon.before(requires_auth)
class ResourceGetSubscribed(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceGetSubscribed, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        try:
            data = []
            for result in current_user.subscribed_to:
                data.append(result.public_profile)
            resp.media = data
            resp.status = falcon.HTTP_200
        except NoResultFound:
            raise falcon.HTTPBadRequest(description='Error ResourceGetSubscribed')


# Elimina de current_user una subscripcion
@falcon.before(requires_auth)
class ResourceDeleteSubscribed(DAMCoreResource):
    def on_delete(self, req, resp, *args, **kwargs):
        super(ResourceDeleteSubscribed, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]
        if "username" in kwargs:

            try:
                current_user.subscribed_to[:] = [x for x in current_user.subscribed_to if
                                                 x.username != kwargs["username"]]
                self.db_session.add(current_user)
                self.db_session.commit()

                resp.media = 1
                resp.status = falcon.HTTP_200
            except NoResultFound:
                raise falcon.HTTPBadRequest(description='Error ResourceDeleteSubscribed')


