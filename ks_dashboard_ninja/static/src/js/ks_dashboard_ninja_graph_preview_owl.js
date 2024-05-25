/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { evaluateExpr } from "@web/core/py_js/py";
import { getNextTabableElement, getPreviousTabableElement } from "@web/core/utils/ui";
import { usePosition } from "@web/core/position_hook";
import { getActiveHotkey } from "@web/core/hotkeys/hotkey_service";
import { shallowEqual } from "@web/core/utils/arrays";
import { _lt } from "@web/core/l10n/translation";
import { AnalyticAutoComplete } from "../autocomplete/autocomplete";

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { TagsList } from "@web/views/fields/many2many_tags/tags_list";
import { useOpenMany2XRecord } from "@web/views/fields/relational_utils";
import { parseFloat as oParseFloat } from "@web/views/fields/parsers";
import { formatPercentage } from "@web/views/fields/formatters";

const { Component, useState, useRef, useExternalListener, onWillUpdateProps, onWillStart, onPatched, onWillRender } = owl;

//const PLAN_APPLICABILITY = {
//    mandatory: _lt("Mandatory"),
//    optional: _lt("Optional"),
//}
//const PLAN_STATUS = {
//    editing: _lt("Editing"),
//    invalid: _lt("Invalid"),
//    ok: _lt("OK"),
//}
export class KsGraphPreview extends Component {
    setup(){
        this.orm = useService("orm");

        this.state = useState({
            showDropdown: false,
            list: {},
        });

        this.widgetRef = useRef("analyticDistribution");
        this.dropdownRef = useRef("analyticDropdown");
        this.mainRef = useRef("mainElement");
        usePosition(() => this.widgetRef.el, {
            popper: "analyticDropdown",
        });

        this.nextId = 1;
        this.focusSelector = false;
        this.activeGroup = false;

        onWillStart(this.willStart);
        onWillRender(this.WillRender);
//        onWillStart(this.WillRender);
    }

    ks_set_default_chart_view() {
            Chart.plugins.register({
                afterDraw: function(chart) {
                    if (chart.data.labels.length === 0) {
                        // No data is present
                        var ctx = chart.chart.ctx;
                        var width = chart.chart.width;
                        var height = chart.chart.height
                        chart.clear();

                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.font = "3rem 'Lucida Grande'";
                        ctx.fillText('No data available', width / 2, height / 2);
                        ctx.restore();
                    }
                }
            });

            Chart.Legend.prototype.afterFit = function() {
                var chart_type = this.chart.config.type;
                if (chart_type === "pie" || chart_type === "doughnut") {
                    this.height = this.height;
                } else {
                    this.height = this.height + 20;
                };
            }
        },

    // Lifecycle
    async willStart() {
//        if (this.editingRecord) {
//            await this.fetchAllPlans(this.props);
//        }
//        await this.formatData(this.props);
        var self = this;
        self.ks_set_default_chart_view();
        core.bus.on("DOM_updated", this, function() {
            if (self.shouldRenderChart && $.find('#ksMyChart').length > 0) self.renderChart();
        });
        Chart.plugins.unregister(ChartDataLabels);
    }

    async WillRender(){
        if (this.props.record.data.ks_dashboard_item_type !== 'ks_tile' && this.props.record.data.ks_dashboard_item_type !== 'ks_kpi' && this.props.record.data.ks_dashboard_item_type !== 'ks_list_view' && this.recordData.ks_dashboard_item_type !== 'ks_to_do') {
            if (this.props.record.data.ks_model_id) {
                if (this.props.record.data.ks_chart_groupby_type == 'date_type' && !this.props.record.data.ks_chart_date_groupby) {
                    return this.$el.append($('<div>').text("Select Group by date to create chart based on date groupby"));
                } else if (tthis.props.record.data.ks_chart_data_count_type === "count" && !this.props.record.data.ks_chart_relation_groupby) {
                    this.$el.append($('<div>').text("Select Group By to create chart view"));
                } else if (this.props.record.data.ks_chart_data_count_type !== "count" && (this.props.record.data.ks_chart_measure_field.count === 0 || !this.props.record.data.ks_chart_relation_groupby)) {
                    this.$el.append($('<div>').text("Select Measure and Group By to create chart view"));
                } else if (!this.props.record.data.ks_chart_data_count_type) {
                    this.$el.append($('<div>').text("Select Chart Data Count Type"));
                } else {
                    this._getChartData();
                }
            } else {
                this.$el.append($('<div>').text("Select a Model first."));
            }

        }
    }

}
KsGraphPreview.template = "analytic.AnalyticDistribution";
KsGraphPreview.supportedTypes = ["char", "text"];
//AnalyticDistribution.components = {
//    AnalyticAutoComplete,
//    TagsList,
//}

//AnalyticDistribution.fieldDependencies = {
//    analytic_precision: { type: 'integer' },
//}
//AnalyticDistribution.props = {
//    ...standardFieldProps,
//    business_domain: { type: String, optional: true },
//    account_field: { type: String, optional: true },
//    product_field: { type: String, optional: true },
//    business_domain_compute: { type: String, optional: true },
//    force_applicability: { type: String, optional: true },
//    allow_save: { type: Boolean },
//}
//AnalyticDistribution.extractProps = ({ field, attrs }) => {
//    return {
//        business_domain: attrs.options.business_domain,
//        account_field: attrs.options.account_field,
//        product_field: attrs.options.product_field,
//        business_domain_compute: attrs.business_domain_compute,
//        force_applicability: attrs.options.force_applicability,
//        allow_save: !Boolean(attrs.options.disable_save),
//    };
//};

registry.category("fields").add("ks_dashboard_graph_preview1", KsGraphPreview);
