odoo.define('sale_component_report.sale_component_report', function(require){
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var SaleComponentReport = AbstractAction.extend({
        template: 'SaleComponentReport',
        events: {
			'change #period': 'ApplyPeriod',
			'click #ProductSearch': '_onClickSearch',
			'click #custom-date-filter' : 'ApplyFilter',
			'click #clear' : 'Clear',
			'click #print-pdf': 'PrintPdf'
		},
        init: function(parent, action){
            this._super(parent, action);
        },
        start: function() {
            var date_to = new Date();
            var date_from = new Date();
            var product = 'all'
            date_from.setDate(date_from.getDate() - 365);
            var self = this
            return this._super().then(function(){
                self.LoadData(date_to,date_from,product)
            });
        },
        LoadData:function(date_to,date_from,product){
            rpc.query({
                model: "sale.component.report",
                method: "load_data",
                args: [{
                    'date_to':date_to,
                    'date_from':date_from,
                    'product':product
                }]
                }).then(function(result){
                    self.$('.table_view_tb').html(QWeb.render('SaleComponentTable', {
                        report_lines:result,
                    }));
                })
        },
        ApplyPeriod: function(){
            var type = $('#period :selected').val()
            var dates = this.GetDate(type)
            var string = $('#ProductInput').val()
            if (string === "") {
                string = 'all'
            }
            if (type !='custom'){
                this.LoadData(dates['date_to'],dates['date_from'],string)
            }
        },
        GetDate: function(type){
            console.log("date function called.......")
            var date_to
            var date_from
            if (type == 'none'){
                date_to = new Date();
                date_from = new Date();
                date_from.setDate(date_from.getDate() - 365);
                $('.custom_date_from').attr('style','display: none');
                $('.custom_date_to').attr('style','display: none');
                $('.custom_date_button1').attr('style','display: none');
                $('#ProductSearch').attr('style','display: block');
                $("#ProductInput").removeAttr("style");
            }
            else if(type == 'today'){
                date_to = new Date()
                date_from = new Date()
                $('.custom_date_from').attr('style','display: none');
                $('.custom_date_to').attr('style','display: none');
                $('.custom_date_button1').attr('style','display: none');
                $('#ProductSearch').attr('style','display: block');
                $("#ProductInput").removeAttr("style");
            }
            else if(type == 'week'){
                var today = new Date();
                var dayOfWeek = today.getDay();
                var startDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() - dayOfWeek);
                var endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() - dayOfWeek + 6);
                date_from = startDate.toISOString().slice(0, 10);
                date_to = endDate.toISOString().slice(0, 10);
                $('.custom_date_from').attr('style','display: none');
                $('.custom_date_to').attr('style','display: none');
                $('.custom_date_button1').attr('style','display: none');
                $('#ProductSearch').attr('style','display: block');
                $("#ProductInput").removeAttr("style");
            }
            else if(type == 'month'){
                var date = new Date();
                date_from = new Date(date.getFullYear(), date.getMonth(), 1);
                date_to = new Date(date.getFullYear(), date.getMonth() + 1, 0);
                $('.custom_date_from').attr('style','display: none');
                $('.custom_date_to').attr('style','display: none');
                $('.custom_date_button1').attr('style','display: none');
                $('#ProductSearch').attr('style','display: block');
                $("#ProductInput").removeAttr("style");
            }
            else if(type == 'year'){
                date_from = new Date(new Date().getFullYear(), 0, 1)
                date_to = new Date(new Date().getFullYear(), 11, 31)
                $('.custom_date_from').attr('style','display: none');
                $('.custom_date_to').attr('style','display: none');
                $('.custom_date_button1').attr('style','display: none');
                $('#ProductSearch').attr('style','display: block');
                $("#ProductInput").removeAttr("style");
            }
            else if(type == 'custom'){
                $('#date_from input').val(new Date())
                $('#date_to input').val(new Date())
                $('.custom_date_from').attr('style','display: block');
                $('.custom_date_to').attr('style','display: block');
                $('.custom_date_button1').attr('style','display: block');
                $('#ProductSearch').attr('style','display: none');
                $('#ProductInput').attr('style','margin-left: -40px;width:160%;');
            }
            var dates = {
                'date_to':date_to,
                'date_from':date_from
            }
            return dates
        },
        _onClickSearch: function(){

            var string = $('#ProductInput').val()
            console.log(string)
            var dates = this.GetDate($('#period :selected').val());
            if ($('#period :selected').val() == 'custom'){
                console.log("if")
                var date_from = new Date($('#date_from input').val())
                var date_to = new Date($('#date_to input').val())
                console.log(date_from,date_to)
                this.LoadData(date_to,date_from,string)
            }
            else{
                console.log("else")
                this.LoadData(dates['date_to'],dates['date_from'],string)
            }

        },
        ApplyFilter: function(){
            var date_from = new Date($('#date_from input').val())
            var date_to = new Date($('#date_to input').val())
            var string = $('#ProductInput').val()
            if (string === ""){
                string = 'all'
            }
            this.LoadData(date_to,date_from,string)
        },
        Clear: function(){
            window.location.reload()
        },
        PrintPdf: function(){
            var self = this
            var string = $('#ProductInput').val()
            var date_from
            var date_to
            var dates = this.GetDate($('#period :selected').val());
            if ($('#period :selected').val() == 'custom'){
                date_from = new Date($('#date_from input').val())
                date_to = new Date($('#date_to input').val())
            }
            else{
                date_from = dates['date_from']
                date_to = dates['date_to']
            }
            rpc.query({
                model: "sale.component.report",
                method: "load_data",
                args: [{
                    'date_to':date_to,
                    'date_from':date_from,
                    'product':string
                }]
                }).then(function(result){
                    var action = {
					'type': 'ir.actions.report',
					'report_type': 'qweb-pdf',
					'report_name': 'sale_component_report.report_sale_component_template',
					'report_file': 'sale_component_report.report_sale_component_template',
					'data': {
						'data': result
					},
					'context': {
						'active_model': 'sale.component.report',
						'landscape': 1,
					}
				};
                return self.do_action(action);
                });
        }
    });
    core.action_registry.add("sale_comp_report",SaleComponentReport);
    return SaleComponentReport;
})