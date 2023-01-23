# -*- coding: utf-8 -*-
import datetime

import dateutil
import pytz

from odoo import api, fields, models

# class BaseModelExtend(models.AbstractModel):
#    _name = 'basemodel.extend'

# def _register_hook(self, cr):
#    @api.cr_uid_context
#    def user_has_groups(self, cr, uid, groups, context=None):
#       #My code
#    models.BaseModel.user_has_groups = user_has_groups
#    return super(BaseModelExtend, self)._register_hook(cr)


@api.model
def _read_group_process_groupby(self, gb, query):
    """
    Helper method to collect important information about groupbys: raw
    field name, type, time information, qualified name, ...
    """
    split = gb.split(":")
    field_type = self._fields[split[0]].type
    gb_function = split[1] if len(split) == 2 else None
    temporal = field_type in ("date", "datetime")
    tz_convert = (
        field_type == "datetime"
        and self._context.get("tz") in pytz.all_timezones
    )
    qualified_field = self._inherits_join_calc(self._table, split[0], query)
    if temporal:
        display_formats = {
            # Careful with week/year formats:
            #  - yyyy (lower) must always be used, *except* for week+year formats
            #  - YYYY (upper) must always be used for week+year format
            #         e.g. 2006-01-01 is W52 2005 in some locales (de_DE),
            #                         and W1 2006 for others
            #
            # Mixing both formats, e.g. 'MMM YYYY' would yield wrong results,
            # such as 2006-01-01 being formatted as "January 2005" in some locales.
            # Cfr: http://babel.pocoo.org/docs/dates/#date-fields
            "hour": "HH:mm dd MMM yyyy",
            "day": "dd MMM yyyy",  # yyyy = normal year
            "week": "'W'w YYYY",  # w YYYY = ISO week-year
            "month": "MMMM yyyy",
            "quarter": "QQQ yyyy",
            "year": "yyyy",
        }
        time_intervals = {
            "hour": dateutil.relativedelta.relativedelta(hours=1),
            "day": dateutil.relativedelta.relativedelta(days=1),
            "week": datetime.timedelta(days=7),
            "month": dateutil.relativedelta.relativedelta(months=1),
            "quarter": dateutil.relativedelta.relativedelta(months=3),
            "year": dateutil.relativedelta.relativedelta(years=1),
        }
        if tz_convert:
            qualified_field = "timezone('%s', timezone('UTC',%s))" % (
                self._context.get("tz", "UTC"),
                qualified_field,
            )
        qualified_field = "date_trunc('%s', %s)" % (
            gb_function or "month",
            qualified_field,
        )
    if field_type == "boolean":
        qualified_field = "coalesce(%s,false)" % qualified_field
    return {
        "field": split[0],
        "groupby": gb,
        "type": field_type,
        "display_format": display_formats[gb_function or "month"]
        if temporal
        else None,
        "interval": time_intervals[gb_function or "month"]
        if temporal
        else None,
        "tz_convert": tz_convert,
        "qualified_field": qualified_field,
    }


models.BaseModel._read_group_process_groupby = _read_group_process_groupby
