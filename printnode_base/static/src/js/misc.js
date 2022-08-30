/** @odoo-module **/

/*
This file includes few snippets related to storing/clearing information about workstation
printers/scales. A bit 'hacky' thing :)
*/

import rpc from 'web.rpc';

import { browser } from '@web/core/browser/browser';
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

import WORKSTATION_DEVICES from './constants';


class DirectPrintMainComponent extends owl.Component {
    /*
    This component manages workstation devices
    */
    constructor(parent, props) {
        super(...arguments);

        this.user = useService("user");
    }

    async willStart() {
        // Remove information about workstation printers from localStorage when logout
        const currentUserId = this.user.userId;
        const storageUserId = browser.localStorage.getItem('printnode_base.user_id');

        // If not user found in localStorage or user changed - clean workstation devices
        if (!storageUserId || (currentUserId != parseInt(storageUserId))) {
            for (let workstationDevice of WORKSTATION_DEVICES) {
                browser.localStorage.removeItem('printnode_base.' + workstationDevice);
            }
        }

        // Save current user in localStorage
        browser.localStorage.setItem('printnode_base.user_id', currentUserId);

        // Check if devices with IDs from localStorage exists
        const devicesInfo = Object.fromEntries(
            WORKSTATION_DEVICES
                .map(n => [n, browser.localStorage.getItem('printnode_base.' + n)])  // Two elements array
                .filter(i => i[1]) // Skip empty values
        );

        return rpc.query({
            model: 'res.users',
            method: 'validate_device_id',
            kwargs: { devices: devicesInfo }
        }).then((data) => {
            let existingWorkstationDevices = {};

            // Remove bad device IDs from localStorage
            for (const workstationDevice in data) {
                if (data[workstationDevice]) {
                    // ID is correct, place in session
                    let workstationDeviceId = browser.localStorage.getItem(
                        'printnode_base.' + workstationDevice);

                    if (workstationDeviceId) {
                        // Add information about printer to user context
                        existingWorkstationDevices[workstationDevice] = workstationDeviceId;
                    }
                } else {
                    // Remove from localStorage
                    browser.localStorage.removeItem('printnode_base.' + workstationDevice);
                }
            }

            // Update workstation devices in context
            this.user.updateContext(existingWorkstationDevices);
        });
    }

};

Object.assign(DirectPrintMainComponent, {
    props: {},
    template: owl.tags.xml`<div/>`,
});

registry.category("main_components").add(
    "DirectPrintMainComponent",
    { Component: DirectPrintMainComponent, props: {} }
);
