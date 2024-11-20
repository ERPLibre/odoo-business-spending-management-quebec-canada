#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import logging
import os

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceSmsHistory(models.Model):
    _name = "plan.view.agile.place.sms.history"
    _description = "plan_view_agile_place_sms_history"
    _order = "id desc"

    name = fields.Text(string="Body")

    from_number_phone = fields.Char()

    from_number_phone_country = fields.Char()

    from_number_real_phone = fields.Char(
        help="This is the real phone to be use, can be overwrite for debug.",
        readonly=True,
    )

    is_sent = fields.Boolean(readonly=True)

    to_number_phone = fields.Char()

    to_number_phone_country = fields.Char()

    to_number_real_phone = fields.Char(
        help="This is the real phone to be use, can be overwrite for debug.",
        readonly=True,
    )

    group_execution_name = fields.Char(
        help=(
            "This can be use to create group of sending, to associate another"
            " SMS history to this."
        )
    )

    processus_id = fields.Many2one(
        "plan.view.agile.place.processus", string="Processus"
    )

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )

    def send_sms(self, ctx=None, api_url=None, api_token=None):
        for rec in self:
            if not api_url or not api_token:
                # Check API
                if rec.session_id and rec.session_id.sms_api_url:
                    api_url = rec.session_id.sms_api_url
                else:
                    _logger.error("Missing API URL to send SMS.")
                if rec.session_id and rec.session_id.api_token:
                    api_token = rec.session_id.sms_api_token
                else:
                    _logger.error("Missing API URL to send SMS.")
                # Check number
                if rec.session_id.sms_to_number_phone_default:
                    to_number_phone = (
                        rec.session_id.sms_to_country_default
                        + rec.session_id.sms_to_number_phone_default
                    )
                else:
                    to_number_phone = (
                        rec.to_number_phone_country + rec.to_number_phone
                    )
                rec.to_number_real_phone = to_number_phone
                if rec.session_id.sms_from_number_phone:
                    from_number_phone = (
                        rec.from_number_phone_country
                        + rec.session_id.sms_from_number_phone
                    )
                else:
                    from_number_phone = (
                        rec.from_number_phone_country + rec.from_number_phone
                    )
                rec.from_number_real_phone = from_number_phone
                for to_number_phone_single in to_number_phone.split(";"):
                    # Create request
                    pre_command = (
                        f"--data-urlencode 'To={to_number_phone_single}'"
                        f" --data-urlencode 'From={from_number_phone}'"
                    )
                    past_command = f' --data-urlencode "Body={rec.name}"'
                    command = pre_command + f" -u {api_token}" + past_command
                    cmd_curl = f"curl '{api_url}' -X POST {command}"

                    if rec.session_id.sms_enable and (
                        not rec.processus_id
                        or (
                            rec.processus_id
                            and not rec.processus_id.sms_in_test_mode
                        )
                    ):
                        os.system(cmd_curl)
                        rec.is_sent = True
                    else:
                        _logger.info(pre_command + past_command)
