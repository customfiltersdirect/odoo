/** @odoo-module **/

import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { FormController } from "@web/views/form/form_controller";
import { session } from "@web/session";


class DownloadCogMenu extends CogMenu {

  async setup() {
    await super.setup(...arguments);
    this.dpcEnabled = session.dpc_user_enabled;
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
    if (this.dpcEnabled) {
      // Add additional option to avoid printing
      this.props.context.download_only = action.download_only === true;
    }

    // Call parent
    return super.executeAction(...arguments);
  }
}

FormController.components.CogMenu = DownloadCogMenu;
