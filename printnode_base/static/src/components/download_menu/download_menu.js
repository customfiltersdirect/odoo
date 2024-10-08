/** @odoo-module **/

import { ActionMenus } from "@web/search/action_menus/action_menus";
import { ListController } from "@web/views/list/list_controller";
import { AccountMoveListController } from "@account/components/bills_upload/bills_upload";
import { session } from "@web/session";

class DownloadActionMenus extends ActionMenus {

  async setup() {
    await super.setup(...arguments);
    this.printnode_enabled = session.dpc_user_enabled;
  }

  get downloadItems() {
    const printActions = this.props.items.print || [];
    return printActions.map((action) => ({
      action: { ...action, download_only: true },
      description: action.name,
      key: action.id,
    }));
  }

  async executeAction(action) {
    if (this.printnode_enabled) {
      // Add additional option to avoid printing
      this.props.context.download_only = action.download_only === true;
    }

    // Call parent
    return super.executeAction(...arguments);
  }
}

ListController.components.ActionMenus = DownloadActionMenus;

// account.move tree view has custom controller, so we need to override it as well
AccountMoveListController.components.ActionMenus = DownloadActionMenus;
