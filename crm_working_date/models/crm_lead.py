# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    due_date = fields.Datetime(
        string="Due Date", help="Add the due date of the project."
    )
    start_date = fields.Datetime(
        string="Start Date", help="Add start date of the project."
    )
    duration_estimate_hour = fields.Integer(
        string="Duration Estimate Hour",
        help="The duration estimated in hour of the project.",
    )

    @api.multi
    @api.onchange("due_date", "start_date")
    def onchange_due_start_date(self):
        """
        Check if due_date is after start_date
        """
        for lead in self:
            warning = {}
            if lead.due_date and lead.start_date:
                # Need to support the same day
                if lead.start_date > lead.due_date:
                    warning = {
                        "title": _("Warning date error"),
                        "message": _("The due date is before the start date."),
                    }

            if warning:
                return {"warning": warning}
