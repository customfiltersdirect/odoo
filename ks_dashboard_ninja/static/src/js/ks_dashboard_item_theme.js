/** @odoo-module **/
import "web.dom_ready";

import { registry } from "@web/core/registry";
import core from 'web.core';
import { qweb } from 'web.core';

 const { Component} = owl;

    //Widget for dashboard item theme using while creating dashboard item.
export class KsDashboardThemeowl extends Component {
        setup(){
           var self = this.props;
            }

         ks_dashboard_theme_input_container_click(ev) {
            var self = this.props;
            var $box = $(ev.currentTarget).find(':input');
            if ($box.is(":checked")) {
                $('.ks_dashboard_theme_input').prop('checked', false)
                $box.prop("checked", true);
            } else {
                $box.prop("checked", false);
            }
            this.props.update($box[0].value);
        }
    }
 KsDashboardThemeowl.template="ks_dashboard_theme_view_owl";
KsDashboardThemeowl.supportedTypes = ["char"];
 registry.category("fields").add('ks_dashboard_item_theme_owl', KsDashboardThemeowl);

