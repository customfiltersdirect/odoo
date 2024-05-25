/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import field_utils from 'web.field_utils';
import { loadCSS,loadJS } from "@web/core/assets";
import { qweb } from 'web.core';
import core from 'web.core';
import session from 'web.session';

const { useEffect, useRef, xml, onWillUpdateProps, onMounted, onWillStart } = owl;

class KsToDOViewPreview extends CharField {
    setup() {
        super.setup();
        const self = this;
        const inputRef = useRef("input");
        useEffect(
            (input) => {
                if (input) {
                    self._Ks_render();
                }
            },
            () => [inputRef.el]

        );
        onWillUpdateProps(this.onWillUpdateProps);
       document.body.addEventListener('click', function(evt) {
        if ($(evt.target).hasClass("ks_li_tab")) {
        self.ksOnToDoClick(evt);
    }
}, false);

    }

    onWillUpdateProps(){
        this._Ks_render()
    }

    _ks_get_rgba_format(val) {
        var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
        rgba = rgba.map(function(v) {
            return parseInt(v, 16)
        }).join(",");
        return "rgba(" + rgba + "," + val.split(',')[1] + ")";
    }

    _Ks_render() {
        const self = this;
        $(this.input.el.parentElement).find('div').remove()
        $(this.input.el.parentElement).find('input').addClass('d-none')
        var rec = self.props.record.data;
        if (rec.ks_dashboard_item_type === 'ks_to_do') {
            var ks_header_color = self._ks_get_rgba_format(rec.ks_header_bg_color);
            var ks_font_color = self._ks_get_rgba_format(rec.ks_font_color);
            var ks_rgba_button_color = self._ks_get_rgba_format(rec.ks_button_color);
             var list_to_do_data = {}
                   if (rec.ks_to_do_data){
                        list_to_do_data = JSON.parse(rec.ks_to_do_data)
                   }
            var $todoViewContainer = $(qweb.render('ks_to_do_container', {

                ks_to_do_view_name: rec.name ? rec.name : 'Name',
                to_do_view_data: list_to_do_data,
            }));
            $todoViewContainer.find('.ks_card_header').addClass('ks_bg_to_color').css({"background-color": ks_header_color });
            $todoViewContainer.find('.ks_card_header').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
            $todoViewContainer.find('.ks_li_tab').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
            $todoViewContainer.find('.ks_chart_heading').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
            $(this.input.el.parentElement).append($todoViewContainer);
        }
    }
    ksOnToDoClick(ev){
            ev.preventDefault();
            var self= this;
            var tab_id = $(ev.target).attr('href');
            var $tab_section = $('#' + tab_id.substring(1));
            $(ev.target).addClass("active");
            $(ev.target).parent().siblings().each(function(){
                $(this).children().removeClass("active");
            });
            $('#' + tab_id.substring(1)).siblings().each(function(){
                $(this).removeClass("active");
                $(this).addClass("fade");
            });
            $tab_section.removeClass("fade");
            $tab_section.addClass("active");
            $(ev.target).parent().parent().siblings().attr('data-section-id', $(ev.target).data().sectionId);
        }
}

registry.category("fields").add("ks_dashboard_to_do_preview", KsToDOViewPreview);

return {
        KsToDOViewPreview: KsToDOViewPreview,
    }
