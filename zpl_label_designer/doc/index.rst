===================
 ZPL Label Designer
===================


On-premise installation
=======================

1. Our ZPL Label Designer is need to be installed as server wide module. Below is quick summary of what you need to add or modify in your odoo.conf file:

| ``server_wide_modules = base,web,zpl_label_designer``

2. Restart your Odoo server.

odoo.sh installation
====================

.. important::
    Please, try to install and use the module without these instructions. In most cases it will work without any additional steps.

1. For odoo.sh you need to login in your account. There will be multiple options like History, Mails, Shell, Editor. Click on the Shell tab.

.. image:: images/docs-1.png
   :align: center
   :class: w-100
   :alt: Click on Shell button

2. Then you will get a shell access of Odoo.sh. Now you need to add the module in the server wide modules. For that you need to open the odoo.conf file:

3. In order to get your config file you can go through the below path:

| ``/home/odoo/.config/odoo/odoo.conf``

4. Add or change the following line:

| ``server_wide_modules = base,web,zpl_label_designer``

|

.. image:: images/docs-2.png
   :align: center
   :class: w-100
   :alt: Add of modify server_wide_modules

5. Now you need to restart the server. Run the following command in the shell:

| ``odoosh-restart``

Feedback
========

- If you have any feedback, please contact us at support@ventor.tech.
- Don't forget to share your experience! :)

Change Log
==========

|

* 1.3.0 (2023-04-16)
    - [NEW] Added support for many2many and one2many fields

* 1.2.0 (2023-02-23)
    - [NEW] Moved designer to a separate UI: labels.ventor.tech
    - [NEW] Migrated to a new framework (Konva.js)
    - [NEW] Added support for different encodings
    - [NEW] Added possibility to change barcode and QR code size
    - [NEW] Added possibility to change font size
    - Fixed some small issues that were affecting the user experience

* 1.0.0 (2022-12-14)
    - Initial version of module

|
