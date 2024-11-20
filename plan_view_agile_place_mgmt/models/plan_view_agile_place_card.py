#!/usr/bin/env python3
# © 2024 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import datetime
import json
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PlanViewAgilePlaceCard(models.Model):
    _name = "plan.view.agile.place.card"
    _description = "plan_view_agile_place_card"

    name = fields.Char(required=True)

    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the card without deleting it.",
    )

    enabled_bind = fields.Boolean(
        help="A card is automatic bind when it's enable. By default, no card will be delete on external source.",
    )

    board_id = fields.Many2one(
        comodel_name="plan.view.agile.place.board",
        required=True,
        string="Board",
    )

    assigned_users = fields.Char(help="Separate pvap id by ;")

    card_id_pvap = fields.Char(
        readonly=True, help="Plan View Agile Plane - Card ID"
    )

    copied_from_card_pvap = fields.Char(
        help="Plan View Agile Plane - Card ID to copy when create"
    )

    card_type_id = fields.Many2one(
        comodel_name="plan.view.agile.place.card.type",
        string="Card Type",
    )

    lane_id = fields.Many2one(
        comodel_name="plan.view.agile.place.lane",
        string="Lane",
        group_expand="_read_group_lane_ids",
        default=lambda self: self._default_stage(),
    )

    lane_name = fields.Char(
        string="Lane name",
        related="lane_id.title",
    )

    lane_root_id = fields.Many2one(
        related="lane_id.lane_root_id",
        # comodel_name="plan.view.agile.place.lane",
        # string="Root Lane",
        # compute="_compute_lane_root_id",
        # group_expand="_read_group_lane_ids",
        # default=lambda self: self._default_stage(),
    )

    lane_root_name = fields.Char(
        related="lane_id.lane_root_name",
    )

    lane_parent_id = fields.Many2one(
        string="Lane parent",
        related="lane_id.lane_parent_id",
        store=True,
    )

    lane_parent_name = fields.Char(
        string="Lane parent name",
        related="lane_id.lane_parent_id.title",
    )

    moved_on = fields.Datetime()

    session_id = fields.Many2one(
        comodel_name="plan.view.agile.place.session",
        string="Session",
    )

    entete = fields.Char()

    external_link = fields.Char()

    card_details = fields.Text()

    description = fields.Html()

    custom_fields = fields.Text()

    size = fields.Integer()

    version = fields.Integer()

    url_card = fields.Char(compute="_compute_url_card")

    @api.returns("self")
    def _default_stage(self):
        return self.env["plan.view.agile.place.lane"].search([], limit=1)

    @api.depends("card_id_pvap", "session_id.name")
    def _compute_url_card(self):
        for rec in self:
            url = ""
            if rec.session_id and rec.card_id_pvap:
                url = f"{rec.session_id.name}/card/{rec.card_id_pvap}"
            rec.url_card = url

    # @api.depends("title", "lane_parent_id")
    # def _compute_lane_root_id(self):
    #     for rec in self:

    @api.model
    def _read_group_lane_ids(self, stages, domain, order):
        # TODO this is so wrong, replace lane_parent_name by title
        # Why we receive domain from card, but we are in lane?
        # if not card_ids:
        if not domain:
            return (
                self.env["plan.view.agile.place.lane"]
                .search([], order=order, limit=80)
                .sorted("name")
            )
        card_ids = self.env["plan.view.agile.place.card"].search(domain)
        lane_ids = self.env["plan.view.agile.place.lane"]
        for card_id in card_ids:
            lane_ids += card_id.lane_id
        return lane_ids
        # return (
        #     self.env["plan.view.agile.place.lane"]
        #     .search(eval(str(domain).replace("lane_parent_name", "title")), order=order)
        #     .sorted("name")
        # )

    def update_card_details(self):
        for rec in self:
            status, response = rec.session_id.request_api_get(
                f"/io/card/{rec.card_id_pvap}"
            )
            if str(status)[0] != "2":
                rec.card_details = ""
                continue
            rec.card_details = json.dumps(response)
            if response.get("customFields"):
                rec.custom_fields = json.dumps(response.get("customFields"))

    @api.model_create_multi
    def create(self, vals_list):
        # Ignore creation if already exist with card_id_pvap
        rec_ids = super().create(vals_list)
        for rec in rec_ids:
            if rec.card_id_pvap:
                # Ignore, already exist in remote
                continue
            data = {
                "boardId": rec.board_id.board_id_pvap,
                "title": rec.name,
                "laneId": rec.lane_id.lane_id_pvap,
            }
            # TODO miss active, moved_on, version, externalLinks,
            if rec.custom_fields:
                data["customFields"] = eval(rec.custom_fields)
            if rec.description:
                data["description"] = rec.description
            if rec.entete:
                data["entete"] = rec.entete
            # TODO Ignore assigned user, use instead /io/card/assign
            # https://success.planview.com/Planview_AgilePlace/AgilePlace_API/01_v2/card/assign-members
            # if rec.assigned_users:
            #     data["assigned_users"] = rec.assigned_users.replace(";", ",")
            if rec.size:
                data["size"] = rec.size
            if rec.entete:
                data["customId"] = rec.entete
            if rec.card_type_id:
                data["typeId"] = rec.card_type_id.card_type_id_pvap
            if rec.copied_from_card_pvap:
                data["copiedFromCardId"] = rec.copied_from_card_pvap

            status, response = rec.session_id.request_api_post(
                "/io/card", data=data
            )
            if str(status)[0] != "2":
                _logger.error(response)
                continue
            # TODO raise error if missing... will already raise error
            rec.card_id_pvap = response.get("id")
        return rec_ids

    def write(self, values):
        status = super().write(values)
        if not status:
            return status
        for rec in self:
            if "lane_id" in values:
                data = {
                    "cardIds": [rec.card_id_pvap],
                    "destination": {"laneId": rec.lane_id.lane_id_pvap},
                }
                status, response = rec.session_id.request_api_post(
                    "/io/card/move", data=data
                )
                if str(status)[0] != "2":
                    continue
        return status

    def unlink(self):
        lst_card_id_pvap = []
        session_id = None
        for rec in self:
            if not rec.card_id_pvap:
                # Ignore, not existing in remote
                continue
            if not session_id:
                session_id = rec.session_id
            if rec.enabled_bind:
                lst_card_id_pvap.append(rec.card_id_pvap)
        # Delete for all bind card
        if lst_card_id_pvap and session_id:
            data_delete = {"cardIds": lst_card_id_pvap}
            result = session_id.request_api_delete(
                "/io/card/", data=data_delete
            )
            if str(result[0])[0] != "2":
                raise ValueError(
                    f"Receive request {result[0]} from delete all"
                    " cards from specific lane."
                )
        else:
            _logger.warning(
                "System asks to delete card, but no one is associate with external source."
            )
        res = super().unlink()
        return res

    def sync_pvap_cards(self, board_id, from_lane=None):
        # from_lane will do partial update
        # Search all under lane with from_lane
        session_id = board_id.session_id

        lane_to_extract_ids = None
        if not from_lane:
            lst_pvap_lane = []
        else:
            lane_to_extract_ids = from_lane.get_list_child_lane_from_lane(
                add_itself=True
            )
            # check if already sync from cache
            self.env.context = dict(self.env.context)
            lst_sync_lane_id_pvap = self.env.context.get(
                "lst_sync_lane_id_pvap", []
            )
            lst_pvap_lane = [
                a.lane_id_pvap
                for a in lane_to_extract_ids
                if a.lane_id_pvap not in lst_sync_lane_id_pvap
            ]
            if len(lst_pvap_lane) != len(lane_to_extract_ids):
                _logger.info(
                    f"Cache {len(lane_to_extract_ids) - len(lst_pvap_lane)} lanes"
                )
            lst_sync_lane_id_pvap.extend(lst_pvap_lane)
            self.env.context.update(
                {"lst_sync_lane_id_pvap": lst_sync_lane_id_pvap}
            )

        # Get all cards
        data = {
            "limit": 500,
            "board": board_id.board_id_pvap,
            # "include": "customFields",
        }
        if lst_pvap_lane:
            data["lanes"] = ",".join(lst_pvap_lane)
        is_include_custom_fields = False
        lst_cards = session_id.request_api_get_unlimited(
            "/io/card", "cards", data=data
        )
        session_id.has_first_sync = True

        # Generate cards
        # Get list before to delete extra not existing after
        if not lane_to_extract_ids:
            all_card_ids = self.env["plan.view.agile.place.card"].search(
                [("board_id", "=", board_id.id)]
            )
        else:
            all_card_ids = self.env["plan.view.agile.place.card"].search(
                [
                    ("board_id", "=", board_id.id),
                    ("lane_id", "in", lane_to_extract_ids.ids),
                ]
            )

        lst_card_pvap_sync = []

        for dct_card in lst_cards:
            # Extract data card
            card_id_pvap = dct_card.get("id")
            archived_on = dct_card.get("archivedOn")
            is_active = True if archived_on is None else False
            lane_id_pvap = dct_card.get("lane").get("id")
            board_id_pvap = dct_card.get("board").get("id")
            str_moved_on = dct_card.get("movedOn")
            moved_on = (
                False
                if not str_moved_on
                else datetime.datetime.fromisoformat(
                    str_moved_on.replace("Z", "+00:00")
                ).replace(tzinfo=None)
            )
            type_id_pvap = dct_card.get("type").get("id")
            title = dct_card.get("title")
            description = (
                False
                if not dct_card.get("description")
                else dct_card.get("description")
            )
            size = dct_card.get("size")
            version = (
                0
                if not dct_card.get("version")
                else int(dct_card.get("version"))
            )
            assigned_users = ";".join(
                [a.get("id") for a in dct_card.get("assignedUsers")]
            )
            if not assigned_users:
                assigned_users = False
            entete = dct_card.get("customId").get("value")

            if dct_card.get("externalLinks"):
                external_link = dct_card.get("externalLinks")[0].get("url")
            else:
                external_link = ""

            if is_include_custom_fields:
                custom_fields = json.dumps(dct_card.get("customFields"))
            else:
                custom_fields = False

            board_id = self.env["plan.view.agile.place.board"].search(
                [("board_id_pvap", "=", board_id_pvap)], limit=1
            )

            card_type_id = self.env["plan.view.agile.place.card.type"].search(
                [
                    ("card_type_id_pvap", "=", type_id_pvap),
                    ("board_id", "=", board_id.id),
                ]
            )

            lane_id = self.env["plan.view.agile.place.lane"].search(
                [
                    ("lane_id_pvap", "=", lane_id_pvap),
                    ("board_id", "=", board_id.id),
                ]
            )

            lst_card_pvap_sync.append(card_id_pvap)

            # Search if exist or create it
            card_id = self.env["plan.view.agile.place.card"].search(
                [
                    ("card_id_pvap", "=", card_id_pvap),
                    ("board_id", "=", board_id.id),
                ]
            )
            if card_id:
                # Update it, except card_id_pvap and session_id
                if title != card_id.name:
                    card_id.name = title
                if is_active != card_id.active:
                    card_id.active = is_active
                if moved_on != card_id.moved_on:
                    card_id.moved_on = moved_on
                if size != card_id.size:
                    card_id.size = size
                if version != card_id.version:
                    card_id.version = version
                if custom_fields != card_id.custom_fields:
                    card_id.custom_fields = custom_fields
                if description != card_id.description:
                    card_id.description = description
                if assigned_users != card_id.assigned_users:
                    card_id.assigned_users = assigned_users
                if entete != card_id.entete:
                    card_id.entete = entete
                if card_type_id != card_id.card_type_id:
                    card_id.card_type_id = card_type_id.id
                if lane_id != card_id.lane_id:
                    card_id.lane_id = lane_id.id
                if board_id != card_id.board_id:
                    card_id.board_id = board_id.id
            else:
                card_value = {
                    "card_id_pvap": card_id_pvap,
                    "active": is_active,
                    "card_type_id": card_type_id.id if card_type_id else False,
                    "lane_id": lane_id.id if lane_id else False,
                    "board_id": board_id.id if board_id else False,
                    "moved_on": moved_on,
                    "name": title,
                    "size": size,
                    "version": version,
                    "session_id": session_id.id,
                    "custom_fields": custom_fields,
                    "description": description,
                    "assigned_users": assigned_users,
                    "entete": entete,
                    "external_link": external_link,
                }

                card_id = self.env["plan.view.agile.place.card"].create(
                    card_value
                )

        card_to_delete_ids = self.env["plan.view.agile.place.card"]
        for card_id in all_card_ids:
            if card_id.card_id_pvap not in lst_card_pvap_sync:
                card_to_delete_ids += card_id
        if card_to_delete_ids:
            card_to_delete_ids.unlink()
