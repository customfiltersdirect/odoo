/** @odoo-module **/

import rpc from 'web.rpc';

import { qweb } from 'web.core';
import { _t } from "@web/core/l10n/translation";
import viewRegistry from 'web.view_registry';
import { WarningDialog } from "@web/core/errors/error_dialogs";
import FormController from 'web.FormController';
import FormView from 'web.FormView';
import { ServerError } from './exceptions';
import { SERVER_DOWN_MESSAGE } from './constants';

// var qweb = core.qweb;


// This controller adds drag&drop support to the label editor (to upload images)
const LabelFormController = FormController.extend({
  _dropAllowedTypes: ['image/png', 'image/jpeg'],

  init: function (parent, model, renderer, params) {
    console.log('LabelFormController.init');
    this._super.apply(this, arguments);

    // Load settings for the label editor
    // TODO: Load only for readonly mode? Move to async method?
    this._loadSettings();
  },

  update: function (params, options) {
    return this._super.apply(this, arguments).then((res) => {
      // Reload settings for the label editor
      return this._loadSettings();
    });
  },

  start: function () {
    this._dropArea = document.querySelector('body');

    // Create overlay for drop area
    if (!this._dropOverlay) {
      this._addDropOverlay();
    }

    // Create functions with attached context 
    this._startFileUploadingCallback = this._startFileUploading.bind(this);
    this._endFileUploadingCallback = this._endFileUploading.bind(this);
    this._dropNewImagesCallback = this._dropNewImages.bind(this);

    return this._super.apply(this, arguments);
  },

  saveRecord: function (recordID, options) {
    return this._super.apply(this, arguments).then((res) => {
      // Reload settings for the label editor
      return this._loadSettings();
    });
  },

  _callButtonAction: function (attrs, record) {
    // TODO: This can (and should) be done like here:
    // https://github.com/OCA/web/tree/15.0/web_ir_actions_act_multi
    return this._super.apply(this, arguments).then((result) => {
      if (['publish', 'unpublish'].includes(attrs.name)) {
        // this.update({}, { reload: true });
        // Manually reload the view to show different set of buttons
        this.reload();
      }
    });
  },

  _loadSettings: function () {
    console.log('Loading settings for the label editor');
    return rpc.query({
      model: 'zld.label',
      method: 'get_settings',
      args: [[this._get_record_id()]],
    }).then(settings => {
      this.settings = settings;

      // A bit hacky way to pass settings to form fields
      this.renderer.settings = settings;
    });
  },

  _setMode: function (mode) {
    if (mode === 'edit') {
      this._enableDragAndDrop();
    } else {
      this._disableDragAndDrop();
    }

    return this._super.apply(this, arguments);
  },

  _enableDragAndDrop: function () {
    // Disable any other actions when user dragging files
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      this._dropArea.addEventListener(eventName, this._preventDefaults, false);
    });

    // Start dragging file
    this._dropArea.addEventListener('dragenter', this._startFileUploadingCallback, false);
    this._dropArea.addEventListener('dragover', this._startFileUploadingCallback, false);

    // End dragging file / Drop file
    // Here we use drop overlay because this element shown above all other elements
    this._dropOverlay.addEventListener('dragleave', this._endFileUploadingCallback, false);
    this._dropOverlay.addEventListener('drop', this._dropNewImagesCallback, false);
  },

  _disableDragAndDrop: function () {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      this._dropArea.removeEventListener(eventName, this._preventDefaults, false);
    });

    this._dropArea.removeEventListener('dragenter', this._startFileUploadingCallback, false);
    this._dropArea.removeEventListener('dragover', this._startFileUploadingCallback, false);

    this._dropOverlay.removeEventListener('dragleave', this._endFileUploadingCallback, false);
    this._dropOverlay.removeEventListener('drop', this._dropNewImagesCallback, false);
  },

  _addDropOverlay: function () {
    // FIXME: Use jQuery but this is not a good solution...
    const $dropOverlay = $(qweb.render("zpl_label_designer.DropOverlay"));

    this._dropOverlay = $dropOverlay[0];
    this._dropArea.append(this._dropOverlay);
  },

  _startFileUploading: function (e) {
    let dt = e.dataTransfer;

    if (dt.types.indexOf('Files') != -1) {
      this._showOverlay();
    }
  },

  _endFileUploading: function (e) {
    let dt = e.dataTransfer;

    if (dt.types.indexOf('Files') != -1) {
      if (e.target == this._dropOverlay) { // Out of overlay area
        this._hideOverlay();
      }
    }
  },

  _dropNewImages: function (e) {
    const dt = e.dataTransfer;

    if (dt.types.indexOf('Files') != -1) {
      const files = dt.files;

      const imageFiles = ([...files]).filter(
        f => this._dropAllowedTypes.includes(f.type));

      imageFiles.forEach(this._addNewImage, this);

      this._hideOverlay();
    }
  },

  _showOverlay: function () {
    this._dropOverlay.classList.remove('d-none');
  },

  _hideOverlay: function () {
    this._dropOverlay.classList.add('d-none');
  },

  _addNewImage: function (file) {
    const fieldWithCanvas = this._getFieldWidgetWithCanvas();

    if (!fieldWithCanvas) {
      // Actually, there is nothing to do here
      return;
    }

    if (file.size > 1 * 1024 * 1024) {
      this.displayNotification({
        title: _t('Image is too big'),
        message: _t('Image is too big. Maximum allowed size is 1 MB'),
        type: 'danger',
      });
      return;
    }

    const filename = file.name;

    const reader = new FileReader();
    const that = this;
    reader.onload = function (file) {
      // TODO: Refactor?
      // Create temp image element
      const previewImage = document.createElement('img');

      // When preview is loaded
      const converterUrl = that.settings.converter_url;
      previewImage.onload = () => {
        fetch(`${converterUrl}/convert-image`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: filename,
            base64: previewImage.src,
          })
        })
          .then(resp => resp.json())
          .then((data) => {
            if (data.status_code !== 200) {
              throw new ServerError(
                _t('Something went wrong'),
                data.message || SERVER_DOWN_MESSAGE
              );
            }

            const dataURI = data.data;

            fabric.Image.fromURL(
              `${dataURI}`,
              (oImg) => { fieldWithCanvas.canvas.add(oImg) },
              { id: that._generateUniqueID() }
            );
          })
          .catch(error => {
            let title = _t('Something went wrong');
            let message = SERVER_DOWN_MESSAGE;

            if (error instanceof ServerError) {
              title = error.title;
              message = error.message;
            }

            return new WarningDialog(
              this,
              { title: title },
              { message: message }
            ).open();
          });
      };

      // Change image source
      previewImage.src = reader.result;
    };

    reader.onerror = function (error) {
      console.log(error);
      alert(`Error occurred reading file: ${filename}`);
    };

    reader.readAsDataURL(file);
  },

  _getFieldWidgetWithCanvas: function () {
    // This is a bit hacky but there is no other way to get access to the canvas
    const widgets = this.renderer.allFieldWidgets;
    return widgets[this.renderer.state.id].filter(w => w.canvas)[0];
  },

  _generateUniqueID: () => (new Date()).getTime(),

  _preventDefaults: (e) => {
    e.preventDefault();
    e.stopPropagation();
  },

  _get_record_id: function () {
    return this.renderer.state.res_id;
  },

});

export const LabelView = FormView.extend({
  config: _.extend({}, FormView.prototype.config, {
    Controller: LabelFormController,
  }),
});

viewRegistry.add('zld_label_form', LabelView);
