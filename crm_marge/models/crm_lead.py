# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class CrmMarge(models.Model):
    _inherit = "crm.lead"

    planned_revenue = fields.Monetary(
        "Expected Revenue",
        currency_field="company_currency",
        track_visibility="always",
        compute="_compute_planned_revenue",
        readonly=True,
    )
    cost = fields.Monetary(string="Cost", currency_field="company_currency")
    gross_margin = fields.Monetary(
        string="Gross margin", currency_field="company_currency"
    )
    gross_margin_percent = fields.Float(string="Gross margin %")
    markup_percent = fields.Float(
        string="Markup %", compute="_compute_markup_percent", readonly=True
    )

    @api.multi
    @api.depends("gross_margin", "cost")
    def _compute_markup_percent(self):
        for lead in self:
            if lead.cost:
                lead.markup_percent = 100.0 * lead.gross_margin / lead.cost
            else:
                lead.markup_percent = 0.0

    @api.multi
    @api.depends("gross_margin", "cost")
    def _compute_planned_revenue(self):
        for lead in self:
            lead.planned_revenue = lead.gross_margin + lead.cost

    @api.multi
    @api.onchange("gross_margin", "cost")
    def onchange_gross_margin(self):
        """
        Update gross_margin_percent with gross_margin
        Influence gross_margin_percent and planned_revenue
        """
        for lead in self:
            if lead.planned_revenue:
                lead.gross_margin_percent = (
                    100.0 * lead.gross_margin / lead.planned_revenue
                )
            else:
                lead.gross_margin_percent = 0.0

    @api.multi
    @api.onchange("gross_margin_percent")
    def onchange_gross_margin_percent(self):
        """
        Update gross_margin with gross_margin_percent
        Influence gross_margin and planned_revenue
        """
        for lead in self:
            if lead.gross_margin_percent >= 100.0:
                lead.gross_margin_percent = 99.999999

            lead.gross_margin = (
                lead.cost / (1 - (lead.gross_margin_percent / 100))
            ) - lead.cost
