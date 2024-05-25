/** @odoo-module **/
import { registry } from "@web/core/registry";
import core from 'web.core';
import { qweb } from 'web.core';
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import fieldUtils from 'web.field_utils';
import utils from 'web.utils';
import session from 'web.session';



const { Component, onWillUpdateProps, useState, onRendered, useRef } = owl;
//import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";


export class estate extends Component{

        file_type_magic_word = {
            '/': 'jpg',
            'R': 'gif',
            'i': 'png',
            'P': 'svg+xml'
        }

                //        Number Formatter into shorthand function
        ksNumFormatter(num, digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: "k"
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "G"
                },
                {
                    value: 1E12,
                    symbol: "T"
                },
                {
                    value: 1E15,
                    symbol: "P"
                },
                {
                    value: 1E18,
                    symbol: "E"
                }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length-1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if (negative) {
                return "-" + (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            } else {
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }
        }

        ksNumColombianFormatter(num, digits, ks_precision_digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: ""
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "M"
                },
                {
                    value: 1E12,
                    symbol: "M"
                },
                {
                    value: 1E15,
                    symbol: "M"
                },
                {
                    value: 1E18,
                    symbol: "M"
                }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length-1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }

            if (si[i].symbol === 'M'){
//                si[i].value = 1000000;
                num = parseInt(num) / 1000000
                num = fieldUtils.format.integer(num, Float64Array)
                if (negative) {
                    return "-" + num + si[i].symbol;
                } else {
                    return num + si[i].symbol;
                }
                }else{
                    if (num % 1===0){
                    num = fieldUtils.format.integer(num, Float64Array)
                    }else{
                        num = fieldUtils.format.float(num, Float64Array, {digits: [0,ks_precision_digits]});
                    }
                    if (negative) {
                        return "-" + num;
                    } else {
                        return num;
                    }
                }

        }

//        Indian format shorthand function
        ksNumIndianFormatter(num, digits) {
            var negative;
            var si = [{
                value: 1,
                symbol: ""
            },
            {
                value: 1E3,
                symbol: "Th"
            },
            {
                value: 1E5,
                symbol: "Lakh"
            },
            {
                value: 1E7,
                symbol: "Cr"
            },
            {
                value: 1E9,
                symbol: 'Arab'
            }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length-1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if (negative) {
                return "-" + (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            } else {
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }

        }

        ks_get_dark_color(color, opacity, percent) { // deprecated. See below.
            var num = parseInt(color.slice(1), 16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1) + "," + opacity;
        }


        constructor(props, env, node) {
            super(...arguments);
            this.props = props;
            this.env = env;
            this.__owl__ = node;
        }

        _get_rgba_format(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        }

        rgba2hex(value) {
        var actual_color=value.split(",")[0];
        var a= value.split(",")[1];
        var hex = ((a * 255) | 1 << 8).toString(16).slice(1);
        hex = actual_color+hex;
        return hex;
        }

        _onKsGlobalFormatter(ks_record_count, ks_data_format, ks_precision_digits){
            var self = this;
            if (ks_data_format == 'exact'){
//                return ks_record_count;
                return fieldUtils.format.float(ks_record_count, Float64Array, {digits: [0, ks_precision_digits]});
            }else{
                if (ks_data_format == 'indian'){
                    return self.ksNumIndianFormatter( ks_record_count, 1);
                }else if (ks_data_format == 'colombian'){
                    return self.ksNumColombianFormatter( ks_record_count, 1, ks_precision_digits);
                }else{
                    return self.ksNumFormatter(ks_record_count, 1);
                }
            }
        }

        setup(){
            var self = this;
            this.props.record_data = this.props.record.data
            onRendered(this.rendered);
            this.dropdownRef=useRef('analyticDropdown1');
            var ks_rgba_background_color, ks_rgba_font_color, ks_rgba_icon_color;
            if (this.props.record.data.ks_background_color=="#00000,0.99"){
            ks_rgba_background_color="#00000f"
            }else{
            ks_rgba_background_color = self.rgba2hex(this.props.record.data.ks_background_color)
            }
            ks_rgba_font_color = self.rgba2hex(this.props.record.data.ks_font_color)
            ks_rgba_icon_color = self.rgba2hex(this.props.record.data.ks_default_icon_color)
            var name = ''
            var ks_rgba_dark_background_color_l2 = self.rgba2hex(self.ks_get_dark_color(this.props.record.data.ks_background_color.split(',')[0], this.props.record.data.ks_background_color.split(',')[1], -10));
            this.props.count_tooltip = fieldUtils.format.float(this.props.record.data.ks_record_count, Float64Array, {digits: [0, this.props.record.data.ks_precision_digits]})
            if (this.props.record.data.ks_multiplier_active){
                var ks_record_count = this.props.record.data.ks_record_count * this.props.record.data.ks_multiplier
                var record_count = self._onKsGlobalFormatter(ks_record_count, this.props.record.data.ks_data_format, this.props.record.data.ks_precision_digits);
                this.props.count_tooltip = ks_record_count;
            }else{
                var record_count = self._onKsGlobalFormatter(this.props.record.data.ks_record_count, this.props.record.data.ks_data_format, this.props.record.data.ks_precision_digits);
            }
            if (this.props.record.data.ks_icon) {
                if (!utils.is_bin_size(this.props.record.data.ks_icon)) {
                    // Use magic-word technique for detecting image type
                    var img_src = 'data:image/' + (self.file_type_magic_word[this.props.record.data.ks_icon] || 'png') + ';base64,' + this.props.record.data.ks_icon;
                } else {
                    var img_src = session.url('/web/image', {
                        model: self.env.model.root.resModel,
                        id: JSON.stringify(this.props.record.data.id),
                        field: "ks_icon",
                        // unique forces a reload of the image when the record has been updated
                        unique: String(this.props.record.data.__last_update.ts),
                    });
                }

            }
//            if (this.props.record.data.ks_icon_select == 'Custom' && !this.props.record.data.ks_icon){
//                var img_src = ''
//            }

            this.state = useState({
             name: name,
             ks_rgba_background_color: ks_rgba_background_color,
             ks_rgba_font_color:ks_rgba_font_color,
             ks_rgba_icon_color:ks_rgba_icon_color,
             record_count:record_count,
             ks_rgba_dark_background_color_l2:ks_rgba_dark_background_color_l2,
             img_src:img_src,
           });
            onWillUpdateProps((nextProps) => {
            if (this.props.record.data.ks_background_color=="#00000,0.99"){
            this.state.ks_rgba_background_color="#00000f"
            }else{
            this.state.ks_rgba_background_color = self.rgba2hex(this.props.record.data.ks_background_color)
            }
            this.state.ks_rgba_font_color = this.rgba2hex(this.props.record.data.ks_font_color);
            this.state.name = this.props.record.data.name ? this.props.record.data.name : this.props.record.data.ks_model_id[1]
            if (this.props.record.data.ks_multiplier_active){
            this.state.record_count= this._onKsGlobalFormatter((this.props.record.data.ks_record_count*this.props.record.data.ks_multiplier), this.props.record.data.ks_data_format, this.props.record.data.ks_precision_digits)
            }else{
            this.state.record_count= this._onKsGlobalFormatter(this.props.record.data.ks_record_count, this.props.record.data.ks_data_format, this.props.record.data.ks_precision_digits);
            }
           this.state.ks_rgba_icon_color=this.rgba2hex(this.props.record.data.ks_default_icon_color);
           this.state.ks_rgba_dark_background_color_l2=this.rgba2hex(this.ks_get_dark_color(this.props.record.data.ks_background_color.split(',')[0], this.props.record.data.ks_background_color.split(',')[1], -10));
           if (this.props.record.data.ks_icon) {
                if (!utils.is_bin_size(this.props.record.data.ks_icon)) {
                    // Use magic-word technique for detecting image type
                    this.state.img_src = 'data:image/' + (self.file_type_magic_word[this.props.record.data.ks_icon] || 'png') + ';base64,' + this.props.record.data.ks_icon;
                } else {
                    this.state.img_src = session.url('/web/image', {
                        model: self.env.model.root.resModel,
                        id: JSON.stringify(this.props.record.data.id),
                        field: "ks_icon",
                        // unique forces a reload of the image when the record has been updated
                        unique: String(this.props.record.data.__last_update.ts),
                    });
                }

            }
            if (this.props.record.data.ks_icon_select == 'Custom' && !this.props.record.data.ks_icon){
                this.state.img_src = ''
            }
        });


            this.props.icon_color = ks_rgba_icon_color
            this.state.name = this.props.record.data.name ? this.props.record.data.name : this.props.record.data.ks_model_id[1]
//            this.props.record.data.name ? this.props.record.data.name : this.props.record.data.ks_model_id[1]
        }

        WillRender() {
            this.__owl__.render(deep === true);
        }

        rendered(){
        }


  }

Object.assign(estate, {
//    props: { record: Object },
    template: 'web.estate',
});
estate.props = {
    ...standardFieldProps,
};

estate.supportedTypes = ["integer", "float"];
registry.category("fields").add('ks_dashboard_item_preview', estate);