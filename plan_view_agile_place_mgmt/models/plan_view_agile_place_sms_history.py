import os

from odoo import _, api, fields, models


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

    def send_sms(self, api_url, api_token):
        for rec in self:
            cmd_curl = (
                f"curl '{api_url}' -X POST --data-urlencode"
                f" 'To={rec.to_number_phone_country}{rec.to_number_phone}'"
                " --data-urlencode"
                f" 'From={rec.from_number_phone_country}{rec.from_number_phone}'"
                f' -u {api_token} --data-urlencode "Body={rec.name}"'
            )

            rec.is_sent = True
            os.system(cmd_curl)
