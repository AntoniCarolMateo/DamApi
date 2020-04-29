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
                resp.media = "OK"
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
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceDeleteSubscribed, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]
        if "username" in kwargs:
            
            try:
                current_user.subscribed_to[:] = [x for x in current_user.subscribed_to if x.username != kwargs["username"]]
                self.db_session.add(current_user)
                self.db_session.commit()

                resp.media = "OK"
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

