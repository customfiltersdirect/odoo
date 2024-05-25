/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

// Messages that might be shown to the user dependening on the state of wkhtmltopdf
const WKHTMLTOPDF_MESSAGES = {
    broken: _t("Your installation of Wkhtmltopdf seems to be broken. The report will be shown in html."),
    install: _t("Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."),
    upgrade: _t(
        "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
        "get a correct display of headers and footers as well as support for " +
        "table-breaking between pages."
    ),
    workers: _t("You need to start Odoo with at least two workers to print a pdf version of the reports."),
};

export {
    WKHTMLTOPDF_MESSAGES,
}