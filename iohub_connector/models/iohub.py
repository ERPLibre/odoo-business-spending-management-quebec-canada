# -*- coding: utf-8 -*-
# Copyright 2021 Apulia Software s.r.l. (<info@apuliasoftware.it>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import Warning

from ..controllers.main import interface

_logger = logging.getLogger(__name__)


class IoHubBox(models.Model):

    _name = "iohub.box"

    controller = interface
    connect = fields.Boolean(default=False)
    name = fields.Char(string="Box name", help="Used also as client id")
    description = fields.Text(string="Description")
    broker_url = fields.Char(size=128)
    broker_port = fields.Integer()
    auth_required = fields.Boolean()
    iohub_username = fields.Char(size=32, string="Username")
    iohub_password = fields.Char(size=32, string="Password")
    iohub_topic_read = fields.Text(string="Topic from Read")
    iohub_topic_write = fields.Text(string="Topic from Write")

    company_ids = fields.Many2many(
        comodel_name="res.company", string="Allowed companies"
    )

    @api.multi
    def action_start_mqtt(self, topic=None):
        # if not topic:
        #     topic = self.iohub_topic
        # self.action_stop_mqtt()
        if self.connect:
            raise Warning(_("Already connect"))

        _logger.info("INFO: connecting to a mqtt broker!")
        data = {
            "host": self.broker_url,
            "port": self.broker_port,
            "ttl": 30,
        }
        if self.auth_required:
            self.controller.client.username_pw_set(
                username=self.iohub_username, password=self.iohub_password
            )
        if not self.connect:
            self.connect = True
            self.controller.client.on_message = self.on_message
            self.controller.push_task("connect", data=data)
            self.controller.push_task("start")
            _logger.info(">>>>>>>>>>>>{t}".format(t=self.iohub_topic_read))
            self.subscribe(self.iohub_topic_read)
        elif self.connect:
            _logger.info("INFO: already connect to a mqtt broker!")

    @api.multi
    def on_message(self, client, userdata, msg):
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            new_self = self.with_env(self.env(cr=new_cr))
            try:
                _logger.info("MESSAGE!!!")
                _logger.info(
                    ">> MQTT Received '{a}' from '{b}' topic".format(
                        a=msg.payload.decode(), b=msg.topic
                    )
                )
                iohub_msg_obj = new_self.env["iohub.message.queue"]
                payload = json.loads(msg.payload.decode())
                vals = {
                    "iohub_box_id": new_self.id,
                    "id_topic": msg.topic,
                    "payload": payload,
                }
                iohub_msg_obj.create(vals)
                new_cr.commit()
            except Exception:
                _logger.info("ABORT!!! NO JSON RECIVED")
                new_self._cr.rollback()
                new_self._cr.close()
                return False
            new_cr.close()

    @api.multi
    def publish(self, topic, msg):
        self.controller.push_task("publish", topic, msg)

    # method to stop mqtt service
    @api.multi
    def action_stop_mqtt(self):
        self.connect = False
        self.controller.push_task("stop")

    # method for subscribe to a Mqtt topic
    @api.multi
    def subscribe(self, topic="#"):
        _logger.info("INFO: subscribing to: {t}".format(t=topic))
        time.sleep(2)
        self.controller.push_task("subscribe", topic)

    def on_disconnect(self, client, userdata, rc):
        type(self).connect = False
        _logger.info("MQTT Client: Unexpected disconnection.")


class IoHubMessageQueue(models.Model):

    _name = "iohub.message.queue"
    _order = "id desc"

    iohub_box_id = fields.Many2one("iohub.box")
    payload = fields.Char()
    id_topic = fields.Char()
    datetime_msg = fields.Datetime()
    processed = fields.Boolean()
    write_value = fields.Boolean()
