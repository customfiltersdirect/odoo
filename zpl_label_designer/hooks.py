from odoo import SUPERUSER_ID, api


def uninstall_hook(cr, registry):
    """
    This hooks cleans links to report. Odoo can't handle such links, so it will ignore some reports
    which was used anywhere in the system.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    reports_model_data = env['ir.model.data'].search_read([
        ('module', '=', 'zpl_label_designer'),
        ('model', '=', 'ir.actions.report')], ['res_id'])
    report_ids = [r['res_id'] for r in reports_model_data]
    reports = env['ir.actions.report'].browse(report_ids)

    # This can cause ValidationError if report_id is required field but this is okay for us
    # This is better than silently leave broken report action without related view
    reports.unlink()
