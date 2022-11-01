/** @odoo-module **/

import { FieldRadio } from 'web.relational_fields';
import { _t } from "@web/core/l10n/translation";
import fieldRegistry from 'web.field_registry';


const LabelRadioField = FieldRadio.extend({
    _render: function () {
        this._super.apply(this, arguments);

        if (!this.values.length) {
            const span = document.createElement('span');
            span.classList.add('text-danger');
            span.innerText = _t('No ZPL Designer labels found');
            this.$el.append(span);
        }
    },
});

fieldRegistry.add('zld_label_radio', LabelRadioField);
