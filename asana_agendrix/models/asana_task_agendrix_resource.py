#!/usr/bin/env python3
# © 2025 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import random
from datetime import datetime
from pprint import pprint

import asana
from asana.rest import ApiException

from odoo import _, api, fields, models


class AsanaSession(models.Model):
    _name = "asana.task.agendrix.resource"
    _description = "Related Asana's task with Agenrix's resource"

    name = fields.Char()

    address = fields.Char()

    asana_task_id_no = fields.Char()

    agendrix_resource_id_no = fields.Char()
