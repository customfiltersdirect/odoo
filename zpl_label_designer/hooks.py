from odoo import SUPERUSER_ID, api


def uninstall_hook(env):
    """
    This hooks cleans links to report. Odoo can't handle such links, so it will ignore some reports
    which was used anywhere in the system.
    """
    reports_model_data = env['ir.model.data'].search_read([
        ('module', '=', 'zpl_label_designer'),
        ('model', '=', 'ir.actions.report')], ['res_id'])
    report_ids = [r['res_id'] for r in reports_model_data]
    reports = env['ir.actions.report'].browse(report_ids)

    # This can cause ValidationError if report_id is required field but this is okay for us.
    # This is better than silently leave broken report action without related view
    reports.unlink()

    # We also need to remove the 'zpl_label_designer.api_key' parameter from the system
    # after removing the module.
    env['ir.config_parameter'].sudo().search([('key', '=', 'zpl_label_designer.api_key')]).unlink()


def post_init_hook(env):
    """
    Generate API key to use for API requests from designer to Odoo.
    """
    Config = env['res.config.settings']
    Config.generate_zld_api_key()
