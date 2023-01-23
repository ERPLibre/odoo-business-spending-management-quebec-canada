import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


# Fiscal Position Region Templates


class AccountFiscalPositionTemplate(models.Model):
    _name = "account.fiscal.position.region.template"
    _description = "Template for Fiscal Position Region"

    sequence = fields.Integer()
    account_fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position.template",
    )
    name = fields.Char(string="Fiscal Position Region Template", required=True)
    code = fields.Integer()
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s - %s" % (rec.code, rec.name)


# Fiscal Position Templates


class AccountFiscalPositionTemplate(models.Model):
    _inherit = "account.fiscal.position.template"
    _name = "account.fiscal.position.template"
    account_fiscal_position_region_ids = fields.One2many(
        string="Account fiscal position region Mapping",
        comodel_name="account.fiscal.position.region.template",
        inverse_name="account_fiscal_position_id",
    )
