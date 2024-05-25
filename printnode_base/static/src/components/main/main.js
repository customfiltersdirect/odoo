/** @odoo-module **/

/*
This file includes few snippets related to storing/clearing information about workstation
printers/scales. A bit "hacky" thing :)

The basic idea is to store the information about computer ID (generated in this script) in the
local storage and then use it to store the information about printers/scales in the database.
*/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { Component, onWillRender } from "@odoo/owl";

const { xml } = owl;

class DirectPrintMainComponent extends Component {
    /*
    This component manages workstation devices
    */
    setup() {
        super.setup();

        this.orm = useService("orm");
        this.user = useService("user");

        onWillRender(async () => {
            if (session.dpc_company_enabled) {
                this._setWorkstationId();
            }
        });
    }

    async _setWorkstationId() {
        // Check if ID is set
        let workstationId = browser.localStorage.getItem("printnode_base.workstation_id");

        if (workstationId) {
            // Convert to int
            workstationId = parseInt(workstationId);

            // Check if record with workstationId is exist in db
            const workstation = await this.orm.call(
                "printnode.workstation",
                "search_read",
                [[["id", "=", workstationId]]],
            )

            if (workstation) {
                // Set ID to context
                this.user.updateContext({ "printnode_workstation_id": workstationId });
            } else {
                console.log("Workstation with such ID was not found!");
                browser.localStorage.removeItem("printnode_base.workstation_id");
            }
        }
    }
};

Object.assign(DirectPrintMainComponent, {
    props: {},
    template: xml`<div/>`,
});

registry.category("main_components").add(
    "DirectPrintMainComponent",
    { Component: DirectPrintMainComponent, props: {} }
);
