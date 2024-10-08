/* @odoo-module */

import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";

import { Component, onWillRender, useState } from "@odoo/owl";

import { Dropdown } from "@web/core/dropdown/dropdown";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const MANAGER_GROUP = "printnode_base.printnode_security_group_manager";

function useDirectPrintStatusMenuSystray() {
    const ui = useState(useService("ui"));
    return {
        class: "o-printnode_base-DirectPrintStatusMenu-class",
        get contentClass() {
            return `d-flex flex-column flex-grow-1 bg-view ${ui.isSmall ? "overflow-auto w-100 mh-100" : ""
                }`;
        },
        get menuClass() {
            return `p-0 o-printnode_base-DirectPrintStatusMenu ${ui.isSmall
                ? "o-mail-systrayFullscreenDropdownMenu start-0 w-100 mh-100 d-flex flex-column mt-0 border-0 shadow-lg"
                : ""
                }`;
        },
    };
}

export class DirectPrintStatusMenu extends Component {
    static components = { Dropdown };
    static props = [];
    static template = "printnode_base.DirectPrintStatusMenu";

    setup() {
        this.directPrintStatusMenuSystray = useDirectPrintStatusMenuSystray();
        this.ui = useState(useService("ui"));
        this.state = useState({
            isOpen: false,
            isManager: false,
            releases: [],
            limits: [],
            devices: {},
            workstations: [],
            isManager: false,
            directPrintEnabled: session.dpc_user_enabled,
            loaded: false,
        });

        this.orm = useService("orm");
        this.user = useService("user");

        onWillRender(async () => {
            if (!this.state.loaded) {
                this.state.isManager = await this.user.hasGroup(MANAGER_GROUP);

                if (this.state.isManager) {
                    const data = await this.orm.call(
                        "printnode.base",
                        "get_status",
                        [],
                        { "only_releases": true });

                    this.state.limits = data.limits;
                    this.state.releases = data.releases;
                    this.state.devices = data.devices;
                    this.state.workstations = data.workstations;
                }

                this.state.loaded = true;
            }
        });
    }

    async beforeOpen() {
        const data = await this.orm.call(
            "printnode.base",
            "get_status",
            [],
            { "only_releases": false });

        this.state.releases = data.releases;
        this.state.limits = data.limits;
        this.state.devices = data.devices;
        this.state.workstations = data.workstations;
    }

    get rateUsURL() {
        // Rate Us URL
        let odooVersion = odoo.info.server_version;
        // This attribute can include some additional symbols we do not need here (like 12.0e+)
        odooVersion = odooVersion.substring(0, 4);

        return `https://apps.odoo.com/apps/modules/${odooVersion}/printnode_base/#ratings`;
    }

    get currentWorkstationId() {
        let workstationId = browser.localStorage.getItem("printnode_base.workstation_id");
        return workstationId;
    }


    close() {
        // hack: click on window to close dropdown, because we use a dropdown
        // without dropdownitem...
        document.body.click();
    }

    setWorkstationDevice(e) {
        const workstationId = e.target.value;

        if (workstationId) {
            browser.localStorage.setItem("printnode_base.workstation_id", workstationId);
            this.user.updateContext({ "printnode_workstation_id": parseInt(workstationId) });
        } else {
            browser.localStorage.removeItem("printnode_base.workstation_id");

            if ("printnode_workstation_id" in this.user.context) {
                this.user.removeFromContext("printnode_workstation_id");
            }
        }

        // Reload data in model
        this.beforeOpen();
    }

}

registry
    .category("systray")
    .add("printnode_base.DirectPrintStatusMenu", { Component: DirectPrintStatusMenu }, { sequence: 25 });
