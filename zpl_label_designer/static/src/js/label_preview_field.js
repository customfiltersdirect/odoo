odoo.define('zpl_label_designer.PreviewField', function (require) {
  "use strict";

  const config = require('web.config');
  const core = require('web.core');
  const FieldRegistry = require('web.field_registry');
  const FieldText = require('web.basic_fields').FieldText;
  const _t = core._t;

  const DENSITY = {
    '152': '6dpmm',
    '203': '8dpmm',
    '300': '12dpmm',
    '600': '24dpmm',
  };

  const PreviewField = FieldText.extend({
    init: function (parent, name, record, options) {
      // Save form object for later use
      this.parent = parent;

      this._super.apply(this, arguments);
    },

    _renderZPLContent: function () {
      // Show raw label content only in debug mode
      if (config.isDebug()) {
        const textarea = document.createElement('textarea');
        textarea.classList.add('zpl-preview-content', 'mt-4');
        textarea.value = this._formatValue(this.value);
        textarea.readOnly = true;

        // Select preview content on double click
        textarea.addEventListener('dblclick', (e) => {
          e.preventDefault();
          textarea.select();
        });

        this.$el.append(textarea);
      }
    },

    _renderEdit: function () {
      // This field looks the same in readonly and edit modes
      this._renderZPLContent();
    },

    _renderReadonly: function () {
      // this._super();
      this._renderZPLContent();

      // Load preview only in readonly mode. We also hide it in edit mode but this method
      // is called anyway
      if (this.parent.mode === 'readonly') {
        this._renderZPLPreview();
      } else {
        this.$el.text(_t('Preview is not available in edit mode'));
      }
    },

    _renderZPLPreview: function () {
      if (this.record.data.preview) {
        // TODO: Move dpmm to readonly calculated field on backend?
        const dpmm = DENSITY[this.record.data.dpi];
        const width = this.record.data.width;
        const height = this.record.data.height;
        const labelaryUrl = `https://api.labelary.com/v1/printers/${dpmm}/labels/${width}x${height}/0/`;

        let formData = new FormData();
        formData.append("file", this.record.data.preview);

        fetch(labelaryUrl, { method: 'POST', body: formData })
          .then(response => response.blob())
          .then(blob => {
            const previewURL = URL.createObjectURL(blob);

            const imageEl = document.createElement('img');
            imageEl.classList.add('border');
            imageEl.src = previewURL;

            this.$el.prepend(imageEl);
          });
        // TODO: Add error catching
      }
    }
  });

  FieldRegistry.add('zld_preview', PreviewField);

  return PreviewField;
});
