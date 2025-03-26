#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import datetime
import json
import logging
import re
import tempfile
import time
from collections import defaultdict
from urllib.parse import quote

from pytz import timezone

try:
    from randomwordfr import RandomWordFr
except ImportError:
    RandomWordFr = None


from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAPProcessus(models.Model):
    _name = "planviewap.processus"
    _description = "planviewap_processus"
    _order = "sequence, name"

    name = fields.Char()

    algo_key = fields.Selection(
        selection=[
            ("multi_process", "Bundle multi-process"),
            ("import", "Import data"),
            ("operate_lane", "Operate lane"),
            ("create_card_from_model", "Build cards into PVAP"),
            ("create_new_board", "Create new board"),
            ("create_model_from_card", "Create Model from Card"),
            ("extract_data", "Extraction"),
            ("send_sms_schedule", "Send SMS schedule"),
            (
                "send_sms_schedule_week_summary",
                "Send SMS schedule week summary",
            ),
            ("send_sms", "Send SMS"),
            (
                "send_sms_all_employee",
                "Send SMS general to all employee",
            ),
            ("rename_lane", "Renommer des lanes"),
            ("copy_cards_from_lane", "Copy cards from lane to lane"),
            ("sync_cards_from_lane", "Sync cards from lane to all board"),
            (
                "copy_cards_from_lane_from_board",
                "Copy cards from board to another board",
            ),
            (
                "alert_on_cards",
                "Alert on cards",
            ),
            (
                "move_root_lane_week",
                "Move root lane week to previous week",
            ),
            ("delete_cards", "Delete cards"),
            ("bind_create_card", "Bind Create card"),
            ("bind_delete_card", "Bind Delete card"),
            ("validation_card", "Validation card"),
        ],
        required=True,
        default="create_model_from_card",
        readonly=True,
    )

    sequence = fields.Integer(default=10)

    algo_rename = fields.Selection(
        selection=[
            ("schedule_week_template", "Schedule week template"),
            ("schedule_week_field_service", "Schedule week field service"),
        ],
    )

    session_id = fields.Many2one(
        comodel_name="planviewap.session",
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

    operate_lane_ignore_string_lane = fields.Char(
        help=("String to remove from lane when search lane for operate_lane")
    )

    operate_lane_name = fields.Char(
        help=(
            "Separate by ; for multiple lane, will add lane after this lane. Search by pattern into each searching lane"
        )
    )

    operate_lane_action = fields.Selection(
        selection=[
            ("add_above", "Add above"),
            ("add_bellow", "Add bellow"),
            ("delete", "Delete"),
            ("rename", "Rename"),
            ("sort_by", "Sort By"),
        ],
        required=True,
        default="add_bellow",
    )

    bind_field = fields.Text()

    create_more_field = fields.Text()

    create_more_field_algo = fields.Text()

    default_value_model = fields.Text()

    ignore_warning_from_name = fields.Char(
        default="",
        help="Separate by ; for multiple, will ignore warning from his name.",
    )

    model_name = fields.Char()

    model_fetch_record = fields.Char()

    alert_execution_msg = fields.Text(
        readonly=True, help="The alert execution will be show in this field."
    )

    alert_min_size_card_enable = fields.Boolean()

    alert_min_size_card = fields.Integer(
        default=0, help="Alert under the min."
    )

    alert_wrong_lane_agencement = fields.Boolean()

    alert_max_size_card_enable = fields.Boolean()

    alert_max_size_card = fields.Integer(
        default=0, help="Alert upper the max."
    )

    custom_process_method_name = fields.Char(
        help="Will call this method instead of normal execution for full custom execution."
    )

    alert_count_card_msg = fields.Char()

    alert_max_count_card_enable = fields.Boolean()

    alert_max_count_card = fields.Integer(
        default=0, help="Alert upper the max."
    )

    alert_min_count_card_enable = fields.Boolean()

    alert_min_count_card = fields.Integer(
        default=0, help="Alert under the min."
    )

    duplicate_multiple_time = fields.Integer(
        default=1, help="Will repeat the duplication if higher then 1"
    )

    model_filter_hr_employee_job_type = fields.Char()

    record_id_i = fields.Integer(
        string="Record index",
        help="The record identifiant to be use from binding.",
    )

    lane_name = fields.Char()

    exclude_lane_name = fields.Char(help="Separate by ; for multiple")

    get_all_lane = fields.Boolean(help="Will extract all lane")

    lane_extract_algo = fields.Selection(
        selection=[
            ("jour d/m", "jour d/m"),
            ("week d/m/y", "week d/m/y"),
            ("week d/m/y from today", "week d/m/y from today"),
            ("week d/m/y from tomorrow", "week d/m/y from tomorrow"),
            ("pattern", "pattern"),
        ]
    )

    delay_in_day = fields.Integer(
        string="Delay in day or week", help="Will depend the lane_extract_algo"
    )

    delay_in_day_plus_one_if_friday = fields.Boolean(
        help="Will add 1 to delay_in_day if now is friday."
    )

    get_all_week = fields.Boolean(
        help="Will ignore delay_in_day to get all week."
    )

    force_sync_before_algo = fields.Boolean(
        help="When True, will force sync into algorithm."
    )

    force_refresh_custom_fields = fields.Boolean(
        help="It's consume lot of time, but will refresh custom_fields."
    )

    debug_show_first_day = fields.Char(
        string="Debug first day",
        help="Will show a debug information about the first day for extraction",
    )

    ignore_run_depend_processus = fields.Boolean(
        help="Enable to accelerate development to ignore execute update processus dependency."
    )

    is_root_lane = fields.Boolean(
        help="Enable when the cards to extract is inside the root lane, because a root lane has no parent lane."
    )

    extract_only_root_lane = fields.Boolean(
        help="Enable to extract only root lane."
    )

    validation_target_achieved = fields.Char(
        help="Validation string in target_achieved for detected card, support ; for multiple choice."
    )

    validation_location_custom_field_name = fields.Char(
        help="Search the custom field name of card to extract information."
    )

    validation_location_custom_field_expected_value = fields.Char(
        help="Expected value to continue the validation from value validation_location_custom_field_name."
    )

    validation_location_expected_associate_type_card_same_lane = fields.Char(
        help="Expected associate type card in same lane, or give error."
    )

    validation_location_expected_associate_different_size = fields.Integer(
        help="Expected associate card with a different size."
    )

    validation_location_expected_associate_target_achieve = fields.Char(
        help="Expected associate card with a specified target achieve."
    )

    validation_algo = fields.Selection(
        selection=[
            (
                "associate_card_location_inclusion",
                "Associate card with location inclusion",
            ),
            (
                "negative_same_name_different_size",
                "Negative same name different size",
            ),
        ],
        help="Will execute a validation algorithm",
    )

    search_lane_required_string = fields.Char(
        help="Need this string when search lane or exclude it. Works only if contains data."
    )

    is_disabled = fields.Boolean(
        help="When true, the processus will not execute."
    )

    force_update_after_create = fields.Boolean(
        help="Sometime, value need to be update after creation, because some compute broke it."
    )

    ignore_weekend = fields.Boolean()

    description = fields.Text()

    check_double_sms_process_id = fields.Many2one(
        comodel_name="planviewap.processus",
        string="Check double SMS process ID",
        help="Will check SMS history in this process, will execute the algorithm and compare the value to send difference reminder.",
    )

    sms_message_prefix = fields.Text()

    sms_message_card_meaning = fields.Char()

    sms_summary_phone = fields.Char(
        help=(
            "Separate by ; for multiple SMS destination. Will send a summary"
            " about the notification SMS for employee"
        )
    )

    sms_detect_card_type_msg_1 = fields.Text()

    sms_detect_card_type_msg_2 = fields.Text()

    sms_detect_card_type_msg_2_default_name = fields.Char()

    sms_detect_card_type_msg_2_msg = fields.Text()

    sms_detect_card_type_msg_2_filter = fields.Text()

    sms_enable_reverse_contact_msg_2_key = fields.Boolean()

    sms_reverse_contact_msg_2_key = fields.Char()

    sms_replace_card_name_to_msg = fields.Text()

    location_type_msg = fields.Char()

    lane_parent_name = fields.Char()

    lane_sub_name = fields.Char()

    lane_root_name = fields.Char()

    board_copy_to_id = fields.Many2one(
        comodel_name="planviewap.board",
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

    sms_unique_number = fields.Boolean(
        help="When create SMS, will ignore if same number already exist. This will remove duplicate number."
    )

    sms_bind_custom_field_phone_number = fields.Char(
        help="Will extract the number phone from this bind custom field."
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
        comodel_name="planviewap.sms.history",
        inverse_name="processus_id",
        string="SMS history",
    )

    board_id = fields.Many2one(
        comodel_name="planviewap.board",
        string="Board",
    )

    rename_card_pattern = fields.Char(help="The pattern need to contain '%s'")

    rename_week_lane_name_pattern = fields.Char(
        help="The pattern need to contain '%s'"
    )

    rename_dont_rename_day_with_number = fields.Boolean(
        help="When rename week, the day is recreate with a number, but not when this field is enable."
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

    board_enable_temp_delete_cards = fields.Boolean(
        help="If True, will enable delete cards and remove it after execution"
    )

    type_template_board_id = fields.Many2one(
        comodel_name="planviewap.board.type",
        string="Type Board depend",
        help="Will duplicate this board and fill it.",
    )

    type_board_depend_ids = fields.Many2many(
        comodel_name="planviewap.board.type",
        relation="type_board_ids_planviewap_processus_rel",
        string="Type template Board",
        help="This is optional, the system will check if has depend, if yes, will force to sync this board to operate processus.",
    )

    log_txt = fields.Text(string="Log")

    log_error_txt = fields.Text(string="Log error")

    depend_process_ids = fields.Many2many(
        comodel_name="planviewap.processus",
        relation="planviewap_processus_depend",
        column1="process_id1",
        column2="process_depend_id2",
        string="Depend Process",
        help="Will execute depend process before execute this process.",
    )

    process_execute_after_ids = fields.Many2many(
        comodel_name="planviewap.processus",
        relation="planviewap_processus_execute_after",
        column1="process_id1",
        column2="process_depend_id2",
        string="Process execute after",
        help="Will execute process after execute this process.",
    )

    def action_debug_show_first_day(self):
        for rec in self:
            user_timezone = timezone(
                self.env.context.get("tz") or self.env.user.tz or "UTC"
            )
            if not rec.lane_extract_algo:
                rec.debug_show_first_day = ""
            delay_in_day = rec.delay_in_day

            if rec.delay_in_day_plus_one_if_friday:
                weekday = self.env[
                    "planviewap.automated.action.log"
                ].get_weekday_now()
                if weekday == 4:
                    delay_in_day += 1

            elif rec.lane_extract_algo == "jour d/m":
                target_date = self.return_next_open_day(
                    datetime.datetime.now().astimezone(user_timezone),
                    delay_day=delay_in_day,
                    is_skipping_weekend=rec.ignore_weekend,
                )
                rec.debug_show_first_day = f"{target_date:%Y/%m/%d}"
            elif rec.lane_extract_algo in [
                "week d/m/y",
                "week d/m/y from today",
                "week d/m/y from tomorrow",
            ]:
                target_date = self.return_monday_day(
                    datetime.datetime.now().astimezone(user_timezone),
                    delay_week=delay_in_day,
                )
                rec.debug_show_first_day = f"{target_date:%Y/%m/%d}"

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

            sms_history_ids = self.env["planviewap.sms.history"]
            if rec.sms_debug:
                if rec.sms_to_number_phone:
                    for sms_to_number_phone in rec.sms_to_number_phone.split(
                        ";"
                    ):
                        sms_history_vals = {
                            "name": rec.sms_message_to_send,
                            "to_number_phone": sms_to_number_phone,
                            "processus_id": rec.id,
                            "session_id": rec.session_id.id,
                        }
                        sms_history_id = self.env[
                            "planviewap.sms.history"
                        ].create(sms_history_vals)
                        sms_history_ids += sms_history_id
            else:
                sms_history_ids = self.env["planviewap.sms.history"].search(
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
            user_timezone = timezone(
                self.env.context.get("tz") or self.env.user.tz or "UTC"
            )
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

            # Init execution
            if rec.board_enable_temp_delete_cards:
                if not rec.board_id:
                    raise ValueError(
                        "Missing board to configure temporary delete."
                    )
                rec.board_id.set_allow_user_to_delete_cards(default=True)

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

            if rec.custom_process_method_name:
                getattr(rec, rec.custom_process_method_name)(
                    ctx=ctx, start_time=start_time
                )
            elif rec.algo_key == "operate_lane":
                rec.operate_lane()
            elif rec.algo_key == "copy_cards_from_lane_from_board":
                rec.fill_board_id(use_from_board=True, raise_error=False)
            elif rec.algo_key == "move_root_lane_week":
                rec.algo_move_root_lane_week()
            elif rec.algo_key == "copy_cards_from_lane":
                rec.algo_copy_cards_from_lane(start_time)
            elif rec.algo_key == "alert_on_cards":
                rec.algo_alert_on_cards(start_time)
            elif rec.algo_key == "sync_cards_from_lane":
                rec.algo_sync_cards_from_lane(start_time)
            elif rec.algo_key == "send_sms":
                # TODO maybe can search employee information
                pass
            elif rec.algo_key == "send_sms_all_employee":
                rec.algo_send_annonce_sms_all_employee()
            elif rec.algo_key == "send_sms_schedule_week_summary":
                rec.algo_send_sms_schedule_week_summary()
            elif rec.algo_key == "send_sms_schedule":
                rec.algo_send_sms_schedule(
                    start_time,
                    dct_custom_field_to_field_name,
                    lst_bind_required_field_list,
                )
            elif rec.algo_key == "delete_cards":
                rec.algo_delete_cards()
            elif rec.algo_key == "validation_card":
                rec.algo_validation_card()
            elif rec.algo_key == "create_new_board":
                rec.algo_create_new_board(start_time)
            elif rec.algo_key == "create_card_from_model":
                rec.algo_create_card_from_model(start_time)
            elif rec.algo_key == "rename_lane":
                rec.algo_rename_lane(start_time)
            elif rec.algo_key == "create_model_from_card":
                rec.algo_create_model_from_card(
                    start_time,
                    dct_custom_field_to_field_name,
                    lst_bind_required_field_list,
                    force_refresh_custom_fields=rec.force_refresh_custom_fields,
                )

            if rec.board_enable_temp_delete_cards:
                if not rec.board_id:
                    raise ValueError(
                        "Missing board to configure temporary delete."
                    )
                rec.board_id.set_allow_user_to_delete_cards(default=False)

            msg_end = (
                f"End of execution processus '{rec.algo_key}' name"
                f" '{rec.name}' {rec.get_str_time_execution(start_time)}\n"
            )
            _logger.info(msg_end.strip())
            rec.log_txt += f"{msg_end}"
            rec.log_error_txt += f"{msg_end}"
            rec.add_log_time_execution(start_time)

    def internal_process_create_model_from_card(self, rec, model_id, card_id):
        pass

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
                if not model_id:
                    msg = f"WAR cannot retrieve model from card name '{card_id.name}'\n"
                    rec.log_txt += msg
                    rec.log_error_txt += msg
                    _logger.warning(msg.strip())

                rec.internal_process_create_model_from_card(
                    rec, model_id, card_id
                )

            rec.log_txt += "\n"
            rec.log_error_txt += "\n"

    def algo_rename_lane(self, start_time):
        user_timezone = timezone(
            self.env.context.get("tz") or self.env.user.tz or "UTC"
        )
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
                and rec.model_filter_hr_employee_job_type
            ):
                job_id = self.env["hr.job"].search(
                    [("name", "=", rec.model_filter_hr_employee_job_type)]
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

    def algo_create_new_board(self, start_time):
        user_timezone = timezone(
            self.env.context.get("tz") or self.env.user.tz or "UTC"
        )
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
            board_template_id = self.env["planviewap.board"].search(
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
            board_id = self.env["planviewap.board"].create(board_value)
            board_id.action_sync()

            # Execute processus of adding cards
            for process_id in rec.process_execute_after_ids:
                process_id.board_id = board_id.id

                # # For copy, the copy_from_board is actuel board
                # if process_id.algo_key == "copy_cards_from_lane_from_board":
                #     # Need to search this official board
                #     process_id.board_copy_to_id =

                process_id.action_execute_algo()

    def algo_send_sms_schedule_week_summary(self):
        for rec in self:
            card_ids = self.search_cards_from_processus(
                sync_cards=rec.force_sync_before_algo
            )

            dct_list_employee = defaultdict(list)
            for card_id in card_ids:
                if not card_id.custom_fields:
                    card_id.update_card_details()
                # Separate per name
                if not card_id.custom_fields:
                    continue
                lst_custom_fields = json.loads(card_id.custom_fields)
                employee_name = card_id.name
                is_cancel = False
                for dct_custom_fields in lst_custom_fields:
                    for bind_required_field in json.loads(
                        rec.bind_required_field_list
                    ):
                        if (
                            dct_custom_fields.get("label")
                            == bind_required_field
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

            sms_history_ids = self.env["planviewap.sms.history"]
            for employee_name, lst_card in dct_list_employee.items():
                # Separate per date
                dct_day = defaultdict(list)
                for card_id in lst_card:
                    dct_day[card_id.lane_parent_name].append(card_id)
                name, phone = employee_name.split("#")
                msg_employee = f"{rec.sms_message_prefix} Calendrier de la semaine pour {name}\n\n"
                # Reorder list from weekday
                lst_weekday = self._get_week_day_fr(ttype="list")
                for weekday in lst_weekday:
                    for str_day, lst_card_week in dct_day.items():
                        if str_day.startswith(weekday.upper()):
                            for card_week_id in lst_card_week:
                                str_date_time = str_day
                                if (
                                    card_week_id.size
                                    and card_week_id.size <= 24
                                ):
                                    str_date_time += f"({card_week_id.size}H)"
                                str_date_time += ": "
                                coule_msg = ""

                                if rec.sms_detect_card_type_msg_1:
                                    lst_type_card = (
                                        rec.sms_detect_card_type_msg_1.split(
                                            ";"
                                        )
                                    )
                                    type_card_msg_1_ids = self.env[
                                        "planviewap.card.type"
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
                                            "planviewap.card"
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
                                            # Show only with size and sorted in, take minimum
                                            lst_card_msg_1_ids = [
                                                a
                                                for a in card_msg_1_ids
                                                if a.size
                                            ]
                                            if lst_card_msg_1_ids:
                                                card_msg_1_ids = sorted(
                                                    lst_card_msg_1_ids,
                                                    key=lambda record: record.size,
                                                )[0]
                                            else:
                                                # No size, take first
                                                card_msg_1_ids = (
                                                    card_msg_1_ids[0]
                                                )
                                        if card_msg_1_ids:
                                            if (
                                                card_msg_1_ids.size
                                                and card_msg_1_ids.size <= 24
                                            ):
                                                coule_msg = f"Coulée à {card_msg_1_ids.size}H"
                                            else:
                                                coule_msg = "Coulée"

                                msg_employee += (
                                    f"{str_date_time}{card_week_id.lane_name}"
                                )
                                if coule_msg:
                                    msg_employee += f" - {coule_msg}"
                                msg_employee += "\n"
                msg_employee += "\nCompte-tenu de l'avancement des travaux, il est possible que l'horaire puisse changer en tout temps.\n\nUn SMS final vous sera envoyé tous les jours à 18H pour votre calendrier final du lendemain."
                sms_history_value = {
                    "to_number_phone": phone,
                    "name": msg_employee,
                    "processus_id": rec.id,
                    "session_id": rec.session_id.id,
                }

                sms_history_ids += self.env["planviewap.sms.history"].create(
                    sms_history_value
                )

    def algo_send_annonce_sms_all_employee(self):
        for rec in self:
            card_ids = rec.search_cards_from_processus(
                sync_cards=rec.force_sync_before_algo
            )
            if not rec.sms_bind_custom_field_phone_number:
                msg_txt = "ERR Cannot extract number phone from cards, please fill field sms_bind_custom_field_phone_number."
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                continue
            lst_number = card_ids.get_custom_field_value(
                rec.sms_bind_custom_field_phone_number
            )
            if not lst_number:
                msg_txt = "ERR No phone number to extract."
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                continue
            if rec.sms_unique_number:
                lst_number = list(set(lst_number))
            rec.sms_to_number_phone = ";".join(lst_number)

            msg_txt = f"Info Found number phone {rec.sms_to_number_phone}."
            rec.log_txt += msg_txt
            _logger.info(msg_txt.strip())

    def algo_send_sms_schedule(
        self,
        start_time,
        dct_custom_field_to_field_name,
        lst_bind_required_field_list,
    ):
        for rec in self:
            lst_value_sms = []
            dct_associate_card_name_with_sms = {}
            if rec.filter_field:
                lst_filter_field = json.loads(rec.filter_field)
            else:
                lst_filter_field = []

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
            i_msg = 0
            date_msg_str = ""
            msg_summary_sms = ""

            card_ids = rec.search_cards_from_processus(
                sync_cards=rec.force_sync_before_algo
            ).sorted("lane_name")

            dct_sms_replace_card_name_to_msg = (
                json.loads(rec.sms_replace_card_name_to_msg)
                if rec.sms_replace_card_name_to_msg
                else {}
            )

            dct_lane_summary = defaultdict(lambda: defaultdict(list))

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
                date_msg_str = card_id.lane_parent_name
                datetime_msg_str = date_msg_str
                msg_time = ""
                if card_id.size and card_id.size <= 24:
                    msg_time = f" à {card_id.size}h"
                    datetime_msg_str += msg_time
                use_replace_msg = False
                if (
                    dct_sms_replace_card_name_to_msg
                    and card_id.lane_name
                    in dct_sms_replace_card_name_to_msg.keys()
                ):
                    msg_template = dct_sms_replace_card_name_to_msg[
                        card_id.lane_name
                    ]
                    msg_sms += msg_template % (
                        employee_id.name,
                        datetime_msg_str,
                    )
                    use_replace_msg = True
                if not use_replace_msg:
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
                if not partner_id and not use_replace_msg:
                    # Ignore this error when it's a replacing msg
                    msg_txt = f"ERR missing partner associate with card {card_id.lane_name}\n"
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt
                    _logger.error(msg_txt.strip())
                # Detect msg 1 from card type
                if rec.sms_detect_card_type_msg_1:
                    lst_type_card = rec.sms_detect_card_type_msg_1.split(";")
                    type_card_msg_1_ids = self.env[
                        "planviewap.card.type"
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
                        card_msg_1_ids = self.env["planviewap.card"].search(
                            lst_query
                        )

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
                            # Show only with size and sorted in, take minimum
                            lst_card_msg_1_ids = [
                                a for a in card_msg_1_ids if a.size
                            ]
                            if lst_card_msg_1_ids:
                                card_msg_1_ids = sorted(
                                    lst_card_msg_1_ids,
                                    key=lambda record: record.size,
                                )[0]
                            else:
                                # No size, take first
                                card_msg_1_ids = card_msg_1_ids[0]
                        if card_msg_1_ids:
                            if (
                                card_msg_1_ids.size
                                and card_msg_1_ids.size <= 24
                            ):
                                msg_coule = (
                                    " + Coulée à" f" {card_msg_1_ids.size}H."
                                )
                            else:
                                msg_coule = " + Coulée."
                            msg_sms += msg_coule
                            msg_summary_sms += msg_coule
                if rec.sms_detect_card_type_msg_2:
                    lst_type_card = rec.sms_detect_card_type_msg_2.split(";")
                    type_card_msg_2_ids = self.env[
                        "planviewap.card.type"
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
                    if type_card_msg_2_ids:
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
                                type_card_msg_2_ids.ids,
                            ),
                        ]
                        card_msg_2_ids = self.env["planviewap.card"].search(
                            lst_query
                        )
                        if card_msg_2_ids:
                            for card_msg_2_id in card_msg_2_ids:
                                dct_lane_summary[card_msg_2_id.name][
                                    card_msg_2_id.lane_name
                                ].append(card_name)
                        elif (
                            rec.sms_detect_card_type_msg_2_default_name
                            and partner_id
                        ):
                            dct_lane_summary[
                                rec.sms_detect_card_type_msg_2_default_name
                            ][partner_id.name].append(card_name)
                        else:
                            msg_txt = "ERR Cannot detect associate card for type msg 2.\n"
                            rec.log_txt += msg_txt
                            rec.log_error_txt += msg_txt
                            _logger.error(msg_txt.strip())
                msg_summary_sms += "\n"
                if partner_id:
                    street_map = quote(partner_id.street)
                    msg_sms += (
                        "\nÀ l'adresse suivante : \n\n"
                        f"{partner_id.street}\n\nhttps://www.google.ca/maps/place/{street_map}"
                    )

                msg_txt = (
                    f"\nSMS({i_msg}) {msg_sms_log_debug}" f"«\n{msg_sms}\n»\n"
                )
                rec.log_txt += msg_txt

                value_sms = {
                    "to_number_phone_country": to_country,
                    "to_number_phone": employee_id.work_phone,
                    "from_number_phone_country": rec.session_id.sms_from_country_default,
                    "from_number_phone": rec.session_id.sms_from_number_phone_default,
                    # "group_execution_name": group_execution_name,
                    "processus_id": rec.id,
                    "session_id": rec.session_id.id,
                    "name": msg_sms,
                }

                lst_value_sms.append(value_sms)
                dct_associate_card_name_with_sms[msg_sms] = card_id.lane_name

            nb_msg_sommaire = i_msg
            if rec.check_double_sms_process_id:
                lst_value_sms, msg_summary_sms = (
                    rec.check_diff_sms_history_and_refactor_it(
                        lst_value_sms,
                        rec.check_double_sms_process_id,
                        date_msg_str,
                        dct_sms_replace_card_name_to_msg,
                        dct_associate_card_name_with_sms,
                        rec.sms_enable_reverse_contact_msg_2_key,
                        rec.sms_reverse_contact_msg_2_key,
                    )
                )
                nb_msg_sommaire = msg_summary_sms.count("\n")

            sms_history_ids = None
            if lst_value_sms:
                sms_history_ids = self.env["planviewap.sms.history"].create(
                    lst_value_sms
                )

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
            title_summary = (
                "Sommaire"
                if not rec.check_double_sms_process_id
                else "Sommaire des ajustements"
            )
            summary_final_msg = f"{rec.sms_message_prefix} {title_summary} ({nb_msg_sommaire} SMS) {date_msg_str}\n{msg_summary_sms}".strip()
            value_summary_sms["name"] = summary_final_msg
            rec.log_txt += "\n" + msg_summary_sms + "\n"

            for to_summary in rec.sms_summary_phone.split(";"):
                value_summary_sms["to_number_phone"] = to_summary
                sms_summary_history_id = self.env[
                    "planviewap.sms.history"
                ].create(value_summary_sms)

            # Support message 2
            for user_name, dct_place in dct_lane_summary.items():
                for place_name, lst_associate_name in dct_place.items():
                    employee_msg2_id = self.env["hr.employee"].search(
                        [("name", "=", user_name.title())],
                        limit=1,
                    )
                    if not rec.check_double_sms_process_id:
                        msg_sms_2 = (
                            ""
                            if not self.sms_message_prefix
                            else self.sms_message_prefix + " "
                        )
                        # lst_filter_associate_name = [a for a in lst_associate_name if a != user_name]
                        msg_associate_name = ""
                        for associate_name in sorted(lst_associate_name):
                            employee_associate_msg2_id = self.env[
                                "hr.employee"
                            ].search(
                                [("name", "=", associate_name.title())],
                                limit=1,
                            )
                            if employee_associate_msg2_id:
                                if employee_associate_msg2_id.pvap_card_id:
                                    # TODO missing employe job
                                    msg_associate_name += f"{associate_name.title()} - {employee_associate_msg2_id.work_phone} - {employee_associate_msg2_id.pvap_card_id.entete}\n"
                                else:
                                    msg_associate_name += f"{associate_name.title()} - {employee_associate_msg2_id.work_phone}\n"
                            else:
                                msg_associate_name += (
                                    f"{associate_name.title()}\n"
                                )
                        if (
                            place_name
                            not in rec.sms_detect_card_type_msg_2_filter.split(
                                ";"
                            )
                        ):
                            transform_msg = (
                                rec.sms_detect_card_type_msg_2_msg
                                % (
                                    date_msg_str,
                                    place_name,
                                    msg_associate_name,
                                )
                            )
                            msg_sms_2 += transform_msg.replace("\\n", "\n")
                            value_msg2_sms = {
                                "name": msg_sms_2,
                                "to_number_phone_country": to_country,
                                "to_number_phone": employee_msg2_id.work_phone,
                                "from_number_phone_country": rec.session_id.sms_from_country_default,
                                "from_number_phone": rec.session_id.sms_from_number_phone_default,
                                # "group_execution_name": group_execution_name,
                                "processus_id": rec.id,
                                "session_id": rec.session_id.id,
                            }
                            sms_2_id = self.env[
                                "planviewap.sms.history"
                            ].create(value_msg2_sms)
                    if rec.sms_enable_reverse_contact_msg_2_key:
                        # Upgrade with contact information
                        sms_history_to_update_msg2_ids = (
                            sms_history_ids.filtered(
                                lambda x: f"«{place_name}»" in x.name
                            )
                        )
                        for (
                            sms_history_to_update_msg2_id
                        ) in sms_history_to_update_msg2_ids:
                            key_msg2 = (
                                "Contact :"
                                if not rec.sms_reverse_contact_msg_2_key
                                else rec.sms_reverse_contact_msg_2_key
                            )
                            msg_to_append_msg2 = f"\n{key_msg2} {employee_msg2_id.name} {employee_msg2_id.work_phone}"
                            sms_history_to_update_msg2_id.name += (
                                msg_to_append_msg2
                            )
            print("End algo_send_sms_schedule")

    def check_diff_sms_history_and_refactor_it(
        self,
        lst_value_sms,
        process_id,
        str_date,
        dct_sms_replace_card_name_to_msg,
        dct_associate_card_name_with_sms,
        sms_reverse_contact_msg_2_key,
        sms_enable_reverse_contact_msg_2_key,
    ):
        self.ensure_one()
        if not lst_value_sms:
            return [], ""
        lst_new_value_sms = []
        msg_summary_sms = ""
        lst_unique_phone = list(
            set(
                [a.get("to_number_phone") for a in lst_value_sms]
                + [a.to_number_phone for a in process_id.sms_history_ids]
            )
        )
        i = 0
        for phone in lst_unique_phone:
            # Support detect new card, less card, no card, modifying card
            lst_new_sms_history = sorted(
                [
                    a.get("name")
                    for a in lst_value_sms
                    if a.get("to_number_phone") == phone
                ]
            )
            lst_existing_sms_history = sorted(
                [
                    a.name
                    for a in process_id.sms_history_ids
                    if a.to_number_phone == phone
                    and "Sommaire (" not in a.name
                    and "Voici ton équipe" not in a.name
                ]
            )
            # Hack the lst_existing_sms_history
            # TODO enable this hack with sms_enable_reverse_contact_msg_2_key
            if sms_reverse_contact_msg_2_key:
                new_list_lst_existing_sms_history = []
                for sms_history_to_hack in lst_existing_sms_history:
                    lst_sms_history_to_hack = [
                        a
                        for a in sms_history_to_hack.split("\n")
                        if not a.startswith(sms_reverse_contact_msg_2_key)
                    ]
                    new_list_lst_existing_sms_history.append(
                        "\n".join(lst_sms_history_to_hack)
                    )
                lst_existing_sms_history = new_list_lst_existing_sms_history
            # TODO work_phone is hardcoded, need to use bind
            employee_id = self.env["hr.employee"].search(
                [("work_phone", "=", phone)],
                limit=1,
            )
            if not employee_id:
                msg_txt = (
                    f"ERR Cannot find employee from number phone {phone}.\n"
                )
                self.log_txt += msg_txt
                self.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                continue
            if lst_new_sms_history != lst_existing_sms_history:
                # Detect a difference, will resend a new schedule for this employee
                msg_sms = (
                    ""
                    if not self.sms_message_prefix
                    else self.sms_message_prefix + " "
                )
                msg_sms += employee_id.name + ", "
                if not lst_new_sms_history:
                    msg_sms += f"vous n'avez plus d'horaire de planifié pour le {str_date}"

                    dct_message = lst_value_sms[0].copy()
                    dct_message["name"] = msg_sms
                    dct_message["to_number_phone"] = phone
                    lst_new_value_sms.append(dct_message)

                    i += 1
                    msg_summary_sms += (
                        f"#{i} {employee_id.name} est enlevé de l'horaire.\n"
                    )
                else:
                    msg_sms += f"affection modifiée de dernière minute, tu vas travailler le {str_date}, au chantier "
                    str_key = "au chantier"
                    # Exception no affection
                    if (
                        len(lst_new_sms_history) == 1
                        and len(lst_existing_sms_history) == 1
                    ):
                        if (
                            "il n'y a pas d'affection"
                            in lst_new_sms_history[0]
                            and "il n'y a pas d'affection"
                            in lst_existing_sms_history[0]
                        ):
                            # Ignore it
                            continue
                        if (
                            "tu dois te rendre le" in lst_new_sms_history[0]
                            and "tu dois te rendre à l'entrepôt"
                            in lst_existing_sms_history[0]
                        ):
                            # Ignore it
                            continue
                    for new_sms_history in lst_new_sms_history:
                        msg_cut = new_sms_history[
                            new_sms_history.find(str_key) + len(str_key) + 1 :
                        ]
                        # Detect time
                        pos_date = new_sms_history.find(str_date) + len(
                            str_date
                        )
                        after_pos_date = new_sms_history.find(",", pos_date)
                        date_time_job = ""
                        if pos_date != after_pos_date:
                            date_time_job = new_sms_history[
                                pos_date:after_pos_date
                            ]
                            msg_sms_with_time = msg_sms.replace(
                                str_date, str_date + date_time_job
                            )
                        else:
                            msg_sms_with_time = msg_sms

                        dct_message = lst_value_sms[0].copy()
                        card_lane_name = dct_associate_card_name_with_sms.get(
                            new_sms_history
                        )
                        if (
                            dct_sms_replace_card_name_to_msg
                            and card_lane_name
                            in dct_sms_replace_card_name_to_msg.keys()
                        ):
                            msg_template = dct_sms_replace_card_name_to_msg[
                                card_lane_name
                            ]

                            msg_sms = (
                                ""
                                if not self.sms_message_prefix
                                else self.sms_message_prefix + " "
                            )
                            msg_sms += msg_template % (
                                employee_id.name,
                                str_date,
                            )

                            dct_message["name"] = msg_sms
                            msg_for_summary = f"«{card_lane_name}»"
                        else:
                            dct_message["name"] = msg_sms_with_time + msg_cut
                            msg_for_summary = msg_cut[: msg_cut.find("\n")]
                            if date_time_job:
                                msg_for_summary = msg_for_summary.replace(
                                    "»", f"» {date_time_job}"
                                )

                        dct_message["to_number_phone"] = phone
                        lst_new_value_sms.append(dct_message)

                        i += 1
                        msg_summary_sms += (
                            f"#{i} {employee_id.name} {msg_for_summary}\n"
                        )
        return lst_new_value_sms, msg_summary_sms

    def algo_delete_cards(self):
        for rec in self:
            card_ids = rec.search_cards_from_processus()

            if card_ids.exists():
                card_ids.enabled_bind = True
                card_ids.unlink()

    def algo_validation_card(self):
        for rec in self:
            card_ids = rec.search_cards_from_processus()
            has_error = False

            for card_id in card_ids:
                if rec.validation_target_achieved:
                    target_achieved = card_id.get_str_target_achieved()
                    if rec.validation_target_achieved != target_achieved:
                        # TODO create record error
                        msg_txt = f"ERR card on lane {card_id.lane_name} and lane parent {card_id.lane_parent_name} with target achieved {target_achieved}, expected {rec.validation_target_achieved}\n"
                        rec.log_txt += msg_txt
                        rec.log_error_txt += msg_txt
                        _logger.error(msg_txt.strip())
                        has_error = True
                if (
                    rec.validation_algo
                    and rec.validation_algo
                    == "negative_same_name_different_size"
                ):
                    _logger.warning(
                        f"Not supported algo {rec.validation_algo}"
                    )
                elif (
                    rec.validation_algo
                    and rec.validation_algo
                    == "associate_card_location_inclusion"
                ):
                    # Search associate card location
                    location_card_id = self.env["planviewap.card"].search(
                        [("entete", "=", card_id.lane_name)]
                    )
                    lst_inclusion = location_card_id.get_custom_field_value(
                        rec.validation_location_custom_field_name
                    )
                    if (
                        rec.validation_location_custom_field_expected_value
                        in lst_inclusion
                    ):
                        card_type_associate_id = self.env[
                            "planviewap.card.type"
                        ].search(
                            [
                                (
                                    "name",
                                    "=",
                                    rec.validation_location_expected_associate_type_card_same_lane,
                                )
                            ]
                        )
                        if not card_type_associate_id:
                            msg_txt = f"ERR missing card type {rec.validation_location_expected_associate_type_card_same_lane}\n"
                            rec.log_txt += msg_txt
                            rec.log_error_txt += msg_txt
                            _logger.error(msg_txt.strip())
                            has_error = True
                            continue
                        associate_validation_card_id = self.env[
                            "planviewap.card"
                        ].search(
                            [
                                ("lane_id", "=", card_id.lane_id.id),
                                (
                                    "card_type_id",
                                    "=",
                                    card_type_associate_id.id,
                                ),
                            ]
                        )
                        if not associate_validation_card_id:
                            # TODO create record error
                            msg_txt = f"ERR validation error, missing card type {rec.validation_location_expected_associate_type_card_same_lane} into lane {card_id.lane_name} associate with card name {card_id.name} on day {card_id.lane_parent_name}\n"
                            rec.log_txt += msg_txt
                            rec.log_error_txt += msg_txt
                            _logger.error(msg_txt.strip())
                            has_error = True
                            continue
                        if (
                            rec.validation_location_expected_associate_different_size
                        ):
                            if (
                                associate_validation_card_id.size
                                == rec.validation_location_expected_associate_different_size
                            ):
                                # TODO create record error
                                msg_txt = f"ERR validation error, associate card {rec.validation_location_expected_associate_type_card_same_lane} into lane {card_id.lane_name} associate with card name {card_id.name} on day {card_id.lane_parent_name} need a different size from {rec.validation_location_expected_associate_different_size}\n"
                                rec.log_txt += msg_txt
                                rec.log_error_txt += msg_txt
                                _logger.error(msg_txt.strip())
                                has_error = True
                        associate_validation_card_id.update_card_details()
                        target = (
                            associate_validation_card_id.get_str_target_achieved()
                        )
                        if (
                            target
                            != rec.validation_location_expected_associate_target_achieve
                        ):
                            # TODO create record error
                            msg_txt = f"ERR validation error, associate card {rec.validation_location_expected_associate_type_card_same_lane} into lane {card_id.lane_name} associate with card name {card_id.name} on day {card_id.lane_parent_name} need target achieve {rec.validation_location_expected_associate_target_achieve}\n"
                            rec.log_txt += msg_txt
                            rec.log_error_txt += msg_txt
                            _logger.error(msg_txt.strip())
                            has_error = True
            if not has_error:
                msg_txt = f"LOG Success no error validation.\n"
                rec.log_txt += msg_txt
                _logger.info(msg_txt.strip())

    def algo_move_root_lane_week(self):
        lst_day_name = self._get_week_day_fr(ttype="list")
        for rec in self:
            lst_lane_week_and_date = rec._get_all_week_lane(
                return_date_monday=True
            )
            lst_lane_week_and_date.sort(key=lambda x: x[1])
            if rec.rename_week_lane_name_icon:
                lst_icon = rec.rename_week_lane_name_icon.split(";")
            else:
                lst_icon = []
            # Detect first week, delete all cards
            # Detect second week, move all cards to first week, rename lane and repeat
            # Last week, create a new week
            last_week_done = None
            for i_week, lst_data in enumerate(lst_lane_week_and_date):
                lane_week_id, lane_date = lst_data
                is_last_week = i_week == len(lst_lane_week_and_date) - 1
                if not last_week_done:
                    lane_week_id.delete_all_cards()
                if last_week_done:
                    lane_week_id.move_to_lane(last_week_done)
                last_week_done = lane_week_id
                if is_last_week:
                    next_week = lane_date + datetime.timedelta(weeks=1)
                    # Rename week to next week
                    if "%s" in rec.rename_week_lane_name_pattern:
                        value_pattern = f"{next_week.day} {self._get_month_fr(ttype='str', value=next_week.month - 1).upper()} {next_week.year}"
                        lane_week_new_name = (
                            rec.rename_week_lane_name_pattern % value_pattern
                        )
                    else:
                        lane_week_new_name = rec.rename_week_lane_name_pattern
                    if lst_icon:
                        lane_week_new_name = (
                            f"{lst_icon[-1]} {lane_week_new_name}"
                        )
                    lane_week_id.with_context(
                        {"enable_sync_lane": True}
                    ).title = lane_week_new_name
                    # Rename child day
                    next_day = next_week
                    for i_day, lane_child_day_id in enumerate(
                        lane_week_id.lane_child_ids
                    ):
                        if rec.rename_dont_rename_day_with_number:
                            day_name = f"{lst_day_name[i_day].upper()}"
                        else:
                            day_name = f"{lst_day_name[i_day].upper()} {next_day.day}/{next_day.month}"
                        lane_child_day_id.with_context(
                            {"enable_sync_lane": True}
                        ).title = day_name
                        next_day += datetime.timedelta(days=1)

    def algo_sync_cards_from_lane(self, start_time):
        for rec in self:
            count_card_to_sync = 0
            count_card_to_no_sync = 0
            card_ids = rec.search_cards_from_processus()
            for card_sync_id in card_ids:
                # Search associate card
                card_to_sync_ids = self.env["planviewap.card"].search(
                    [
                        ("board_id", "=", rec.board_id.id),
                        ("card_id_pvap", "!=", card_sync_id.card_id_pvap),
                        ("name", "=", card_sync_id.name),
                        ("custom_fields", "!=", card_sync_id.custom_fields),
                    ]
                )
                card_to_no_sync_ids = self.env["planviewap.card"].search(
                    [
                        ("board_id", "=", rec.board_id.id),
                        ("card_id_pvap", "!=", card_sync_id.card_id_pvap),
                        ("name", "=", card_sync_id.name),
                        ("custom_fields", "!=", card_sync_id.custom_fields),
                    ]
                )
                count_card_to_no_sync += len(card_to_no_sync_ids)
                for card_to_sync_id in card_to_sync_ids:
                    # Be sure it's different
                    lst_dct_to_sync = json.loads(card_to_sync_id.custom_fields)
                    lst_dct_sync = json.loads(card_sync_id.custom_fields)
                    is_same = self.compare_custom_fields(
                        lst_dct_to_sync, lst_dct_sync
                    )
                    if not is_same:
                        count_card_to_sync += 1
                        card_to_sync_id.with_context(
                            {"enable_sync_card": True}
                        ).custom_fields = card_sync_id.custom_fields
                    else:
                        count_card_to_no_sync += 1
            msg_txt = f"LOG Update {count_card_to_sync} cards with sync algorithm VS {count_card_to_no_sync} no need to sync.\n"
            rec.log_txt += msg_txt
            _logger.info(msg_txt.strip())

    @staticmethod
    def compare_custom_fields(liste1, liste2):
        ensemble1 = {c.get("label"): c.get("value") for c in liste1}
        ensemble2 = {c.get("label"): c.get("value") for c in liste2}
        return ensemble1 == ensemble2

    def algo_alert_on_cards(self, start_time):
        for rec in self:
            # System alert
            if rec.alert_wrong_lane_agencement:
                dct_info = {}
                lane_ids = rec.search_lanes_from_processus(
                    sync_cards=rec.force_sync_before_algo
                )
                for root_lane_id in lane_ids:
                    for lvl2_lane_id in root_lane_id.lane_child_ids:
                        lst_col_name = lvl2_lane_id.lane_child_ids.sorted(
                            "sequence"
                        ).mapped("title")
                        info_name = (
                            f"{root_lane_id.title}\n{lvl2_lane_id.title}"
                        )
                        dct_info[info_name] = lst_col_name
                # TODO compare all dct_info
                msg_txt = ""
                set_info = {}
                i = 0
                for info_name, lst_info in dct_info.items():
                    if not set_info:
                        set_info = set(lst_info)
                    else:
                        set_lst_info = set(lst_info)
                        lst_diff = set_info.difference(set_lst_info)
                        lst_diff2 = set_lst_info.difference(set_info)
                        if lst_diff or lst_diff2:
                            i += 1
                            msg_txt += (
                                f"#{i} "
                                + info_name.replace("\n", " // ")
                                + "\n"
                            )
                        if lst_diff:
                            msg_txt += "Missing : " + str(lst_diff) + "\n"
                        if lst_diff2:
                            msg_txt += "Missing : " + str(lst_diff2) + "\n"
                        if lst_diff or lst_diff2:
                            msg_txt += "\n"
                        # print(info_name)
                        # print(lst_diff)
                rec.log_txt += msg_txt
                if not dct_info:
                    msg_txt = (
                        "ERR Cannot get information to validation structure.\n"
                    )
                    rec.log_error_txt += msg_txt
                    rec.log_txt += msg_txt
                    _logger.error(msg_txt.strip())
                    rec.add_log_time_execution(start_time)
                continue
            card_ids = rec.search_cards_from_processus(
                sync_cards=rec.force_sync_before_algo
            )
            if not card_ids:
                msg_txt = "ERR Cannot find cards.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                rec.add_log_time_execution(start_time)
                continue
            lst_msg_alert = []

            for card_id in card_ids:
                msg_sms = (
                    ""
                    if not rec.sms_message_prefix
                    else rec.sms_message_prefix + " "
                )

                # Alert on min size
                if (
                    rec.alert_min_size_card_enable
                    and card_id.size < rec.alert_min_size_card
                ):
                    card_name = (
                        card_id.card_type_id.name + " - " + card_id.name
                    )
                    lane_name = (
                        card_id.lane_name
                        if not card_id.lane_parent_name
                        else card_id.lane_name
                        + " - "
                        + card_id.lane_parent_name
                    )
                    context_meaning_msg = (
                        ""
                        if not rec.sms_message_card_meaning
                        else rec.sms_message_card_meaning
                        + " "
                        + lane_name
                        + " "
                    )
                    msg_min_size = _(
                        "La carte %s %s est de taille %s et devrait être plus grand que %s."
                    ) % (
                        card_name,
                        context_meaning_msg,
                        card_id.size,
                        rec.alert_min_size_card,
                    )
                    msg_alert = f"{msg_sms}{msg_min_size}"

                    # Add URL to the card
                    msg_alert += (
                        f"\n{rec.session_id.name}/card/{card_id.card_id_pvap}"
                    )
                    lst_msg_alert.append(msg_alert)

                # Alert on max size
                if (
                    rec.alert_max_size_card_enable
                    and card_id.size > rec.alert_max_size_card
                ):
                    card_name = (
                        card_id.card_type_id.name + " - " + card_id.name
                    )
                    lane_name = (
                        card_id.lane_name
                        if not card_id.lane_parent_name
                        else card_id.lane_name
                        + " - "
                        + card_id.lane_parent_name
                    )
                    context_meaning_msg = (
                        ""
                        if not rec.sms_message_card_meaning
                        else rec.sms_message_card_meaning
                        + " "
                        + lane_name
                        + " "
                    )
                    msg_max_size = _(
                        "La carte %s %s est de taille %s et devrait être plus petit que %s."
                    ) % (
                        card_name,
                        context_meaning_msg,
                        card_id.size,
                        rec.alert_max_size_card,
                    )
                    msg_alert = f"{msg_sms}{msg_max_size}"

                    # Add URL to the card
                    msg_alert += (
                        f"\n{rec.session_id.name}/card/{card_id.card_id_pvap}"
                    )
                    lst_msg_alert.append(msg_alert)

            # Alert on min count cards into lane
            if (
                rec.alert_min_count_card_enable
                and len(card_ids) < rec.alert_min_count_card
            ):
                msg_sms = (
                    ""
                    if not rec.sms_message_prefix
                    else rec.sms_message_prefix + " "
                )
                colonne_name = " - ".join(set([a.lane_name for a in card_ids]))
                lane_name_ordered_ids = (
                    card_ids.lane_parent_id.sorted_all_by_sequence()
                )
                lane_name = (
                    colonne_name
                    + " "
                    + " - ".join([a.title for a in lane_name_ordered_ids])
                )
                if rec.alert_count_card_msg:
                    msg_min_count = rec.alert_count_card_msg % (lane_name,)
                else:
                    msg_min_count = _(
                        "La colonne %s contient %s cartes et devrait contenir plus de %s cartes."
                    ) % (
                        lane_name,
                        len(card_ids),
                        rec.alert_min_count_card - 1,
                    )
                msg_alert = f"{msg_sms}{msg_min_count}"

                # Add URL to the card
                for card_id in card_ids:
                    msg_alert += (
                        f"\n{rec.session_id.name}/card/{card_id.card_id_pvap}"
                    )
                lst_msg_alert.append(msg_alert)

            # Alert on max count cards into lane
            if (
                rec.alert_max_count_card_enable
                and len(card_ids) > rec.alert_max_count_card
            ):
                msg_sms = (
                    ""
                    if not rec.sms_message_prefix
                    else rec.sms_message_prefix + " "
                )
                colonne_name = " - ".join(set([a.lane_name for a in card_ids]))
                lane_name_ordered_ids = (
                    card_ids.lane_parent_id.sorted_all_by_sequence()
                )
                lane_name = (
                    colonne_name
                    + " "
                    + " - ".join([a.title for a in lane_name_ordered_ids])
                )
                if rec.alert_count_card_msg:
                    msg_max_count = rec.alert_count_card_msg % (lane_name,)
                else:
                    msg_max_count = _(
                        "La colonne %s contient %s cartes et devrait contenir moins de %s cartes."
                    ) % (
                        lane_name,
                        len(card_ids),
                        rec.alert_max_count_card + 1,
                    )
                msg_alert = f"{msg_sms}{msg_max_count}"

                # Add URL to the card
                for card_id in card_ids[:3]:
                    msg_alert += (
                        f"\n{rec.session_id.name}/card/{card_id.card_id_pvap}"
                    )
                if len(card_ids) > 3:
                    msg_alert += "\n[...]"
                lst_msg_alert.append(msg_alert)

            # Send message
            for i_msg, msg_alert in enumerate(lst_msg_alert):
                msg_sms_log_debug = ""
                msg_txt = (
                    f"\nSMS({i_msg}) {msg_sms_log_debug}"
                    f"«\n{msg_alert}\n»\n"
                )
                rec.log_txt += msg_txt

                lst_phone = (
                    rec.sms_to_number_phone.split(";")
                    if rec.sms_to_number_phone
                    else rec.session_id.sms_to_number_phone_default.split(";")
                )
                for number_phone in lst_phone:
                    value_sms = {
                        "to_number_phone_country": rec.session_id.sms_to_country_default,
                        "to_number_phone": number_phone,
                        "from_number_phone_country": rec.session_id.sms_from_country_default,
                        "from_number_phone": rec.session_id.sms_from_number_phone_default,
                        # "group_execution_name": group_execution_name,
                        "processus_id": rec.id,
                        "session_id": rec.session_id.id,
                        "name": msg_alert,
                    }
                    sms_history_id = self.env["planviewap.sms.history"].create(
                        value_sms
                    )

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
            lane_to_copy_ids = lane_to_copy_ids.sorted_all_by_sequence()

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
                card_to_delete_ids = self.env["planviewap.card"].search(
                    [
                        ("lane_id", "in", lane_to_copy_ids.ids),
                        ("board_id", "=", rec.board_id.id),
                    ]
                )
                if card_to_delete_ids:
                    card_to_delete_ids.enabled_bind = True
                    card_to_delete_ids.unlink()

            # Get all cards to copy
            card_to_copy_ids = self.env["planviewap.card"].search(
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
                            "custom_fields": card_to_copy_id.custom_fields,
                            "description": card_to_copy_id.description,
                            "assigned_users": card_to_copy_id.assigned_users,
                            "session_id": rec.session_id.id,
                        }
                        self.env["planviewap.card"].create(data)

    def _get_lane_from_regex_day(self):
        self.ensure_one()
        rec = self
        user_timezone = timezone(
            self.env.context.get("tz") or self.env.user.tz or "UTC"
        )
        find_lane_ids = self.env["planviewap.lane"]
        lane_ids = self.env["planviewap.lane"].search(
            [("board_id", "=", rec.board_id.id)]
        )
        regex = r"(?P<jour>[A-Z]+)\s+(?P<journee>\d+)/(?P<mois>\d+)"

        delay_in_day = rec.delay_in_day
        if rec.delay_in_day_plus_one_if_friday:
            weekday = self.env[
                "planviewap.automated.action.log"
            ].get_weekday_now()
            if weekday == 4:
                delay_in_day += 1

        next_day = self.return_next_open_day(
            datetime.datetime.now().astimezone(user_timezone),
            delay_day=delay_in_day,
            is_skipping_weekend=rec.ignore_weekend,
        )

        for lane_id in lane_ids:
            result = re.search(regex, lane_id.title)
            if not result:
                continue
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
        elif ttype == "int":
            return lst_value.index(value) + 1
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

    def _get_lane_from_regex_week(
        self, ignore_before_today=False, ignore_before_tomorrow=False
    ):
        user_timezone = timezone(
            self.env.context.get("tz") or self.env.user.tz or "UTC"
        )
        time_now = (
            datetime.datetime.now()
            .astimezone(user_timezone)
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )
        time_tomorrow = time_now + datetime.timedelta(days=1)
        mois_en_francais = self._get_month_fr()
        find_lane_ids = self.env["planviewap.lane"]
        regex = r"(?P<journee>\d{1,2})\s+(?P<mois>\w+)\s+(?P<annee>\d{4})"
        for rec in self:
            delay_in_day = rec.delay_in_day
            if self.delay_in_day_plus_one_if_friday:
                weekday = self.env[
                    "planviewap.automated.action.log"
                ].get_weekday_now()
                if weekday == 4:
                    delay_in_day += 1

            lane_ids = self.env["planviewap.lane"].search(
                [
                    ("board_id", "=", rec.board_id.id),
                    ("lane_parent_id", "=", False),
                ]
            )
            monday_day = self.return_monday_day(
                time_now,
                delay_week=delay_in_day,
            )
            for lane_id in lane_ids:
                result = re.search(regex, lane_id.title)
                if not result:
                    continue
                if (
                    rec.get_all_week
                    or mois_en_francais[monday_day.strftime("%B")]
                    == result.group("mois").title()
                    and monday_day.day == int(result.group("journee"))
                    and monday_day.year == int(result.group("annee"))
                ):
                    if (
                        rec.search_lane_required_string
                        and rec.search_lane_required_string
                        not in lane_id.title
                    ):
                        # Ignore this value
                        continue
                    if not ignore_before_today and not ignore_before_tomorrow:
                        find_lane_ids += lane_id
                    else:
                        for under_lane_id in lane_id.lane_child_ids:
                            # extract inner day
                            regex_day = r"(?P<jour>[A-Z]+)\s+(?P<journee>\d+)/(?P<mois>\d+)"
                            result_day = re.search(
                                regex_day, under_lane_id.title
                            )
                            if not result:
                                continue
                            check_date = user_timezone.localize(
                                datetime.datetime(
                                    int(result.group("annee")),
                                    int(result_day.group("mois")),
                                    int(result_day.group("journee")),
                                )
                            )
                            if (
                                ignore_before_today and check_date >= time_now
                            ) or (
                                ignore_before_tomorrow
                                and check_date >= time_tomorrow
                            ):
                                find_lane_ids += under_lane_id
        return find_lane_ids

    def _get_lane_from_pattern(self):
        find_lane_ids = self.env["planviewap.lane"]
        for rec in self:
            lane_ids = self.env["planviewap.lane"].search(
                [
                    ("board_id", "=", rec.board_id.id),
                    ("lane_parent_id", "=", False),
                ]
            )
            for lane_id in lane_ids:
                if rec.search_lane_required_string in lane_id.title:
                    find_lane_ids += lane_id
        return find_lane_ids

    def _get_all_week_lane(self, return_date_monday=False):
        find_lane_ids = self.env["planviewap.lane"]
        lst_return_date_monday = []
        regex = r"(?P<journee>\d{1,2})\s+(?P<mois>\w+)\s+(?P<annee>\d{4})"
        for rec in self:
            lane_ids = self.env["planviewap.lane"].search(
                [
                    ("board_id", "=", rec.board_id.id),
                    ("lane_parent_id", "=", False),
                ]
            )
            for lane_id in lane_ids:
                result = re.search(regex, lane_id.title)
                if not result:
                    continue
                find_lane_ids += lane_id
                day = int(result.group("journee"))
                month = self._get_month_fr(
                    ttype="int", value=result.group("mois").title()
                )
                year = int(result.group("annee"))
                lane_date = datetime.date(year, month, day)
                if (
                    rec.search_lane_required_string
                    and rec.search_lane_required_string not in lane_id.title
                ):
                    # Ignore this value
                    continue
                lst_return_date_monday.append((lane_id, lane_date))

        if not return_date_monday:
            return find_lane_ids
        return lst_return_date_monday

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
            try:
                lst_custom_field = json.loads(card_id.custom_fields)
            except Exception as e:
                lst_custom_field = None
                msg_txt = f"ERR card name '{card_id.name}' card entete '{card_id.entete}', missing custom fields.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
        if not lst_custom_field:
            msg_txt = f"ERR '{rec.model_name}' Missing custom fields\n"
            rec.log_txt += msg_txt
            rec.log_error_txt += msg_txt
        # Bind value
        else:
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
                            and custom_field_name
                            in lst_bind_required_field_list
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

        # if rec.create_more_field:
        #     try:
        #         create_more_field = json.loads(rec.create_more_field)
        #         for field_name_bind, model_info_bind in create_more_field.items():
        #             model_name_bind = model_info_bind.get("model")
        #             new_model_value[field_name_bind] = self.env[model_name_bind].create({"name": new_model_value.get("name")}).id
        #     except Exception as e:
        #         lst_custom_field = None
        #         msg_txt = f"ERR card name '{card_id.name}' card entete '{card_id.entete}', fail to load rec.create_more_field value '{rec.create_more_field}'.\n"
        #         rec.log_txt += msg_txt
        #         rec.log_error_txt += msg_txt
        #         _logger.error(msg_txt.strip())
        if (
            rec.create_more_field_algo
            and rec.create_more_field_algo == "fsm.equipment with stock"
        ):
            # Create product
            product_id = self.env["product.product"].create(
                {"name": new_model_value.get("name")}
            )
            new_model_value["product_id"] = product_id.id
            # Create lot
            lot_id = self.env["stock.lot"].create(
                {
                    "name": new_model_value.get("name"),
                    "product_id": product_id.id,
                }
            )
            new_model_value["lot_id"] = lot_id.id

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
        self, sync_cards=True, limit=-1, order="sequence asc"
    ):
        for rec in self:
            return rec.search_lanes(
                rec.name,
                rec.board_id,
                rec.lane_root_name,
                lane_extract_algo=rec.lane_extract_algo,
                lane_parent_name=rec.lane_parent_name,
                lane_sub_name=rec.lane_sub_name,
                exclude_lane_name=rec.exclude_lane_name,
                get_all_lane=rec.get_all_lane,
                is_root_lane=rec.is_root_lane,
                lane_name=rec.lane_name,
                sync_cards=sync_cards,
                extract_only_root_lane=rec.extract_only_root_lane,
                limit=limit,
                order=order,
                log_txt=rec.log_txt,
                log_error_txt=rec.log_error_txt,
            )

    def search_lanes(
        self,
        process_name,
        board_id,
        lane_root_name=None,
        lane_extract_algo=None,
        lane_parent_name=None,
        lane_sub_name=None,
        exclude_lane_name=None,
        get_all_lane=False,
        lane_name=None,
        is_root_lane=False,
        sync_cards=True,
        extract_only_root_lane=False,
        limit=-1,
        order=None,
        log_txt=None,
        log_error_txt=None,
    ):
        self.ensure_one()
        lst_lane_name = [] if not lane_name else lane_name.split(";")
        if lane_extract_algo:
            if lane_extract_algo == "jour d/m":
                lane_root_ids = self._get_lane_from_regex_day()
                is_root_lane = True
            elif lane_extract_algo in [
                "week d/m/y",
                "week d/m/y from today",
                "week d/m/y from tomorrow",
            ]:
                ignore_before_today = lane_extract_algo in [
                    "week d/m/y from today"
                ]
                ignore_before_tomorrow = lane_extract_algo in [
                    "week d/m/y from tomorrow"
                ]
                lane_root_ids = self._get_lane_from_regex_week(
                    ignore_before_today=ignore_before_today,
                    ignore_before_tomorrow=ignore_before_tomorrow,
                )
                if ignore_before_today or ignore_before_tomorrow:
                    lane_parent_name = ";".join(
                        [a.title for a in lane_root_ids]
                    )
                    lane_root_ids = None
            elif lane_extract_algo == "pattern":
                lane_root_ids = self._get_lane_from_pattern()
            else:
                msg_txt = f"ERR processus '{process_name}' not supported lane_extract_algo {lane_extract_algo}.\n"
                if log_txt:
                    log_txt += msg_txt
                if log_error_txt:
                    log_error_txt += msg_txt
                return
        else:
            if not lane_root_name and not get_all_lane:
                msg_txt = f"ERR processus '{process_name}' root lane name is empty.\n"
                if log_txt:
                    log_txt += msg_txt
                if log_error_txt:
                    log_error_txt += msg_txt
                return
            if get_all_lane:
                lane_root_ids = self.env["planviewap.lane"].search(
                    [
                        ("board_id", "=", board_id.id),
                    ]
                )
            else:
                lst_title_root = lane_root_name.split(";")
                lane_root_ids = self.env["planviewap.lane"].search(
                    [
                        ("title", "in", lst_title_root),
                        ("lane_parent_id", "=", False),
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
                return self.env["planviewap.lane"]
        # Force auto refresh root lane
        if sync_cards and lane_root_ids:
            if lane_root_name:
                msg_txt = (
                    f"INFO sync cards from processus '{process_name}' root lane name"
                    f" '{lane_root_name}'\n"
                )
            else:
                msg_txt = (
                    f"INFO sync cards from processus '{process_name}' root lane name"
                    f" '{';'.join([a.title for a in lane_root_ids])}'\n"
                )
            if log_txt:
                log_txt += msg_txt
            _logger.info(msg_txt.strip())

            lane_root_ids.action_sync_cards()

        if is_root_lane or get_all_lane:
            lane_ids = lane_root_ids
        else:
            lane_query = [
                ("board_id", "=", board_id.id),
            ]
            if lane_root_ids:
                lane_query.append(("lane_root_id", "in", lane_root_ids.ids))

            if lst_lane_name:
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
                lane_ids = self.env["planviewap.lane"].search(
                    lane_query, order=order
                )
            else:
                lane_ids = self.env["planviewap.lane"].search(lane_query)

        # Force to search with recursive, cannot have cards if contain lanes TODO no need this when get_all_lane
        if not extract_only_root_lane:
            lane_ids = lane_ids.get_list_child_lane_from_lane(add_itself=True)
            if lst_lane_name and is_root_lane:
                lane_ids = lane_ids.filtered(
                    lambda l: l.title in lst_lane_name
                )

        if exclude_lane_name:
            lst_exclude_lane_name = exclude_lane_name.split(";")
            # TODO implement better mechanism, maybe a dedicated method?
            lane_ids = lane_ids.filtered(
                lambda l: l.title not in lst_exclude_lane_name
                and l.lane_parent_name not in lst_exclude_lane_name
                and l.lane_root_name not in lst_exclude_lane_name
            )
        if limit > 0:
            return lane_ids[:limit]
        # Remove doublon
        lst_unique_ids = set(lane_ids.ids)
        if len(lane_ids.ids) != len(lst_unique_ids):
            lane_ids = self.env["planviewap.lane"].browse(list(lst_unique_ids))
        return lane_ids

    def operate_lane(self):
        for rec in self:
            if not rec.operate_lane_name and rec.operate_lane_action in [
                "add_above",
                "add_bellow",
                "sort_by",
            ]:
                msg_txt = "ERR Need the new lane_name to add lane.\n"
                rec.log_txt += msg_txt
                rec.log_error_txt += msg_txt
                _logger.error(msg_txt.strip())
                continue
            # TODO create sorted by sequence, but root first, after child for all element
            lane_ids = self.search_lanes_from_processus(sync_cards=False)
            lane_ids = lane_ids.sorted_all_by_sequence()
            lst_op = []
            cmd_gen = {"operate_lane": lst_op}
            for lane_id in lane_ids:
                if rec.operate_lane_ignore_string_lane:
                    lane_path = [
                        a.replace(rec.operate_lane_ignore_string_lane, "")
                        for a in lane_id.get_hierarchy_list()
                    ]
                else:
                    lane_path = lane_id.get_hierarchy_list()
                # TODO Fix bug into selenium, remove all string into ()
                new_lst_lane_path = []
                for lane_path_str in lane_path:
                    new_lane_path = lane_path_str
                    if "(" in new_lane_path:
                        new_lane_path = new_lane_path[
                            : new_lane_path.find("(")
                        ]
                    if ")" in new_lane_path:
                        new_lane_path = new_lane_path[
                            : new_lane_path.find(")")
                        ]
                    new_lst_lane_path.append(new_lane_path)
                lane_path = new_lst_lane_path

                dct_op = {
                    "action": rec.operate_lane_action,
                    "lane_path": lane_path,
                }
                if rec.operate_lane_name:
                    dct_op["action_value"] = rec.operate_lane_name.split(";")
                lst_op.append(dct_op)
            str_cmd_gen = json.dumps(cmd_gen)
            # str_cmd_gen = str_cmd_gen.replace(" ", "%20").replace('"', "'")
            temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
            json.dump(cmd_gen, temp_file)
            msg_txt = (
                f"Write json config file with {len(lst_op)} operations \n"
            )
            msg_txt += temp_file.name
            temp_file.close()
            msg_txt += f"\n\n{str_cmd_gen}\n\n"
            rec.log_txt += msg_txt
            _logger.info(msg_txt.strip())

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
        card_ids = self.env["planviewap.card"]
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
                type_card_ids = self.env["planviewap.card.type"].search(
                    [
                        ("name", "in", lst_type_card),
                        ("board_id", "=", rec.board_id.id),
                    ]
                )
                if not type_card_ids:
                    msg_txt = (
                        f"WARN cannot find type card '{lst_type_card}'.\n"
                    )
                    rec.log_txt += msg_txt
                    rec.log_error_txt += msg_txt

                lst_query.append(("card_type_id", "in", type_card_ids.ids))
            lst_query.append(("board_id", "=", rec.board_id.id))
            card_ids += self.env["planviewap.card"].search(lst_query)
            if rec.force_refresh_custom_fields:
                for card_id in card_ids:
                    card_id.update_card_details()

        msg_txt = f"LOG Info {len(card_ids)} cards\n"
        self.log_txt += msg_txt
        self.log_error_txt += msg_txt
        _logger.info(msg_txt.strip())
        return card_ids

    @staticmethod
    def return_monday_day(date_to_find, delay_week=0):
        jour_semaine = date_to_find.weekday()
        lundi = (
            date_to_find
            - datetime.timedelta(days=jour_semaine)
            + datetime.timedelta(weeks=delay_week)
        )
        return lundi

    @staticmethod
    def return_next_open_day(
        selected_date, delay_day=1, is_skipping_weekend=True
    ):
        # TODO support weekday, check next day from calendar into system
        target_date = selected_date
        remaining_days = abs(delay_day)
        increment = 1 if delay_day > 0 else -1
        while remaining_days > 0:
            target_date += datetime.timedelta(days=increment)
            if not is_skipping_weekend or target_date.weekday() < 5:
                # Ignore weekend
                remaining_days -= 1

        return target_date

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
