from openupgradelib import openupgrade

_delete_xmlids = ["account.menu_finance"]


@openupgrade.migrate()
def migrate(env, version):

    openupgrade.delete_records_safely_by_xml_id(env, _delete_xmlids)
