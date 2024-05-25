import json

from odoo import fields, release
from odoo.http import Controller, route, request
from werkzeug.exceptions import NotFound

from .utils import add_env, required, validate


ALLOWED_FIELDS = [
    fields.Char, fields.Text,
    fields.Integer, fields.Float,
    fields.Boolean, fields.Many2one,
    fields.Selection, fields.Datetime,
    # Experimental
    fields.One2many, fields.Many2many,
]
FIELDS_TO_IGNORE = ['create_uid', 'write_uid']

RESPONSE_HEADERS = {
    'Content-Type': 'application/json',
}


class ZLDController(Controller):
    @route('/zld/<string:db>/ping', type='http', auth='none', methods=['GET'])
    @add_env
    @validate
    def ping(self, db):
        """
        Ping the server to check if it is alive and has installed the module
        """
        module_version = request.env['ir.module.module'].search(
            [['name', '=', 'zpl_label_designer']]).latest_version
        odoo_version = release.major_version

        return request.make_response(
            json.dumps({'data': {'odoo_version': odoo_version, 'zld_version': module_version}}),
            headers=RESPONSE_HEADERS)

    @route('/zld/<string:db>/models', type='http', auth='none', methods=['GET'])
    @add_env
    @validate
    def get_allowed_models(self, db, *args, **kwargs):
        """
        Returns allowed models to use in the designer.
        """
        allowed_models = [
            {'id': model.id, 'model': model.model, 'name': model.name}
            for model in request.env.company.zld_allowed_models.sudo()]

        return request.make_response(
            json.dumps({'data': allowed_models}),
            headers=RESPONSE_HEADERS)

    @route('/zld/<string:db>/fields/<string:model>', type='http', auth='none', methods=['GET'])
    @add_env
    @validate
    def get_allowed_fields(self, db, model, *args, **kwargs):
        """
        Returns list of fields to use in label design (sorted by label)
        like [{name: ..., label: ..., type: ..., comodel: ...}, ...]

        :param model: optional str: 'res.company', 'res.partner', ...
        """
        if model not in request.env:
            raise NotFound('Model does not found')

        fields_ = []

        for field_name, field in request.env[model]._fields.items():
            if field_name in FIELDS_TO_IGNORE or field_name.startswith('_'):
                continue

            if any([isinstance(field, FieldType) for FieldType in ALLOWED_FIELDS]):
                fields_.append({
                    'name': field_name,
                    'label': field.string,
                    'type': type(field).type,
                    'comodel': getattr(field, 'comodel_name', False),
                })

        fields_.sort(key=lambda d: d['label'])

        return request.make_json_response(
            {'data': fields_},
            headers=RESPONSE_HEADERS)

    @route('/zld/<string:db>/preview', type='http', auth='none', csrf=False, methods=['POST'])
    @add_env
    @validate
    @required('model', 'fields')
    def get_preview(self, db, *args, **kwargs):
        """
        Returns preview with demo data.
        """
        data = request.get_json_data()
        model = data['model']
        fields = data['fields']

        try:
            data_for_preview = request.env['zld.label'].get_preview_data(model, fields)
        except Exception as e:
            return request.make_json_response(
                {'error': str(e)},
                headers=RESPONSE_HEADERS,
                status=400)

        return request.make_json_response(
            {'data': data_for_preview},
            headers=RESPONSE_HEADERS)

    @route('/zld/<string:db>/labels', type='http', auth='none', csrf=False, methods=['POST'])
    @add_env
    @validate
    @required('name', 'model', 'qweb_xml', 'label_fields', 'width', 'height', 'dpi', 'orientation', 'designer_label_id')  # NOQA
    def create_label(self, db, *args, **kwargs):
        """
        Return preview with demo data.
        """
        data = request.get_json_data()

        try:
            label_id = request.env['zld.label'].create_label(data)
        except Exception as e:
            return request.make_json_response(
                {'error': str(e)},
                headers=RESPONSE_HEADERS,
                status=400)

        return request.make_json_response(
            {'data': {'label_id': label_id}},
            headers=RESPONSE_HEADERS)

    @route('/zld/<string:db>/labels/<int:label_id>', type='http', auth='none', csrf=False, methods=['PUT'])  # NOQA
    @add_env
    @validate
    @required('name', 'qweb_xml', 'label_fields', 'width', 'height', 'dpi', 'orientation', 'designer_label_id')  # NOQA
    def update_label(self, db, label_id, *args, **kwargs):
        """
        Update label and return label ID.
        """
        data = request.get_json_data()

        try:
            label_id = request.env['zld.label'].update_label(label_id, data)
        except Exception as e:
            return request.make_json_response(
                {'error': str(e)},
                headers=RESPONSE_HEADERS,
                status=400)

        return request.make_json_response(
            {'data': {'label_id': label_id}},
            headers=RESPONSE_HEADERS)

    @route('/zld/<string:db>/labels/<int:label_id>', type='http', auth='none', csrf=False, methods=['DELETE'])  # NOQA
    @add_env
    @validate
    def delete_label(self, db, label_id, *args, **kwargs):
        """
        Delete label and return label ID.
        """
        try:
            request.env['zld.label'].delete_label(label_id)
        except Exception as e:
            return request.make_json_response(
                {'error': str(e)},
                headers=RESPONSE_HEADERS,
                status=400)

        return request.make_json_response(
            {'data': []},
            headers=RESPONSE_HEADERS)
