import datetime
import json
import logging
import re
import time
from urllib.parse import quote

from pytz import timezone

try:
    from randomwordfr import RandomWordFr
except ImportError:
    RandomWordFr = None


from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceProcessus(models.Model):
    _name = "plan.view.agile.place.processus"
    _description = "plan_view_agile_place_processus"

    name = fields.Char()

    algo_key = fields.Selection(
        selection=[
            ("create_card_from_model", "Build cards into PVAP"),
            ("create_new_board", "Create new board"),
            ("create_model_from_card", "Create Model from Card"),
            ("create_model_from_lane", "Create Model from Lane"),
            ("send_sms_schedule", "Send SMS schedule"),
            (
                "send_reminder_sms_schedule_condition",
                "Send reminder SMS schedule condition",
            ),
            ("copy_cards", "Copy cards from lane to lane"),
            ("delete_cards", "Delete cards"),
            ("bind_create_card", "Bind Create card"),
            ("bind_delete_card", "Bind Delete card"),
        ],
        required=True,
        default="create_model_from_card",
        readonly=True,
    )

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )

    bind_custom_field = fields.Text(
        help="Contain JSON, key is custom field and value is field name"
    )

    bind_required_field_list = fields.Text(
        help=(
            "Contain JSON of list, when required, will show warning if missing"
            " value."
        )
    )

    filter_field = fields.Text(
        help=(
            "Contain JSON, key is field name, value depend on type. Selection"
            " will be a boolean filter."
        )
    )

    bind_field = fields.Text()

    default_value_model = fields.Text()

    ignore_warning_from_name = fields.Char(
        default="",
        help="Separate by ; for multiple, will ignore warning from his name.",
    )

    model_name = fields.Char()

    model_fetch_record = fields.Char()

    duplicate_multiple_time = fields.Integer(
        default=1, help="Will repeat the duplication if higher then 1"
    )

    model_filter_hr_empoyee_job_type = fields.Char()

    record_id_i = fields.Integer(
        string="Record index",
        help="The record identifiant to be use from binding.",
    )

    lane_name = fields.Char()

    fake_regex_lane = fields.Char(help="Expect {'model': type_card_name}")

    type_card_bind = fields.Char()

    delay_in_day = fields.Integer()

    ignore_run_depend_processus = fields.Boolean(
        help="Enable to accelerate development to ignore execute update processus dependency."
    )

    is_root_lane = fields.Boolean(
        help="Enable when the cards to extract is inside the root lane, because a root lane has no parent lane."
    )

    is_disabled = fields.Boolean(
        help="When true, the processus will not execute."
    )

    compute_model_fsm_location = fields.Boolean(
        help="Associate with model res.partner, will create fsm.location associate with partner"
    )

    compute_model_fsm_person = fields.Boolean(
        help="Associate with model hr.employee, will create fsm.person associate with employee"
    )

    force_update_after_create = fields.Boolean(
        help="Sometime, value need to be update after creation, because some compute broke it."
    )

    ignore_weekend = fields.Boolean()

    description = fields.Text()

    sms_message_prefix = fields.Text()

    sms_summary_phone = fields.Char(
        help=(
            "Separate by ; for multiple SMS destination. Will send a summary"
            " about the notification SMS for employee"
        )
    )

    sms_detect_card_type_msg_1 = fields.Text()

    location_type_msg = fields.Char()

    lane_parent_name = fields.Char()

    lane_root_name = fields.Char()

    copy_from_lane = fields.Char()

    copy_to_lane = fields.Char()

    clean_before_card_from_lane = fields.Boolean(
        help="Will delete all card when using from_lane"
    )

    sms_enable = fields.Boolean(related="session_id.sms_enable")

    sms_to_number_phone = fields.Char(help="Separate multiple with ;")

    sms_to_country = fields.Char(default="+1")

    sms_message_to_send = fields.Text()

    sms_debug = fields.Boolean()

    sms_in_test_mode = fields.Boolean(help="Enable to fake sending SMS")

    force_update_model = fields.Boolean(
        help="Will force to update model when sync with another lane."
    )

    sms_limit_iteration = fields.Integer(
        help="0 is default, will be ignore and run."
    )

    sms_history_ids = fields.One2many(
        comodel_name="plan.view.agile.place.sms.history",
        inverse_name="processus_id",
        string="SMS history",
    )

    board_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board",
        string="Board",
    )

    # sub_lane_name = fields.Char(
    #     help=(
    #         "NOT SUPPORTED Optional, will search only into this lane and"
    #         " childs lane"
    #     )
    # )

    type_card = fields.Char(
        help="Optional, search only with this type of card"
    )

    new_board_name = fields.Char(
        help="The name of the new board, need a %s inside for the date"
    )

    type_template_board_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board.type",
        string="Type Board depend",
        help="Will duplicate this board and fill it.",
    )

    type_board_depend_ids = fields.Many2many(
        comodel_name="plan.view.agile.place.board.type",
        relation="type_board_ids_plan_view_agile_place_processus_rel",
        string="Type template Board",
        help="This is optional, the system will check if has depend, if yes, will force to sync this board to operate processus.",
    )

    log_txt = fields.Text(string="Log")

    log_error_txt = fields.Text(string="Log error")

    depend_process_ids = fields.Many2many(
        comodel_name="plan.view.agile.place.processus",
        relation="plan_view_agile_place_processus_depend",
        column1="process_id1",
        column2="process_depend_id2",
        string="Depend Process",
        help="Will execute depend process before execute this process.",
    )

    process_execute_after_ids = fields.Many2many(
        comodel_name="plan.view.agile.place.processus",
        relation="plan_view_agile_place_processus_execute_after",
        column1="process_id1",
        column2="process_depend_id2",
        string="Process execute after",
        help="Will execute process after execute this process.",
    )

    def action_clear_log(self):
        for rec in self:
            rec.log_txt = ""
            rec.log_error_txt = ""

    def action_clear_log_depend(self):
        self.action_clear_log()
        for rec in self:
            for process_id in rec.depend_process_ids:
                process_id.action_clear_log_depend()

    def action_execute_send_sms(self):
        if RandomWordFr:
            rw = RandomWordFr()
            group_execution_name = (
                rw.get().get("word")
                + " "
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            group_execution_name = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        for rec in self:
            if not rec.session_id.sms_enable or rec.is_disabled:
                continue

            summary_final_msg = rec.sms_message_prefix
            summary_msg = ""
            sms_history_ids = self.env["plan.view.agile.place.sms.history"]

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
                "group_execution_name": group_execution_name,
                "session_id": rec.session_id.id,
            }
            if self.sms_debug and body:
                # Send single message
                sms_history_id = self.env[
                    "plan.view.agile.place.sms.history"
                ].create(value_sms)
                sms_history_id.send_sms()
                return
            dct_sms_data = {"lst_data": []}
            # TODO the algorith can create data into a new model, like this, the execution will be more fast
            rec.action_execute_algo(dct_sms_data=dct_sms_data)
            lst_data = dct_sms_data.get("lst_data")
            date_msg_str = ""
            for i, dct_sms in enumerate(lst_data):
                if not (
                    not rec.sms_limit_iteration or rec.sms_limit_iteration > i
                ):
                    continue
                if not date_msg_str:
                    date_msg_str = dct_sms.get("date")
                summary_msg += f"#{i+1} {dct_sms.get('summary')}\n"
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
                sms_history_id.send_sms()
                sms_history_ids += sms_history_id
            # Send summary SMS
            summary_final_msg += f"Sommaire ({len(lst_data)} SMS) {date_msg_str}\n{summary_msg}".strip()
            rec.log_txt += "\n" + summary_final_msg + "\n"
            for to_summary in rec.sms_summary_phone.split(";"):
                value_sms = {
                    "name": summary_final_msg,
                    "to_number_phone_country": to_country,
                    "to_number_phone": to_summary,
                    "from_number_phone_country": rec.session_id.sms_from_country,
                    "from_number_phone": rec.session_id.sms_from_number_phone,
                    "processus_id": rec.id,
                    "group_execution_name": group_execution_name,
                    "session_id": rec.session_id.id,
                }
                sms_history_id = self.env[
                    "plan.view.agile.place.sms.history"
                ].create(value_sms)
                sms_history_id.send_sms()

    def action_execute_algo(self, ctx=None, dct_sms_data=None):
        for rec in self:
            if rec.is_disabled:
                continue

            start_time = time.time()

            if rec.log_txt is False:
                rec.log_txt = ""
            if rec.log_error_txt is False:
                rec.log_error_txt = ""

            if (
                not rec.board_id
                and rec.type_board_depend_ids
                and not rec.ignore_run_depend_processus
            ):
                str_board_type = ",".join(
                    [a.name for a in rec.type_board_depend_ids]
                )
                if len(rec.type_board_depend_ids) > 1:
                    _logger.error(
                        "Support only 1 type of board at this moment."
                    )
                for type_board_id in rec.type_board_depend_ids:
                    for board_id in rec.session_id.board_ids:
                        if type_board_id in board_id.type_board_ids:
                            rec.board_id = board_id.id
                            break
                if not rec.board_id:
                    raise ValueError(
                        f"Cannot find board_id associate with type '{str_board_type}'."
                    )
            # First log
            user_timezone = timezone(self.env.user.tz or "UTC")
            hour_now = datetime.datetime.now(user_timezone)
            delay_timezone = hour_now.utcoffset().total_seconds() / 3600
            diff_hour_timezone = int(delay_timezone)
            msg_txt = (
                f"LOG Execute algo '{rec.algo_key}' '{rec.name}' -"
                f" {datetime.datetime.now().astimezone(user_timezone).strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt
            _logger.info(msg_txt.strip())
            ctx = dict(self.env.context)
            ctx.update({"lst_sync_lane_id_pvap": []})

            # Execute dependencies before
            if rec.depend_process_ids:
                lst_processus_executed = []
                for process_id in rec.depend_process_ids:
                    if "lst_processus_executed" in ctx:
                        lst_processus_executed = (
                            ctx["lst_processus_executed"]
                            + lst_processus_executed
                        )
                    if process_id.name not in lst_processus_executed:
                        lst_processus_executed.append(process_id.name)
                        msg_txt = f"Begin execution depend algo '{process_id.name}'\n"
                        _logger.info(msg_txt)
                        rec.log_txt += msg_txt
                        ctx.update(
                            {"lst_processus_executed": lst_processus_executed}
                        )
                        process_id.with_context(ctx).action_execute_algo()
                        rec.log_txt += process_id.log_txt
                        rec.log_error_txt += process_id.log_error_txt
                    else:
                        _logger.warning(
                            f"Ignore second execution of process '{process_id.name}'"
                        )

            # Compute variable
            dct_custom_field_to_field_name = {}
            if rec.bind_custom_field:
                dct_custom_field_to_field_name = json.loads(
                    rec.bind_custom_field
                )
            lst_bind_required_field_list = []
            if rec.bind_required_field_list:
                lst_bind_required_field_list = json.loads(
                    rec.bind_required_field_list
                )

            if rec.algo_key == "copy_cards":
                # print(rec.copy_to_lane)
                # print(rec.copy_from_lane)
                # print(rec.lane_root_name)
                # print(rec.type_card)
                # print(rec.lane_parent_name)

                # TODO do refresh data for from lane et to lane

                if not rec.copy_to_lane:
                    # TODO raise error
                    pass
                lane_to_query = [
                    ("lane_root_name", "=", rec.lane_root_name),
                    ("lane_parent_name", "=", rec.lane_parent_name),
                    (
                        "title",
                        "in",
                        rec.copy_to_lane.split(";"),
                        ("board_id", "=", rec.board_id.id),
                    ),
                ]
                lane_to_ids = self.env["plan.view.agile.place.lane"].search(
                    lane_to_query
                )

                if rec.clean_before_card_from_lane:
                    # get all cards to delete
                    card_to_delete_ids = self.env[
                        "plan.view.agile.place.card"
                    ].search(
                        [
                            ("lane_id", "in", lane_to_ids.ids),
                            ("board_id", "=", rec.board_id.id),
                        ]
                    )
                    card_to_delete_ids.enabled_bind = True
                    card_to_delete_ids.unlink()

                # Get lane from and lane to
                if not rec.copy_from_lane:
                    # TODO raise error
                    pass
                lst_copy_from_lane = rec.copy_from_lane.split(";")
                for copy_from_lane in lst_copy_from_lane:
                    card_from_query = [
                        ("lane_root_name", "=", rec.lane_root_name),
                        ("lane_name", "=", copy_from_lane),
                        ("lane_parent_name", "=", rec.lane_parent_name),
                        ("board_id", "=", rec.board_id.id),
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

            elif rec.algo_key == "send_reminder_sms_schedule_condition":
                # TODO maybe can search employee information
                pass

            elif rec.algo_key == "delete_cards":
                card_ids = rec.search_cards_from_processus()
                if card_ids.exists():
                    card_ids.enabled_bind = True
                    card_ids.unlink()

            elif rec.algo_key == "send_sms_schedule":
                lst_filter_field = json.loads(rec.filter_field)
                if rec.fake_regex_lane == "jour d/m":
                    lane_ids = self._get_lane_from_regex_day(
                        rec, user_timezone
                    )

                    for lane_id in lane_ids:
                        # Find root lane
                        # Force auto refresh root lane
                        lane_id.action_sync_cards()

                        lst_query = [
                            ("board_id", "=", rec.board_id.id),
                            (
                                "lane_id",
                                "in",
                                lane_id.lane_child_ids.ids,
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
                            # TODO validate double employee, validate time or raise error if missing time
                            card_name = card_id.name.strip()
                            if rec.force_update_model:
                                employee_id = rec.create_model_from_card(
                                    card_id,
                                    dct_custom_field_to_field_name,
                                    lst_bind_required_field_list,
                                )
                            else:
                                # Find employee
                                employee_id = self.env["hr.employee"].search(
                                    [("name", "=", card_name.title())],
                                    limit=1,
                                )

                            ignore_this_employee = False
                            if lst_filter_field:
                                ignore_this_employee = not any(
                                    [
                                        getattr(employee_id, a)
                                        for a in lst_filter_field
                                    ]
                                )
                            if ignore_this_employee:
                                rec.add_log_time_execution(start_time)
                                continue

                            if not employee_id:
                                msg_txt = (
                                    "ERR Missing employee card"
                                    f" '{card_name}'. Check lane_root"
                                    f" '{card_id.lane_root_name}',"
                                    " lane_parent"
                                    f" '{card_id.lane_parent_name}',"
                                    f" lane '{card_id.lane_name}'\n"
                                )
                                rec.log_txt += msg_txt
                                rec.log_error_txt += msg_txt
                                _logger.error(msg_txt.strip())
                                rec.add_log_time_execution(start_time)
                                continue
                            elif not employee_id.work_phone:
                                msg_txt = (
                                    "ERR Employee"
                                    f" '{employee_id.name}' missing"
                                    " phone number\n"
                                )
                                rec.log_txt += msg_txt
                                rec.log_error_txt += msg_txt
                                _logger.error(msg_txt.strip())
                                rec.add_log_time_execution(start_time)
                                continue
                            i_msg += 1
                            msg_sms_log_debug = (
                                f"PHONE: {employee_id.work_phone}\n"
                            )
                            msg_sms = (
                                ""
                                if not rec.sms_message_prefix
                                else rec.sms_message_prefix + " "
                            )
                            msg_summary_sms = ""
                            # Find contact location
                            date_msg_str = lane_id.title.title()
                            datetime_msg_str = lane_id.title.title()
                            msg_time = ""
                            if card_id.size:
                                msg_time = f" à {card_id.size}h"
                                datetime_msg_str += msg_time
                            msg_sms += (
                                f"{employee_id.name}, tu travailles le"
                                f" {datetime_msg_str}, au"
                                f" {rec.location_type_msg} «{card_id.lane_name}»"
                            )
                            msg_summary_sms += f"{employee_id.name} «{card_id.lane_name}»{msg_time}"
                            partner_id = self.env["res.partner"].search(
                                [("name", "=", card_id.lane_name)],
                                limit=1,
                            )
                            if not partner_id:
                                msg_txt = f"ERR missing partner associate with card {card_id.lane_name}\n"
                                rec.log_txt += msg_txt
                                rec.log_error_txt += msg_txt
                                _logger.error(msg_txt.strip())
                            # Detect msg 1 from card type
                            if rec.sms_detect_card_type_msg_1:
                                lst_type_card = (
                                    rec.sms_detect_card_type_msg_1.split(";")
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
                                        _logger.error(msg_txt.strip())
                                    if card_msg_1_ids:
                                        if card_msg_1_ids.size:
                                            msg_coule = (
                                                " + Coulée à"
                                                f" {card_msg_1_ids.size}h."
                                            )
                                        else:
                                            msg_coule = " + Coulée."
                                        msg_sms += msg_coule
                                        msg_summary_sms += msg_coule
                            if partner_id:
                                street_map = quote(partner_id.street)
                                msg_sms += (
                                    "\nÀ l'adresse suivante : \n\n"
                                    f"{partner_id.street}\n\nhttps://www.google.ca/maps/place/{street_map}"
                                )
                            # Detect
                            # TODO detect coulee type
                            # detect taille coule + taille actuel

                            msg_txt = (
                                f"\nSMS({i_msg}) {msg_sms_log_debug}"
                                f"«\n{msg_sms}\n»\n"
                            )
                            rec.log_txt += msg_txt

                            if dct_sms_data:
                                dct_sms_data["lst_data"].append(
                                    {
                                        "to": employee_id.work_phone,
                                        "body": msg_sms,
                                        "summary": msg_summary_sms,
                                        "date": date_msg_str,
                                    }
                                )
                else:
                    msg_txt = (
                        f"ERR processus '{rec.name}' missing field"
                        " 'fake_regex_lane'\n"
                    )
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())
            elif rec.algo_key == "create_model_from_lane":
                # This will find the lane_root
                # TODO problème avec utc?
                monday_day = self.return_monday_day(
                    datetime.datetime.now().astimezone(user_timezone),
                ).replace(hour=0, minute=0, second=0, microsecond=0)
                lane_ids = self._get_lane_from_regex_week(rec, user_timezone)
                if len(lane_ids) > 1:
                    multi_lane_name = ",".join([a.title for a in lane_ids])
                    msg_txt = f"ERR Find {len(lane_ids)} lanes with the regex '{multi_lane_name}'.\n"
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())
                elif len(lane_ids) == 0:
                    msg_txt = (
                        f"ERR Cannot found lane with regex of next day.\n"
                    )
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())
                    rec.add_log_time_execution(start_time)
                    continue
                rec.lane_root_name = lane_ids[0].title
                card_ids = rec.search_cards_from_processus()
                for card_id in card_ids:
                    # TODO bug name, fix that!
                    # location_id = self.env["fsm.location"].search(
                    #     [("name", "like", card_id.lane_name)], limit=1
                    # )
                    location_ids = self.env["fsm.location"].search([])
                    location_id = None
                    for a_location_id in location_ids:
                        # TODO this is not good, hardcoded from data client, need a dynamic way
                        if a_location_id.name[:5] == card_id.lane_name[:5]:
                            location_id = a_location_id
                    if not location_id:
                        msg_txt = f"WARN Cannot found fsm.location with name '{card_id.lane_name}'.\n"
                        rec.log_txt += msg_txt
                        rec.log_error_txt += msg_txt
                        _logger.warning(msg_txt.strip())
                        rec.add_log_time_execution(start_time)
                        continue
                    # Get weekdate
                    regex = (
                        r"(?P<jour>[A-Z]+)\s+(?P<journee>\d+)/(?P<mois>\d+)"
                    )
                    result = re.search(regex, card_id.lane_parent_name)
                    diff_date = int(result.group("journee")) - monday_day.day
                    # TODO this is an hack, need to retrieve the exact day with month and day
                    actual_day = monday_day + datetime.timedelta(
                        days=diff_date
                    )
                    next_day = actual_day + datetime.timedelta(days=1)
                    fsm_order_id = self.env["fsm.order"].search(
                        [
                            ("location_id", "=", location_id.id),
                            ("scheduled_date_start", ">=", actual_day),
                            ("scheduled_date_start", "<", next_day),
                        ],
                        limit=1,
                    )
                    actual_day_time_work = actual_day + datetime.timedelta(
                        hours=7 + diff_hour_timezone
                    )
                    if not fsm_order_id:
                        # Create a new one
                        fsm_order_vals = {
                            "name": card_id.lane_name,
                            "location_id": location_id.id,
                            "scheduled_date_start": actual_day_time_work.replace(
                                tzinfo=None
                            ),
                            "scheduled_duration": 6,
                        }
                        fsm_order_id = self.env["fsm.order"].create(
                            fsm_order_vals
                        )
                    # Add this card
                    json_type_card_bind = json.loads(rec.type_card_bind)
                    lst_card_type_name = json_type_card_bind.get(
                        "fsm.person"
                    ).split(";")
                    if lst_card_type_name:
                        for card_type_name in lst_card_type_name:
                            card_type_id = self.env[
                                "plan.view.agile.place.card.type"
                            ].search(
                                [
                                    ("name", "=", card_type_name),
                                    ("board_id", "=", rec.board_id.id),
                                ]
                            )
                            if (
                                card_type_id
                                and card_id.card_type_id == card_type_id
                            ):
                                fsm_person_id = self.env["fsm.person"].search(
                                    [("name", "=", card_id.name.title())],
                                    limit=1,
                                )
                                if fsm_person_id:
                                    fsm_order_id.write(
                                        {"person_ids": [(4, fsm_person_id.id)]}
                                    )
            elif rec.algo_key == "create_new_board":
                # Algorithm description :
                # 1. duplicate board with all cards
                # 2. fill the board
                date_new_timezone = datetime.datetime.now().astimezone(
                    user_timezone
                )
                str_date_new_timezone = date_new_timezone.strftime(
                    "%Y/%m/%d %H:%M:%S"
                )
                new_board_name = rec.new_board_name % str_date_new_timezone

                # Find board template
                board_template_id = self.env[
                    "plan.view.agile.place.board"
                ].search(
                    [("type_board_ids", "in", rec.type_template_board_id.ids)]
                )

                if not board_template_id:
                    msg_txt = f"ERR Cannot find board type '{rec.type_template_board_id.name}' to duplicate it.\n"
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())
                    rec.add_log_time_execution(start_time)
                    continue

                title = new_board_name
                if not rec.session_id.production_enabled:
                    title = f"TEST {title}"

                data = {
                    "title": title,
                    "fromBoardId": board_template_id.board_id_pvap,
                    "includeCards": True,
                    "includeExistingUsers": True,
                    "excludeCompletedAndArchiveViolations": True,
                    "baseWipOnCardSize": True,
                }

                status, response = rec.session_id.request_api_post(
                    "/io/board", data=data
                )
                if str(status)[0] != "2":
                    msg_txt = f"ERR Cannot create board.\n"
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())
                    rec.add_log_time_execution(start_time)
                    continue
                board_value = {
                    "name": title,
                    "session_id": rec.session_id.id,
                    "board_id_pvap": response.get("id"),
                    "type_board_ids": [
                        (6, 0, rec.board_id.type_board_ids.ids)
                    ],
                }
                board_id = self.env["plan.view.agile.place.board"].create(
                    board_value
                )
                board_id.action_sync()

                # Execute processus of adding cards
                for process_id in rec.process_execute_after_ids:
                    process_id.board_id = board_id.id
                    process_id.action_execute_algo()

            elif rec.algo_key == "create_card_from_model":
                if (
                    rec.model_name == "hr.employee"
                    and rec.model_filter_hr_empoyee_job_type
                ):
                    job_id = self.env["hr.job"].search(
                        [("name", "=", rec.model_filter_hr_empoyee_job_type)]
                    )
                    if job_id:
                        record_ids = self.env[rec.model_name].search(
                            [("job_id", "=", job_id.id)]
                        )
                    else:
                        record_ids = None
                else:
                    record_ids = self.env[rec.model_name].search(
                        eval(rec.model_fetch_record)
                    )
                if not record_ids:
                    msg_txt = f"ERR Cannot found card.\n"
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())
                    rec.add_log_time_execution(start_time)
                    continue
                record_ids.generate_pvap_card(rec)
            elif rec.algo_key == "create_model_from_card":
                if not rec.lane_root_name:
                    msg_txt = "WARN Ignore this processus, create_model_from_card need a lane_root_name."
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.warning(msg_txt.strip())
                    rec.add_log_time_execution(start_time)
                    continue

                card_ids = rec.search_cards_from_processus()

                lst_existing_name = []
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
                            _logger.warning(msg_txt.strip())
                        rec.add_log_time_execution(start_time)
                        continue
                    else:
                        lst_existing_name.append(card_id.name)
                    # Create it
                    model_id = rec.create_model_from_card(
                        card_id,
                        dct_custom_field_to_field_name,
                        lst_bind_required_field_list,
                    )
                    if rec.compute_model_fsm_location:
                        # Find associate fsm.location or create it
                        fsm_location_id = self.env["fsm.location"].search(
                            [("owner_id", "=", model_id.id)], limit=1
                        )
                        # TODO do we need to update geo_localize when exist?
                        if not fsm_location_id:
                            fsm_location_value = {
                                "name": model_id.name,
                                "owner_id": model_id.id,
                            }
                            fsm_location_id = self.env["fsm.location"].create(
                                fsm_location_value
                            )
                            # Update partner_id information
                            fsm_location_id.partner_id.type = "contact"
                            fsm_location_id.geo_localize()
                            # Validate or show an error
                            if (
                                not fsm_location_id.partner_latitude
                                and not fsm_location_id.partner_longitude
                            ):
                                msg = f"WAR cannot localize '{fsm_location_id.name}' with address '{fsm_location_id.street}'\n"
                                rec.log_txt += msg
                                rec.log_error_txt += msg
                                _logger.warning(msg_txt.strip())

                    if rec.compute_model_fsm_person:
                        # Create a user associate
                        # hr.employee
                        # model_id.
                        user_id = self.env["res.users"].search(
                            [("name", "=", model_id.name)], limit=1
                        )
                        if not user_id:
                            user_vals = {
                                "name": model_id.name,
                                "login": model_id.name,
                                "email": model_id.name,
                                "password": model_id.name,
                            }
                            user_id = self.env["res.users"].create(user_vals)
                        model_id.user_id = user_id.id
                        partner_id = user_id.partner_id
                        # Find associate fsm.location or create it
                        fsm_person_id = self.env["fsm.person"].search(
                            [("partner_id", "=", partner_id.id)], limit=1
                        )
                        if not fsm_person_id:
                            # TODO this is hardcoded, need to use mapping
                            fsm_person_vals = {
                                "name": model_id.name,
                                "partner_id": partner_id.id,
                                "phone": model_id.work_phone,
                            }
                            fsm_person_id = self.env["fsm.person"].create(
                                fsm_person_vals
                            )

                rec.log_txt += "\n"
                rec.log_error_txt += "\n"

            msg_end = (
                f"End of execution processus '{rec.algo_key}' name"
                f" '{rec.name}' {rec.get_str_time_execution(start_time)}\n"
            )
            _logger.info(msg_end.strip())
            rec.log_txt += f"{msg_end}"
            rec.log_error_txt += f"{msg_end}"
            rec.add_log_time_execution(start_time)

    def _get_lane_from_regex_day(self, rec, user_timezone):
        find_lane_ids = self.env["plan.view.agile.place.lane"]
        lane_ids = self.env["plan.view.agile.place.lane"].search(
            [("board_id", "=", rec.board_id.id)]
        )
        regex = r"(?P<jour>[A-Z]+)\s+(?P<journee>\d+)/(?P<mois>\d+)"
        for lane_id in lane_ids:
            result = re.search(regex, lane_id.title)
            if not result:
                continue
            # data = {
            #     "jour": result.group("jour"),
            #     "journee": int(result.group("journee")),
            #     "mois": int(result.group("mois")),
            # }

            next_day = self.return_next_open_day(
                datetime.datetime.now().astimezone(user_timezone),
                delay_day=rec.delay_in_day,
                is_skipping_weekend=rec.ignore_weekend,
            )
            if next_day.month == int(
                result.group("mois")
            ) and next_day.day == int(result.group("journee")):
                find_lane_ids += lane_id
        return find_lane_ids

    def _get_lane_from_regex_week(self, rec, user_timezone):
        # TODO use odoo traduction
        mois_en_francais = {
            "January": "Janvier",
            "February": "Février",
            "March": "Mars",
            "April": "Avril",
            "May": "Mai",
            "June": "Juin",
            "July": "Juillet",
            "August": "Août",
            "September": "Septembre",
            "October": "Octobre",
            "November": "Novembre",
            "December": "Décembre",
        }
        find_lane_ids = self.env["plan.view.agile.place.lane"]
        lane_ids = self.env["plan.view.agile.place.lane"].search(
            [("board_id", "=", rec.board_id.id)]
        )
        regex = r"(?P<journee>\d{2})\s+(?P<mois>\w+)\s+(?P<annee>\d{4})"
        for lane_id in lane_ids:
            result = re.search(regex, lane_id.title)
            if not result:
                continue
            monday_day = self.return_monday_day(
                datetime.datetime.now().astimezone(user_timezone),
            )
            if (
                mois_en_francais[monday_day.strftime("%B")]
                == result.group("mois").title()
                and monday_day.day == int(result.group("journee"))
                and monday_day.year == int(result.group("annee"))
            ):
                find_lane_ids += lane_id
        return find_lane_ids

    def create_model_from_card(
        self,
        card_id,
        dct_custom_field_to_field_name,
        lst_bind_required_field_list,
    ):
        rec = self
        if rec.default_value_model:
            new_model_value = json.loads(rec.default_value_model)
        else:
            new_model_value = {}
        new_model_value["pvap_card_id"] = card_id.id
        if rec.bind_field:
            dct_model_value = json.loads(rec.bind_field)
            for k, v in dct_model_value.items():
                if v == "name":
                    value = (
                        card_id.name
                        if not card_id.name.isupper()
                        else card_id.name.title()
                    )
                else:
                    value = getattr(card_id, v)
                new_model_value[k] = value
        name = new_model_value.get("name").strip()
        # Custom Fields
        if not card_id.custom_fields:
            card_id.update_card_details()
            dct_detail = json.loads(card_id.card_details)
            lst_custom_field = dct_detail.get("customFields")
        else:
            lst_custom_field = json.loads(card_id.custom_fields)
        if not lst_custom_field:
            msg_txt = f"ERR '{rec.model_name}' Missing custom fields\n"
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt
            return
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
                if not name in rec.ignore_warning_from_name.split(";"):
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
                custom_field_label = dct_custom_field.get("label")
                value = dct_custom_field.get("value")
                # When field_name is dict, a structure to choose another field_name
                if value:
                    # support integer and selection to enable boolean
                    if type(field_name) is dict:
                        for item_value in value:
                            field_name_find = field_name.get(item_value)
                            if not field_name_find:
                                msg_txt = (
                                    f"WAR '{name}' cannot extract"
                                    " custom field"
                                    f" '{custom_field_label}' with"
                                    f" value '{item_value}'\n"
                                )
                                rec.log_txt += msg_txt
                                rec.log_error_txt += msg_txt
                                continue
                            else:
                                new_model_value[field_name_find] = True
                    else:
                        new_model_value[field_name] = value
                else:
                    if (
                        not name in rec.ignore_warning_from_name.split(";")
                        and custom_field_name in lst_bind_required_field_list
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

        # Refactor new_model_value for type many2one
        for key, value in new_model_value.items():
            if (
                self.env[rec.model_name]._fields[key].type == "many2one"
                and type(value) is str
            ):
                related_model_name = (
                    self.env[rec.model_name]._fields[key].comodel_name
                )
                # TODO name is suppose to be the rec_name
                rec_find_id = self.env[related_model_name].search(
                    [("name", "=", value)], limit=1
                )
                if not rec_find_id:
                    rec_find_id = self.env[related_model_name].create(
                        {"name": value}
                    )
                new_model_value[key] = rec_find_id.id

        # Update or create
        new_model_id = self.env[rec.model_name].search(
            [("name", "=", name)], limit=1
        )
        if new_model_id:
            msg_txt = (
                f"LOG Update '{rec.model_name}' with name"
                f" '{name}' id '{card_id.card_id_pvap}\n"
            )
            _logger.info(msg_txt.strip())
            rec.log_txt += msg_txt
            new_model_id.write(new_model_value)
        else:
            msg_txt = (
                f"LOG Create '{rec.model_name}' with name"
                f" '{name}' id '{card_id.card_id_pvap}'\n"
            )
            _logger.info(msg_txt.strip())
            rec.log_txt += msg_txt
            new_model_id = self.env[rec.model_name].create(new_model_value)
            if rec.force_update_after_create:
                new_model_id.write(new_model_value)
            # TODO send id to client, can visualize all created data
            #  or maybe not, too much link into database, maybe create html link
        return new_model_id

    def search_lanes_from_processus(self, sync_cards=True, limit=-1):
        for rec in self:
            lane_root_id = self.env["plan.view.agile.place.lane"].search(
                [
                    ("title", "=", rec.lane_root_name),
                    ("board_id", "=", rec.board_id.id),
                ]
            )
            if not lane_root_id:
                msg_txt = (
                    f"ERR processus '{rec.name}' root lane name"
                    f" '{rec.lane_root_name}'\n"
                )
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                continue
            # Force auto refresh root lane
            if sync_cards:
                msg_txt = (
                    f"INFO sync cards from processus '{rec.name}' root lane name"
                    f" '{rec.lane_root_name}'\n"
                )
                rec.log_txt += msg_txt
                _logger.info(msg_txt.strip())

                lane_root_id.action_sync_cards()

            if not rec.is_root_lane:
                lane_query = [
                    ("lane_root_id", "=", lane_root_id.id),
                    ("board_id", "=", rec.board_id.id),
                ]
                if rec.lane_name:
                    lst_lane_name = rec.lane_name.split(";")
                    lane_query.append(("title", "in", lst_lane_name))
                if rec.lane_parent_name:
                    lst_lane_parent_name = rec.lane_parent_name.split(";")
                    lane_query.append(
                        ("lane_parent_name", "in", lst_lane_parent_name)
                    )
                lane_ids = self.env["plan.view.agile.place.lane"].search(
                    lane_query
                )
            else:
                lane_ids = lane_root_id

            if limit > 0:
                return lane_ids[:limit]

            return lane_ids

    def search_cards_from_processus(self, sync_cards=True):
        # This method sync card before search it
        card_ids = self.env["plan.view.agile.place.card"]
        for rec in self:
            lane_ids = rec.search_lanes_from_processus(sync_cards=sync_cards)

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
            lst_query.append(("board_id", "=", rec.board_id.id))
            card_ids += self.env["plan.view.agile.place.card"].search(
                lst_query
            )
        return card_ids

    @staticmethod
    def return_monday_day(date_to_find, delay_week=0):
        jour_semaine = date_to_find.weekday()
        lundi = date_to_find - datetime.timedelta(days=jour_semaine)
        return lundi

    @staticmethod
    def return_next_open_day(date, delay_day=1, is_skipping_weekend=True):
        # TODO support weekday, check next day from calendar into system
        prochain_jour = date + datetime.timedelta(days=delay_day)

        if is_skipping_weekend:
            while prochain_jour.weekday() in (
                5,
                6,
            ):  # 5 = saturday, 6 = sunday
                prochain_jour += datetime.timedelta(days=delay_day)

        return prochain_jour

    @staticmethod
    def get_str_time_execution(start_time):
        end_time = time.time()
        execution_time = end_time - start_time
        return f"Temps d'exécution : {execution_time:.3f} secondes"

    def add_log_time_execution(self, start_time):
        msg_txt = "\nINFO " + self.get_str_time_execution(start_time) + "\n"
        for rec in self:
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt
            _logger.info(msg_txt.strip())
