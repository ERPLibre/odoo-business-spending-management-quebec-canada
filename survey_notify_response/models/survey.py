from odoo import api, fields, models, tools, SUPERUSER_ID, _


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    @api.multi
    def write(self, vals):
        rec = super().write(vals)
        if self.state == "done":
            self.survey_id.sudo().with_context(
                {"token": self.token, "lang": self.env.context.get("lang")}
            ).message_post_with_template(
                self.env.ref(
                    "survey_notify_response.email_template_notify_create_survey_survey"
                ).id,
            )
        return rec
