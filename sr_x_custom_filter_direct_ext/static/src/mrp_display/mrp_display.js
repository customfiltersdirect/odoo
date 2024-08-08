    /** @odoo-module */


    import { patch } from "@web/core/utils/patch";
    import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";
    import { makeActiveField } from "@web/model/relational_model/utils";

    //var core = require('web.core');
    //var session = require('web.session');
    //var utils = require('web.utils');
    //var field_utils = require('web.field_utils');





    patch(MrpDisplay.prototype, {
     // Define the patched method here
    // setup() {
    //   this._super.apply(this, arguments);
    // },

    _makeModelParams() {
            const res = super._makeModelParams();
//            res.limit = 300
//            debugger;
            return res
        },
    async onClickRefresh() {
        await super.onClickRefresh();
        const check = this._makeModelParams();
        debugger;
    }
    });

