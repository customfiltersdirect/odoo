/** @odoo-module **/

import ajax from 'web.ajax';
import rpc from 'web.rpc';
import session from 'web.session';

import { registry } from '@web/core/registry';

import WORKSTATION_DEVICES from './constants';

const systrayRegistry = registry.category('systray');
const MANAGER_GROUP = 'printnode_base.printnode_security_group_manager';

export class PrintnodeStatusMenu extends owl.Component {
    setup() {
        this.state = owl.useState({
            limits: [],
            devices: [],
            releases: [],
            newRelease: false,
            isManager: false,
        });

        // Rate Us URL
        let odooVersion = odoo.info.server_version;
        // This attribute can include some additional symbols we do not need here (like 12.0e+)
        odooVersion = odooVersion.substring(0, 4);
        this.rateUsURL = `https://apps.odoo.com/apps/modules/${odooVersion}/printnode_base/#ratings`;
    }

    async willStart() {
        // We check if current user has Manager group to make some elements of status menu
        // visible only for managers
        const groupCheckPromise = session.user_has_group(MANAGER_GROUP).then(
            this._loadContent.bind(this));

        return groupCheckPromise;
    }

    async _loadContent(isManager) {
        this.state.isManager = isManager;

        if (isManager) {
            const limitsPromise = rpc.query({ model: 'printnode.account', method: 'get_limits' });

            // Check if model with releases already exists 
            const releasesPromise = ajax.post("/dpc/release-model-check").then((data) => {
                const status = JSON.parse(data);

                // If model exists load releases
                if (status) {
                    return rpc.query({ model: 'printnode.release', method: 'search_read' });
                }
                // If not exist return empty array
                return [];
            });

            return Promise.all(
                [limitsPromise, releasesPromise]
            ).then(this._loadedCallback.bind(this));
        }
    }

    _loadedCallback([limits, releases]) {
        // Process limits
        this.state.limits = limits;

        // Process accounts
        this.state.releases = releases;
        this.state.newRelease = releases.length > 0;
    }

    _capitalizeWords(str) {
        const words = str.split(" ");
        let capitalizedWords = words.map(w => w[0].toUpperCase() + w.substr(1));
        return capitalizedWords.join(' ');
    }

    _onStatusMenuShow() {
        /*
        Update workstation devices each time user clicks on the status menu
        */
        // Clean old information about workstation devices
        this.state.devices = [];

        const devicesInfo = Object.fromEntries(
            WORKSTATION_DEVICES
                .map(n => [n, localStorage.getItem('printnode_base.' + n)])  // Two elements array
                .filter(i => i[1]) // Skip empty values
        );

        const devicesPromise = rpc.query({
            model: 'res.users',
            method: 'validate_device_id',
            kwargs: { devices: devicesInfo }
        });

        devicesPromise.then((data) => {
            // Process workstation devices
            const devices = WORKSTATION_DEVICES.map(
                device => {
                    // Remove printnode_ and _id from the of string
                    let deviceName = device.substring(10, device.length - 3).replace(/_/g, ' ');

                    // Return pairs (type, name)
                    return [this._capitalizeWords(deviceName), data[device]];
                }
            );

            this.state.devices = devices;
        });
    }
}

Object.assign(PrintnodeStatusMenu, {
    props: {},
    template: 'printnode_base.StatusMenu',
});

systrayRegistry.add('printnode_base.StatusMenu', {
    Component: PrintnodeStatusMenu,
});