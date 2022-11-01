import json
import re
import requests

from odoo import api, exceptions, fields, models, _
from odoo.tools.safe_eval import safe_eval

from .constants import Constants


class Label(models.Model):
    _name = 'zld.label'
    _description = 'ZPL Designer Label'

    name = fields.Char(
        string='Name',
        required=True,
    )

    blob = fields.Text(
        string='Blob',
        default='{}',
    )

    zpl = fields.Text(
        string="ZPL",
        default='',
    )

    preview = fields.Text(
        string="Preview (with demo data)",
        default=False,
    )

    width = fields.Float(
        string="Width, inch",
        default=5,
        required=True,
    )

    height = fields.Float(
        string="Height, inch",
        default=2.5,
        required=True,
    )

    dpi = fields.Selection(
        string="DPI",
        default='152',
        selection=[
            ('152', '6dpmm (152 dpi)'),
            ('203', '8dpmm (203 dpi)'),
            ('300', '12dpmm (300 dpi)'),
            ('600', '24dpmm (600 dpi)'),
        ],
        required=True,
    )

    orientation = fields.Selection(
        string="Orientation",
        default="normal",
        selection=[
            ('normal', 'Normal'),
            ('inverted', 'Inverted'),
        ],
    )

    is_published = fields.Boolean(
        string="Is Published?",
    )

    is_modified = fields.Boolean(
        string="Is Modified After Publishing?",
        compute='_compute_is_modified',
    )

    action_report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Related ir.actions.report ID'
    )

    view_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Related ir.ui.view ID'
    )

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Label Model',
        ondelete='cascade',
        required=True,
        domain=[("model", "in", Constants.ALLOWED_MODELS)],
    )

    # This is experimental functionality: allow to set custom print report name
    print_report_name = fields.Char(
        string='Report Name',
        help=(
            'This field allows to set custom print report name.'
            'There can be any valid Python expression.'
            'If empty, label name will be used.'
        ),
    )

    print_report_name_preview = fields.Char(
        string='Report Name Preview',
        compute='_compute_print_report_name_preview',
    )

    @api.depends('name', 'print_report_name')
    def _compute_print_report_name_preview(self):
        for rec in self:
            if rec.print_report_name:
                random_record = rec._get_random_record()
                rec.print_report_name_preview = safe_eval(
                    rec.print_report_name,
                    {'object': random_record}
                )
            else:
                rec.print_report_name_preview = rec.name

    @api.onchange('print_report_name')
    def _onchange_print_report_name(self):
        if self.print_report_name:
            # Check if expression is valid
            try:
                self._compute_print_report_name_preview()
            except Exception as e:
                raise exceptions.ValidationError(
                    _('Invalid Print Report Name expression: {}').format(e)
                )

    @api.constrains('width', 'height')
    def _check_dimensions(self):
        """
        Do now allow to set negative width.
        """
        if self.width <= 0 or self.height <= 0:
            raise exceptions.ValidationError(_('Width and height must be positive'))

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = "Copy of " + self.name

        return super().copy(default=default)

    def unlink(self):
        for label in self:
            if label.is_published:
                raise exceptions.UserError(_('Cannot delete published label'))

        return super().unlink()

    def generate_zpl(self):
        """
        Generate ZPL content for current state of label. Used as button callback.
        """
        self.ensure_one()

        self.zpl = self._get_zpl_label()
        # TODO: Refactor? Looks like we can easily miss validation of label fields with
        # this approach
        self._validate_placeholders()
        self.preview = self._generate_preview()

    def publish(self):
        """
        This method publish label to Odoo. It creates (or updates) ir.action.report and ir.ui.view.
        """
        self.ensure_one()

        # Update label
        self.generate_zpl()

        if not self.zpl.strip():  # Strip is just in case
            raise exceptions.UserError(
                _('Label is empty. Please add at least one element to the label'))

        if self.action_report_id:
            # Do update of label content and exit
            self._update_label()
            return

        view_xmlid = f'zpl_label_designer.{self.model_id.model.replace(".", "_")}_label_{self.id}'
        label_view_id = self.env['ir.ui.view'].create({
            'type': 'qweb',
            'arch': self._prepare_label_template(),
            'name': view_xmlid,
            'key': view_xmlid
        })
        self.env['ir.model.data'].create({
            'module': 'zpl_label_designer',
            'name': view_xmlid,
            'model': 'ir.ui.view',
            'res_id': label_view_id.id,
            # Make it no updatable to avoid deletion on module upgrade
            'noupdate': True,
        })

        self.view_id = label_view_id

        action_xmlid = f'zpl_label_designer.{self.model_id.model.replace(".", "_")}_label_action_{self.id}'  # NOQA
        label_action_report = self.env['ir.actions.report'].create({
            'xml_id': action_xmlid,
            'name': self.name,
            'model': self.model_id.model,
            'report_type': 'qweb-text',
            'report_name': view_xmlid,
            'report_file': view_xmlid,
            'print_report_name': self.print_report_name or f"'{self.name}'",
            'binding_model_id': self.model_id.id,
            'binding_type': 'report',
        })
        self.env['ir.model.data'].create({
            'module': 'zpl_label_designer',
            'name': action_xmlid,
            'model': 'ir.actions.report',
            'res_id': label_action_report.id,
            # Make it no updatable to avoid deletion on module upgrade
            'noupdate': True,
        })

        self.action_report_id = label_action_report
        self.is_published = True

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Label was published'),
                'message': _('Label {} was successfully published').format(self.name),
                'type': 'success',
                'sticky': False,
            },
        }

    def unpublish(self):
        self.ensure_one()

        if self.action_report_id:
            self.action_report_id.unlink()
            self.view_id.unlink()

        self.is_published = False

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Label was unpublished'),
                'message': _('Label {} was successfully unpublished').format(self.name),
                'type': 'success',
                'sticky': False,
            },
        }

    def open_view(self):
        self.ensure_one()

        if not self.view_id:
            raise exceptions.UserError(_('Label is not published'))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.ui.view',
            'res_id': self.view_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.depends('view_id')
    def _compute_is_modified(self):
        for label in self:
            label.is_modified = bool(label.view_id and label.view_id.write_date < label.write_date)

    def _get_allowed_fields(self):
        """
        This method returns list of fields to use in label design (sorted by label)
        """
        self.ensure_one()

        if not self.model_id:
            return {}

        model_fields = self.env[self.model_id.model]._fields

        def _is_allowed_field_type(field):
            return any([isinstance(field, cls) for cls in Constants.ALLOWED_FIELDS])

        def _prepare_dict_with_allowed_fields(fields_, prefix='', label_prefix='', with_nested=True):  # NOQA
            """
            Returns list with allowed fields like pairs [(name, label), ...]
            """
            result = []
            for field_name, field in fields_.items():
                if field_name in Constants.FIELDS_TO_IGNORE or field_name.startswith('_'):
                    continue

                if _is_allowed_field_type(field):
                    if type(field) == fields.Many2one:
                        if not with_nested:
                            continue

                        comodel = self.env[field.comodel_name]
                        nested_fields = _prepare_dict_with_allowed_fields(
                            comodel._fields,
                            prefix + field_name + '.',
                            label_prefix + field.string + ' → ',
                            with_nested=False)

                        result += nested_fields
                    else:
                        if label_prefix:
                            result.append([prefix + field_name, label_prefix + field.string])
                        else:
                            result.append([prefix + field_name, field.string])

            return result

        fields_ = _prepare_dict_with_allowed_fields(model_fields)
        fields_.sort(key=lambda i: i[1])

        return fields_

    def _generate_preview(self):
        """
        This method replaces placeholders with demo data.
        """
        self.ensure_one()

        label_preview = self.zpl
        placeholders = re.findall(Constants.PLACEHOLDER_REGEX, label_preview)

        random_record = self._get_random_record()

        # Replace placeholders with data
        for placeholder in placeholders:
            placeholder_attr = placeholder[2:-2]  # Remove %% from start and end

            # We allow single level of nesting
            if '.' in placeholder_attr:
                field, nested_field = placeholder_attr.split('.')
                nested_model = getattr(random_record, field)
                placeholder_value = str(getattr(nested_model, nested_field, ''))
            else:
                placeholder_value = str(getattr(random_record, placeholder_attr, ''))

            label_preview = label_preview.replace(placeholder, placeholder_value)

        return label_preview

    def _validate_placeholders(self):
        """
        This method validates placeholders in label design.
        """
        self.ensure_one()

        placeholders = re.findall(Constants.PLACEHOLDER_REGEX, self.zpl)
        Model = self.env[self.model_id.model]

        for placeholder in placeholders:
            placeholder_attr = placeholder[2:-2]  # Remove %% from start and end

            field = placeholder_attr
            nested_field = None

            # We allow single level of nesting
            if '.' in placeholder_attr:
                field, nested_field = placeholder_attr.split('.')

                if not nested_field:
                    raise exceptions.ValidationError(
                        _('Invalid placeholder: "{}"').format(placeholder))

            if field not in Model._fields:
                raise exceptions.UserError(
                    _('Field "{}" does not exist in "{}" model').format(
                        placeholder_attr, self.model_id.name)
                )

            if nested_field:
                if Model._fields[field].type != 'many2one':
                    raise exceptions.UserError(
                        _(
                            'Field "{}" is not a many2one field and '
                            'can not be used to get nested fields'
                        ).format(field)
                    )

                Comodel = self.env[Model._fields[field].comodel_name]

                if nested_field not in Comodel._fields:
                    raise exceptions.UserError(
                        _('Field "{}" does not exist in "{}" relation').format(
                            nested_field, field)
                    )

        return True

    def _get_random_record(self):
        """
        This method returns random record from model
        (tries to find record with fields that are not empty)
        """
        self.ensure_one()

        placeholders = re.findall(Constants.PLACEHOLDER_REGEX, self.zpl)

        # Try to find objects with not empty fields
        not_empty_fields = [p[2:-2] for p in placeholders]
        domain = [(f, '!=', False) for f in not_empty_fields]
        random_record = self.env[self.model_id.model].search(domain, limit=1)

        if not random_record:
            # If no object found, try to find any object
            random_record = self.env[self.model_id.model].search([], limit=1)

        return random_record

    def _get_zpl_label(self):
        self.ensure_one()

        payload = {
            "name": self.name,
            "inverted": self.orientation == 'inverted',
            "dpi": self.dpi,
            "content": json.loads(self.blob),
        }
        resp = requests.post(self._get_converter_url('convert-label'), json=payload)

        if resp.status_code >= 500:  # Can be 500 or 502 if server is down
            raise exceptions.UserError(Constants.SERVER_DOWN_MESSAGE)

        data = resp.json()
        if data.get('status_code') != 200:
            raise exceptions.UserError(data.get('message', Constants.SERVER_DOWN_MESSAGE))

        return resp.json().get('data', {})

    def _prepare_label_template(self):
        self.ensure_one()

        # Replace placeholders with qweb fields
        label_content = self.zpl

        # Replace special characters in placeholders with html entities
        for char, replacement in Constants.SPECIAL_CHARACTERS.items():
            label_content = label_content.replace(char, replacement)

        placeholders = re.findall(Constants.PLACEHOLDER_REGEX, label_content)

        for placeholder in placeholders:
            placeholder_attr = placeholder[2:-2]  # Remove %% from start and end
            placeholder_value = Constants.FIELD_PLACEHOLDER.format(placeholder_attr)

            label_content = label_content.replace(placeholder, placeholder_value)

        template = Constants.TEMPLATE_BASE.format(content=label_content)

        return template

    def _update_label(self):
        self.ensure_one()

        # Update label with new content
        self.view_id.arch = self._prepare_label_template()

        # Update action report
        self.action_report_id.name = self.name
        self.action_report_id.print_report_name = self.print_report_name or f"'{self.name}'"

    def _get_converter_url(self, uri=''):
        base_url = self.env['ir.config_parameter'].sudo()\
            .get_param('zpl_label_designer.zld_converter_url')
        return f'{base_url}/{uri}' if uri else base_url

    def _get_quick_fields(self):
        self.ensure_one()

        return Constants.FIELDS_FOR_QUICK_BUTTONS.get(self.model_id.model, {})

    def get_settings(self):
        self.ensure_one()

        return {
            'converter_url': self._get_converter_url(),
            'allowed_fields': self._get_allowed_fields(),
            'quick_fields': self._get_quick_fields(),
        }
