#!/usr/bin/env python3
# © 2025 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)


from odoo import _, api, fields, models


class AsanaAgendrixActionLog(models.Model):
    _name = "asana.agendrix.action.log"
    _description = "asana association with agendrix, log the action"

    name = fields.Char(compute="_compute_name")

    asana_agendrix_id = fields.Many2one(comodel_name="asana.agendrix")

    asana_id_target_object = fields.Char()

    asana_id_empotency_key = fields.Char()

    asana_id_action_type = fields.Char()

    asana_id_action = fields.Char()

    asana_app_configuration_json = fields.Text()

    asana_expires_at = fields.Datetime()

    asana_id_project = fields.Char()

    asana_id_user = fields.Char()

    asana_id_workspace = fields.Char()

    has_different_configuration = fields.Boolean()

    execution_error = fields.Boolean()

    execution_error_reason = fields.Text()

    @api.depends(
        "asana_expires_at",
        "asana_id_target_object",
        "asana_id_user",
        "asana_id_action",
        "asana_id_project",
    )
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.asana_expires_at} - {rec.asana_id_target_object} - {rec.asana_id_user} - {rec.asana_id_action} - {rec.asana_id_project}"
