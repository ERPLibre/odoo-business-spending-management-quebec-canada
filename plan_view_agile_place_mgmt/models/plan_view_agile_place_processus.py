#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import collections
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
            ("multi_process", "Bundle multi-process"),
            ("create_card_from_model", "Build cards into PVAP"),
            ("create_new_board", "Create new board"),
            ("create_model_from_card", "Create Model from Card"),
            ("create_model_from_lane", "Create Model from Lane"),
            ("send_sms_schedule", "Send SMS schedule"),
            (
                "send_sms_schedule_week_summary",
                "Send SMS schedule week summary",
            ),
            (
                "send_reminder_sms_schedule_condition",
                "Send reminder SMS schedule condition",
            ),
            ("rename_lane", "Renommer des lanes"),
            ("copy_cards_from_lane", "Copy cards from lane to lane"),
            (
                "copy_cards_from_lane_from_board",
                "Copy cards from board to another board",
            ),
            ("delete_cards", "Delete cards"),
            ("bind_create_card", "Bind Create card"),
            ("bind_delete_card", "Bind Delete card"),
        ],
        required=True,
        default="create_model_from_card",
        readonly=True,
    )

    algo_rename = fields.Selection(
        selection=[
            ("schedule_week_template", "Schedule week template"),
            ("schedule_week_field_service", "Schedule week field service"),
        ],
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

    force_sync_before_algo = fields.Boolean(
        help="When True, will force sync into algorithm."
    )

    force_refresh_custom_fields = fields.Boolean(
        help="It's consume lot of time, but will refresh custom_fields."
    )

    ignore_run_depend_processus = fields.Boolean(
        help="Enable to accelerate development to ignore execute update processus dependency."
    )

    is_root_lane = fields.Boolean(
        help="Enable when the cards to extract is inside the root lane, because a root lane has no parent lane."
    )

    search_recursive_lane = fields.Boolean(
        help="Get all card recursively from lane_id."
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

    lane_sub_name = fields.Char()

    lane_root_name = fields.Char()

    board_copy_to_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board",
        string="Board to copy",
    )

    copy_to_lane = fields.Char()

    copy_to_parent_lane = fields.Char()

    copy_to_sub_lane = fields.Char()

    copy_to_root_lane = fields.Char()

    copy_is_root_lane = fields.Boolean()

    validate_copy_lane_number = fields.Integer(
        default=-1,
        help="Will show error if validation fail, to count the lane to copy.",
    )

    copy_multiple_time = fields.Integer(
        default=1, help="Will repeat the copy if higher then 1"
    )

    clean_before_card_into_copy_to_lane = fields.Boolean(
        help="Will delete all card when using into copy_to_lane"
    )

    sms_enable = fields.Boolean(related="session_id.sms_enable")

    sms_to_number_phone = fields.Char(help="Separate multiple with ;")

    sms_to_country = fields.Char(default="+1")

    sms_message_to_send = fields.Text()

    sms_debug = fields.Boolean(
        help="Will overwrite automatic message by this manual message."
    )

    sms_in_test_mode = fields.Boolean(
        help="Enable to fake sending SMS, will never send SMS if True"
    )

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

    rename_card_pattern = fields.Char(help="The pattern need to contain '%s'")

    rename_week_lane_name_pattern = fields.Char(
        help="The pattern need to contain '%s'"
    )

    rename_week_lane_name_icon = fields.Char(
        help="Put your ascii and will be show before lane name"
    )

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
            rec.sms_history_ids.processus_id = False

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

            if rec.log_txt is False:
                rec.log_txt = ""
            if rec.log_error_txt is False:
                rec.log_error_txt = ""

            if rec.sms_debug:
                sms_history_ids = self.env["plan.view.agile.place.sms.history"]
                for sms_to_number_phone in rec.sms_to_number_phone.split(";"):
                    sms_history_vals = {
                        "name": rec.sms_message_to_send,
                        "to_number_phone": sms_to_number_phone,
                        "processus_id": rec.id,
                        "session_id": rec.session_id.id,
                    }
                    sms_history_id = self.env[
                        "plan.view.agile.place.sms.history"
                    ].create(sms_history_vals)
                    sms_history_ids += sms_history_id
            else:
                sms_history_ids = self.env[
                    "plan.view.agile.place.sms.history"
                ].search(
                    [("processus_id", "=", rec.id), ("is_sent", "=", False)]
                )

            if sms_history_ids:
                # Group execution is associate when send SMS
                sms_history_ids.group_execution_name = group_execution_name
                # if not (
                #     not rec.sms_limit_iteration
                #     or rec.sms_limit_iteration > i
                # ):
                sms_history_ids.send_sms()
                for sms_history_id in sms_history_ids:
                    if sms_history_id.error_msg:
                        msg_txt = f"ERR {sms_history_id.error_msg}\n"
                        rec.log_txt += msg_txt
                        rec.log_error_txt += msg_txt
                        _logger.error(msg_txt.strip())
            else:
                msg_txt = f"WARN No SMS to send\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.warning(msg_txt.strip())

    def action_execute_algo(self, ctx=None):
        for rec in self:
            if rec.is_disabled:
                continue

            start_time = time.time()

            if rec.log_txt is False:
                rec.log_txt = ""
            if rec.log_error_txt is False:
                rec.log_error_txt = ""

            rec.fill_board_id()

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
            if rec.depend_process_ids and not rec.ignore_run_depend_processus:
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

            if rec.algo_key == "copy_cards_from_lane_from_board":
                rec.fill_board_id(use_from_board=True, raise_error=False)
            elif rec.algo_key == "copy_cards_from_lane":
                rec.algo_copy_cards_from_lane(start_time)
            elif rec.algo_key == "send_reminder_sms_schedule_condition":
                # TODO maybe can search employee information
                pass
            elif rec.algo_key == "delete_cards":
                rec.algo_delete_cards()
            elif rec.algo_key == "send_sms_schedule":
                rec.algo_send_sms_schedule(
                    start_time,
                    user_timezone,
                    dct_custom_field_to_field_name,
                    lst_bind_required_field_list,
                )
            elif rec.algo_key == "send_sms_schedule_week_summary":
                rec.algo_send_sms_schedule_week_summary(user_timezone)
            elif rec.algo_key == "create_model_from_lane":
                rec.algo_create_model_from_lane(
                    start_time, user_timezone, diff_hour_timezone
                )
            elif rec.algo_key == "create_new_board":
                rec.algo_create_new_board(start_time, user_timezone)
            elif rec.algo_key == "create_card_from_model":
                rec.algo_create_card_from_model(start_time)
            elif rec.algo_key == "rename_lane":
                rec.algo_rename_lane(start_time, user_timezone)
            elif rec.algo_key == "create_model_from_card":
                rec.algo_create_model_from_card(
                    start_time,
                    dct_custom_field_to_field_name,
                    lst_bind_required_field_list,
                    force_refresh_custom_fields=rec.force_refresh_custom_fields,
                )

            msg_end = (
                f"End of execution processus '{rec.algo_key}' name"
                f" '{rec.name}' {rec.get_str_time_execution(start_time)}\n"
            )
            _logger.info(msg_end.strip())
            rec.log_txt += f"{msg_end}"
            rec.log_error_txt += f"{msg_end}"
            rec.add_log_time_execution(start_time)

    def algo_create_model_from_card(
        self,
        start_time,
        dct_custom_field_to_field_name,
        lst_bind_required_field_list,
        force_refresh_custom_fields=False,
    ):
        for rec in self:
            if not rec.lane_root_name:
                msg_txt = "WARN Ignore this processus, create_model_from_card need a lane_root_name."
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.warning(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue

            card_ids = rec.search_cards_from_processus()
            msg_txt = f"LOG Info {len(card_ids)} cards\n"
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt
            _logger.info(msg_txt.strip())

            lst_existing_name = []
            for card_id in card_ids:
                # Check doublon from card
                if card_id.name in lst_existing_name:
                    if not card_id.name in rec.ignore_warning_from_name.split(
                        ";"
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
                    force_refresh_custom_fields=force_refresh_custom_fields,
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
                            _logger.warning(msg.strip())

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

    def algo_rename_lane(self, start_time, user_timezone):
        for rec in self:
            if not rec.lane_root_name:
                msg_txt = "WARN Ignore this processus, create_model_from_card need a lane_root_name.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.warning(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue

            if rec.algo_rename not in [
                "schedule_week_field_service",
                "schedule_week_template",
            ]:
                msg_txt = f"WARN Ignore this processus, don't support algo rename '{rec.algo_rename}'.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.warning(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue

            last_week_day = self.return_next_open_day(
                datetime.datetime.now().astimezone(user_timezone),
                delay_day=rec.delay_in_day - 7,
            )
            last_week_day_monday = self.return_monday_day(last_week_day)
            current_day = last_week_day_monday
            current_week_day = last_week_day_monday

            if rec.rename_week_lane_name_icon:
                lst_icon = rec.rename_week_lane_name_icon.split(";")
            else:
                lst_icon = []

            root_name_list = rec.lane_root_name.split(";")
            parent_name_list = rec.lane_parent_name.split(";")
            dct_week_card = {}
            for i_week, root_name in enumerate(root_name_list):
                dct_day_card = {}
                lane_week_id = rec.search_lanes(
                    rec.name,
                    rec.board_id,
                    root_name,
                    is_root_lane=True,
                    sync_cards=False,
                )
                if not lane_week_id:
                    msg_txt = f"ERR cannot find lane week '{root_name}'.\n"
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.warning(msg_txt.strip())
                    rec.add_log_time_execution(start_time)
                    continue
                dct_week_card[root_name] = {
                    "days": dct_day_card,
                    "week_card_id": lane_week_id,
                }
                for i_day, parent_name in enumerate(parent_name_list):
                    lane_day_id = rec.search_lanes(
                        rec.name,
                        rec.board_id,
                        root_name,
                        lane_name=parent_name,
                        sync_cards=False,
                    )
                    if not lane_day_id:
                        msg_txt = f"ERR cannot find lane day '{root_name}'.\n"
                        rec.log_txt += msg_txt
                        rec.log_error_txt += msg_txt
                        _logger.warning(msg_txt.strip())
                        rec.add_log_time_execution(start_time)
                        continue

                    lane_ids = rec.search_lanes(
                        rec.name,
                        rec.board_id,
                        lane_root_name=root_name,
                        lane_parent_name=parent_name,
                        sync_cards=False,
                        order="sequence asc",
                    )
                    dct_day_card[parent_name] = {
                        "chantier": lane_ids,
                        "day_card_id": lane_day_id,
                    }
                    if rec.algo_rename == "schedule_week_field_service":
                        fsm_location_ids = self.env["fsm.location"].search(
                            [],
                            order="name asc",
                        )
                    else:
                        fsm_location_ids = self.env["fsm.location"]

                    # Begin compute here
                    for no_lane, lane_id in enumerate(lane_ids):
                        if "%s" in rec.rename_card_pattern:
                            new_name = rec.rename_card_pattern % str(
                                no_lane
                            ).zfill(4)
                        else:
                            new_name = rec.rename_card_pattern
                        if (
                            rec.algo_rename == "schedule_week_field_service"
                            and fsm_location_ids
                            and len(fsm_location_ids) > no_lane
                        ):
                            new_name = fsm_location_ids[no_lane].name

                        if lane_id.title != new_name:
                            lane_id.with_context(
                                {"enable_sync_lane": True}
                            ).title = new_name

                    if rec.algo_rename == "schedule_week_field_service":
                        lane_day_id.with_context(
                            {"enable_sync_lane": True}
                        ).title = f"{parent_name} {current_day.day}/{current_day.month}"

                    current_day += datetime.timedelta(days=1)

                if (
                    rec.algo_rename == "schedule_week_field_service"
                    and rec.rename_week_lane_name_pattern
                ):
                    if "%s" in rec.rename_week_lane_name_pattern:
                        value_pattern = f"{current_week_day.day} {self._get_month_fr(ttype='str', value=current_week_day.month - 1).upper()} {current_week_day.year}"
                        lane_week_new_name = (
                            rec.rename_week_lane_name_pattern % value_pattern
                        )
                    else:
                        lane_week_new_name = rec.rename_week_lane_name_pattern
                    if lst_icon:
                        lane_week_new_name = f"{lst_icon[i_week if i_week < len(lst_icon) else -1]} {lane_week_new_name}"
                    lane_week_id.with_context(
                        {"enable_sync_lane": True}
                    ).title = lane_week_new_name

                current_week_day += datetime.timedelta(weeks=1)

            if not dct_week_card:
                msg_txt = f"ERR Cannot find lane to rename it of processus '{rec.name}'\n."
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.warning(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue

    def algo_create_card_from_model(self, start_time):
        for rec in self:
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

    def algo_create_new_board(
        self,
        start_time,
        user_timezone,
    ):
        for rec in self:
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
            board_template_id = self.env["plan.view.agile.place.board"].search(
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
                "type_board_ids": [(6, 0, rec.board_id.type_board_ids.ids)],
            }
            board_id = self.env["plan.view.agile.place.board"].create(
                board_value
            )
            board_id.action_sync()

            # Execute processus of adding cards
            for process_id in rec.process_execute_after_ids:
                process_id.board_id = board_id.id

                # # For copy, the copy_from_board is actuel board
                # if process_id.algo_key == "copy_cards_from_lane_from_board":
                #     # Need to search this official board
                #     process_id.board_copy_to_id =

                process_id.action_execute_algo()

    def algo_create_model_from_lane(
        self,
        start_time,
        user_timezone,
        diff_hour_timezone,
    ):
        for rec in self:
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
                msg_txt = f"ERR Cannot found lane with regex of next day.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue
            rec.lane_root_name = lane_ids[0].title
            card_ids = rec.search_cards_from_processus()
            msg_txt = f"LOG Info {len(card_ids)} cards\n"
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt
            _logger.info(msg_txt.strip())

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
                regex = r"(?P<jour>[A-Z]+)\s+(?P<journee>\d+)/(?P<mois>\d+)"
                result = re.search(regex, card_id.lane_parent_name)
                diff_date = int(result.group("journee")) - monday_day.day
                # TODO this is an hack, need to retrieve the exact day with month and day
                actual_day = monday_day + datetime.timedelta(days=diff_date)
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
                    fsm_order_id = self.env["fsm.order"].create(fsm_order_vals)
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

    def algo_send_sms_schedule_week_summary(self, user_timezone):
        for rec in self:
            # lst_filter_field = json.loads(rec.filter_field)
            if rec.algo_key in ["send_sms_schedule_week_summary"]:
                # lane_week_root_id = self._get_lane_from_regex_day(
                #     rec, user_timezone
                # )
                card_ids = self.search_cards_from_processus(
                    sync_cards=rec.force_sync_before_algo
                )
                msg_txt = f"LOG Info {len(card_ids)} cards\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.info(msg_txt.strip())

                dct_list_employee = collections.defaultdict(list)
                for card_id in card_ids:
                    if not card_id.custom_fields:
                        card_id.update_card_details()
                    # Separate per name
                    if not card_id.custom_fields:
                        continue
                    lst_custom_fields = json.loads(card_id.custom_fields)
                    employee_name = card_id.name
                    is_cancel = True
                    for dct_custom_fields in lst_custom_fields:
                        if (
                            dct_custom_fields.get("label")
                            == "NOTIFICATION SMS: EMPLOYÉ"
                        ):
                            if dct_custom_fields["value"] == [
                                "Rappel horaire EMPLOYÉ"
                            ]:
                                is_cancel = False
                        if (
                            dct_custom_fields.get("label")
                            == "TÉLÉPHONE: EMPLOYÉ"
                        ):
                            phone_value = dct_custom_fields["value"]
                            if not phone_value:
                                is_cancel = True
                                break
                            employee_name += "#" + phone_value
                    if is_cancel:
                        print(f"Cancel {employee_name}")
                        continue
                    dct_list_employee[employee_name].append(card_id)

                sms_history_ids = self.env["plan.view.agile.place.sms.history"]
                for employee_name, lst_card in dct_list_employee.items():
                    # Separate per date
                    dct_day = collections.defaultdict(list)
                    for card_id in lst_card:
                        dct_day[card_id.lane_parent_name].append(card_id)
                    name, phone = employee_name.split("#")
                    msg_employe = f"{rec.sms_message_prefix} Calendrier de la semaine pour {name}\n\n"
                    # Reorder list from weekday
                    lst_weekday = self._get_week_day_fr(ttype="list")
                    for weekday in lst_weekday:
                        for str_day, lst_card_week in dct_day.items():
                            if str_day.startswith(weekday.upper()):
                                for card_week_id in lst_card_week:
                                    str_date_time = str_day
                                    if card_week_id.size:
                                        str_date_time += (
                                            f"({card_week_id.size}H)"
                                        )
                                    str_date_time += ": "
                                    coule_msg = ""

                                    if rec.sms_detect_card_type_msg_1:
                                        lst_type_card = rec.sms_detect_card_type_msg_1.split(
                                            ";"
                                        )
                                        type_card_msg_1_ids = self.env[
                                            "plan.view.agile.place.card.type"
                                        ].search(
                                            [
                                                (
                                                    "name",
                                                    "in",
                                                    lst_type_card,
                                                ),
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
                                                    card_week_id.lane_id.ids,
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
                                                    f" '{card_week_id.lane_name}'"
                                                )
                                                rec.log_txt += msg_txt
                                                rec.log_error_txt += msg_txt
                                                _logger.error(msg_txt.strip())
                                            if card_msg_1_ids:
                                                if card_msg_1_ids.size:
                                                    coule_msg = f"Coulée à {card_msg_1_ids.size}H"
                                                else:
                                                    coule_msg = "Coulée"

                                    msg_employe += f"{str_date_time}{card_week_id.lane_name}"
                                    if coule_msg:
                                        msg_employe += f" - {coule_msg}"
                                    msg_employe += "\n"
                    msg_employe += "\nCompte-tenu de l'avancement des travaux, il est possible que l'horaire puisse changer en tout temps.\n\nUn SMS final vous sera envoyé tous les jours à 18H pour votre calendrier final du lendemain."
                    sms_history_value = {
                        "to_number_phone": phone,
                        "name": msg_employe,
                        "processus_id": rec.id,
                        "session_id": rec.session_id.id,
                    }
                    sms_history_ids += self.env[
                        "plan.view.agile.place.sms.history"
                    ].create(sms_history_value)

    def algo_send_sms_schedule(
        self,
        start_time,
        user_timezone,
        dct_custom_field_to_field_name,
        lst_bind_required_field_list,
    ):
        for rec in self:
            lst_filter_field = json.loads(rec.filter_field)
            if rec.fake_regex_lane != "jour d/m":
                msg_txt = (
                    f"ERR processus '{rec.name}' missing field"
                    " 'fake_regex_lane'\n"
                )
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
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

            lane_ids = self._get_lane_from_regex_day(rec, user_timezone)
            i_msg = 0
            date_msg_str = ""
            msg_summary_sms = ""
            for lane_id in lane_ids:
                # Find root lane
                # Force auto refresh root lane
                if rec.force_sync_before_algo:
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

                card_ids = self.env["plan.view.agile.place.card"].search(
                    lst_query
                )
                msg_txt = f"LOG Info {len(card_ids)} cards\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.info(msg_txt.strip())

                msg_summary_sms = ""
                for card_id in card_ids:
                    # TODO validate double employee, validate time or raise error if missing time
                    card_name = card_id.name.strip()
                    if rec.force_update_model:
                        employee_id = rec.create_model_from_card(
                            card_id,
                            dct_custom_field_to_field_name,
                            lst_bind_required_field_list,
                            force_refresh_custom_fields=rec.force_refresh_custom_fields,
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
                            [getattr(employee_id, a) for a in lst_filter_field]
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
                    msg_sms_log_debug = f"PHONE: {employee_id.work_phone}\n"
                    msg_sms = (
                        ""
                        if not rec.sms_message_prefix
                        else rec.sms_message_prefix + " "
                    )

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
                    msg_summary_sms += f"#{i_msg} {employee_id.name} «{card_id.lane_name}»{msg_time}"
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
                    msg_summary_sms += "\n"
                    if partner_id:
                        street_map = quote(partner_id.street)
                        msg_sms += (
                            "\nÀ l'adresse suivante : \n\n"
                            f"{partner_id.street}\n\nhttps://www.google.ca/maps/place/{street_map}"
                        )

                    msg_txt = (
                        f"\nSMS({i_msg}) {msg_sms_log_debug}"
                        f"«\n{msg_sms}\n»\n"
                    )
                    rec.log_txt += msg_txt

                    value_sms = {
                        "to_number_phone_country": to_country,
                        "to_number_phone": (
                            employee_id.work_phone
                            if employee_id.work_phone
                            else to
                        ),
                        "from_number_phone_country": rec.session_id.sms_from_country_default,
                        "from_number_phone": rec.session_id.sms_from_number_phone_default,
                        # "group_execution_name": group_execution_name,
                        "processus_id": rec.id,
                        "session_id": rec.session_id.id,
                    }
                    value_sms["name"] = msg_sms
                    value_sms["to_number_phone"] = employee_id.work_phone
                    sms_history_id = self.env[
                        "plan.view.agile.place.sms.history"
                    ].create(value_sms)

            if not msg_summary_sms:
                continue

            value_summary_sms = {
                "to_number_phone_country": to_country,
                "to_number_phone": to,
                "from_number_phone_country": rec.session_id.sms_from_country_default,
                "from_number_phone": rec.session_id.sms_from_number_phone_default,
                # "group_execution_name": group_execution_name,
                "processus_id": rec.id,
                "session_id": rec.session_id.id,
            }
            summary_final_msg = f"{rec.sms_message_prefix} Sommaire ({i_msg} SMS) {date_msg_str}\n{msg_summary_sms}".strip()
            value_summary_sms["name"] = summary_final_msg
            rec.log_txt += "\n" + msg_summary_sms + "\n"

            for to_summary in rec.sms_summary_phone.split(";"):
                value_summary_sms["to_number_phone"] = to_summary
                sms_summary_history_id = self.env[
                    "plan.view.agile.place.sms.history"
                ].create(value_summary_sms)

    def algo_delete_cards(self):
        for rec in self:
            card_ids = rec.search_cards_from_processus()
            msg_txt = f"LOG Info {len(card_ids)} cards\n"
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt
            _logger.info(msg_txt.strip())

            if card_ids.exists():
                card_ids.enabled_bind = True
                card_ids.unlink()

    def algo_copy_cards_from_lane(self, start_time):
        for rec in self:
            lane_from_copy_ids = rec.search_lanes_from_processus(
                sync_cards=rec.force_sync_before_algo
            )
            board_to_copy = (
                rec.board_copy_to_id if rec.board_copy_to_id else rec.board_id
            )
            lane_to_copy_ids = rec.search_lanes(
                rec.name,
                board_to_copy,
                rec.copy_to_root_lane,
                lane_parent_name=rec.copy_to_parent_lane,
                lane_sub_name=rec.copy_to_sub_lane,
                is_root_lane=rec.copy_is_root_lane,
                lane_name=rec.copy_to_lane,
                sync_cards=rec.force_sync_before_algo,
                log_txt=rec.log_txt,
                log_error_txt=rec.log_error_txt,
            )

            if not lane_from_copy_ids:
                msg_txt = "ERR Cannot find lane, check search lane variable.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue
            if not lane_to_copy_ids:
                msg_txt = "ERR Cannot find lane to copy, check search lane copy variable.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue
            if (
                rec.validate_copy_lane_number > 0
                and len(lane_to_copy_ids) < rec.validate_copy_lane_number
            ):
                msg_txt = f"WAR Expected {rec.validate_copy_lane_number} lane_to_copy and got {len(lane_to_copy_ids)}.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())

            if rec.clean_before_card_into_copy_to_lane:
                # get all cards to delete
                card_to_delete_ids = self.env[
                    "plan.view.agile.place.card"
                ].search(
                    [
                        ("lane_id", "in", lane_to_copy_ids.ids),
                        ("board_id", "=", rec.board_id.id),
                    ]
                )
                if card_to_delete_ids:
                    card_to_delete_ids.enabled_bind = True
                    card_to_delete_ids.unlink()

            # Get all cards to copy
            card_to_copy_ids = self.env["plan.view.agile.place.card"].search(
                [
                    ("lane_id", "in", lane_from_copy_ids.ids),
                    ("board_id", "=", rec.board_id.id),
                ]
            )
            for lane_to_copy_id in lane_to_copy_ids:
                for card_to_copy_id in card_to_copy_ids:
                    for i in range(rec.copy_multiple_time):
                        # Custom Fields
                        if not card_to_copy_id.custom_fields:
                            card_to_copy_id.update_card_details()

                        data = {
                            "copied_from_card_pvap": card_to_copy_id.card_id_pvap,
                            "board_id": lane_to_copy_id.board_id.id,
                            "name": card_to_copy_id.name,
                            "lane_id": lane_to_copy_id.id,
                            "size": card_to_copy_id.size,
                            "card_type_id": card_to_copy_id.card_type_id.id,
                            "entete": card_to_copy_id.entete,
                            "custom_fields": str(
                                json.loads(card_to_copy_id.custom_fields)
                            ),
                            "description": card_to_copy_id.description,
                            "assigned_users": card_to_copy_id.assigned_users,
                            "session_id": rec.session_id.id,
                        }
                        self.env["plan.view.agile.place.card"].create(data)

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

    def _get_month_fr(self, ttype="dict", value=0):
        # TODO use odoo traduction
        lst_value = [
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin",
            "Juillet",
            "Août",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre",
        ]
        if ttype == "list":
            return lst_value
        elif ttype == "str":
            return lst_value[value]
        return {
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

    def _get_week_day_fr(self, ttype="dict", value=0):
        # TODO use odoo traduction
        lst_value = [
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ]
        if ttype == "list":
            return lst_value
        elif ttype == "str":
            return lst_value[value]
        # return {
        #     "January": "Janvier",
        #     "February": "Février",
        #     "March": "Mars",
        #     "April": "Avril",
        #     "May": "Mai",
        #     "June": "Juin",
        #     "July": "Juillet",
        #     "August": "Août",
        #     "September": "Septembre",
        #     "October": "Octobre",
        #     "November": "Novembre",
        #     "December": "Décembre",
        # }

    def _get_lane_from_regex_week(self, rec, user_timezone):
        mois_en_francais = self._get_month_fr()
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
        force_refresh_custom_fields=False,
    ):
        self.ensure_one()
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
        if not card_id.custom_fields or force_refresh_custom_fields:
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

    def search_lanes_from_processus(
        self, sync_cards=True, limit=-1, order=None
    ):
        for rec in self:
            return rec.search_lanes(
                rec.name,
                rec.board_id,
                rec.lane_root_name,
                lane_parent_name=rec.lane_parent_name,
                lane_sub_name=rec.lane_sub_name,
                is_root_lane=rec.is_root_lane,
                search_recursive_lane=rec.search_recursive_lane,
                lane_name=rec.lane_name,
                sync_cards=sync_cards,
                limit=limit,
                order=order,
                log_txt=rec.log_txt,
                log_error_txt=rec.log_error_txt,
            )

    def search_lanes(
        self,
        process_name,
        board_id,
        lane_root_name,
        lane_parent_name=None,
        lane_sub_name=None,
        lane_name=None,
        is_root_lane=False,
        search_recursive_lane=False,
        sync_cards=True,
        limit=-1,
        order=None,
        log_txt=None,
        log_error_txt=None,
    ):
        self.ensure_one()
        if not lane_root_name:
            msg_txt = (
                f"ERR processus '{process_name}' root lane name is empty.\n"
            )
            if log_txt:
                log_txt += msg_txt
            if log_error_txt:
                log_error_txt += msg_txt
            return
        lst_title_root = lane_root_name.split(";")
        # TODO maybe a root has not parent
        lane_root_ids = self.env["plan.view.agile.place.lane"].search(
            [
                ("title", "in", lst_title_root),
                ("board_id", "=", board_id.id),
            ]
        )
        if not lane_root_ids:
            msg_txt = (
                f"ERR processus '{process_name}' root lane name"
                f" '{lane_root_name}'\n"
            )
            if log_txt:
                log_txt += msg_txt
            if log_error_txt:
                log_error_txt += msg_txt
            return self.env["plan.view.agile.place.lane"]
        # Force auto refresh root lane
        if sync_cards:
            msg_txt = (
                f"INFO sync cards from processus '{process_name}' root lane name"
                f" '{lane_root_name}'\n"
            )
            if log_txt:
                log_txt += msg_txt
            _logger.info(msg_txt.strip())

            lane_root_ids.action_sync_cards()

        if is_root_lane:
            lane_ids = lane_root_ids
        else:
            lane_query = [
                ("board_id", "=", board_id.id),
                ("lane_root_id", "in", lane_root_ids.ids),
            ]

            if lane_name:
                lst_lane_name = lane_name.split(";")
                lane_query.append(("title", "in", lst_lane_name))
            if lane_parent_name:
                lst_lane_parent_name = lane_parent_name.split(";")
                lane_query.append(
                    ("lane_parent_name", "in", lst_lane_parent_name)
                )
            if lane_sub_name:
                lst_lane_sub_name = lane_sub_name.split(";")
                lane_query.append(("lane_sub_name", "in", lst_lane_sub_name))
            if order:
                lane_ids = self.env["plan.view.agile.place.lane"].search(
                    lane_query, order=order
                )
            else:
                lane_ids = self.env["plan.view.agile.place.lane"].search(
                    lane_query
                )

        if search_recursive_lane:
            lane_ids = lane_ids.get_list_child_lane_from_lane(add_itself=True)

        if limit > 0:
            return lane_ids[:limit]

        return lane_ids

    def fill_board_id(self, use_from_board=False, raise_error=True):
        for rec in self:
            if (
                (use_from_board and rec.board_copy_to_id)
                or (not use_from_board and rec.board_id)
                or not rec.type_board_depend_ids
            ):
                # Nothing to fill
                continue
            str_board_type = ",".join(
                [a.name for a in rec.type_board_depend_ids]
            )
            if len(rec.type_board_depend_ids) > 1:
                msg_txt = "ERR Support only 1 type of board at this moment.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())

            for type_board_id in rec.type_board_depend_ids:
                for board_id in rec.session_id.board_ids:
                    if type_board_id in board_id.type_board_ids:
                        if use_from_board:
                            rec.board_copy_to_id = board_id.id
                        else:
                            rec.board_id = board_id.id
                        break

            if (not rec.board_id and not use_from_board) or (
                not rec.board_copy_to_id and use_from_board
            ):
                msg_txt = f"ERR Cannot find board_id associate with type '{str_board_type}'.\n"
                if raise_error:
                    raise ValueError(msg_txt.strip())
                else:
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())

    def search_cards_from_processus(self, sync_cards=True):
        # This method sync card before search it
        card_ids = self.env["plan.view.agile.place.card"]
        for rec in self:
            lane_ids = rec.search_lanes_from_processus(sync_cards=sync_cards)
            if not lane_ids:
                msg_txt = f"ERR cannot find lane into '{rec.name}'.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                continue

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
