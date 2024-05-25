/** @odoo-module **/

import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';

const { onWillStart } = owl;

export class LabelListController extends ListController {
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
    onClickCreate() {
        window.open(this.designerURL, '_blank');
    }
}

registry.category('views').add('zld_label_list_view', {
    ...listView,
    Controller: LabelListController,
});
