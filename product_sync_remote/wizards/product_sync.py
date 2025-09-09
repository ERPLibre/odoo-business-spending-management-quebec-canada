from odoo import api, fields, models


class ProductSyncWizard(models.TransientModel):
    _name = "product.sync.wizard"
    _description = "Assistant de synchronisation des produits"

    remote_url = fields.Char(required=True)
    remote_db = fields.Char(required=True)
    remote_user = fields.Char(required=True)
    remote_password = fields.Char(required=True)

    create_missing_attributes = fields.Boolean(default=True)
    update_existing = fields.Boolean(default=True)
    limit = fields.Integer(default=0)

    def action_start(self):
        job = self.env["product.sync.job"].create(
            {
                "remote_url": self.remote_url,
                "remote_db": self.remote_db,
                "remote_user": self.remote_user,
                "remote_password": self.remote_password,
                "create_missing_attributes": self.create_missing_attributes,
                "update_existing": self.update_existing,
                "limit": self.limit,
            }
        )
        # job.action_run()
        # Ouvrir le job
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.sync.job",
            "view_mode": "form",
            "res_id": job.id,
        }
