#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import re

import falcon
from falcon.media.validators import jsonschema
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


import messages
from db.models import User, Instruments, MusicalGenere, AssociationUserInstruments, AssociationUserMusicalGenre
from hooks import requires_auth
from resources.base_resources import DAMCoreResource

mylogger = logging.getLogger(__name__)

@falcon.before(requires_auth)
class ResourceAddGeneres(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceAddGeneres, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]
        try:
            for genre in req.media:
                if genre["name"] is not None:

                    aux_genre_name = genre["name"]

                    aux_genre = self.db_session.query(MusicalGenere).\
                        filter(MusicalGenere.name == aux_genre_name).one()

                    if aux_genre is not None:
                        current_user.user_musicalgeneres.append(aux_genre)

            self.db_session.commit()
            resp.status = falcon.HTTP_200

        except NoResultFound:
            raise falcon.HTTPBadRequest(description=messages.instrument_dont_exist)


@falcon.before(requires_auth)
class ResourceGetGenereList(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetGenereList, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        user_musicalGenere_query = self.db_session.query(AssociationUserMusicalGenre, MusicalGenere.name). \
            join(MusicalGenere) \
            .filter(AssociationUserMusicalGenre.c.id_user == current_user.id)

        response_musical_generes = list()
        aux_response = user_musicalGenere_query.all()

        if aux_response is not None:
            for current_musical_genere in aux_response:
                response = {
                    'name': current_musical_genere[2]
                }
                response_musical_generes.append(response)

        resp.media = response_musical_generes
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceRemoveGenere(DAMCoreResource):
    def on_delete(self, req, resp, *args, **kwargs):
        super(ResourceRemoveGenere, self).on_delete(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        if "name" in kwargs:
            print(kwargs["name"])
            musical_genere = self.db_session.query(MusicalGenere) \
                .filter(MusicalGenere.name == kwargs["name"]).one()

            d = AssociationUserMusicalGenre.delete().where(and_(
                AssociationUserMusicalGenre.c.id_user == current_user.id,
                AssociationUserMusicalGenre.c.id_genre == musical_genere.id
            ))

            self.db_session.execute(d)

        self.db_session.commit()
        resp.status = falcon.HTTP_200

