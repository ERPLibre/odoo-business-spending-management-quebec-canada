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


class AsanaAgendrixController(http.Controller):

    @staticmethod
    def _add_cors_headers(response):
        # TODO reuse this method from AsanaController
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

    # TODO need to support /health with asana?
    @http.route(
        "/asana_integration/agendrix/create_resource/rule_run_action",
        type="http",
        csrf=False,
        auth="public",
        methods=["POST"],
    )
    def rule_run_action(self, **kwargs):
        _logger.info("run_action agendrix create resource")

        params = json.loads(request.httprequest.data)
        dct_param = json.loads(params.get("data"))
        asana_task_id_no = dct_param.get("target_object")

        session_id = request.env["asana.session"].sudo().search([], limit=1)
        dct_task_information = session_id.get_task_information(
            asana_task_id_no
        )

        # dct_bind = {"ID. de projet": "name", "Lieux de l'événement": "address"}

        default_name = "TEST"
        default_address = "TEST"
        for dct_custom_fields in dct_task_information.get("custom_fields", []):
            if dct_custom_fields.get("name") == "ID. de projet":
                default_name = dct_custom_fields.get("text_value")
            elif dct_custom_fields.get("name") == "Lieux de l'événement":
                default_address = dct_custom_fields.get("text_value")

        asana_agendrix_id = (
            request.env["asana.agendrix"].sudo().search([], limit=1)
        )
        if not asana_agendrix_id:
            agendrix_session_id = (
                request.env["agendrix.session"].sudo().search([], limit=1)
            )
            if not agendrix_session_id:
                agendrix_session_id = (
                    request.env["agendrix.session"]
                    .sudo()
                    .create({"name": "First connexion agendrix"})
                )

            asana_agendrix_id = (
                request.env["asana.agendrix"]
                .sudo()
                .create(
                    {
                        "name": "First connexion",
                        "asana_session_id": session_id.id,
                        "agendrix_session_id": agendrix_session_id.id,
                    }
                )
            )

        resource_url = asana_agendrix_id.sudo().create_resources(
            default_name,
            default_address,
            asana_task_id_no,
            search_for_no_double=True,
        )

        # resource_url = f"https://{config['ngrok_url']}/asana_integration/get_ressource"

        form_rule = {
            "action_result": "resources_created",
            "resources_created": [
                {
                    "resource_name": "Lien vers Agendrix",
                    "resource_url": resource_url,
                }
            ],
        }
        response = Response(
            json.dumps(form_rule), content_type="application/json"
        )
        return self._add_cors_headers(response)

    @http.route(
        "/asana_integration/agendrix/create_resource/rule_run_metadata",
        type="http",
        auth="public",
        website=True,
        # csrf=False,
        methods=["GET", "OPTIONS"],
    )
    def rule_metadata(self, **kwargs):
        _logger.info(
            "Receive request from /asana_integration/agendrix/create_resource/rule_run_metadata"
        )
        form_value = {
            "template": "form_metadata_v0",
            "metadata": {
                "title": "Mon formulaire",
                "submit_button_text": "Créer",
                "on_submit_callback": f"https://{config['ngrok_url']}/asana_integration/agendrix/create_resource/on_submit_callback",
                "fields": [
                    {
                        "type": "single_line_text",
                        "id": "single_line_text_full_width",
                        "name": "Single-line text field",
                        "value": "",
                        "is_required": False,
                        "placeholder": "Type something SVP...",
                        "width": "full",
                    },
                    {
                        "type": "dropdown",
                        "id": "dropdown",
                        "name": "Dropdown field",
                        "is_required": False,
                        "options": [
                            {
                                "id": "1",
                                "label": "Option 1",
                                "icon_url": "https://www.fillmurray.com/16/16",
                            },
                            {
                                "id": "2",
                                "label": "Option 2",
                                "icon_url": "https://www.fillmurray.com/16/16",
                            },
                        ],
                        "width": "full",
                    },
                ],
            },
        }
        response = Response(
            json.dumps(form_value), content_type="application/json"
        )
        return self._add_cors_headers(response)

    @http.route(
        "/asana_integration/agendrix_url_widget",
        type="http",
        auth="public",
        # csrf=False,
        methods=["GET", "OPTIONS"],
        # website=True,
    )
    def rule_on_url_widget(self, **kwargs):
        _logger.info("on_url_widget")

        resource_ids = (
            request.env["agendrix.resource"]
            .sudo()
            .search([], limit=2, order="id desc")
        )
        # TODO search with task_id and agendrix_project
        # TODO search by resource_url or attachment
        lst_fields = []
        if resource_ids:
            for resource_id in [resource_ids[1]]:
                lst_fields.append(
                    {
                        "name": "Nom",
                        "type": "text_with_icon",
                        "text": resource_id.name,
                    }
                )
                lst_fields.append(
                    {
                        "name": "Adresse",
                        "type": "text_with_icon",
                        "text": resource_id.address,
                    }
                )
        if not lst_fields:
            footer_text = "Information manquante, svp contacter votre développeur!"
        else:
            footer_text = f"Ressource complémentaire : {resource_id.name} - PRÉ - POST PRODUCTION"
        form_value = {
            "template": "summary_with_details_v0",
            "metadata": {
                "title": "Ressource associée",
                "subtitle": "Création d'une ressource",
                "fields": lst_fields,
                "footer": {
                    "footer_type": "custom_text",
                    "text": footer_text,
                    # "text": f"Ressource complémentaire : {resource_ids[0].name} - PRÉ - POST PRODUCTION",
                },
            },
        }
        response = Response(
            json.dumps(form_value), content_type="application/json"
        )
        return self._add_cors_headers(response)

    @http.route(
        "/asana_integration/agendrix_url_regex_widget",
        type="http",
        auth="public",
        csrf=False,
        methods=["GET", "OPTIONS"],
        website=True,
    )
    def rule_on_widget_corr(self, **kwargs):
        _logger.info("on_url_widget_corr")
        response = Response("Succeed", status=200)
        return self._add_cors_headers(response)

    @http.route(
        "/asana_integration/agendrix/create_resource/on_submit_callback",
        type="http",
        auth="public",
        csrf=False,
        methods=["POST", "OPTIONS"],
        website=True,
    )
    def rule_on_submit_callback(self, **kwargs):
        _logger.info(
            "/asana_integration/agendrix/create_resource/on_submit_callback"
        )
        response = Response("Succeed", status=200)
        return self._add_cors_headers(response)
