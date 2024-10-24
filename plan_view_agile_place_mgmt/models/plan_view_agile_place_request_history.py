from odoo import _, api, fields, models


class PlanViewAgilePlaceRequestHistory(models.Model):
    _name = "plan.view.agile.place.request_history"
    _description = "plan_view_agile_place_request_history"

    name = fields.Char()

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )
