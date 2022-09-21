/** @odoo-module **/

import fieldRegistry from 'web.field_registry';
import { browser } from '@web/core/browser/browser';
import { FieldMany2One } from 'web.relational_fields';
import session from 'web.session';


const WorkstationDeviceField = FieldMany2One.extend({
    init: function (parent, name, record, options) {
        // Save form object for later use
        this.parent = parent;

        this._super.apply(this, arguments);
    },

    commitChanges: function () {
        // This is not a perfect way to update workstations devices but the best one we can use :)
        // The only disadvantage of use of this method is inability to detect form validation
        // issues (in this case we still will update workstation devices)
        const invalidFields = this.parent.canBeSaved(this.record.id);

        // If there is not invalid fields then save the new workstation device
        if (invalidFields.length === 0) {
            if (this.value.data) {
                const workstationDeviceId = this.value.data.id;

                // Save in localStorage for future use
                browser.localStorage.setItem('printnode_base.' + this.name, workstationDeviceId);

                // Update context to send with every request
                let userContext = session.user_context;
                userContext[this.name] = workstationDeviceId;

                // Replace context with updated object
                Object.defineProperties(session, {
                    user_context: {
                        value: userContext,
                        configurable: true,
                    },
                });
            } else {
                // Clean localStorage
                browser.localStorage.removeItem('printnode_base.' + this.name);

                // Remove from user context
                // JFYI: It is strange but we can't add new items in context but easily can
                // remove added ones... This can be changed in the future
                delete session.user_context[this.name];
            }
        }

        return this._super.apply(this, arguments);
    },
});

fieldRegistry.add('printnode_res_users_workstation_device_many2one', WorkstationDeviceField);

export default WorkstationDeviceField;
