from typing import Any, Dict, List, Union

from odoo import api, exceptions, fields, models, _
from odoo.tools.safe_eval import safe_eval


LABEL_VIEW_XMLID = 'zpl_label_designer.{model}_label_{label_id}'
LABEL_ACTION_REPORT_XMLID = 'zpl_label_designer.{model}_label_action_{label_id}'


class Label(models.Model):
    _name = 'zld.label'
    _description = 'ZPL Designer Label'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=True,
    )

    zpl = fields.Text(
        string="ZPL",
        default='',
        readonly=True,
    )

    preview = fields.Text(
        string="Preview (with demo data)",
        default=False,
        readonly=True,
    )

    width = fields.Float(
        string="Width, inch",
        default=5,
        required=True,
        readonly=True,
    )

    height = fields.Float(
        string="Height, inch",
        default=2.5,
        required=True,
        readonly=True,
    )

    dpi = fields.Float(
        string="DPI",
        required=True,
        readonly=True,
    )

    orientation = fields.Char(
        string="Orientation",
        readonly=True,
    )

    is_published = fields.Boolean(
        string="Is Published?",
        default=False,
        copy=False,
    )

    is_modified = fields.Boolean(
        string="Is Modified After Publishing?",
        default=False,
    )

    action_report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Related ir.actions.report ID',
        copy=False,
    )

    view_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Related ir.ui.view ID',
        copy=False,
    )

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Label Model',
        ondelete='cascade',
        required=True,
        readonly=True,
    )

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

    designer_label_id = fields.Char(
        string='Designer Label ID',
        readonly=True,
    )

    @api.depends('name', 'print_report_name')
    def _compute_print_report_name_preview(self):
        for rec in self:
            if rec.print_report_name:
                random_record = rec.env[rec.model_id.model].search([], limit=1)
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

    def copy(self, default=None):
        raise exceptions.UserError(_(
            "You can't duplicate a label. Please, go to the ZPL Label Designer to create labels."
        ))

    def unlink(self):
        for label in self:
            if label.is_published:
                raise exceptions.UserError(_('Cannot delete published label'))

            if not self.env.is_superuser() and label.designer_label_id:
                raise exceptions.UserError(_(
                    "You can't delete a label from Odoo that is synced with labels.ventor.tech. "
                    "Please, go to the labels.ventor.tech to do this."
                ))

        return super().unlink()

    #
    # Button actions
    #
    def publish(self):
        """
        Create or update report and view for label
        """
        self.ensure_one()

        if not self.view_id:
            raise exceptions.UserError(_(
                'To publish this label, please go to the Designer (using "Open in Designer" button)'
                ' and publish it there'
            ))

        self.view_id.active = True

        if self.action_report_id:
            # Update action report
            self.action_report_id.name = self.name
            self.action_report_id.print_report_name = self.print_report_name or f"'{self.name}'"
        else:
            # Create action report
            self.action_report_id = self._create_label_action_report()

        self.is_published = True

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Label was published'),
                'message': _('Label {} was successfully published').format(self.name),
                'type': 'success',
                'sticky': False,
                'next': {  # Refresh the page after publishing
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            },
        }

    def unpublish(self):
        self.ensure_one()

        if self.action_report_id:
            self.action_report_id.unlink()
            self.view_id.active = False

        self.is_published = False

        return True

    def update_published_label(self):
        self.publish()
        self.is_modified = False

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
            'context': {
                'no_breadcrumbs': False,
            }
        }

    def open_in_designer(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': self.get_label_designer_url(self.designer_label_id),
            'target': 'blank',
        }

    #
    # Public methods
    #
    @api.model
    def create_label(self, attrs):
        qweb_xml, label_fields, prepared_attrs = self._prepare_data_for_label(attrs)

        label = self.create([prepared_attrs])
        label._publish_label(qweb_xml)
        label._update_preview(label_fields)

        return label.id

    @api.model
    def update_label(self, label_id, attrs):
        # Use exists to make sure that label really exists
        label = self.browse(label_id).exists()

        if not label:
            # Create new label if it doesn't exist
            label_id = self.create_label(attrs)
            return label_id

        qweb_xml, label_fields, prepared_attrs = self._prepare_data_for_label(attrs)

        label.write(prepared_attrs)
        label.view_id.arch = qweb_xml
        label._update_preview(label_fields)

        return label.id

    @api.model
    def delete_label(self, label_id):
        label = self.browse(label_id).exists()

        if not label:
            # TODO: Maybe it's better just to return success?
            raise ValueError(_('Not label with such ID found in Odoo'))

        # This will raise exception if label published
        label.unlink()

    @api.model
    def get_preview_data(self, model_name, fields):
        """
        Returns example of data to populate label for preview
        """
        # Validate fields
        self._validate_label_fields(model_name, fields)

        # Try to find objects with not empty fields
        domain = [(f, '!=', False) for f in fields.keys()]
        random_record = self.env[model_name].search(domain, limit=1)

        if not random_record:
            # If no object found, try to find any object
            random_record = self.env[model_name].search([], limit=1)

        # Example of fields: [{"order_line": ["product_id.name", "product_uom_qty"]}, "state"]
        # We need to leave only fields that are in fields list
        data = self._get_data_from_record(random_record, fields)

        return data

    #
    # Internal methods
    #
    def _update_preview(self, label_fields: Dict[str, Union[None, List[Any], Dict[str, Any]]]):
        """
        Generate label preview from Qweb template based on random record
        """
        random_record_id = self._get_random_record(self.model_id.model, label_fields)
        self.preview = self._render_qweb_text([random_record_id.id]).decode("utf-8")

    def _publish_label(self, qweb_xml: str):
        """ Internal method to create report and view for label
        """
        label_view_id = self._create_label_view(qweb_xml)

        self.view_id = label_view_id

        label_action_report = self._create_label_action_report()

        self.action_report_id = label_action_report
        self.is_published = True

    def _get_random_record(self, model_name: str, fields: Dict[str, Union[None, List[Any], Dict[str, Any]]]):  # NOQA
        """
        This method returns random record from model
        (tries to find record with fields that are not empty)
        """
        domain = [(f, '!=', False) for f in fields.keys()]
        random_record = self.env[model_name].search(domain, limit=1)

        if not random_record:
            # If no object found, try to find any object
            random_record = self.env[model_name].search([], limit=1)

        return random_record

    def _create_label_view(self, view_content: str):
        """ This method creates view for current label
        """
        self.ensure_one()

        view_xmlid = LABEL_VIEW_XMLID.format(
            model=self.model_id.model.replace(".", "_"), label_id=self.id)

        label_view_id = self.env['ir.ui.view'].create({
            'type': 'qweb',
            'arch': view_content,
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

        return label_view_id

    def _create_label_action_report(self):
        """ This method creates actions report for current label
        """
        self.ensure_one()

        action_xmlid = LABEL_ACTION_REPORT_XMLID.format(
            model=self.model_id.model.replace(".", "_"), label_id=self.id)

        view_xmlid = self.view_id.get_external_id()[self.view_id.id]

        if not view_xmlid:
            raise exceptions.UserError(_(
                "View have not been created for the label - have not view - it's not possible to "
                "create an action report for this label."
            ))

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

        return label_action_report

    def _prepare_data_for_label(self, attrs):
        """ Prepare attributes to create (update) label
        """
        qweb_xml = attrs.pop('qweb_xml', None)
        if not qweb_xml:
            raise exceptions.UserError(
                _('Label is empty. Please add at least one element to the label'))

        model_name = attrs.pop('model', None)
        if not model_name:
            raise exceptions.UserError(_('Model is not specified'))

        # Replace model with model_id. It's a bit hacky but for now it's the easiest way
        attrs['model_id'] = self.env['ir.model'].search([('model', '=', model_name)]).id

        label_fields = attrs.pop('label_fields', None)

        self._validate_label_fields(model_name, label_fields)

        return qweb_xml, label_fields, attrs

    def _render_qweb_text(self, docids: list):
        """
        Render Qweb template to text
        """
        self.ensure_one()

        docs = self.env[self.model_id.model].browse(docids)
        view_xmlid = self.view_id.get_external_id()[self.view_id.id]
        data = {
            'doc_ids': docids,
            'doc_model': self.model_id.model,
            'docs': docs,
        }
        return self.env['ir.actions.report'] \
            .with_context(minimal_qcontext=True) \
            ._render_template(view_xmlid, data)

    @classmethod
    def _get_data_from_record(cls, random_record, fields: Dict[str, Union[None, List[Any], Dict[str, Any]]]):  # NOQA
        """
        Recursive method to get fields values from record
        """
        data = {}

        for field, subfields in fields.items():
            if subfields is None:
                # Simple field
                data[field] = getattr(random_record, field)
            elif isinstance(subfields, dict):
                # Dict means that the field is many2one field
                data[field] = cls._get_data_from_record(getattr(random_record, field), subfields)
            elif isinstance(subfields, list):
                # List means that the field is many2many or one2many field
                data[field] = []

                for record in getattr(random_record, field):
                    data[field].append(cls._get_data_from_record(record, subfields[0]))
            else:
                raise ValueError('Something is wrong with used fields')

        return data

    @api.model
    def _validate_label_fields(self, model_name: str, fields: Dict[str, Union[None, List[Any], Dict[str, Any]]]):  # NOQA
        """
        Recursive method to validate existance of specified fields
        """
        Model = self.env[model_name]
        model_label = Model._description

        for field, subfields in fields.items():
            if field not in Model._fields:
                    raise exceptions.UserError(_(
                        f"Field '{field}' does not exist in model '{model_label}' ({model_name})"
                    ))

            if subfields is None:
                # Simple field, checked above
                pass
            elif isinstance(subfields, dict):
                # Dict means that the field is many2one field
                if Model._fields[field].type != 'many2one':
                    raise exceptions.UserError(_(
                        f"Field '{field}' is not many2one field in model '{model_label}' ({model_name})"  # NOQA
                    ))

                self._validate_label_fields(Model._fields[field].comodel_name, subfields)
            elif isinstance(subfields, list):
                # List means that the field is many2many or one2many field
                if Model._fields[field].type not in ('many2many', 'one2many'):
                    raise exceptions.UserError(_(
                        f"Field '{field}' is not many2many or one2many field in model '{model_label}' ({model_name})"  # NOQA
                    ))

                self._validate_label_fields(Model._fields[field].comodel_name, subfields[0])
            else:
                raise ValueError('Something is wrong with used fields')

    #
    # Method to call from UI
    #
    @api.model
    def get_label_designer_url(self, label_id: str = None):
        base_url = self.env['ir.config_parameter'].sudo() \
            .get_param('zpl_label_designer.designer_url')

        if not label_id:
            return f'{base_url}/'

        return f'{base_url}/{label_id}'
