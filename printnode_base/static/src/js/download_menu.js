/** @odoo-module **/

import Context from 'web.Context';
import DropdownMenu from 'web.DropdownMenu';
import DropdownMenuItem from 'web.DropdownMenuItem';

class DownloadDDMenuItem extends DropdownMenuItem {
    constructor() {
        super(...arguments);
        this.downloadOnly = true;
    }
}

class DownloadDDMenu extends DropdownMenu { }

DownloadDDMenu.template = 'printnode.DownloadDDMenu';
DownloadDDMenu.components = { DownloadDDMenuItem };

const ActionMenus = require("web.ActionMenus");

class DownloadActionMenus extends ActionMenus {

    async willStart() {
        await super.willStart(...arguments);
        this.printnode_enabled = this.env.session.printnode_enabled;
    }

    async _executeAction(action) {
        if (event.originalComponent.downloadOnly) {
            // If selected from Download menu add additional option
            const downloadOnly = event.originalComponent.downloadOnly;
            let activeIds = this.props.activeIds;
            if (this.props.isDomainSelected) {
                activeIds = await this.rpc({
                    model: this.env.action.res_model,
                    method: 'search',
                    args: [this.props.domain],
                    kwargs: {
                        limit: this.env.session.active_ids_limit,
                    },
                });
            }
            const activeIdsContext = {
                active_id: activeIds[0],
                active_ids: activeIds,
                active_model: this.env.action.res_model,
            };
            if (this.props.domain) {
                // keep active_domain in context for backward compatibility
                // reasons, and to allow actions to bypass the active_ids_limit
                activeIdsContext.active_domain = this.props.domain;
            }

            const context = new Context(this.props.context, activeIdsContext).eval();
            const result = await this.rpc({
                route: '/web/action/load',
                params: { action_id: action.id, context },
            });
            result.context = new Context(result.context || {}, activeIdsContext)
                .set_eval_context(context);
            result.flags = result.flags || {};
            result.flags.new_window = true;
            this.trigger('do-action', {
                action: result,
                options: {
                    // here we add option
                    download: downloadOnly,
                    on_close: () => this.trigger('reload'),
                },
            });
        } else {
            return super._executeAction(...arguments);
        }
    }
}

DownloadActionMenus.components.DownloadDDMenu = DownloadDDMenu;

const ControlPanel = require("web.ControlPanel");
ControlPanel.components.ActionMenus = DownloadActionMenus;

export { DownloadDDMenu, DownloadDDMenu, DownloadActionMenus };
