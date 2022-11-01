/** @odoo-module **/

import config from 'web.config';
import AbstractField from 'web.AbstractField';
import fieldRegistry from 'web.field_registry';

import { _t } from "@web/core/l10n/translation";

import {
  CONTROL_CORNER_SIZE, FONTS, GOOGLE_FONTS,
  PROPERTIES_TO_SAVE, RECT_CONTROLS, TEXT_CONTROLS, WORD_JOINERS
} from './constants';


const LabelEditorField = AbstractField.extend({
  template: 'zpl_label_designer.LabelEditor',

  events: _.extend({}, AbstractField.prototype.events, {}),
  custom_events: _.extend({}, AbstractField.prototype.custom_events, {}),

  init: function (parent) {
    this._super.apply(this, arguments);

    // Save form object for later use
    this.parent = parent;

    // Do not consider space as a word joiner
    // This way text breaks only when the user types Enter
    fabric.Textbox.prototype._wordJoiners = WORD_JOINERS;

    // TODO: Refactor? Need a better way to hide controls
    const originalGetVisibility = fabric.Control.prototype.getVisibility;
    fabric.Control.prototype.getVisibility = function (fabricObject, controlKey) {
      if (fabricObject.type === 'image' && ['increaseControl', 'decreaseControl', 'fillControl'].includes(controlKey)) {
        return false;
      }

      return originalGetVisibility.call(this, fabricObject, controlKey);
    };

    // Icons for controls
    this.controlIcons = {};
  },

  _renderEdit: function () {
    this._setupEditor();
  },

  _renderReadonly: function () {
    this._setupEditor(true);
    this.$el.find('.control-panel').hide();
  },

  _setupEditor: function (readonly = false) {
    if (!this.record.data.id) {
      // No record yet, do not render anything
      return;
    }

    // Load custom fonts before the canvas initialization
    const observers = GOOGLE_FONTS.map(font => {
      const observer = new FontFaceObserver(font[0], font[1]);
      return observer.load();
    });

    Promise.all(observers)
      .then(() => {
        // Initialize canvas
        const width = this.record.data.width * this.record.data.dpi;
        const height = this.record.data.height * this.record.data.dpi;

        this.canvasEl = this.$el.find('canvas')[0];

        this.canvas = new fabric.Canvas(
          this.canvasEl,
          {
            width: width,
            height: height,
            snapThreshold: 45,
            snapAngle: 90,
          }
        );

        this._loadControls();

        // Load content
        if (this.record.data.blob) {
          // TODO: Need to provide a check for a correct JSON string
          this.canvas.loadFromJSON(this.record.data.blob, () => {
            this.canvas.forEachObject(function (object) {
              object.selectable = !readonly;

              // Detect if we want to split by spaces. It is used mostly for QR only
              // object._wordJoiners = object.splitWords ? DEFAULT_WORD_JOINERS : WORD_JOINERS;
            });
          });
        }

        // Load different parts required for editor
        if (!readonly) {
          this._loadControlIcons();
          this._addQuickFieldsButtons();
          this._addEvents();
          this._updateCustomFields();
        }

        // Debug logging
        if (config.isDebug()) {
          console.log(this.canvas);
          console.log(this.record);
        }
      });
  },

  _addQuickFieldsButtons: function () {
    console.log(this.parent);
    const quickFields = this.parent.settings.quick_fields || {};

    // Clean buttons container
    const containerEl = this.el.querySelector('.quick-buttons');
    while (containerEl.firstChild) {
      containerEl.removeChild(containerEl.firstChild);
    }

    // Add new buttons
    Object.entries(quickFields).forEach(f => {
      const [field, value] = f;
      const buttonEl = document.createElement('button');
      buttonEl.innerText = field;
      buttonEl.classList.add('btn', 'btn-outline-primary', 'mr-2', 'mb-2', 'zld-add-text');
      buttonEl.dataset.value = `%%${value}%%`;

      containerEl.append(buttonEl);
    });
  },

  _addEvents: function () {
    this.el.querySelectorAll('.zld-add-text').forEach(
      el => el.addEventListener('click', this._addTextboxCallback.bind(this))
    );
    this.el.querySelector('#zld-add-rectangle').addEventListener(
      'click', this._addRectCallback.bind(this));

    this.el.querySelector('.zld-add-custom-field button').addEventListener(
      'click', this._addCustomFieldCallback.bind(this));

    // Listen to keyboard events
    // This is not actually a good option to listen to document events
    // but there is no other way to do it (at least for now)
    // TODO: http://fabricjs.com/events
    document.onkeydown = (e) => {
      // Notice: e.key is not fully supported in all browsers! Need to check it
      const key = e.key;

      if (key === 'Backspace' || key === 'Delete') {
        const activeObject = this.canvas.getActiveObject();

        if (activeObject && !activeObject.isEditing) {
          this.canvas.remove(activeObject);
          this.canvas.renderAll();
        }
      }
    };

    this.canvas.on("text:changed", this._adjustTextWidth);
  },

  _updateCustomFields: function () {
    const fields = this.parent.settings.allowed_fields || [];
    const selectEl = this.el.querySelector('.zld-add-custom-field select');

    fields.forEach(([key, value]) => {
      const optionEl = document.createElement('option');
      optionEl.value = key;
      optionEl.text = value;
      selectEl.appendChild(optionEl);
    });
  },

  _adjustTextWidth: (e) => {
    const object = e.target;

    if (object instanceof fabric.IText) {
      // Adjust text width
      const textLinesMaxWidth = object.textLines.reduce(
        (max, _, i) => Math.max(max, object.getLineWidth(i)), 0);
      object.set({ width: textLinesMaxWidth });
    }
  },

  commitChanges: function () {
    // Save canvas content only if record exists
    if (this.record.data.id) {
      this._setValue(
        JSON.stringify(this.canvas.toJSON(PROPERTIES_TO_SAVE)),
        { notify: false }
      );
    }
  },

  _addTextboxCallback: function (e) {
    e.preventDefault();

    const text = e.target.dataset.value || 'Lorum ipsum';

    // Everything with data- attribute should be not editable
    // const editable = !e.target.dataset.value;

    this._addTextbox(text, true);
  },

  _addRectCallback: function (e) {
    e.preventDefault();

    const rect = new fabric.Rect({
      id: this._generateUniqueID(),
      left: 100,
      top: 100,
      // borderColor: 'black',
      stroke: 'black',
      strokeWidth: 5,
      fill: null,
      width: 50,
      height: 50,
      noScaleCache: false,
      strokeUniform: true,
    });

    this.canvas.add(rect);
  },

  _addCustomFieldCallback: function (e) {
    e.preventDefault();

    const value = this.el.querySelector('.zld-add-custom-field select').value;

    if (!value) {
      alert(_t('Please select a field to add'));
      return;
    }

    this._addTextbox(`%%${value}%%`, true);
  },

  _addTextbox: function (text, editable) {
    const textbox = new fabric.Textbox(text, {
      id: this._generateUniqueID(),
      left: 50,
      top: 50,
      fontSize: 20,
      fontFamily: FONTS[0],
      padding: 2,
      editable: editable,
      snapAngle: 90,
      snapThreshold: 45,
      objectCaching: false,
      showTextBoxBorder: true,
      textboxBorderColor: '#dddddd',
    });

    this.canvas.add(textbox);
  },

  _generateUniqueID: () => {
    return (new Date()).getTime();
  },

  _loadControls: function () {
    // This variable used to add additional space between groups of controls
    let lastGroup = null;
    let offsetX = 0;

    TEXT_CONTROLS.forEach((control, i) => {
      // Add additional offset if group had changed
      const additionalOffsetX = (!lastGroup || lastGroup === control.group) ? 0 : CONTROL_CORNER_SIZE;
      offsetX += additionalOffsetX;
      lastGroup = control.group;

      const props = {
        x: -0.5,
        y: -0.5,
        offsetX: offsetX,
        offsetY: -(CONTROL_CORNER_SIZE / 2 + 6),
        cursorStyle: 'pointer',
        cornerSize: CONTROL_CORNER_SIZE,
        render: this._renderControlIcon(control),
        mouseUpHandler: this._getMouseUpHandler(control),
      };

      fabric.Textbox.prototype.controls[`${control.name}Control`] = new fabric.Control(props);

      // Update offset for the next control
      offsetX += CONTROL_CORNER_SIZE + 4
    });

    lastGroup = null;
    offsetX = 0;

    RECT_CONTROLS.forEach((control, i) => {
      const additionalOffsetX = (!lastGroup || lastGroup === control.group) ? 0 : CONTROL_CORNER_SIZE;
      offsetX += additionalOffsetX;
      lastGroup = control.group;

      const props = {
        x: -0.5,
        y: -0.5,
        offsetX: offsetX,
        offsetY: -(CONTROL_CORNER_SIZE / 2 + 6),
        cursorStyle: 'pointer',
        cornerSize: CONTROL_CORNER_SIZE,
        render: this._renderControlIcon(control),
        mouseUpHandler: this._getMouseUpHandler(control),
      };

      fabric.Rect.prototype.controls[`${control.name}Control`] = new fabric.Control(props);

      // Update offset for the next control
      offsetX += CONTROL_CORNER_SIZE + 4
    });
  },

  _loadControlIcons: function () {
    /*
    * Load control icons. We load them once to avoid unnecessary requests
    */
    const controls = [].concat(TEXT_CONTROLS, RECT_CONTROLS);
    controls.forEach((control, i) => {
      const controlIcon = document.createElement('img');
      controlIcon.src = control.image;

      const controlIconInactive = document.createElement('img');
      controlIconInactive.src = control.imageInactive;

      this.controlIcons[control.name] = {
        active: controlIcon,
        inactive: controlIconInactive,
      };
    });
  },

  _renderControlIcon: function (control) {
    return (ctx, left, top, styleOverride, fabricObject) => {
      /*
      General method to load icon for any control
      */
      ctx.save();
      ctx.translate(left, top);
      ctx.rotate(fabric.util.degreesToRadians(fabricObject.angle));

      const state = control.isActive(fabricObject) ? 'active' : 'inactive';
      const icon = this.controlIcons[control.name][state];

      ctx.drawImage(
        icon,
        -CONTROL_CORNER_SIZE / 2, -CONTROL_CORNER_SIZE / 2,
        CONTROL_CORNER_SIZE, CONTROL_CORNER_SIZE);

      ctx.restore();
    }
  },

  _getMouseUpHandler: function (control) {
    return (eventData, transform) => {
      const target = transform.target;
      const canvas = target.canvas;

      if (control.toggle || control.isActive(target)) {
        control.mouseUpHandlerCallback(target, canvas);
        canvas.requestRenderAll();
      }
    };
  }
});

fieldRegistry.add('zld_label_editor', LabelEditorField);
