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
from db.models import User, UserInstruments, Instruments
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

@falcon.before(requires_auth)
class ResourceAddInstrument(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):
        super(ResourceAddInstrument, self).on_post(req, resp, *args, **kwargs)
        print("chivato")
        
        aux_instrument = UserInstruments()
        
        try:
            # RECOGEMOS LOS VALORS, A PARTIR DE LA AUTENTICACIÓN QUE REQUIERE ESTA CALL,
            # conseguimos el id del usuario que quiere añadir elementos
            # --- req.media --- Cogemos del cuerpo JSON

            auth_user = req.context["auth_user"]

            aux_instrumentName = req.media["nameInstrument"]
            aux_expirience = req.media["expirience"]

            #mediante el String instrumento, hacemos una query para buscar su id
            aux_idInstrument = self.db_session.query(Instruments).filter(Instruments.name == aux_instrumentName).one()
            

            #Guardamos los valores en el objeto UserInstruments, para acutaliarlo en la base e datos
            aux_instrument.id  = auth_user.id
            aux_instrument.id_instrument = aux_idInstrument.id_instrument
            aux_instrument.expirience = aux_expirience

            self.db_session.add(aux_instrument)
            self.db_session.commit()

        except KeyError:
             raise falcon.HTTPBadRequest(description=messages.parameters_invalid)
        
        resp.status = falcon.HTTP_200

@falcon.before(requires_auth)
class ResourceGetTableInstruments(DAMCoreResource):
    def on_get(self, req, resp, *args, **kwargs):
        super(ResourceGetTableInstruments, self).on_get(req, resp, *args, **kwargs)
        
        current_user = req.context["auth_user"]
        data = []

        #Comprovamos cuantos instrumentos tiene el usuario
        count = self.db_session.query(UserInstruments).filter(UserInstruments.id == current_user.id).count()
        print(count)

        #recogemos los datos de estos
        result = self.db_session.query(Instruments, UserInstruments.expirience).select_from(Instruments).filter(UserInstruments.id_instrument == Instruments.id_instrument).all()

        #A CADA FILA tenim 3 columnes, id_instrument, el seu nom, i la experiencia
        #-------> row[0] = sifnifica la part qu té INSTRUMENT, nom e id.
        #-------> row[1] = La par de USERINSTRUMENT, experiènicia
        for i in range(count):
            row = result.pop(i - 1)
            json = row[0].json_model
            json["expirience"] = row[1]
            data.append(json)
                
        print(data)

        resp.media = data
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

# funcional, aún falta algunos retoques
@falcon.before(requires_auth)
class ResourceRemoveInstrument(DAMCoreResource):
     def on_post(self, req, resp, *args, **kwargs):
        super(ResourceRemoveInstrument, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        aux_instrumentName = req.media["nameInstrument"]

        aux_idInstrument = self.db_session.query(Instruments).filter(Instruments.name == aux_instrumentName).one()

        aux_instrument = self.db_session.query(UserInstruments).filter(UserInstruments.id_instrument == aux_idInstrument.id_instrument , UserInstruments.id == current_user.id).one()

        print(aux_instrument.json_model)

        self.db_session.delete(aux_instrument)
        self.db_session.commit()


        resp.media = "removed"
        resp.status = falcon.HTTP_200

       


        


    



     
     


