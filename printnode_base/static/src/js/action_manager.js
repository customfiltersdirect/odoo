/** @odoo-module */

import { registry } from "@web/core/registry";
import { ErrorDialog } from "@web/core/errors/error_dialogs";
import { session } from '@web/session';
import { csrf_token } from 'web.core';
import { browser } from '@web/core/browser/browser';

import WORKSTATION_DEVICES from './constants';

// Variable to store state of wkhtmltopdf
let wkhtmltopdfState;

function get_WKHTMLTOPDF_MESSAGES(env) {
    const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';

    return {
        broken:
            env._t(
                "Your installation of Wkhtmltopdf seems to be broken. The report will be shown " +
                "in html."
            ) + link,
        install:
            env._t(
                "Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."
            ) + link,
        upgrade:
            env._t(
                "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
                "get a correct display of headers and footers as well as support for " +
                "table-breaking between pages."
            ) + link,
        workers: env._t(
            "You need to start Odoo with at least two workers to print a pdf version of " +
            "the reports."
        ),
    }
}

function _getReportUrl(action, type, env) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};

    if (action.data && JSON.stringify(action.data) !== "{}") {
        // Build a query string with `action.data` (it's the place where reports
        // using a wizard to customize the output traditionally put their options)
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}`;
        }

        if (type === "html") {
            const context = encodeURIComponent(JSON.stringify(env.services.user.context));
            url += `?context=${context}`;
        }
    }

    return url;
}

async function _triggerDownload(action, options, type, env) {
    const url = _getReportUrl(action, type, env);
    const rtype = 'qweb-' + url.split('/')[2];

    env.services.ui.block();

    const workstationDevices = _getWorkstationDevices();
    const payload = JSON.stringify([
        url, rtype,
        action.context.printer_id,
        action.context.printer_bin,
        workstationDevices,
    ]);

    let checkPromise = env.services.http.post(
        "/report/check",
        { csrf_token: csrf_token, data: payload },
    );

    const checkResult = await checkPromise;
    if (checkResult === true) {
        let printPromise = env.services.http.post(
            '/report/print',
            { csrf_token: csrf_token, data: payload },
            "text",
        );
        const printResult = await printPromise;

        env.services.ui.unblock();

        try { // Case of a serialized Odoo Exception: It is Json Parsable
            const printResultJson = JSON.parse(printResult);
            if (printResultJson.success && printResultJson.notify) {
                env.services.notification.add(printResultJson.message, {
                    sticky: false,
                    type: "info",
                });
            } else if (printResultJson.success === false) {
                env.services.dialog.add(ErrorDialog, { traceback: printResultJson.data.debug });
            }
        } catch (e) { // Arbitrary uncaught python side exception
            const doc = new DOMParser().parseFromString(printResult, 'text/html');
            const nodes = doc.body.children.length === 0 ? doc.body.childNodes : doc.body.children;
            let traceback = null;

            try { // Case of a serialized Odoo Exception: It is Json Parsable
                const node = nodes[1] || nodes[0];
                const err = JSON.parse(node.textContent);
                traceback = err.data.debug
            } catch (e) { // Arbitrary uncaught python side exception
                traceback = nodes.length > 1 ? nodes[1].textContent : nodes.length > 0 ? nodes[0].textContent : '';
            }

            env.services.dialog.add(ErrorDialog, { traceback: traceback });
        }

        const onClose = options.onClose;
        if (action.close_on_report_download) {
            return doAction({ type: "ir.actions.act_window_close" }, { onClose });
        } else if (onClose) {
            onClose();
            return print;
        }
    }
}

async function executeAccountReportDownload(action, options, env) {
    let download_only = false;

    if (options.download || (action.context && action.context.download_only)) {
        download_only = true;
    }

    if (action.report_type === "qweb-pdf") {
        // Check for selected printer because even when printnode disabled on user level
        // we want to try to print (of course, if module enabled on company level)
        if (!download_only && (session.printnode_enabled || action.context.printer_id)) {
            // Check the state of wkhtmltopdf before proceeding
            await _checkWkhtmltopdfState(env);

            if (wkhtmltopdfState === "upgrade" || wkhtmltopdfState === "ok") {
                // Trigger the download of the PDF report
                return _triggerDownload(action, options, "pdf", env);
            }
        }
    } else if (action.report_type === "qweb-text") {
        // Check for selected printer because even when printnode disabled on user level
        // we want to try to print (of course, if module enabled on company level)
        if (!download_only && (session.printnode_enabled || action.context.printer_id)) {
            return _triggerDownload(action, options, "text", env);
        }
    }
}

async function _checkWkhtmltopdfState(env) {
    if (!wkhtmltopdfState) {
        let wkhtmltopdfStateProm = env.services.rpc("/report/check_wkhtmltopdf");
        wkhtmltopdfState = await wkhtmltopdfStateProm;
    }

    // Display a notification according to wkhtmltopdf's state
    const WKHTMLTOPDF_MESSAGES = get_WKHTMLTOPDF_MESSAGES(env);
    if (wkhtmltopdfState in WKHTMLTOPDF_MESSAGES) {
        env.services.notification.add(WKHTMLTOPDF_MESSAGES[wkhtmltopdfState], {
            sticky: false,
            title: env._t("Report"),
        });
    }
}

function _getWorkstationDevices() {
    let res = {};

    for (let workstationDevice of WORKSTATION_DEVICES) {
        res[workstationDevice] = browser.localStorage.getItem('printnode_base.' + workstationDevice);
    }

    return res;
}

registry
    .category("ir.actions.report handlers")
    .add('print_or_download_report', executeAccountReportDownload);
