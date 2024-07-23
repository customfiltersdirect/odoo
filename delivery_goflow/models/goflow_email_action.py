from odoo import api, models, fields
import traceback

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def update_so_invoice_delivery_cron(self):
        try:
            self.sudo().update_so_invoice_delivery()
            self.send_success_email()
        except Exception as e:
            error_message = traceback.format_exc()
            self.send_error_email(error_message)
            raise

    # without cc email modification

    # def send_success_email(self):
    #     email_to = 'kashif.ali@skyrocket.com.pk'
    #     subject = 'Success Notification'
    #     body_html = """
    #         <p>The scheduled action completed successfully.</p>
    #     """
    #     mail_values = {
    #         'subject': subject,
    #         'body_html': body_html,
    #         'email_to': email_to,
    #         'email_from': self.env.user.email or 'no-reply@example.com',
    #     }
    #     mail = self.env['mail.mail'].create(mail_values)
    #     mail.send()
    #
    # def send_error_email(self, error_message):
    #     email_to = 'kashif.ali@skyrocket.com.pk'
    #     subject = 'Error Notification'
    #     body_html = f"""
    #             <p>An error occurred in the scheduled action:</p>
    #             <pre>{error_message}</pre>
    #         """
    #     mail_values = {
    #         'subject': subject,
    #         'body_html': body_html,
    #         'email_to': email_to,
    #         'email_from': self.env.user.email or 'no-reply@example.com',
    #     }
    #     mail = self.env['mail.mail'].create(mail_values)
    #     mail.send()


    # with cc emails modification
    def send_error_email(self, error_message):
        email_to = 'odooerrors@customfiltersdirect.com'
        email_cc = ['hamza.khattak@skyrocket.com.pk','aadeel@skyrocket.com.pk','kashif.ali@skyrocket.com.pk']  # List of CC email addresses
        subject = 'Error Notification'
        body_html = f"""
            <p>An error occurred in the scheduled action:</p>
            <pre>{error_message}</pre>
        """
        mail_values = {
            'subject': subject,
            'body_html': body_html,
            'email_to': email_to,
            'email_cc': ','.join(email_cc),
            'email_from': self.env.user.email or 'no-reply@example.com',
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    def send_success_email(self):
        email_to = 'odooerrors@customfiltersdirect.com'
        email_cc = ['hamza.khattak@skyrocket.com.pk','aadeel@skyrocket.com.pk','kashif.ali@skyrocket.com.pk']  # List of CC email addresses
        subject = 'Success Notification'
        body_html = """
            <p>The scheduled action completed successfully.</p>
        """
        mail_values = {
            'subject': subject,
            'body_html': body_html,
            'email_to': email_to,
            'email_cc': ','.join(email_cc),
            'email_from': self.env.user.email or 'no-reply@example.com',
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
