#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import logging
import time
from datetime import datetime

from dateutil import tz

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceAutomatedActionLog(models.Model):
    _name = "plan.view.agile.place.automated.action.log"
    _description = "plan_view_agile_place_automated_action_log"

    name = fields.Text()

    time_execution = fields.Char()

    ir_cron_id = fields.Many2one(
        comodel_name="ir.cron",
    )

    process_ids = fields.Many2many(
        comodel_name="plan.view.agile.place.processus",
        relation="plan_view_agile_place_action_log_processus_rel",
        string="Process execution",
        help="List of process that be executed.",
    )

    def get_weekday_now(self):
        return datetime.now(
            tz.gettz(self.env.ref("base.user_admin").tz)
        ).weekday()
