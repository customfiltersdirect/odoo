    /** @odoo-module */

    import { patch } from "@web/core/utils/patch";
    import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";
    import { makeActiveField } from "@web/model/relational_model/utils";

    patch(MrpDisplay.prototype, {
     // Define the patched method here
		async setup() {
			super.setup();
			this.state.limit = 300;
		},

    	_makeModelParams() {
            const res = super._makeModelParams();
            res.limit = 300;
            return res
        }
    });

