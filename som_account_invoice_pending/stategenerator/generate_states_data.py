#!/usr/bin/env python
# -*- encoding: utf8 -*-


from yamlns import namespace as ns
from io import open

"""
select state.id, state.weight, state.name, state.pending_days, state.pending_days_type, semid.module, semid.name
from account_invoice_pending_state as state
left join ir_model_data as semid
on semid.res_id=state.id
and semid.model='account.invoice.pending.state'
order by id;
"""  # noqa: E501
with open("states.tsv", encoding="utf8") as tsv:
    lines = tsv.readlines()
    header = lines[0].split("\t")
    content = lines[1:]
    states = [
        ns((k.strip(), v.strip()) for k, v in zip(header, line.split("\t")))
        for line in sorted(content)
    ]

ns(data=states).dump("states.yaml")

defaultProcessModule = "account_invoice_pending"
defaultProcess = "default_pending_state_process"
defaultProcessFull = "{}.{}".format(defaultProcessModule, defaultProcess)

bonoSocialProcessModule = "giscedata_facturacio_comer_bono_social"
bonoSocialProcess = "bono_social_pending_state_process"
bonoSocialProcessFull = "{}.{}".format(bonoSocialProcessModule, bonoSocialProcess)

pendingDaysTypeTemplate = u"""\
            <field name="pending_days_type">{}</field>
"""

fragment = u"""\
        <record model="account.invoice.pending.state" id="{module}.{id}">
            <field name="name">{name}</field>
            <field name="weight">{weight}</field>
            <field name="pending_days">{pending_days}</field>
            <field name="process_id" ref="{process_sem_id}"/>
{pendingDaysTypeLine}\
        </record>
"""

xmlheader = u"""\
<?xml version="1.0" encoding="UTF-8" ?>
<openerp>
    <data noupdate="1">
        <!-- SomEnergia specific pending states -->
"""
xmlfooter = u"""\
    </data>
</openerp>
"""


with open("states.xml", "w", encoding="utf8") as xml:
    xml.write(xmlheader)
    for state in states:
        if state.module != "som_account_invoice_pending":
            continue
        process = defaultProcessFull
        if state.process_id == "Bo Social":
            process = bonoSocialProcessFull
        xml.write(
            fragment.format(
                process_sem_id=process,
                pendingDaysTypeLine=pendingDaysTypeTemplate.format(state.pending_days_type)
                if state.pending_days_type
                else "",
                **state
            )
        )
    xml.write(xmlfooter)
