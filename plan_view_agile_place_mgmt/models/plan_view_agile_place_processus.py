import datetime
import json
import logging
import os
import re

import requests

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceProcessus(models.Model):
    _name = "plan.view.agile.place.processus"
    _description = "plan_view_agile_place_processus"

    name = fields.Char()

    algo_key = fields.Selection(
        selection=[
            ("create_model", "Create Model"),
            ("send_sms_schedule", "Send SMS schedule"),
            (
                "send_reminder_sms_schedule_condition",
                "Send reminder SMS schedule condition",
            ),
            ("copy_cards", "Copy cards from lane to lane"),
        ],
        required=True,
        default="create_model",
        readonly=True,
    )

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
        related="board_id.session_id",
    )

    bind_custom_field = fields.Text()

    bind_field = fields.Text()

    default_value_model = fields.Text()

    ignore_warning_from_name = fields.Char(
        default="",
        help="Separate by ; for multiple, will ignore warning from his name.",
    )

    model_name = fields.Char()

    lane_name = fields.Char()

    fake_regex_lane = fields.Char()

    sms_message_prefix = fields.Text()

    sms_detect_card_type_msg_1 = fields.Text()

    location_type_msg = fields.Char()

    parent_lane_name = fields.Char()

    root_lane_name = fields.Char()

    copy_from_lane = fields.Char()

    copy_to_lane = fields.Char()

    clean_before_card_from_lane = fields.Boolean(
        help="Will delete all card when using from_lane"
    )

    sms_enable = fields.Boolean(related="session_id.sms_enable")

    sms_to_number_phone = fields.Char(help="Separate multiple with ;")

    sms_to_country = fields.Char(default="+1")

    sms_message_to_send = fields.Text()

    sms_debug = fields.Boolean(default=True)

    sms_limit_iteration = fields.Integer(
        help="0 is default, will be ignore and run."
    )

    sms_history_ids = fields.One2many(
        comodel_name="plan.view.agile.place.sms.history",
        inverse_name="processus_id",
        string="Processus",
    )

    board_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board",
        string="Board",
    )

    sub_lane_name = fields.Char(
        help=(
            "NOT SUPPORTED Optional, will search only into this lane and"
            " childs lane"
        )
    )

    type_card = fields.Char(
        help="Optional, search only with this type of card"
    )

    log_txt = fields.Text(string="Log")

    log_error_txt = fields.Text(string="Log error")

    @api.multi
    def action_clear_log(self):
        for rec in self:
            rec.log_txt = ""
            rec.log_error_txt = ""

    @api.multi
    def action_execute_send_sms(self):
        for rec in self:
            if not rec.session_id.sms_enable:
                continue

            to = (
                rec.session_id.sms_to_number_phone_default
                if not rec.sms_to_number_phone
                else rec.sms_to_number_phone
            )
            to_country = (
                rec.session_id.sms_to_country_default
                if not rec.sms_to_country
                else rec.sms_to_country
            )

            body = rec.sms_message_to_send

            value_sms = {
                "name": body,
                "to_number_phone_country": to_country,
                "to_number_phone": to,
                "from_number_phone_country": rec.session_id.sms_from_country,
                "from_number_phone": rec.session_id.sms_from_number_phone,
                "processus_id": rec.id,
            }
            if self.sms_debug and body:
                # Send single message
                sms_history_id = self.env[
                    "plan.view.agile.place.sms.history"
                ].create(value_sms)
                sms_history_id.send_sms(
                    rec.session_id.sms_api_url, rec.session_id.sms_api_token
                )
                return
            dct_sms_data = {"lst_data": []}
            rec.action_execute_algo(dct_sms_data=dct_sms_data)
            for i, dct_sms in enumerate(dct_sms_data.get("lst_data")):
                if not (
                    not rec.sms_limit_iteration or rec.sms_limit_iteration > i
                ):
                    continue
                to_country = (
                    dct_sms.get("to_country")
                    if dct_sms.get("to_country")
                    else rec.session_id.sms_to_country_default
                )
                body = dct_sms.get("body")
                if self.sms_debug:
                    # TODO missing user name
                    ir_employee = self.env["hr.employee"].search(
                        [("work_phone", "=", dct_sms.get("to"))], limit=1
                    )
                    send_to = to_country + dct_sms.get("to")
                    if ir_employee:
                        send_to = ir_employee.name + " " + send_to
                    body = f"DEBUG SEND TO [{send_to}]\n\n" + body
                msg_to = dct_sms.get("to") if not self.sms_debug else to
                value_sms["to_number_phone"] = msg_to
                value_sms["name"] = body
                sms_history_id = self.env[
                    "plan.view.agile.place.sms.history"
                ].create(value_sms)
                sms_history_id.send_sms(
                    rec.session_id.sms_api_url, rec.session_id.sms_api_token
                )

    @api.multi
    def action_execute_algo(self, ctx=None, dct_sms_data=None):
        for rec in self:
            if rec.log_txt is False:
                rec.log_txt = ""
            if rec.log_error_txt is False:
                rec.log_error_txt = ""

            if not rec.board_id:
                board_id = self.env["plan.view.agile.place.board"].search([])
                if len(board_id) != 1:
                    raise exceptions.Warning("Missing board_id")
                rec.board_id = board_id.id

            # First log
            msg_txt = (
                f"LOG Execute algo '{rec.algo_key}' -"
                f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt

            if rec.algo_key == "send_reminder_sms_schedule_condition":
                print("ok")
            if rec.algo_key == "copy_cards":
                # print(rec.copy_to_lane)
                # print(rec.copy_from_lane)
                # print(rec.root_lane_name)
                # print(rec.type_card)
                # print(rec.parent_lane_name)

                # TODO do refresh data for from lane et to lane

                if not rec.copy_to_lane:
                    # TODO raise error
                    pass
                lane_to_query = [
                    ("root_lane_name", "=", rec.root_lane_name),
                    ("parent_lane_name", "=", rec.parent_lane_name),
                    ("title", "in", rec.copy_to_lane.split(";")),
                ]
                lane_to_ids = self.env["plan.view.agile.place.lane"].search(
                    lane_to_query
                )

                if rec.clean_before_card_from_lane:
                    # get all cards to delete
                    card_to_delete_ids = self.env[
                        "plan.view.agile.place.card"
                    ].search([("lane_id", "in", lane_to_ids.ids)])
                    array_card_pvap = [
                        a.card_id_pvap for a in card_to_delete_ids
                    ]
                    if array_card_pvap:
                        data_delete = {"cardIds": array_card_pvap}
                        result = rec.board_id.session_id.request_api_delete(
                            "/io/card/", data=data_delete
                        )
                        if str(result[0])[0] != "2":
                            raise exceptions.Warning(
                                f"Receive request {result[0]} from delete all"
                                " cards from specific lane."
                            )
                        card_to_delete_ids.unlink()

                # Get lane from and lane to
                if not rec.copy_from_lane:
                    # TODO raise error
                    pass
                lst_copy_from_lane = rec.copy_from_lane.split(";")
                for copy_from_lane in lst_copy_from_lane:
                    card_from_query = [
                        ("root_lane_name", "=", rec.root_lane_name),
                        ("lane_name", "=", copy_from_lane),
                        ("lane_parent_name", "=", rec.parent_lane_name),
                    ]

                    card_from_ids = self.env[
                        "plan.view.agile.place.card"
                    ].search(card_from_query)
                    for lane_to_id in lane_to_ids:
                        for card_id in card_from_ids:
                            data = {
                                "copied_from_card_pvap": card_id.card_id_pvap,
                                "board_id": card_id.board_id.id,
                                "name": card_id.name,
                                "lane_id": lane_to_id.id,
                                "size": card_id.size,
                                "card_type_id": card_id.card_type_id.id,
                                "entete": card_id.entete,
                                "custom_fields": card_id.custom_fields,
                                "description": card_id.description,
                                "assigned_users": card_id.assigned_users,
                                "session_id": rec.session_id.id,
                            }
                            self.env["plan.view.agile.place.card"].create(data)

            if rec.algo_key == "send_sms_schedule":
                if rec.fake_regex_lane == "jour d/m":
                    lane_ids = self.env["plan.view.agile.place.lane"].search(
                        [("board_id", "=", rec.board_id.id)]
                    )
                    regex = (
                        r"(?P<jour>[A-Z]+)\s+(?P<journee>\d+)/(?P<mois>\d+)"
                    )
                    for lane_id in lane_ids:
                        result = re.search(regex, lane_id.title)
                        if result:
                            # data = {
                            #     "jour": result.group("jour"),
                            #     "journee": int(result.group("journee")),
                            #     "mois": int(result.group("mois")),
                            # }
                            next_day = self.return_next_open_day(
                                datetime.date.today()
                            )
                            if next_day.month == int(
                                result.group("mois")
                            ) and next_day.day == int(result.group("journee")):
                                lst_query = [
                                    ("board_id", "=", rec.board_id.id),
                                    (
                                        "lane_id",
                                        "in",
                                        lane_id.child_lane_ids.ids,
                                    ),
                                ]
                                if rec.type_card:
                                    lst_type_card = rec.type_card.split(";")
                                    type_card_ids = self.env[
                                        "plan.view.agile.place.card.type"
                                    ].search(
                                        [
                                            ("name", "in", lst_type_card),
                                            ("board_id", "=", rec.board_id.id),
                                        ]
                                    )
                                    lst_query.append(
                                        (
                                            "card_type_id",
                                            "in",
                                            type_card_ids.ids,
                                        )
                                    )
                                card_ids = self.env[
                                    "plan.view.agile.place.card"
                                ].search(lst_query)
                                # TODO switch for ready production
                                i_msg = 0
                                for card_id in card_ids:
                                    i_msg += 1
                                    # TODO validate double employee, validate time or raise error if missing time
                                    # Find employee
                                    employee_id = self.env[
                                        "hr.employee"
                                    ].search(
                                        [("name", "=", card_id.name.title())],
                                        limit=1,
                                    )
                                    if not employee_id.work_phone:
                                        msg_txt = (
                                            "ERR Employee"
                                            f" '{employee_id.name}' missing"
                                            " phone number\n"
                                        )
                                        rec.log_txt += msg_txt
                                        rec.log_error_txt += msg_txt
                                        continue
                                    msg_sms_log_debug = (
                                        f"PHONE: {employee_id.work_phone}\n"
                                    )
                                    msg_sms = (
                                        ""
                                        if not rec.sms_message_prefix
                                        else rec.sms_message_prefix
                                    )
                                    # Find contact location
                                    datetime_msg_str = lane_id.title.title()
                                    if card_id.size:
                                        datetime_msg_str += (
                                            f" à {card_id.size}h"
                                        )
                                    msg_sms += (
                                        "Tu travailles le"
                                        f" {datetime_msg_str}, au"
                                        f" {rec.location_type_msg} «{card_id.lane_name}»"
                                    )
                                    partner_id = self.env[
                                        "res.partner"
                                    ].search(
                                        [("name", "=", card_id.lane_name)],
                                        limit=1,
                                    )
                                    # Detect msg 1 from card type
                                    if rec.sms_detect_card_type_msg_1:
                                        lst_type_card = rec.sms_detect_card_type_msg_1.split(
                                            ";"
                                        )
                                        type_card_msg_1_ids = self.env[
                                            "plan.view.agile.place.card.type"
                                        ].search(
                                            [
                                                ("name", "in", lst_type_card),
                                                (
                                                    "board_id",
                                                    "=",
                                                    rec.board_id.id,
                                                ),
                                            ]
                                        )
                                        if type_card_msg_1_ids:
                                            lst_query = [
                                                (
                                                    "board_id",
                                                    "=",
                                                    rec.board_id.id,
                                                ),
                                                (
                                                    "lane_id",
                                                    "in",
                                                    card_id.lane_id.ids,
                                                ),
                                                (
                                                    "card_type_id",
                                                    "in",
                                                    type_card_msg_1_ids.ids,
                                                ),
                                            ]
                                            card_msg_1_ids = self.env[
                                                "plan.view.agile.place.card"
                                            ].search(lst_query)

                                            if len(card_msg_1_ids) > 1:
                                                msg_txt = (
                                                    "ERR Double card"
                                                    f" '{lst_type_card}' into"
                                                    " lane"
                                                    f" '{card_id.lane_name}'"
                                                )
                                                rec.log_txt += msg_txt
                                                rec.log_error_txt += msg_txt
                                            if card_msg_1_ids:
                                                if card_msg_1_ids.size:
                                                    msg_sms += (
                                                        " + Couler à"
                                                        f" {card_msg_1_ids.size}h."
                                                    )
                                                else:
                                                    msg_sms += " + Couler."
                                    if partner_id:
                                        street_map = partner_id.street.replace(
                                            " ", "%20"
                                        )
                                        msg_sms += (
                                            "\nÀ l'adresse suivante : \n\n"
                                            f"{partner_id.street}\n\nhttps://www.google.ca/maps/place/{street_map}"
                                        )
                                    # Detect
                                    # TODO detect coulee type
                                    # detect taille coule + taille actuel

                                    msg_txt = (
                                        f"\nSMS({i_msg})"
                                        f" '{msg_sms_log_debug}{msg_sms}'\n\n"
                                    )
                                    rec.log_txt += msg_txt

                                    if dct_sms_data:
                                        dct_sms_data["lst_data"].append(
                                            {
                                                "to": employee_id.work_phone,
                                                "body": msg_sms,
                                            }
                                        )
                else:
                    msg_txt = (
                        f"ERR processus '{rec.name}' missing field"
                        " 'fake_regex_lane'\n"
                    )
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
            elif rec.algo_key == "create_model":
                root_lane_id = self.env["plan.view.agile.place.lane"].search(
                    [("title", "=", rec.root_lane_name)]
                )
                lane_query = [("root_lane_id", "=", root_lane_id.id)]
                if rec.lane_name:
                    lane_query.append(("title", "=", rec.lane_name))
                lane_ids = self.env["plan.view.agile.place.lane"].search(
                    lane_query
                )
                lst_query = [("lane_id", "in", lane_ids.ids)]
                if rec.type_card:
                    lst_type_card = rec.type_card.split(";")
                    type_card_ids = self.env[
                        "plan.view.agile.place.card.type"
                    ].search(
                        [
                            ("name", "in", lst_type_card),
                            ("board_id", "=", rec.board_id.id),
                        ]
                    )
                    lst_query.append(("card_type_id", "in", type_card_ids.ids))
                card_ids = self.env["plan.view.agile.place.card"].search(
                    lst_query
                )

                lst_existing_name = []
                dct_custom_field_to_field_name = json.loads(
                    rec.bind_custom_field
                )
                for card_id in card_ids:
                    # Check doublon from card
                    if card_id.name in lst_existing_name:
                        if (
                            not card_id.name
                            in rec.ignore_warning_from_name.split(";")
                        ):
                            msg_txt = (
                                f"WAR '{rec.model_name}' Ignore duplicate name"
                                f" '{card_id.name}'\n"
                            )
                            rec.log_txt += msg_txt
                            rec.log_error_txt += msg_txt
                        continue
                    else:
                        lst_existing_name.append(card_id.name)
                    # Create it
                    if rec.default_value_model:
                        new_model_value = json.loads(rec.default_value_model)
                    else:
                        new_model_value = {}
                    if rec.bind_field:
                        dct_model_value = json.loads(rec.bind_field)
                        for k, v in dct_model_value.items():
                            if v == "name":
                                name = (
                                    card_id.name
                                    if not card_id.name.isupper()
                                    else card_id.name.title()
                                )
                            else:
                                name = getattr(card_id, v)
                            new_model_value[k] = name
                    name = new_model_value.get("name")
                    # Custom Fields
                    if not card_id.custom_fields:
                        card_id.update_card_details()
                        dct_detail = json.loads(card_id.card_details)
                        lst_custom_field = dct_detail.get("customFields")
                    else:
                        lst_custom_field = json.loads(card_id.custom_fields)
                    if not lst_custom_field:
                        msg_txt = (
                            f"ERR '{rec.model_name}' Missing custom fields\n"
                        )
                        rec.log_txt += msg_txt
                        rec.log_error_txt += msg_txt
                        continue
                    # Bind value
                    for (
                        custom_field_name,
                        field_name,
                    ) in dct_custom_field_to_field_name.items():
                        lst_find_lst_custom_field = [
                            a
                            for a in lst_custom_field
                            if a.get("label") == custom_field_name
                        ]
                        if not lst_find_lst_custom_field:
                            if not name in rec.ignore_warning_from_name.split(
                                ";"
                            ):
                                msg_txt = (
                                    f"WAR '{rec.model_name}' Missing custom"
                                    f" field '{custom_field_name}' about name"
                                    f" '{name}' id '{card_id.card_id_pvap}."
                                    " Try auto-update\n"
                                )
                            rec.log_txt += msg_txt
                            rec.log_error_txt += msg_txt

                            card_id.update_card_details()
                            dct_detail = json.loads(card_id.card_details)
                            lst_custom_field = dct_detail.get("customFields")
                            lst_find_lst_custom_field = [
                                a
                                for a in lst_custom_field
                                if a.get("label") == custom_field_name
                            ]

                        for dct_custom_field in lst_find_lst_custom_field:
                            value = dct_custom_field.get("value")
                            if value:
                                new_model_value[field_name] = value
                            else:
                                if (
                                    not name
                                    in rec.ignore_warning_from_name.split(";")
                                ):
                                    msg_txt = (
                                        f"WAR '{rec.model_name}' Missing value"
                                        " for custom field"
                                        f" '{custom_field_name}' about name"
                                        f" '{name}' id"
                                        f" '{card_id.card_id_pvap}\n"
                                    )
                                    rec.log_txt += msg_txt
                                    rec.log_error_txt += msg_txt

                    # Update or create
                    new_model_id = self.env[rec.model_name].search(
                        [("name", "=", name)], limit=1
                    )
                    if new_model_id:
                        msg_txt = (
                            f"LOG Update '{rec.model_name}' with name"
                            f" '{name}' id '{card_id.card_id_pvap}\n"
                        )
                        rec.log_txt += msg_txt
                        new_model_id.write(new_model_value)
                    else:
                        msg_txt = (
                            f"LOG Create '{rec.model_name}' with name"
                            f" '{name}' id '{card_id.card_id_pvap}'\n"
                        )
                        rec.log_txt += msg_txt
                        new_model_id = self.env[rec.model_name].create(
                            new_model_value
                        )
                        # TODO send id to client, can visualize all created data
                        #  or maybe not, too much link into database, maybe create html link
                rec.log_txt += "\n"
                rec.log_error_txt += "\n"

                # TODO generate SMS message with adresse and job and employ
            _logger.info(f"End of execution processus '{rec.algo_key}'")

    @staticmethod
    def return_next_open_day(date):
        # TODO support weekday, check next day from calendar into system
        prochain_jour = date + datetime.timedelta(days=1)

        while prochain_jour.weekday() in (5, 6):  # 5 = saturday, 6 = sunday
            prochain_jour += datetime.timedelta(days=1)

        return prochain_jour
