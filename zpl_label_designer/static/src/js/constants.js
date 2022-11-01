/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

const MODULE_STATIC_PATH = '/zpl_label_designer/static/src/images';

// Removed 'splitWords'. Need to check if everythings is ok.
const PROPERTIES_TO_SAVE = ['id', 'editable', 'snapAngle', 'isQR', 'isBarcode', , 'aCoords'];
const CONTROL_CORNER_SIZE = 24;
// This is splitters we used to not split the text into lines (because of different fonts)
const WORD_JOINERS = /[]/;

const FONTS = ['Roboto Condensed', 'Roboto Mono'];
const GOOGLE_FONTS = [['Roboto Condensed', { 'weight': 700 }], ['Roboto Mono', {}]];

const TEXT_CONTROLS = [
  {
    name: 'barcode',
    group: 'barcode',
    image: `${MODULE_STATIC_PATH}/upc.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/upc-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      object.set({ isBarcode: !object.isBarcode, isQR: false });
      console.log(object);
    },
    toggle: true,
    isActive: (object) => object.isBarcode,
  },
  {
    name: 'qr',
    group: 'barcode',
    image: `${MODULE_STATIC_PATH}/qr-code.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/qr-code-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      object.set({ isQR: !object.isQR, isBarcode: false });
    },
    toggle: true,
    isActive: (object) => object.isQR,
  },
  {
    name: 'left',
    group: 'text-alignment',
    image: `${MODULE_STATIC_PATH}/text-left.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/text-left-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      object.set({ textAlign: 'left' });
    },
    toggle: true,
    isActive: (object) => object.textAlign === 'left',
  },
  {
    name: 'center',
    group: 'text-alignment',
    image: `${MODULE_STATIC_PATH}/text-center.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/text-center-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      object.set({ textAlign: 'center' });
    },
    toggle: true,
    isActive: (object) => object.textAlign === 'center',
  },
  {
    name: 'right',
    group: 'text-alignment',
    image: `${MODULE_STATIC_PATH}/text-right.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/text-right-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      object.set({ textAlign: 'right' });
    },
    toggle: true,
    isActive: (object) => object.textAlign === 'right',
  },
  {
    name: 'font',
    group: 'font',
    image: `${MODULE_STATIC_PATH}/file-font.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/file-font.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      const currentFont = object.fontFamily;

      // Find next font
      const currentFontIndex = FONTS.indexOf(currentFont);
      const newFontIndex = currentFontIndex < FONTS.length - 1 ? currentFontIndex + 1 : 0;
      const newFont = FONTS[newFontIndex];

      console.log([currentFont, newFont]);

      object.set({ styles: {}, fontFamily: newFont });
    },
    isActive: (object) => true,
  },
];

const RECT_CONTROLS = [
  {
    name: 'fill',
    group: 'fill',
    image: `${MODULE_STATIC_PATH}/square-fill.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/square-fill-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      object.set({ fill: object.fill === null ? 'black' : null });
    },
    toggle: true,
    isActive: (object) => object.fill !== null,
  },
  {
    name: 'increase',
    group: 'stroke-width',
    image: `${MODULE_STATIC_PATH}/plus-square.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/plus-square-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      // Have to mark as dirty to rerender object on canvas
      object.set({
        strokeWidth: ++object.strokeWidth,
        dirty: true
      });
    },
    toggle: false,
    isActive: (object) => {
      const width = object.width * object.scaleX;
      const height = object.height * object.scaleY;

      return width > object.strokeWidth && height > object.strokeWidth;
    },
  },
  {
    name: 'decrease',
    group: 'stroke-width',
    image: `${MODULE_STATIC_PATH}/dash-square.svg`,
    imageInactive: `${MODULE_STATIC_PATH}/dash-square-inactive.svg`,
    mouseUpHandlerCallback: (object, canvas) => {
      // Have to mark as dirty to rerender object on canvas
      object.set({
        strokeWidth: --object.strokeWidth,
        dirty: true
      });
    },
    toggle: false,
    isActive: (object) => object.strokeWidth > 1,
  },
];

const SERVER_DOWN_MESSAGE = _t(`ZPL Converter Server is on maintenance. Try again in a few minutes.
If the issue will not be solved, please, drop us an email at support@ventor.tech`);

export {
  MODULE_STATIC_PATH,
  TEXT_CONTROLS,
  RECT_CONTROLS,
  SERVER_DOWN_MESSAGE,
  PROPERTIES_TO_SAVE,
  CONTROL_CORNER_SIZE,
  WORD_JOINERS,
  FONTS,
  GOOGLE_FONTS,
};
