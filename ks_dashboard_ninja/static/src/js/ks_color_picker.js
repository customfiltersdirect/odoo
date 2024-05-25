/** @odoo-module **/

import "web.dom_ready";

import { registry } from "@web/core/registry";
import core from 'web.core';
import { qweb } from 'web.core';
import { loadCSS,loadJS } from "@web/core/assets";
import { useAutofocus } from "@web/core/utils/hooks"
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component,useState,onWillUpdateProps} = owl;

    //Widget for color picker being used in dashboard item create view.
    //TODO : This color picker functionality can be improved a lot.
export class KsColorPicker extends Component{
        setup(){
        var self=this.props;
         this.state = useState({
           ks_color_value: this.props.value.split(",")[0] || "#376CAE",
           ks_color_opacity:this.props.value.split(",")[1] ||'0.99',
        });
        onWillUpdateProps((nextProps) => {
            this.state.ks_color_value = nextProps.value.split(",")[0] || "#376CAE";
            this.state.ks_color_opacity = nextProps.value.split(",")[1] ||'0.99'
        });

        }

        _ksOnColorChange(ev) {
            var new_value=(ev.currentTarget.value.concat("," + this.props.value.split(',')[1]));
            this.props.update(new_value);

        }
//
        _ksOnOpacityChange(ev) {
            var new_value=(this.props.value.split(',')[0].concat("," + event.currentTarget.value));
            this.props.update(new_value);
        }

        _ksOnOpacityInput(ev) {
            var self = this;
            var color;
            if (this.props.name == "ks_background_color") {
                color = $('.ks_db_item_preview_color_picker').css("background-color")
                $('.ks_db_item_preview_color_picker').css("background-color", self.get_color_opacity_value(color, event.currentTarget.value))

                color = $('.ks_db_item_preview_l2').css("background-color")
                $('.ks_db_item_preview_l2').css("background-color", self.get_color_opacity_value(color, event.currentTarget.value))

            } else if (this.props.name == "ks_default_icon_color") {
                color = $('.ks_dashboard_icon_color_picker > span').css('color')
                $('.ks_dashboard_icon_color_picker > span').css('color', self.get_color_opacity_value(color, event.currentTarget.value))
            } else if (this.props.name == "ks_font_color") {
                color = $('.ks_db_item_preview').css("color")
                color = $('.ks_db_item_preview').css("color", self.get_color_opacity_value(color, event.currentTarget.value))
            }
        }

        get_color_opacity_value(color, val) {
            if (color) {
                return color.replace(color.split(',')[3], val + ")");
            } else {
                return false;
            }
        }


 }
 KsColorPicker.template="ks_color_picker_opacity_view";
 KsColorPicker.props = {
    ...standardFieldProps,
};
 KsColorPicker.supportedTypes = ["char"];
 registry.category("fields").add('ks_dashboard_color_picker_owl', KsColorPicker);
