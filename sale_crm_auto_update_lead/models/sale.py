# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_quotation_send(self):
        status = super(SaleOrder, self).action_quotation_send()
        # If New or Qualified, update it to Proposition
        tpl_stage = (
            self.env.ref("crm.stage_lead1").id,
            self.env.ref("crm.stage_lead2").id,
        )
        if (
            self.opportunity_id
            and self.opportunity_id.stage_id.id in tpl_stage
        ):
            self.opportunity_id.stage_id = self.env.ref("crm.stage_lead3").id
        return status

    @api.multi
    def action_confirm(self):
        status = super(SaleOrder, self).action_confirm()
        # If New, Qualified or Proposition, update it to Won
        tpl_stage = (
            self.env.ref("crm.stage_lead1").id,
            self.env.ref("crm.stage_lead2").id,
            self.env.ref("crm.stage_lead3").id,
        )

        if (
            self.opportunity_id
            and self.opportunity_id.stage_id.id in tpl_stage
        ):
            self.opportunity_id.stage_id = self.env.ref("crm.stage_lead4").id
        return status
