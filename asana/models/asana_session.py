from odoo import _, api, fields, models


class AsanaSession(models.Model):
    _name = "asana.session"
    _description = "asana_session"

    name = fields.Char()
