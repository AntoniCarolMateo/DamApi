#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging.config

import falcon

import messages
import middlewares
from resources import account_resources, common_resources, user_resources
from settings import configure_logging

# LOGGING
mylogger = logging.getLogger(__name__)
configure_logging()


# DEFAULT 404
# noinspection PyUnusedLocal
def handle_404(req, resp):
    resp.media = messages.resource_not_found
    resp.status = falcon.HTTP_404


# FALCON
app = application = falcon.API(
    middleware=[
        middlewares.DBSessionManager(),
        middlewares.Falconi18n()
    ]
)
application.add_route("/", common_resources.ResourceHome())

application.add_route("/account/profile", account_resources.ResourceAccountUserProfile())
application.add_route("/account/update_profile", account_resources.ResourceAccountUpdateUserProfile())
application.add_route("/account/create_token", account_resources.ResourceCreateUserToken())
application.add_route("/account/delete_token", account_resources.ResourceDeleteUserToken())

application.add_route("/users/register", user_resources.ResourceRegisterUser())
application.add_route("/users/show/{username}", user_resources.ResourceGetUserProfile())
application.add_route("/users/all", user_resources.ResourceGetUsers())

#------------------------------- GESTIÓN USER-INSTRUMENTS ------------------------------------------#
application.add_route("/users/profile/addInstrument", user_resources.ResourceSetTableInstruments())
application.add_route("/users/profile/getInstrumentList", user_resources.ResourceGetTableInstruments())
application.add_route("/users/profile/deleteInstrument", user_resources.ResourceRemoveInstrument())

application.add_sink(handle_404, "")
