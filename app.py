#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging.config

import falcon

import messages
import middlewares
from resources import account_resources, common_resources, user_resources, data_app_resources
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
application.add_route("/account/create_token", account_resources.ResourceCreateUserToken())
application.add_route("/account/delete_token", account_resources.ResourceDeleteUserToken())

application.add_route("/account/update_profile", account_resources.ResourceAccountUpdateUserProfile())
application.add_route("/account/profile/setUsername/{username}", account_resources.ResourceAccountSetUsername())
application.add_route("/account/profile/setUserRol/{rol}", account_resources.ResourceAccountSetUserRole())
app.add_route("/account/profile/show", account_resources.ResourceAccountShowUserProfile())

application.add_route("/account/profile/setfirstSetUp", account_resources.ResourceCompletedFirstSetUp())
application.add_route("/account/profile/getfirstSetUp", account_resources.ResourceGetFirstSetUp())

application.add_route("/users/register", user_resources.ResourceRegisterUser())
application.add_route("/users/show/{username}", user_resources.ResourceGetUserProfile())


application.add_route("/users/get_subscribed", user_resources.ResourceGetSubscribed())
application.add_route("/users/get_info_by_subscription/{username}", user_resources.ResourceGetInfoSubscription())

application.add_route("/users/subscribe/{username}", user_resources.ResourceSubscribeUser())
application.add_route("/users/delete_subscribed/{username}", user_resources.ResourceDeleteSubscribed())

application.add_route("/users/all", user_resources.ResourceGetUsers())
application.add_route("/users/match", user_resources.ResourceGetUserMatch())

#------------------------------- GESTIÓN USER-INSTRUMENTS ------------------------------------------#
application.add_route("/users/profile/instruments/add", user_resources.ResourceAddInstrument())
application.add_route("/users/profile/instruments/list", user_resources.ResourceGetTableInstruments())
application.add_route("/users/profile/instruments/delete/{name}", user_resources.ResourceRemoveInstrument())

#------------------------------- GESTIÓN USER-GENERES ------------------------------------------#
application.add_route("/users/profile/musical_genres/add", user_resources.ResourceAddGeneres())
application.add_route("/users/profile/musical_genres/list", user_resources.ResourceGetGenereList())
application.add_route("/users/profile/musical_genres/delete/{name}", user_resources.ResourceRemoveGenere())


#------------------------------- Recursos para que la app este completa ------------------------------------------#
application.add_route("/data/musical_genres/avalible", data_app_resources.ResourceDataMusicalGenres())

application.add_sink(handle_404, "")
