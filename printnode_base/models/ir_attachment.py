from odoo import models, _
from odoo.exceptions import UserError


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    def dpc_print(self):
        """
        Send attachments to printer
        """
        printer = self.env.user.printnode_printer or self.env.company.printnode_printer
        printer_bin = printer.default_printer_bin

        job_ids = []

        if not printer:
            raise UserError(
                _("Default printer is not defined neither on user, nor on company level")
            )

        for attachment in self:
            params = {
                "title": attachment.name,
                "type": "qweb-pdf"
                if attachment.mimetype == "application/pdf"
                else "qweb-text",
                "options": {"bin": printer_bin.name} if printer_bin else {},
            }
            job_id = printer.printnode_print_b64(
                attachment.datas.decode("ascii"), params, check_printer_format=False
            )
            job_ids.append(job_id)

        names = ', '.join([a.name for a in self])
        message = _(
            'Successfully sent %(names)s to printer %(printer)s',
            names=names,
            printer=printer.name
        )

        return message, job_ids

    def remote_dpc_print(self):
        """
        Special method to call from the API
        """
        try:
            message, job_ids = self.dpc_print()
            return {"status": True, "job_ids": job_ids, "message": message}
        except UserError as exc:
            return {"status": False, "job_ids": [], "message": str(exc)}
