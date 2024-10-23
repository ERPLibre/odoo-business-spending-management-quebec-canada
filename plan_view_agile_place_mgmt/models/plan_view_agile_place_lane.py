from odoo import _, api, fields, models


class PlanViewAgilePlaceLane(models.Model):
    _name = "plan.view.agile.place.lane"
    _description = "plan_view_agile_place_lane"

    name = fields.Char()
