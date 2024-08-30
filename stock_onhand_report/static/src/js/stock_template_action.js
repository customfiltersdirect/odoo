/** @odoo-module **/

import { registry } from "@web/core/registry";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { intersection, unique } from "@web/core/utils/arrays";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { PERIODS } from "@spreadsheet_edition/assets/helpers";
import { omit } from "@web/core/utils/objects";
//import rpc from 'web.rpc';

import { _t } from "@web/core/l10n/translation";
import { SpreadsheetSelectorDialog } from "@spreadsheet_edition/assets/components/spreadsheet_selector_dialog/spreadsheet_selector_dialog";

import { onWillStart } from "@odoo/owl";

patch(PivotRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.userService = useService("user");
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        onWillStart(async () => {
            const insertionGroups = registry.category("spreadsheet_view_insertion_groups").getAll();
            const userGroups = await Promise.all(
                insertionGroups.map((group) => this.userService.hasGroup(group))
            );
            this.canInsertPivot = userGroups.some((group) => group);
        });
    },

    _onOpenCustomWizard() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Date Range',
            res_model: 'date.range.wizard',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            flags: {
                action_reload: true,
                reload_on_any_change: true,
            },
        });
    },

    _onTriggerCustomQuery() {
        this.actionService.doAction({
            type: 'ir.actions.server',
            id: 1215,
        });
    },

});
