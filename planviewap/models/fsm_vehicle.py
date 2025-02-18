#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import json
import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class FSMVehicle(models.Model):
    _inherit = "fsm.vehicle"

    pvap_card_id = fields.Many2one(
        comodel_name="planviewap.card",
        string="Card",
    )
