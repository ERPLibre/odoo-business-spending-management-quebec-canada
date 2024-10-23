from odoo import _, api, fields, models


class PlanViewAgilePlaceBoard(models.Model):
    _name = "plan.view.agile.place.board"
    _description = "plan_view_agile_place_board"

    name = fields.Char()
