#!/usr/bin/env python3
# © 2025 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import random
from datetime import datetime
from pprint import pprint

import requests

from odoo import _, api, fields, models
from odoo.http import Response, request


class AsanaAgendrix(models.Model):
    _name = "asana.agendrix"
    _description = "asana association with agendrix"

    name = fields.Char(compute="_compute_name")

    asana_session_id = fields.Many2one(comodel_name="asana.session")

    agendrix_session_id = fields.Many2one(comodel_name="agendrix.session")

    agendrix_environment = fields.Selection(
        selection=[("1", "sandbox"), ("2", "production")],
        default="1",
    )

    reason_connexion = fields.Html()

    asana_id_action = fields.Char()

    asana_id_action_type = fields.Char()

    asana_expires_at = fields.Datetime()

    asana_id_project = fields.Char()

    asana_rule_name = fields.Text()

    asana_id_user = fields.Char()

    asana_id_workspace = fields.Char()

    asana_bind_field_name = fields.Char()

    asana_bind_field_address = fields.Char()

    @api.depends(
        "asana_expires_at",
        "asana_id_user",
        "asana_id_action",
        "asana_id_project",
        "asana_id_workspace",
    )
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.asana_expires_at} - {rec.asana_id_user} - {rec.asana_id_action} - {rec.asana_id_project} - {rec.asana_id_workspace}"

    def create_resources_url(
        self,
        resource_name,
        resource_address,
        asana_task_id_no,
        type_job_site=True,
        search_for_no_double=False,
        asana_agendrix_action_log_id=False,
    ):
        for rec in self:
            # TODO send link to agendrix
            resource_id, agendrix_id_no = (
                rec.agendrix_session_id.create_resources(
                    resource_name=resource_name,
                    resource_address=resource_address,
                    type_job_site=type_job_site,
                    search_for_no_double=search_for_no_double,
                    asana_agendrix_action_log_id=asana_agendrix_action_log_id,
                )
            )

            resource_url = ""
            if agendrix_id_no:
                request.env["asana.task.agendrix.resource"].sudo().create(
                    {
                        "name": resource_name,
                        "address": resource_address,
                        "agendrix_resource_id_no": agendrix_id_no,
                        "asana_task_id_no": asana_task_id_no,
                    }
                )
                project_number = rec.agendrix_session_id.project_name
                resource_url = f"{rec.agendrix_session_id.get_prefix_api_url(is_api=False)}/o/{project_number}/resources/{agendrix_id_no}/summary/"
            return resource_url, resource_id, agendrix_id_no
