#!/usr/bin/env python3
# © 2025 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import random
from datetime import datetime
from pprint import pprint

import requests

from odoo import _, api, fields, models
from odoo.http import Response, request


class AgendrixResource(models.Model):
    _name = "agendrix.resource"
    _description = "agendrix_resource"

    name = fields.Char()

    address = fields.Char()

    agendrix_id_no = fields.Char()

    type_job_site = fields.Boolean()

    agendrix_create_at = fields.Datetime()

    agendrix_update_at = fields.Datetime()
