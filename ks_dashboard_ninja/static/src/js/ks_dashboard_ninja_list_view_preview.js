/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import field_utils from 'web.field_utils';
import { qweb } from 'web.core';

const { useEffect, useRef, xml, onWillUpdateProps} = owl;


class KsListViewPreview extends CharField {
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
//        onWillUpdateProps()
        onWillUpdateProps(this.onWillUpdateProps);

//        useState(
//            (input) => {
//                if (!input) {
//                    self._Ks_render(input);
//                }
//            },
//            () => [inputRef.el]
//        );

    }
    onWillUpdateProps(){
        this._Ks_render()
    }



    _Ks_render() {
        const self = this;
//        $(this.input.el.parentElement).empty()
        $(this.input.el.parentElement).find('div').remove()
        $(this.input.el.parentElement).find('input').addClass('d-none')
        var rec = self.props.record.data;
        if (rec.ks_dashboard_item_type === 'ks_list_view') {
            if (rec.ks_model_id) {
                if (rec.ks_list_view_type == "ungrouped") {
                    if (rec.ks_list_view_fields.count !== 0) {
                        self.ksRenderListView();
                    } else {
                        $(self.input.el.parentElement).append($('<div>').text("Select Fields to show in list view."));
                    }
                } else if (rec.ks_list_view_type == "grouped") {
                    if (rec.ks_list_view_group_fields.count !== 0 && rec.ks_chart_relation_groupby) {
                        if (rec.ks_chart_groupby_type === 'relational_type' || rec.ks_chart_groupby_type === 'selection' || rec.ks_chart_groupby_type === 'other' || rec.ks_chart_groupby_type === 'date_type' && rec.ks_chart_date_groupby) {
                            self.ksRenderListView();
                        } else {
                            $(self.input.el.parentElement).append($('<div>').text("Select Group by Date to show list data."));
                        }

                    } else {
                        $(self.input.el.parentElement).append($('<div>').text("Select Fields and Group By to show in list view."));

                    }
                }
            }else {
                $(self.input.el.parentElement).append($('<div>').text("Select a Model first."));
            }
        }
    }

    ksRenderListView() {
        var self = this;
        var field = self.props.record.data;
        var ks_list_view_name;
        var list_view_data = JSON.parse(field.ks_list_view_data);
        var count = field.ks_record_count;
        if (field.name) ks_list_view_name = field.name;
        else if (field.ks_model_name) ks_list_view_name = field.ks_model_id[1];
        else ks_list_view_name = "Name";
        if (field.ks_list_view_type === "ungrouped" && list_view_data) {
            var index_data = list_view_data.date_index;
            if (index_data){
                for (var i = 0; i < index_data.length; i++) {
                    for (var j = 0; j < list_view_data.data_rows.length; j++) {
                        var index = index_data[i]
                        var date = list_view_data.data_rows[j]["data"][index]
                        if (date){
                         if( list_view_data.fields_type[index] === 'date'){
                                list_view_data.data_rows[j]["data"][index] = moment(new Date(date)).format(this.date_format) , {}, {timezone: false};
                         } else{
                            list_view_data.data_rows[j]["data"][index] = field_utils.format.datetime(moment(moment(date).utc(true)._d), {}, {
                            timezone: false
                        });
                        }

                        }else {list_view_data.data_rows[j]["data"][index] = "";}
                    }
                }
            }
        }

        if (field.ks_list_view_data) {
            var data_rows = list_view_data.data_rows;
            if (data_rows){
                for (var i = 0; i < list_view_data.data_rows.length; i++) {
                for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++) {
                    if (typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]) {
                        if (typeof(list_view_data.data_rows[i].data[j]) === "number") {
                            list_view_data.data_rows[i].data[j] = field_utils.format.float(list_view_data.data_rows[i].data[j], Float64Array, {digits: [0, field.ks_precision_digits]})
                        }
                    } else {
                        list_view_data.data_rows[i].data[j] = "";
                    }
                }
            }
            }
        } else list_view_data = false;
        count = list_view_data && field.ks_list_view_type === "ungrouped" ? count - list_view_data.data_rows.length : false;
        count = count ? count <=0 ? false : count : false;
        var $listViewContainer = $(qweb.render('ks_list_view_container', {
            ks_list_view_name: ks_list_view_name,
            list_view_data: list_view_data,
            count: count,
            layout: field.ks_list_view_layout,
        }));
        if (!field.ks_show_records === true) {
            $listViewContainer.find('#ks_item_info').hide();
        }
        if (this.input.el !== null)
        {
            $(this.input.el.parentElement).append($listViewContainer);

        }

    }

}

registry.category("fields").add("ks_dashboard_list_view_preview", KsListViewPreview);

return {
        KsListViewPreview: KsListViewPreview,
    }




