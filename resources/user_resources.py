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
        request_genres_list = list()
        if request_genres is not None:
            request_genres_list = request_genres.split(",")

        request_instruments = req.get_param("instruments", False)
        request_instruments_list = list()
        if request_instruments is not None:
            request_instruments_list = request_instruments.split(",")


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


## Match

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
            a = sin(dlat / 2)**2 + cos(lat) * cos(lat_user) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c

            if(distance < limite_distancia):
                resultados_filtro_distancia.append(result)


        if(len(resultados_filtro_distancia) == 0):
            resultados_filtro_distancia = results


        #---- Filtro instrumentos
        user_instruments_query = self.db_session.query(AssociationUserInstruments.expirience, Instruments.name).join(
            Instruments).filter(
            AssociationUserInstruments.id_user == current_user.id)

        response_instruments = list()
        aux_response = user_instruments_query.all()

        instrumentos_user = []
        if aux_response is not None:
            for current_instrument in aux_response:
                #print(current_instrument[1])
                instrumentos_user.append(current_instrument[1])
        

        resultados_filtro_instrumentos = []
        if(len(instrumentos_user) != 0):
            
            for result in resultados_filtro_distancia:
                #print(result.public_profile)
                user_instruments_query = self.db_session.query(AssociationUserInstruments.expirience, Instruments.name).join(
                Instruments).filter(AssociationUserInstruments.id_user == result.id)

                response_instruments = list()
                aux_response = user_instruments_query.all()
                if aux_response is not None:
                    for current_instrument in aux_response:
                        #print(current_instrument[1])
                        response_instruments.append(current_instrument[1])
                if(len(response_instruments) != 0):
                    #print("Hay instrumentos a comparar")
                    instrumentos_user_set = set(instrumentos_user) 
                    instrumentos_aux_set = set(response_instruments) 
                    if len(instrumentos_user_set.intersection(instrumentos_aux_set)) > 0: 
                        #print("Hay instrumentos en comun")
                        resultados_filtro_instrumentos.append(result)
            if(len(resultados_filtro_instrumentos) == 0):
                resultados_filtro_instrumentos = resultados_filtro_distancia

        else:
            resultados_filtro_instrumentos = resultados_filtro_distancia
                



        #---- Filtro Generos
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


                if(len(generes_aux)!= 0):
                    generes_user_set = set(generes_user) 
                    generes_aux_set = set(generes_aux) 
                    if len(generes_user_set.intersection(generes_aux_set)) > 0: 
                        print("Hay generos en comun")
                        resultados_filtro_generos.append(result)
                    
            if(len(resultados_filtro_generos) == 0):
                resultados_filtro_generos = resultados_filtro_instrumentos 



        else:
           resultados_filtro_generos = resultados_filtro_instrumentos 



        resp.media = resultados_filtro_generos[0].public_profile
        resp.status = falcon.HTTP_200





# ------------------- Da una info u otra del perfil, dependiendo de si current user esta subscrito a el user por parametro------------------------
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
                data.append({"subscribed" : is_subscribed})
                resp.media  = data

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
                current_user.subscribed_to[:] = [x for x in current_user.subscribed_to if x.username != kwargs["username"]]
                self.db_session.add(current_user)
                self.db_session.commit()

                resp.media = 1
                resp.status = falcon.HTTP_200
            except NoResultFound:
                raise falcon.HTTPBadRequest(description='Error ResourceDeleteSubscribed')



#------------------------------- GESTIÓN USER-INSTRUMENTS ------------------------------------------#


@falcon.before(requires_auth)
class ResourceAddInstrument(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceAddInstrument, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        try:
            for instrument in req.media:
                print(req.media)
                if (instrument['name'] and instrument['expirience']) is not None:

                    aux_instrument_name = instrument['name']

                    aux_instrument = self.db_session.query(Instruments). \
                        filter(Instruments.name == aux_instrument_name).one()

                    user_exp_instrument = \
                        self.db_session.query(AssociationUserInstruments).filter(
                            AssociationUserInstruments.id_user == current_user.id,
                            AssociationUserInstruments.id_instrument == aux_instrument.id_instrument
                        ).all()

                    if len(user_exp_instrument) == 0:
                        # Init association
                        association = AssociationUserInstruments()
                        # Inserting the instrument into the relationship
                        association.assoc_instruments = aux_instrument
                        association.expirience = instrument["expirience"]
                        # Finally we save our instrument with his expirience in ot user
                        current_user.user_instruments.append(association)
                    else:
                        print("El usuari tiene ya experiencia, simplemente actualizo")
                        user_exp_instrument[0].expirience = instrument["expirience"]

            self.db_session.commit()
            resp.status = falcon.HTTP_200

        except NoResultFound:
            raise falcon.HTTPBadRequest(description=messages.instrument_dont_exist)


@falcon.before(requires_auth)
class ResourceGetTableInstruments(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetTableInstruments, self).on_get(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        user_instruments_query = self.db_session.query(AssociationUserInstruments.expirience, Instruments.name).join(
            Instruments).filter(
            AssociationUserInstruments.id_user == current_user.id)

        response_instruments = list()
        aux_response = user_instruments_query.all()

        if aux_response is not None:
            for current_instrument in aux_response:
                response = {
                    'expirience': current_instrument[0],
                    'name': current_instrument[1]
                }
                response_instruments.append(response)

        resp.media = response_instruments
        resp.status = falcon.HTTP_200


@falcon.before(requires_auth)
class ResourceRemoveInstrument(DAMCoreResource):
    def on_delete(self, req, resp, *args, **kwargs):
        super(ResourceRemoveInstrument, self).on_delete(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]
        print("vhivat")
        try:
            if "name" in kwargs:
                print(kwargs["name"])
                query = self.db_session.query(AssociationUserInstruments).join(Instruments)
                aux_instrument = query. \
                    filter(Instruments.name == kwargs["name"],
                           AssociationUserInstruments.id_user == current_user.id).one()
                self.db_session.delete(aux_instrument)
                print(aux_instrument)
            self.db_session.commit()
            resp.status = falcon.HTTP_200
        except KeyError:
            raise falcon.HTTPBadRequest(description=messages.parameters_invalid)
        except NoResultFound:
            # Aquest missatge es mostra si (instrument no existeix) o (instrument no es del usuari)
            raise falcon.HTTPBadRequest(description=messages.instrument_dont_exist)


# Seguir model instruments
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

