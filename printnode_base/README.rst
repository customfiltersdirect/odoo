Odoo Direct Print module
========================


Change Log
##########

|

* 2.6.10 (2024-08-14)
    - Fixed issue with scenario

* 2.6.9 (2024-07-04)
    - [NEW] Added the ability to use Report Rules and User Rules to define the default printer for Print Labels and other printing wizards.

* 2.6.8 (2024-06-04)
    - Fix issue with double printing for UPS Connector
    - Ignoring the printing of attachments that are not shipping labels for the SendCloud Connector

* 2.6.7 (2024-04-03)
    - Fixed issue with "Print Reports" wizard (Odoo 17.0)

* 2.6.6 (2024-03-12)
    - Fixed issue with missed Download button to invoices (Odoo 17.0)

* 2.6.5 (2024-02-16)
    - Fixed issue with QUnit tests (Odoo 17.0)

* 2.6.4 (2024-02-08)
    - Fixed issue with scales integration
    - Added support of debug scales to simplify testing of scales integration

* 2.6.3 (2023-12-13)
    - Fixed issue with put in pack button

* 2.6.2 (2023-10-28)
    - Fix issue with printing reports created with py3o (OCA module)

* 2.6.1 (2023-09-30)
    - Fix issue with missed notification after replenishment

* 2.6.0 (2023-06-08)
    - [NEW] Added new security printing mode: this mode allows to print documents without sending them to Direct Print servers
    - [NEW] Added improved workstation features: user can create multiple workstations and assign printers to them
    - Fixed security issues. Improved and cleaned code of the module
    - Fixed priority of printer selection for shipping labels
    - Fixed issue with error while cancelling tracking number for shipping label

* 2.5.1 (2023-03-20)
    - [NEW] Added new scenario "Print Operations document on Transfer (after validation)" to print reports based on stock.move model

* 2.5.0 (2023-02-27)
    - [NEW] Added "Print Operation Reports" wizard to print reports based on stock.move model
    - [NEW] Added "Print Order Line Reports" wizard to print reports based on sale.order.line model
    - [NEW] Added possibility to set printer for report (through Report Settings)
    - [NEW] Added button to remove old devices (computers / scales / printers)
    - [NEW] Added a new checkbox "Allow to execute printing scenarios from crons" to control scenarios execution from crons
    - Updated workstation feature to store default device in DB to provide reliable performance
    - Improved performance while printing shipping labels
    - Updated status menu to show all levels of default devices (workstation, user and company levels)
    - Fixed issue with shipping label printer selection in multi-company mode
    - Fixed some small issues that were affecting the user experience

* 2.4.0 (2022-11-10)
    - Added an advanced logging feature
    - Improved the logic of the workstation devices feature: devices won't be cleaned on user change
    - Improved the logic of computer/printer status updates in Odoo
    - Fixed issue with broken Print Reports wizard when trying to print reports with quantity > 1
    - Cleaned module code

* 2.3.2 (2022-09-07)
    - Improve compatibility with ZPL Label Designer module
    - Fix issue with printing from wizards (i.e. with "Print & Send" button on Invoice view)

* 2.3.1 (2022-07-20)
    - [NEW] Added new settings: allow to print document without auto-fitting to the page
    - Printing statistics and information about new releases in status menu visible only for managers
    - Fixed issue with new releases in status menu after module upgrade

* 2.3.0 (2022-06-20)
    - [NEW] Added possibility to set number of copies for specific record in Print Report / Print Attachments wizards
    - [NEW] Added new scenarios: Print single / multiple lot label on Transfer (after validation)
    - [NEW] Added possibility to define printer for delivery carriers
    - Fixed issue with duplicated printjobs (under heavy load)
    - Fixed issue with ignored workstation printers when printing through Action menu (Odoo 15)
    - Fixed issues with Odoo JS tests (related to workstation devices feature)
    - After module upgrade print wizards are no longer deleted

* 2.2.0 (2022-05-16)
    - [NEW] Added functionality to mass print lot labels (from list of Lots/Serial Numbers)
    - [NEW] Allow to add new Print Report action to any model (through Configure Print Wizard menu)
    - Display inactive Computers, Printers, Scales in Configuration menu (usability improvement)
    - Improved status menu to update workstation devices dynamically after change in user settings
    - Fixed issue with missed ir.model.data records
    - Fixed issue with missed "name" attribute for scales
    - Fixed printing product labels using scenarios (only in Odoo 15.0)
    - Improved tests coverage (up to 80% of code)

* 2.1.9 (2022-04-04)
    - Added cron to clean print jobs older that 15 days
    - Fixed issue in tests when other modules are running auto-tests
    - Fixed compatibility of workstations devices feature with HR module

* 2.1.8 (2022-02-25)
    - Fixed regression caused by new feature related to workstations printing

* 2.1.7 (2022-02-23)
    - Added possibility to link printers to workstations
    - Replaced print job ID from int to text (to provide compatibility with 64 bits PrintNode IDs)
    - Improved layout of Direct Print Settings page
    - Improved tests to mute catched errors in logs when running tests
    - Improved Print Labels wizard: take printer from "User Rules" (if exists)

* 2.1.6 (2022-01-20)
    - Improved module logic to work with PrintNode subaccounts functionality
    - Added new scenario: Print Package on Put in Pack
    - Fixed issue with connecting multiple scales of the same model to account
    - Fixed issues with printing product labels through Print Labels wizard

* 2.1.5 (2021-12-31)
    - Added possibility to auto-print return labels
    - Added new scenario: Print Document on Picking Status Change
    - Improved scenario "Print Picking Document after Sales Order Confirmation" to print only Ready Picking
    - Added "Printed/Not Printed" filters to supported models
    - Fixed synchronization with DPC/PrintNode: update computer or printer names when they changed
    - Fixed printing multiple ZPL labels: it only printed the first label from all labels
    - Added Rate Us link to status menu

* 2.1.4 (2021-12-01)
    - Fixed issue with access rights for "ir.model" model

* 2.1.3 (2021-11-24)
    - Added standard Odoo icon to all company specific options
    - Fixed error when save settings with empty API Key
    - Added special method to print attachments from the Ventor app
    - Added new demo scenario to print report for all outgoing transfers (after validation)
    - Added auto disable the "Print Package just after Shipping Label" setting with warning if the user disables the "Packages" setting
    - Added notifications about new releases

* 2.1.2 (2021-10-14)
    - Removed redundant report to print Pricelist from Product Label Print wizard
    - Upgraded standard Odoo Print Labels wizard to allow usage of Direct Print functionality
    - Fixed access rights issues appearing for regular user due to more strict access rights Odoo policy

* 2.1.1 (2021-10-04)
    - Added Print Scenario to print Invoice document after it is Validated (Posted)

* 2.1.0 (2021-09-24)
    - Added Scales integration during 'Put In Pack' action on Delivery Order (to send proper weight to Carrier)
    - Improved compatability with Odoo Native Mobile App
    - (Beta) Added Support for py3o (OCA module) generated reports (ONLY PDF)

* 2.0.1 (2021-09-17)
    - Fixed issue with auto-printing of the complex reports (e.g. POS Sales Reports)

* 2.0.0 (2021-09-13)
    - Added support of Direct Print Client platform

* 1.9.4 (2021-09-02)
    - Fixed issue with SO and PO not returning actions on Confirmation

* 1.9.3 (2021-08-23)
    - Added "Print Scenario" to print document after Purchase order confirmation
    - Added "Print Scenario" to print "Receipt Document" after Purchase Order Validation

* 1.9.2 (2021-08-13)
    - Added possibility to exclude particular report from printing in "Print Settings"

* 1.9.1 (2021-07-29)
    - Fixed error in module installation with other modules that are changing user's form view
    - Fixed regression issue with impossibility to quick print product label via wizard
    - Fixed issue with settings not properly working in multi-company environment

* 1.9.0 (2021-07-27)
    - Download Printer Bins Information (Paper Trays).
    - Allow to define Printer Bin (Tray) to be used in all places (Print Actions, Print Scenarios, User Rules)
    - When deleting account - delete all related objects (Computers, Printers, Print Jobs, User Rules, Printer Bins)

* 1.8.1 (2021-07-20)
    - Switching off "Print via Printnode" on user or company also should switch off auto-printing of shipping label on DO Validation

* 1.8.0 (2021-07-14)
    - Added possibility to print Package Document together with the Shipping Label
    - Added Print Scenario to Print all Packages after Transfer Validation

* 1.7.3 (2021-07-13)
    - Fixed issue with auto-test for purchase order flow

* 1.7.2 (2021-07-08)
    - Fixed issue with printing multiple documents using scenarios with the same action

* 1.7.1 (2021-06-30)
    - Fixed issue with automatic Shipping Label printing from attachments via "Print Last Shipping Label" button on Delivery Order
    - Added possibility to enable debug logging on the account to log requests that are sent to PrintNode (needed to communicate with support)

* 1.7 (2021-06-14)
    - When automatic printing is enabled in User Preferences, display near "Print" menu new dropdown "Download" that will allow to Download reports as in Odoo standard

* 1.6.3 (2021-06-08)
    - Method _create_backorder() must return a recordset like the original method does, so that other modules could extend it as well

* 1.6.2 (2021-06-05)
    - Fixed issue with download of printers when there is big amount of printers in Printnode account
    - When deleting account also delete inactive computers and printers

* 1.6.1 (2021-05-31)
    - Fixed issue that makes module incompatible with modules redefining Controller for report download (e.g. report_xlsx)

* 1.6 (2021-04-16)
    - Added possibility to define Universal Print Attachments Wizard for any model in the Odoo
    - (Experimental) Added settings to allow auto-printing of shipping labels from attachments. To support shipping carriers implemented not according to Odoo standards
    - Fixed printing error when sending to PrintNode many documents at the same time

* 1.5.2 (2021-03-26)
    - Added print scenarios to print "Lot labels" or "Product Labels" in real time when receiving items
      It allows either to print single label (to stick on box) OR multiple labels equal to quantity of received items

* 1.5.1 (2021-03-13)
    - Fixed an issue with Report Download controller interruption
    - Fixed an issue with printing document with scenarios for different report model

* 1.5 (2021-02-25)
    - Removed warning with Unit tests when installing module on Odoo.sh
    - Added new scenario: print product labels for validated transfers
    - Added new scenario: print picking document after sale order confirmation

* 1.4.2 (2021-01-13)
    - Added possibility to view the number of prints consumed from the printnode account (experimental)

* 1.4.1 (2021-01-12)
    - Updating the "printed" flag on stock.picking model after Print Scenario execution

* 1.4 (2020-12-21)
    - Added possibility to define number of copies to be printed in "Print Action Button" menu
    - Added Print Scenarios which allows to print reports on pre-programmed actions

* 1.3.1 (2020-11-10)
    - Added constraints not to allow creation of not valid "Print Action Buttons" and "Methods"
    - On product label printing wizard pre-select printer in case only 1 suitable was found

* 1.3 (2020-10-09)
    - Added possibility to print product labels while processing Incoming Shipment into your Warehouse
      Also you can mass print product labels directly from individual product or product list
    - Show info message on User Preferences in case there are User Rules that can redefine Default user Printer
    - Added examples to Print Action menu for some typical use cases for Delivery Order and Sales Order printing

* 1.2.1 (2020-10-07)
    - When direct-printing via Print menu, there is popup message informing user about successful printing
      Now this message can be disabled via Settings
    - Fixed issue with wrong Delivery Slip printing, after backorder creation

* 1.2 (2020-07-28)
    -  Made Printer non-required in "Print action buttons" menu. If not defined, than printer will be selected
       based on user or company printer setting.
    -  Added Support for Odoo Enterprise Barcode Interface. Now it is compatible with "Print action buttons" menu
    -  "Print action buttons" menu now allows to select filter for records, where reports should be auto-printed
       E.g. Print Delivery Slip only for Pickings of Type = Delivery Order

* 1.1 (2020-07-24)
    -  Added Support for automatic/manual printing of Shipping Labels
       Supporting all Odoo Enterprise included Delivery Carries (FedEx, USPS, UPS, bpost and etc.)
       Also Supporting all custom carrier integration modules that are written according to Odoo Standards

* 1.0 (2020-07-20)
    - Initial version providing robust integration of Odoo with PrintNode for automatic printing

|
