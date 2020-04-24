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
from db.models import User, Instruments, MusicalGenere, AssociationUserInstruments
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


class ResourceGetUsers(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetUsers, self).on_get(req, resp, *args, **kwargs)
        data = []

        results = self.db_session.query(User).all()

        for result in results:
            data.append(result.public_profile)

        resp.media = data
        resp.status = falcon.HTTP_200


# ------------------------------- GESTIÓN USER-INSTRUMENTS ------------------------------------------#

@falcon.before(requires_auth)
class ResourceAddInstrument(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceAddInstrument, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        # Init association
        association = AssociationUserInstruments()

        # Get input instrument
        if req.media["name"] is not None:
            aux_instrument_name = req.media["name"]

        # Query to get the instrument data from Instruments table
        aux_instrument = self.db_session.query(Instruments). \
            filter(Instruments.name == aux_instrument_name).one()

        # Set none constrained columns, expirience
        if req.media["expirience"] is not None:
            association.expirience = req.media["expirience"]

        # Inserting the instrument into the relationship
        association.usersInstruments = aux_instrument

        # Finally we save our instrument with his expirience in ot user
        current_user.user_instruments.append(association)

        self.db_session.commit()
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceGetTableInstruments(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetTableInstruments, self).on_get(req, resp, *args, **kwargs)
        pass


@falcon.before(requires_auth)
class ResourceRemoveInstrument(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceRemoveInstrument, self).on_post(req, resp, *args, **kwargs)
        pass


@falcon.before(requires_auth)
class ResourceAddGenere(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceAddGenere, self).on_post(req, resp, *args, **kwargs)
        pass


@falcon.before(requires_auth)
class ResourceGetGenereList(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetGenereList, self).on_get(req, resp, *args, **kwargs)
        pass


@falcon.before(requires_auth)
class ResourceRemoveGenere(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceRemoveGenere, self).on_post(req, resp, *args, **kwargs)
        pass
