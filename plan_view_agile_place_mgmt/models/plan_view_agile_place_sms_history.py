import logging
import os

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceSmsHistory(models.Model):
    _name = "plan.view.agile.place.sms.history"
    _description = "plan_view_agile_place_sms_history"

    name = fields.Char(string="Body")

    from_number_phone = fields.Char()

    from_number_phone_country = fields.Char()

    is_sent = fields.Boolean(readonly=True)

    to_number_phone = fields.Char()

    to_number_phone_country = fields.Char()

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
                if rec.session_id.sms_from_number_phone:
                    from_number_phone = (
                        rec.from_number_phone_country
                        + rec.session_id.sms_from_number_phone
                    )
                else:
                    from_number_phone = (
                        rec.from_number_phone_country + rec.from_number_phone
                    )
                for to_number_phone_single in to_number_phone.split(";"):
                    # Create request
                    pre_command = (
                        f"--data-urlencode 'To={to_number_phone_single}'"
                        f" --data-urlencode 'From={from_number_phone}'"
                    )
                    past_command = f' --data-urlencode "Body={rec.name}"'
                    command = pre_command + f" -u {api_token}" + past_command
                    cmd_curl = f"curl '{api_url}' -X POST {command}"

                    rec.is_sent = True
                    if (
                        rec.session_id.sms_enable
                        or rec.processus_id.board_id.session_id.sms_enable
                    ):
                        os.system(cmd_curl)
                    else:
                        _logger.info(pre_command + past_command)
