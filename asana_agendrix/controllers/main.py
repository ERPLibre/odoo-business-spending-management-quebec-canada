#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import json
import logging
from datetime import datetime

from odoo import _, http
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

        asana_agendrix_id = (
            request.env["asana.agendrix"]
            .sudo()
            .search(
                [
                    ("asana_id_workspace", "=", dct_param.get("workspace")),
                    ("asana_id_project", "=", dct_param.get("project")),
                    ("asana_id_action", "=", dct_param.get("action")),
                    (
                        "asana_id_action_type",
                        "=",
                        dct_param.get("action_type"),
                    ),
                ],
                limit=1,
            )
        )

        app_configuration_json = dct_param.get("app_configuration_json")

        dct_app_configuration = json.loads(app_configuration_json)
        has_different_configuration = True

        try:
            dct_fields = {
                dct_value.get("id"): dct_value
                for dct_value in dct_app_configuration.get("metadata").get(
                    "fields"
                )
            }
        except Exception as e:
            _logger.exception(e)
            response = Response(
                "Cannot read parameters metadata, check asana communication action.",
                status=500,
            )
            return response

        field_bind_agendrix_name = dct_fields.get(
            "agendrix_field_name_bind"
        ).get("value")
        field_bind_agendrix_address = dct_fields.get(
            "agendrix_field_address_bind"
        ).get("value")
        if asana_agendrix_id:
            if (
                field_bind_agendrix_name
                == asana_agendrix_id.asana_bind_field_name
                and field_bind_agendrix_address
                == asana_agendrix_id.asana_bind_field_address
            ):
                has_different_configuration = False
        else:
            agendrix_session_id = (
                request.env["agendrix.session"].sudo().search([], limit=1)
            )
            if not agendrix_session_id:
                agendrix_session_id = (
                    request.env["agendrix.session"]
                    .sudo()
                    .create({"name": "First connexion agendrix"})
                )

        action_log_values = {
            "asana_agendrix_id": (
                False if not asana_agendrix_id else asana_agendrix_id.id
            ),
            "asana_id_workspace": dct_param.get("workspace"),
            "asana_id_target_object": dct_param.get("target_object"),
            "asana_id_action_type": dct_param.get("action_type"),
            "asana_id_action": dct_param.get("action"),
            "asana_id_user": dct_param.get("user"),
            "asana_app_configuration_json": app_configuration_json,
            "asana_id_empotency_key": dct_param.get("idempotency_key"),
            "asana_expires_at": datetime.strptime(
                dct_param.get("expires_at"), "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "has_different_configuration": has_different_configuration,
        }
        asana_agendrix_action_log_id = (
            request.env["asana.agendrix.action.log"]
            .sudo()
            .create(action_log_values)
        )

        default_name = "ERROR"
        default_address = "ERROR"
        for dct_custom_fields in dct_task_information.get("custom_fields", []):
            if dct_custom_fields.get("name") == field_bind_agendrix_name:
                default_name = dct_custom_fields.get("text_value")
            elif dct_custom_fields.get("name") == field_bind_agendrix_address:
                default_address = dct_custom_fields.get("text_value")

        if not asana_agendrix_id:
            environment = dct_fields.get("environment").get("value")
            agendrix_session_id = (
                request.env["agendrix.session"]
                .sudo()
                .search(
                    [("production_enabled", "=", environment == "2")],
                    limit=1,
                )
            )
            asana_agendrix_id = (
                request.env["asana.agendrix"]
                .sudo()
                .create(
                    {
                        "name": "Fix missing from database, create a new one",
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
            asana_agendrix_action_log_id=asana_agendrix_action_log_id,
        )

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
        # Check builder from https://app.asana.com/0/my-apps/response-builder
        form_value = {
            "template": "form_metadata_v0",
            "metadata": {
                "title": _("Information de connexion vers Agendrix"),
                "submit_button_text": _("Créer"),
                "on_submit_callback": f"https://{config['ngrok_url']}/asana_integration/agendrix/create_resource/on_submit_callback",
                "fields": [
                    {
                        "type": "dropdown",
                        "id": "environment",
                        "name": "Environment",
                        "is_required": True,
                        "options": [
                            {
                                "id": "1",
                                "label": _("Sandbox"),
                                "icon_url": "https://img.icons8.com/?size=100&id=ZKAK_hw7x9Dv&format=png&color=FF0000",
                            },
                            {
                                "id": "2",
                                "label": _("Production"),
                                "icon_url": "https://img.icons8.com/?size=100&id=lOpR2t8Ke7gs&format=png&color=FF0000",
                            },
                        ],
                        "width": "full",
                    },
                    {
                        "type": "rich_text",
                        "id": "reason_connection",
                        "name": _("Raison de la connexion avec Agendrix"),
                        "value": _(
                            "1) Lier des tâches à des ressources selon les champs suivants."
                        ),
                        "is_required": True,
                        "placeholder": _(
                            "Expliquer la raison de la connexion."
                        ),
                        "width": "full",
                    },
                    {
                        "type": "single_line_text",
                        "id": "agendrix_field_name_bind",
                        "name": _("Bind sur champs Agendrix 'name'"),
                        "value": "🔢 ID. de projet",
                        "is_required": True,
                        "placeholder": "Nom du champs Agendrix 'name'",
                        "width": "full",
                    },
                    {
                        "type": "single_line_text",
                        "id": "agendrix_field_address_bind",
                        "name": _("Bind sur champs Agendrix 'address'"),
                        "value": "📍 Lieux de l'événement",
                        "is_required": True,
                        "placeholder": "Nom du champs Agendrix 'address'",
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

        task_no = kwargs.get("task")

        resource_ids = (
            request.env["asana.task.agendrix.resource"]
            .sudo()
            .search([("asana_task_id_no", "=", task_no)], limit=2)
        )

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
            footer_text = (
                "Information manquante, svp contacter votre développeur!"
            )
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
        if request.httprequest.data:
            try:
                json_data = json.loads(request.httprequest.data)
                data = json.loads(json_data.get("data"))

                environment = data.get("values").get("environment")

                agendrix_session_id = (
                    request.env["agendrix.session"]
                    .sudo()
                    .search(
                        [("production_enabled", "=", environment == "2")],
                        limit=1,
                    )
                )
                asana_session_id = (
                    request.env["asana.session"].sudo().search([], limit=1)
                )
                asana_agendrix_values = {
                    "asana_session_id": asana_session_id.id,
                    "agendrix_session_id": agendrix_session_id.id,
                    "agendrix_environment": environment,
                    "reason_connexion": data.get("values").get(
                        "reason_connection"
                    ),
                    "asana_id_action": data.get("action"),
                    "asana_id_action_type": data.get("action_type"),
                    "asana_expires_at": datetime.strptime(
                        data.get("expires_at"), "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "asana_id_project": data.get("project"),
                    "asana_rule_name": data.get("rule_name"),
                    "asana_id_user": data.get("user"),
                    "asana_id_workspace": data.get("workspace"),
                    "asana_bind_field_name": data.get("values").get(
                        "agendrix_field_name_bind"
                    ),
                    "asana_bind_field_address": data.get("values").get(
                        "agendrix_field_address_bind"
                    ),
                }
                asana_agendrix_id = (
                    request.env["asana.agendrix"]
                    .sudo()
                    .create(asana_agendrix_values)
                )
                response = Response("Succeed", status=200)
            except Exception as e:
                _logger.error(e)
                response = Response(
                    "Cannot read parameters, check asana communication after modals form.",
                    status=500,
                )
        else:
            response = Response("Ignore empty request", status=200)

        return self._add_cors_headers(response)
