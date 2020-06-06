#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging


import falcon
from sqlalchemy.orm.exc import NoResultFound


import messages
from db.models import User, Instruments, AssociationUserInstruments
from hooks import requires_auth
from resources.base_resources import DAMCoreResource

mylogger = logging.getLogger(__name__)


@falcon.before(requires_auth)
class ResourceAddInstrument(DAMCoreResource):
    def on_post(self, req, resp, *args, **kwargs):

        super(ResourceAddInstrument, self).on_post(req, resp, *args, **kwargs)

        current_user = req.context["auth_user"]

        try:
            for instrument in req.media:

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