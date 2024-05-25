/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, xml } from '@odoo/owl';

const DENSITY = {
    152: '6dpmm',
    203: '8dpmm',
    300: '12dpmm',
    600: '24dpmm',
};

export class LabelPreviewField extends Component {
    setup() {
        this.imageSrc = useState({ value: null });

        onWillStart(async () => {
            const record = this.props.record;

            const dpmm = DENSITY[record.data.dpi];
            const width = record.data.width;
            const height = record.data.height;
            const data = record.data[this.props.name];

            const formData = new FormData();
            formData.append('file', data);

            fetch(this.generateLabelaryUrl(dpmm, width, height), { method: 'POST', body: formData })
                .then((response) => response.blob())
                .then((blob) => {
                    const previewURL = URL.createObjectURL(blob);

                    // Update image source
                    this.imageSrc.value = previewURL;
                });
        });
    }

    generateLabelaryUrl(dpmm, width, height) {
        return `https://api.labelary.com/v1/printers/${dpmm}/labels/${width}x${height}/0/`;
    }

}

LabelPreviewField.template = 'zpl_label_designer.LabelPreviewField';

registry.category('fields').add('zld_label_preview', { component: LabelPreviewField });
