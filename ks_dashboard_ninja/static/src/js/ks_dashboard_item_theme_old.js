/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import field_utils from 'web.field_utils';
import { qweb } from 'web.core';
import utils from 'web.utils';
import session from 'web.session';

const { useEffect, useRef, xml, onWillUpdateProps,onWillStart} = owl;

class KsDashboardTheme extends CharField {
        setup() {
        super.setup();
        const self = this;
        const inputRef = useRef("input");
        useEffect(
            (input) => {
                if (input) {
                    self.theme_render();
                }
            },
            () => [inputRef.el]

        );
        onWillUpdateProps(this.onWillUpdateProps);
        document.body.addEventListener('click', function(evt) {
            if ($(evt.target).hasClass("ks_dashboard_theme_input")) {
                self.ks_dashboard_theme_input_container_click(evt);
            }
        }, false);
    }

    onWillUpdateProps(){
        this.theme_render()
    }

    theme_render() {
        var self = this;
        $(this.input.el.parentElement).find('div').remove()
        $(this.input.el.parentElement).find('input').addClass('d-none')
        var $view = $(qweb.render('ks_dashboard_theme_view'));
        if (self.props.record.data.ks_dashboard_item_theme) {
            $view.find("input[value='" + self.props.record.data.ks_dashboard_item_theme + "']").prop("checked", true);
        }
        $(this.input.el.parentElement).append($view)
    }

    ks_dashboard_theme_input_container_click(e) {
        var self = this;
        var $box = $(e.target.parentElement).find(':input');
        if ($box.is(":checked")) {
            if ($(this.input.el).parent().length >0) {
                $(this.input.el.parentElement).find('.ks_dashboard_theme_input').prop('checked', false)
            }else{
                $('.ks_dashboard_theme_input').prop('checked', false)
            }
            $box.prop("checked", true);
        } else {
            $box.prop("checked", false);
        }
        this.props.update($box[0].value);
    }
    }

    registry.category("fields").add('ks_dashboard_item_theme_old', KsDashboardTheme);

    return {
        KsDashboardTheme: KsDashboardTheme
    }
