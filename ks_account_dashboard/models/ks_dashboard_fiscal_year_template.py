from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import datetime
import json


class KsDashboardNinjaFiscalYear(models.Model):
    _inherit = 'ks_dashboard_ninja.board'

    # ks_date_filter_selection =  fields.Selection([
    #     ('l_none', 'All Time'),
    #     ('l_day', 'Today'),
    #     ('t_week', 'This Week'),
    #     ('t_month', 'This Month'),
    #     ('t_quarter', 'This Quarter'),
    #     ('t_year', 'This Year'),
    #     # ('t_fiscal_year', 'This Fiscal Year'),
    #     ('n_day', 'Next Day'),
    #     ('n_week', 'Next Week'),
    #     ('n_month', 'Next Month'),
    #     ('n_quarter', 'Next Quarter'),
    #     ('n_year', 'Next Year'),
    #     # ('n_fiscal_year', 'Next  Fiscal Year'),
    #     ('ls_day', 'Last Day'),
    #     ('ls_week', 'Last Week'),
    #     ('ls_month', 'Last Month'),
    #     ('ls_quarter', 'Last Quarter'),
    #     ('ls_year', 'Last Year'),
    #     # ('ls_fiscal_year', 'Last Fiscal Year'),
    #     ('l_week', 'Last 7 days'),
    #     ('l_month', 'Last 30 days'),
    #     ('l_quarter', 'Last 90 days'),
    #     ('l_year', 'Last 365 days'),
    #     ('ls_past_until_now', 'Past Till Now'),
    #     ('ls_pastwithout_now', ' Past Excluding Today'),
    #     ('n_future_starting_now', 'Future Starting Now'),
    #     ('n_futurestarting_tomorrow', 'Future Starting Tomorrow'),
    #     ('l_custom', 'Custom Filter'),
    # ], default='l_none', string="Default Date Filter")
