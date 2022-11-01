/** @odoo-module **/
export class ServerError extends Error {
  constructor(title, message) {
    super(message);

    this.title = title;
  }
};
