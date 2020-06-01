#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging.config

import falcon

import messages
import middlewares
from resources import account_resources, common_resources, user_resources, data_app_resources
from resources import instruments_resources, musicalGenres_resources, profile_resources, \
    match_resources, suscription_resource
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

# ------------------------------- REGISTER and LOGIN ------------------------------------------ #
application.add_route("/account/create_token", account_resources.ResourceCreateUserToken())
application.add_route("/account/delete_token", account_resources.ResourceDeleteUserToken())
application.add_route("/users/register", user_resources.ResourceRegisterUser())
application.add_route("/users/show/{username}", user_resources.ResourceGetUserProfile())
application.add_route("/users/all", user_resources.ResourceGetUsers())

# ------------------------------- PROFILE ------------------------------------------ #
application.add_route("/account/update_profile", profile_resources.ResourceAccountUpdateUserProfile())
application.add_route("/account/profile/setUsername/{username}", profile_resources.ResourceAccountSetUsername())
application.add_route("/account/profile/setUserRol/{rol}", profile_resources.ResourceAccountSetUserRole())

application.add_route("/account/profile/setfirstSetUp", profile_resources.ResourceCompletedFirstSetUp())
application.add_route("/account/profile/getfirstSetUp", profile_resources.ResourceGetFirstSetUp())

application.add_route("/account/profile", profile_resources.ResourceAccountUserProfile())
app.add_route("/account/profile/show", profile_resources.ResourceAccountShowUserProfile())

# ------------------------------- MATCH AND SUSCRIPTION ------------------------------------------ #
application.add_route("/users/match", match_resources.ResourceGetUserMatch())
application.add_route("/users/get_subscribed", suscription_resource.ResourceGetSubscribed())
application.add_route("/users/get_info_by_subscription/{username}", suscription_resource.ResourceGetInfoSubscription())
application.add_route("/users/subscribe/{username}", suscription_resource.ResourceSubscribeUser())
application.add_route("/users/delete_subscribed/{username}", suscription_resource.ResourceDeleteSubscribed())


# ------------------------------- GESTIÓN USER-INSTRUMENTS ------------------------------------------ #
application.add_route("/users/profile/instruments/add", instruments_resources.ResourceAddInstrument())
application.add_route("/users/profile/instruments/list", instruments_resources.ResourceGetTableInstruments())
application.add_route("/users/profile/instruments/delete/{name}", instruments_resources.ResourceRemoveInstrument())

# ------------------------------- GESTIÓN USER-GENERES ------------------------------------------ #
application.add_route("/users/profile/musical_genres/add", musicalGenres_resources.ResourceAddGeneres())
application.add_route("/users/profile/musical_genres/list", musicalGenres_resources.ResourceGetGenereList())
application.add_route("/users/profile/musical_genres/delete/{name}", musicalGenres_resources.ResourceRemoveGenere())


# ------------------------------- Recursos para que la app este completa ------------------------------------------#
application.add_route("/data/musical_genres/avalible", data_app_resources.ResourceDataMusicalGenres())

application.add_sink(handle_404, "")
