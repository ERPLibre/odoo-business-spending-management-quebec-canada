from odoo import _, api, fields, models


class PlanViewAgilePlaceCard(models.Model):
    _name = "plan.view.agile.place.card"
    _description = "plan_view_agile_place_card"

    name = fields.Char()

    board_id = fields.Many2one(
        comodel_name="_unknown",
        string="Board",
    )

    lane_id = fields.Many2one(
        comodel_name="_unknown",
        string="Lane",
    )
