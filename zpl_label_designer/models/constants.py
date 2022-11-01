from odoo import fields, _


class Constants:
    """
    Constants class for the ZPL Label Designer add-on.
    """
    PLACEHOLDER_REGEX = r'\%\%[a-z_\d\.]+?\%\%'
    FIELD_PLACEHOLDER = '<t t-esc="doc.{}"/>'
    TEMPLATE_BASE = '<t t-foreach="docs" t-as="doc">{content}</t>'
    SERVER_DOWN_MESSAGE = _(
        'ZPL Converter Server is on maintenance. Try again in a few minutes. '
        'If the issue will not be solved, please, drop us an email at support@ventor.tech')

    ALLOWED_MODELS = [
        "product.product", "product.template",
        "stock.production.lot", "stock.quant.package"
    ]
    ALLOWED_FIELDS = [
        fields.Char, fields.Text,
        fields.Integer, fields.Float,
        fields.Boolean, fields.Many2one,
        fields.Selection, fields.Datetime,
    ]
    FIELDS_TO_IGNORE = ['create_uid', 'write_uid']
    FIELDS_FOR_QUICK_BUTTONS = {
        "product.template": {
            "Name": "name",
            "Internal Reference": "default_code",
            "Barcode": "barcode",
            "Sales Price": "list_price",
            "Unit of Measure": "uom_id.name",
        },
        "product.product": {
            "Name": "name",
            "Internal Reference": "default_code",
            "Barcode": "barcode",
            "Sales Price": "list_price",
            "Unit of Measure": "uom_id.name",
        },
        "stock.production.lot": {
            "Lot Name": "name",
            "Expiration Date": "expiration_date",
            "Best Before Date": "use_date",
            "Product → Name": "product_id.name",
            "Product → Internal Reference": "product_id.default_code",
            "Product → Barcode": "product_id.barcode",
            "Product → Sales Price": "product_id.list_price",
        },
        "stock.quant.package": {
            "Name": "name",
        }
    }

    SPECIAL_CHARACTERS = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
    }
