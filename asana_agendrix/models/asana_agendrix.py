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

    name = fields.Char()

    asana_session_id = fields.Many2one(comodel_name="asana.session")

    agendrix_session_id = fields.Many2one(comodel_name="agendrix.session")

    def create_resources(
        self,
        resource_name,
        resource_address,
        asana_task_id_no,
        type_job_site=True,
        search_for_no_double=False,
    ):
        for rec in self:
            # TODO send link to agendrix
            resource_id = rec.agendrix_session_id.create_resources(
                resource_name=resource_name,
                resource_address=resource_address,
                type_job_site=type_job_site,
                search_for_no_double=search_for_no_double,
            )

            request.env["asana.task.agendrix.resource"].sudo().create(
                {
                    "name": resource_name,
                    "address": resource_address,
                    "agendrix_resource_id_no": resource_id.agendrix_id_no,
                    "asana_task_id_no": asana_task_id_no,
                }
            )
            # TODO fill agendrix project number
            # "https://sandbox.agendrix.net/o/1544aa85-3522-4780-982e-d8b1b21b3968/resources/{resource_id.agendrix_id_no}/summary/"
            resource_url = f"{rec.agendrix_session_id.get_prefix_api_url(is_api=False)}/o/1544aa85-3522-4780-982e-d8b1b21b3968/resources/{resource_id.agendrix_id_no}/summary/"
            return resource_url
