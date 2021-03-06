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
class ResourceGetUserMatch(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetUserMatch, self).on_get(req, resp, *args, **kwargs)
        limite_distancia = 300
        # approximate radius of earth in km
        R = 6373.0

        current_user = req.context["auth_user"]

        # Filtro OR &

        data = []

        query = self.db_session.query(User).filter(
            User.id != current_user.id)

        results = query.all()
        latlng_user = current_user.gps.split(",")
        lat_user = radians(float(latlng_user[0]))
        lng_user = radians(float(latlng_user[1]))
        resultados_filtro_distancia = []

        for result in results:
            latlng = result.gps.split(",")
            lat = radians(float(latlng[0]))
            lng = radians(float(latlng[1]))
            dlat = lat_user - lat
            dlon = lng_user - lng
            a = sin(dlat / 2) ** 2 + cos(lat) * cos(lat_user) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c

            if (distance < limite_distancia):
                resultados_filtro_distancia.append(result)

        if (len(resultados_filtro_distancia) == 0):
            resultados_filtro_distancia = results

        # ---- Filtro instrumentos
        user_instruments_query = self.db_session.query(AssociationUserInstruments.expirience, Instruments.name).join(
            Instruments).filter(
            AssociationUserInstruments.id_user == current_user.id)

        response_instruments = list()
        aux_response = user_instruments_query.all()

        instrumentos_user = []
        if aux_response is not None:
            for current_instrument in aux_response:
                # print(current_instrument[1])
                instrumentos_user.append(current_instrument[1])

        resultados_filtro_instrumentos = []

        if (len(instrumentos_user) != 0):

            for result in resultados_filtro_distancia:
                # print(result.public_profile)
                user_instruments_query = self.db_session.query(AssociationUserInstruments.expirience,
                                                               Instruments.name).join(
                    Instruments).filter(AssociationUserInstruments.id_user == result.id)

                response_instruments = list()
                aux_response = user_instruments_query.all()
                if aux_response is not None:
                    for current_instrument in aux_response:
                        # print(current_instrument[1])
                        response_instruments.append(current_instrument[1])
                if (len(response_instruments) != 0):
                    # print("Hay instrumentos a comparar")
                    instrumentos_user_set = set(instrumentos_user)
                    instrumentos_aux_set = set(response_instruments)
                    if len(instrumentos_user_set.intersection(instrumentos_aux_set)) > 0:
                        # print("Hay instrumentos en comun")
                        resultados_filtro_instrumentos.append(result)
            if (len(resultados_filtro_instrumentos) == 0):
                resultados_filtro_instrumentos = resultados_filtro_distancia

        else:
            resultados_filtro_instrumentos = resultados_filtro_distancia

        # ---- Filtro Generos
        resultados_filtro_generos = []

        user_musicalGenere_query = self.db_session.query(AssociationUserMusicalGenre, MusicalGenere.name). \
            join(MusicalGenere) \
            .filter(AssociationUserMusicalGenre.c.id_user == current_user.id)

        aux_response = user_musicalGenere_query.all()
        generes_user = []
        if aux_response is not None:
            print("El usuario tiene generos")
            for current_musical_genere in aux_response:
                print(current_musical_genere[2])
                generes_user.append(current_musical_genere[2])

            for result in resultados_filtro_instrumentos:
                user_musicalGenere_query = self.db_session.query(AssociationUserMusicalGenre, MusicalGenere.name). \
                    join(MusicalGenere) \
                    .filter(AssociationUserMusicalGenre.c.id_user == result.id)
                aux_response = user_musicalGenere_query.all()

                generes_aux = []
                if aux_response is not None:
                    for current_musical_genere in aux_response:
                        print("El user aux tiene  generos")
                        print(current_musical_genere[2])
                        generes_aux.append(current_musical_genere[2])

                if (len(generes_aux) != 0):
                    generes_user_set = set(generes_user)
                    generes_aux_set = set(generes_aux)
                    if len(generes_user_set.intersection(generes_aux_set)) > 0:
                        print("Hay generos en comun")
                        resultados_filtro_generos.append(result)

            if (len(resultados_filtro_generos) == 0):
                resultados_filtro_generos = resultados_filtro_instrumentos



        else:
            resultados_filtro_generos = resultados_filtro_instrumentos

        print(format(resultados_filtro_generos[0].public_profile))
        resp.media = resultados_filtro_generos[0].public_profile
        resp.status = falcon.HTTP_200

