# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class SurveyPage(models.Model):
    _inherit = "survey.page"

    # enable_timer = fields.Boolean(default=False, help="Active timer of field timer_duration.")
    #
    # timer_duration = fields.Integer(default=30, help="Duration in second. Will be enable with field enable_timer.")
