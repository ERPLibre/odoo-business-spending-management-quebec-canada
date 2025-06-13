#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import json
import logging
import os
import uuid

import asana
import requests
import werkzeug.utils
import werkzeug.wrappers
from asana.rest import ApiException
from werkzeug.utils import redirect

from odoo import http
from odoo.http import Response, request
from odoo.tools import config

_logger = logging.getLogger(__name__)


class AsanaController(http.Controller):

    @staticmethod
    def _add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = (
            "https://app.asana.com"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, x-asana-request-signature"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        return response

    @http.route(
        "/asana_integration/auth", type="http", auth="public", website=True
    )
    def auth(self, **kwargs):
        _logger.info("Auth happened!")
        asana_url = "/asana_integration/static/auth.html"
        _logger.info(asana_url)
        return self._add_cors_headers(request.redirect(asana_url))

    @http.route(
        "/asana_integration/authenticate",
        type="http",
        auth="public",
        website=True,
    )
    def authenticate(self, **kwargs):
        state = str(uuid.uuid4())
        request.session["state"] = state
        asana_url = (
            f"https://app.asana.com/-/oauth_authorize?response_type=code&client_id={os.getenv('CLIENT_ID')}"
            f"&redirect_uri={os.getenv('REDIRECT_URI')}&state={state}"
        )
        _logger.info(asana_url)
        return self._add_cors_headers(request.redirect(asana_url))

    @http.route(
        "/asana_integration/oauth-callback",
        type="http",
        auth="public",
        website=True,
    )
    def oauth_callback(self, **kwargs):
        state = kwargs.get("state")
        if state != request.session.get("state"):
            response = Response(
                "State mismatch. Possible CSRF attack.", status=422
            )
            return self._add_cors_headers(response)

        code = kwargs.get("code")
        token_url = "https://app.asana.com/-/oauth_token"
        data = {
            "grant_type": "authorization_code",
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "redirect_uri": os.getenv("REDIRECT_URI"),
            "code": code,
        }

        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")
            request.session["access_token"] = access_token
            return self._add_cors_headers(
                request.redirect(
                    f"/asana_integration/?access_token={access_token}"
                )
            )
        else:
            response = Response("Error exchanging code for token.", status=500)
            return self._add_cors_headers(response)

    @http.route(
        "/asana_integration/get-me", type="http", auth="public", website=True
    )
    def get_me(self, **kwargs):
        access_token = request.session.get("access_token")
        if access_token:
            configuration = asana.Configuration()
            configuration.access_token = access_token
            api_client = asana.ApiClient(configuration)
            users_api_instance = asana.UsersApi(api_client)
            user_gid = "me"
            try:
                api_response = users_api_instance.get_user(user_gid)
                return Response(
                    json.dumps(api_response), content_type="application/json"
                )
            except ApiException as e:
                response = Response(
                    f"Exception when calling UsersApi->get_user: {e}",
                    status=500,
                )
                return self._add_cors_headers(response)
        else:
            return self._add_cors_headers(
                request.redirect("/asana_integration/auth")
            )

    @http.route(
        "/asana_integration/rule/typeahead",
        type="http",
        auth="public",
        website=True,
    )
    def rule_typeahead(self, **kwargs):
        _logger.info("typeahead")
        return "Typeahead"

    @http.route(
        "/asana_integration/rule/on_change",
        type="http",
        auth="public",
        website=True,
    )
    def rule_on_change(self, **kwargs):
        _logger.info("on_change")
        return "On Change"

    @http.route(
        "/asana_integration/get_ressource",
        type="http",
        auth="public",
        # csrf=False,
        methods=["GET", "OPTIONS"],
        website=True,
    )
    def rule_on_get_ressource(self, **kwargs):
        _logger.info("on_get_ressource")
        # response = Response("Succeed", status=200)
        # return self._add_cors_headers(response)
        return self._add_cors_headers(
            redirect("https://www.google.com", code=303)
        )

    @http.route(
        "/asana_integration/on_submit_callback",
        type="http",
        auth="public",
        csrf=False,
        methods=["POST", "OPTIONS"],
        website=True,
    )
    def rule_on_submit_callback(self, **kwargs):
        _logger.info("on_submit_callback")
        response = Response("Succeed", status=200)
        return self._add_cors_headers(response)
