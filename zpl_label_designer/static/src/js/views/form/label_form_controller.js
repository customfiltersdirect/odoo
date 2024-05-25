/** @odoo-module **/

import { registry } from '@web/core/registry';
import { formView } from '@web/views/form/form_view';
import { FormController } from '@web/views/form/form_controller';

const { onWillStart } = owl;

export class LabelFormController extends FormController {
    setup() {
        super.setup();

        onWillStart(async () => {
            this.designerURL = await this.env.services.orm.call(
                'zld.label',
                'get_label_designer_url');
        });
    }

    /**
     * @override
     */
    async create() {
        window.open(this.designerURL, '_blank');
    }
}

registry.category('views').add('zld_label_form_view', {
    ...formView,
    Controller: LabelFormController,
});
