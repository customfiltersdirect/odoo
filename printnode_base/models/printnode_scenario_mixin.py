# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models

from .constants import Constants


SECURITY_GROUP = 'printnode_base.printnode_security_group_user'


class PrintNodeScenarioMixin(models.AbstractModel):
    _name = 'printnode.scenario.mixin'
    _inherit = 'printnode.logger.mixin'
    _description = 'Abstract scenario printing mixin'

    def print_scenarios(self, action, ids_list=None, **kwargs):
        """
        Find all scenarios for current model and print reports.

        Returns True when something printed or False in other cases.
        """
        try:
            return self.env['printnode.scenario'].print_reports(
                action=action,
                ids_list=ids_list or self.mapped('id'),
                **kwargs)
        except Exception as err:
            self.printnode_logger(
                log_type=Constants.SCENARIOS_LOG_TYPE,
                log_string=f'Exception occurred while printing: {err}',
            )

            # Do not raise any interface errors from DPC module to no break crons
            if self.env.context.get('printnode_from_cron'):
                return False

            raise err

    def change_dictionary_keys_type_to_string(self, dct):
        """Change dictionary keys type to string
        """
        new_dict = {}
        for i in dct:
            new_dict[str(i)] = dct[i]
        return new_dict
