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
from db.models import User, Instruments, MusicalGenere, AssociationUserInstruments, AssociationUserMusicalGenre
from resources.schemas import SchemaUserToken

mylogger = logging.getLogger(__name__)


@falcon.before(requires_auth)
class ResourceDataMusicalGenres(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceDataMusicalGenres, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        response_genres = list()

        query_aux = self.db_session.query(MusicalGenere.name)
        query_aux = self.db_session.query(MusicalGenere.name).\
            distinct(MusicalGenere.name)



        for m in query_aux.all():
            response_genres.append(m)

        print(response_genres)





        resp.status = falcon.HTTP_200
