# -*- coding: utf-8 -*-

from collections import defaultdict, OrderedDict
from datetime import date, timedelta
import json

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round, format_date, float_is_zero

from odoo import Command, models


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"

    #hello