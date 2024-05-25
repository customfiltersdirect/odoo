/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import field_utils from 'web.field_utils';
import { loadCSS,loadJS } from "@web/core/assets";
import { qweb } from 'web.core';
import core from 'web.core';
import session from 'web.session';
const { useListener } = require("@web/core/utils/hooks");

const { useEffect, useRef, xml, onWillUpdateProps,onMounted,onWillStart} = owl;


 export class KsImageWidget extends CharField {

    setup() {
        super.setup();
        const self = this;
        this.props.ksSelectedIcon = false
        this.props.ks_icon_set = ['home', 'puzzle-piece', 'clock-o', 'comments-o', 'car', 'calendar', 'calendar-times-o', 'bar-chart', 'commenting-o', 'star-half-o', 'address-book-o', 'tachometer', 'search', 'money', 'line-chart', 'area-chart', 'pie-chart', 'check-square-o', 'users', 'shopping-cart', 'truck', 'user-circle-o', 'user-plus', 'sun-o', 'paper-plane', 'rss', 'gears', 'check', 'book'];
        var ks_self = this.props;
        var url = this.placeholder;
    }

    ks_icon_container_open_button(ev){
        var ks_self = this;
        ks_self.props.update(ks_self.ksSelectedIcon);
        this.modal.hide();
    }
     ks_remove_icon(ev){
        var ks_self = this;
        ks_self.props.update("");
     }

     ks_image_widget_icon_container(ev){
         var self = this;
         this.props.ks_icon_set = ['home', 'puzzle-piece', 'clock-o', 'comments-o', 'car', 'calendar', 'calendar-times-o', 'bar-chart', 'commenting-o', 'star-half-o', 'address-book-o', 'tachometer', 'search', 'money', 'line-chart', 'area-chart', 'pie-chart', 'check-square-o', 'users', 'shopping-cart', 'truck', 'user-circle-o', 'user-plus', 'sun-o', 'paper-plane', 'rss', 'gears', 'check', 'book']
         var $modal=$(qweb.render("ks_icon_container_modal_template",{ ks_fa_icons_set: this.props.ks_icon_set}));
         const modal_new=new Modal($modal[0]);
         this.modal = modal_new;
         for (var i = 0; i < this.modal._element.querySelectorAll('.ks_icon_container_list').length; i++) {
                this.modal._element.querySelectorAll('.ks_icon_container_list')[i].addEventListener('click', this.ks_icon_container_list.bind(this));
            }
         this.modal._element.querySelector('.ks_icon_container_open_button').addEventListener('click',this.ks_icon_container_open_button.bind(this))
         this.modal._element.querySelector('.ks_fa_icon_search').addEventListener('click',this.ks_fa_icon_search.bind(this))
         this.modal._element.querySelector('.ks_modal_icon_input').addEventListener('keyup',this.ks_modal_icon_input_enter.bind(this))
         this.modal._element.querySelector('.ks_close_modal').addEventListener('click',this.ks_close_modal.bind(this))
         modal_new.show();
    }

    ks_icon_container_list(e) {
        var self = this;
        self.ksSelectedIcon = $(e.currentTarget).find('span').attr('id').split('.')[1]
        _.each($('.ks_icon_container_list'), function(selected_icon) {
            $(selected_icon).removeClass('ks_icon_selected');
        });

        $(e.currentTarget).addClass('ks_icon_selected')
        $('.ks_icon_container_open_button').show()
    }

    ks_fa_icon_search(e) {
            var self = this
            if(self.modal._element.querySelectorAll('.ks_fa_search_icon').length > 0){
                self.modal._element.querySelectorAll('.ks_fa_search_icon').forEach(function(el){
                    el.remove();
                })
            }
            var ks_fa_icon_name = self.modal._element.querySelectorAll('.ks_modal_icon_input')[0].value;
            if (ks_fa_icon_name.slice(0, 3) === "fa-") {
                ks_fa_icon_name = ks_fa_icon_name.slice(3)
            }
            var ks_fa_icon_render = $('<div>').addClass('ks_icon_container_list ks_fa_search_icon')
            $('<span>').attr('id', 'ks.' + ks_fa_icon_name.toLocaleLowerCase()).addClass("fa fa-" + ks_fa_icon_name.toLocaleLowerCase() + " fa-4x").appendTo($(ks_fa_icon_render))
            $(ks_fa_icon_render).appendTo(self.modal._element.querySelector('.ks_icon_container_grid_view'))
        }

    ks_modal_icon_input_enter(e) {
            var ks_self = this
            if (e.keyCode == 13) {
                ks_self.modal._element.querySelector('.ks_fa_icon_search').click()
            }
        }

    ks_close_modal(e){
        this.modal.hide();
    }

}

registry.category("fields").add("ks_image_widget",KsImageWidget);
KsImageWidget.template="image_widget";
