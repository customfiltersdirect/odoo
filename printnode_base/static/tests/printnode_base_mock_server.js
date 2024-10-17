/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MockServer } from "@web/../tests/helpers/mock_server";

patch(MockServer.prototype, {
    /**
     * Simulate the `get_status` route response to render StatusMenu
     * @override
     */
    async _performRPC(route, args) {
        if (args.model === 'printnode.base' && args.method === 'get_status') {
            return Promise.resolve({
                'limits': [],
                'devices': {},
                'releases': [],
            });
        }
        return super._performRPC(...arguments);
    },
});
