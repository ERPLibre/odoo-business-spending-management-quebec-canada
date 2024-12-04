#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import logging
import os

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

MAX_CHAR_SMS = 1599


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

    error_msg = fields.Char()

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

            # Check number phone
            # TO
            # TODO support ; into TO
            if rec.session_id.sms_to_number_phone_default:
                to_number_phone = (
                    rec.session_id.sms_to_country_default
                    + rec.session_id.sms_to_number_phone_default
                )
            elif rec.to_number_phone:
                if rec.to_number_phone_country:
                    to_number_phone = (
                        rec.to_number_phone_country + rec.to_number_phone
                    )
                else:
                    to_number_phone = (
                        rec.session_id.sms_to_country_default
                        + rec.to_number_phone
                    )
            else:
                error_msg = "Cannot send SMS, missing number phone TO."
                _logger.error(error_msg)
                continue
            rec.to_number_real_phone = to_number_phone

            # FROM
            if rec.session_id.sms_from_number_phone_default:
                from_number_phone = (
                    rec.session_id.sms_from_country_default
                    + rec.session_id.sms_from_number_phone_default
                )
            elif rec.from_number_phone:
                if rec.from_number_phone_country:
                    # TODO what happen when crash, string append boolean
                    from_number_phone = (
                        rec.from_number_phone_country + rec.from_number_phone
                    )
                else:
                    from_number_phone = (
                        rec.session_id.sms_from_country_default
                        + rec.from_number_phone
                    )
            else:
                error_msg = "Cannot send SMS, missing number phone FROM."
                _logger.error(error_msg)
                continue

            if not rec.name:
                error_msg = f"Empty SMS, will not send to number phone {rec.to_number_phone}."
                _logger.error(error_msg)
                continue

            rec.from_number_real_phone = from_number_phone

            if len(rec.name) > MAX_CHAR_SMS:
                body = rec.name
                lst_body = []
                i_start = 0
                i_end = 0
                while i_start < len(body):
                    i_end = i_start + MAX_CHAR_SMS
                    if i_end < len(body):
                        # Manage break line
                        dernier_saut = body.rfind("\n", i_start, i_end)
                        if dernier_saut != -1:
                            i_end = dernier_saut + 1
                        else:
                            # Manage space
                            last_space = body.rfind(" ", i_start, i_end)
                            if last_space != -1:
                                i_end = last_space + 1

                    # TODO maybe remove strip to accept whitespace before or after
                    lst_body.append(body[i_start:i_end].strip())
                    i_start = i_end
            else:
                lst_body = [rec.name]
            for body in lst_body:
                for to_number_phone_single in to_number_phone.split(";"):
                    # Create request
                    pre_command = (
                        f"--data-urlencode 'To={to_number_phone_single}'"
                        f" --data-urlencode 'From={from_number_phone}'"
                    )
                    past_command = f' --data-urlencode "Body={body}"'
                    command = pre_command + f" -u {api_token}" + past_command
                    cmd_curl = f"curl '{api_url}' -X POST {command}"

                    if rec.session_id.sms_enable and (
                        not rec.processus_id
                        or (
                            rec.processus_id
                            and not rec.processus_id.sms_in_test_mode
                        )
                    ):
                        # TODO catch output
                        os.system(cmd_curl)
                        rec.is_sent = True
                    else:
                        _logger.info(pre_command + past_command)
