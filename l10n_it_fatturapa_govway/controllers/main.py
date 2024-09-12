import logging

from odoo.http import Controller, request, route

_logger = logging.getLogger()


class FatturaPAGovWay(Controller):
    # incoming invoices
    @route(["/fatturapa/govway/ricevi_fattura"], type="http", auth="user", website=True)
    def ricevi_fattura(self, *args, **post):
        # headers
        # - GovWay-SDI-FormatoArchivioBase64
        # - GovWay-SDI-FormatoArchivioInvioFattura
        # - GovWay-SDI-FormatoFatturaPA
        # - GovWay-SDI-IdentificativoSdI
        # - GovWay-SDI-MessageId
        # - GovWay-SDI-NomeFile
        # - GovWay-SDI-NomeFileMetadati
        # - GovWay-Transaction-ID
        identificativo_sdi = request.httprequest.headers.get(
            "GovWay-SDI-IdentificativoSdI", ""
        )
        sdi_nomefile = request.httprequest.headers.get("GovWay-SDI-NomeFile", "")
        transaction_id = request.httprequest.headers.get("GovWay-Transaction-ID", "")

        request.httprequest.headers.get("GovWay-SDI-FormatoArchivioBase64", "")
        request.httprequest.headers.get("GovWay-SDI-FormatoArchivioInvioFattura", "")
        request.httprequest.headers.get("GovWay-SDI-FormatoFatturaPA", "")
        request.httprequest.headers.get("GovWay-SDI-MessageId", "")
        request.httprequest.headers.get("GovWay-SDI-NomeFileMetadati", "")

        _logger.info(
            "ricevi_fattura(): {} {} {}".format(
                identificativo_sdi, sdi_nomefile, transaction_id
            )
        )
        _logger.debug("ricevi_fattura(): args={}".format(repr(args)))
        _logger.debug("ricevi_fattura(): post={}".format(repr(post)))

    @route(["/fatturapa/govway/ricevi_ndt"], type="http", auth="user", website=True)
    def ricevi_ndt(self, *args, **post):
        # headers
        # - GovWay-SDI-IdentificativoSdI
        # - GovWay-SDI-NomeFile
        # - GovWay-Transaction-ID
        identificativo_sdi = request.httprequest.headers.get(
            "GovWay-SDI-IdentificativoSdI", ""
        )
        sdi_nomefile = request.httprequest.headers.get("GovWay-SDI-NomeFile", "")
        transaction_id = request.httprequest.headers.get("GovWay-Transaction-ID", "")

        _logger.info(
            "ricevi_ndt(): {} {} {}".format(
                identificativo_sdi, sdi_nomefile, transaction_id
            )
        )
        _logger.debug("ricevi_ndt(): args={}".format(repr(args)))
        _logger.debug("ricevi_ndt(): post={}".format(repr(post)))

    # outgoing invoices
    @route(
        ["/fatturapa/govway/ricevi_notifica"],
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
    )
    def ricevi_notifica(self, *args, **post):
        # headers:
        # - GovWay-SDI-IdentificativoSdI
        # - GovWay-SDI-NomeFile
        # - GovWay-Transaction-ID
        identificativo_sdi = request.httprequest.headers.get(
            "GovWay-SDI-IdentificativoSdI", ""
        )
        sdi_nomefile = request.httprequest.headers.get("GovWay-SDI-NomeFile", "")
        transaction_id = request.httprequest.headers.get("GovWay-Transaction-ID", "")

        _logger.info(
            "ricevi_notifica(): {} {} {}".format(
                identificativo_sdi, sdi_nomefile, transaction_id
            )
        )
        _logger.debug("ricevi_notifica(): args={}".format(repr(args)))
        _logger.debug("ricevi_notifica(): post={}".format(repr(post)))
        # request.env["sdi.channel"].sdi_channel_model.receive_notification(
        # { sdi_nomefile: post })
