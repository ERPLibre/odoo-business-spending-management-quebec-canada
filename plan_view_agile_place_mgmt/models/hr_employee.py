#!/usr/bin/env python3
# © 2021-2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceBoard(models.Model):
    _inherit = "hr.employee"

    enable_sms_rappel_horaire_gestionnaire = fields.Boolean()

    enable_sms_rappel_horaire_employee = fields.Boolean()
