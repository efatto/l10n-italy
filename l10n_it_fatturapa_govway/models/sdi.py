import base64
from urllib.parse import urljoin

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError


class SdiChannel(models.Model):
    _inherit = "sdi.channel"

    channel_type = fields.Selection(
        selection_add=[("govway", "GovWay")], ondelete={"govway": "cascade"}
    )
    govway_url = fields.Char(
        string="GovWay URL",
    )
    govway_user = fields.Char(string="GovWay User")
    govway_password = fields.Char(string="GovWay Password")

    # @api.constrains("fetch_pec_server_id")
    # def check_fetch_pec_server_id(self):
    #     pec_channels = self.filtered(lambda c: c.channel_type == "pec")
    #     for channel in pec_channels:
    #         domain = [
    #             ("fetch_pec_server_id", "=", channel.fetch_pec_server_id.id),
    #             ("id", "in", pec_channels.ids),
    #         ]
    #         elements = self.search(domain)
    #         if len(elements) > 1:
    #             raise exceptions.ValidationError(
    #                 _("The channel %s with pec server %s already exists")
    #                 % (channel.name, channel.fetch_pec_server_id.name)
    #             )
    #
    # @api.constrains("pec_server_id")
    # def check_pec_server_id(self):
    #     pec_channels = self.filtered(lambda c: c.channel_type == "pec")
    #     for channel in pec_channels:
    #         domain = [
    #             ("pec_server_id", "=", channel.pec_server_id.id),
    #             ("id", "in", pec_channels.ids),
    #         ]
    #         elements = self.search(domain)
    #         if len(elements) > 1:
    #             raise exceptions.ValidationError(
    #                 _("The channel %s with pec server %s already exists")
    #                 % (channel.name, channel.pec_server_id.name)
    #             )
    #
    # @api.constrains("email_exchange_system")
    # def check_email_validity(self):
    #     if self.env.context.get("skip_check_email_validity"):
    #         return
    #     pec_channels = self.filtered(lambda c: c.channel_type == "pec")
    #     for channel in pec_channels:
    #         if not extract_rfc2822_addresses(channel.email_exchange_system):
    #             raise exceptions.ValidationError(
    #                 _("Email %s is not valid") % channel.email_exchange_system
    #             )

    def send_via_govway(self, attachment_out_ids):
        if not self.govway_url:
            raise UserError(_("Missing GovWay URL"))
        for att in attachment_out_ids:
            if not att.datas or not att.name:
                raise UserError(_("File content and file name are mandatory"))
            company = att.company_id
            vat = company.vat.split("IT")[1]
            url = (
                "govway/sdi/out/xml2soap/Pretecno"
                "/CentroServiziFatturaPA/SdIRiceviFile/v1"
            )
            url = urljoin(self.govway_url, url)
            params = {
                "Versione": "FPR12",  # VersioneFatturaPA
                "TipoFile": "XML",  # P7M: application/pkcs7-mime
                "IdPaese": "IT",
                "IdCodice": vat,
                "NomeFile": att.name,
            }
            try:
                response = requests.post(
                    url=url,
                    data=base64.b64decode(att.datas),
                    params=params,
                    timeout=60,
                    auth=(self.govway_user, self.govway_password),
                    headers={"Content-Type": "application/octet-stream"},
                )
                if not response.ok:
                    raise Exception(
                        _(
                            "Failed to send to GovWay instance with error code: "
                            "%s and error message: %s"
                        )
                        % (response.status_code, response.text)
                    )
            except Exception as e:
                raise UserError(
                    _("GovWay server not available for %s. Please configure it.")
                    % str(e)
                )
            att.state = "sent"
            att.sending_date = fields.Datetime.now()
            att.sending_user = self.env.user.id
            msg = _(
                "XML file for FatturaPA %s sent to Exchange System to "
                "the GovWay system %s."
            ) % (att.name, self.govway_url)
            att.message_post(body=msg)

        return {"result": "ok"}
