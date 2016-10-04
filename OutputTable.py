#!python3

"""
OutputTable is a template class for the output of the aus-senate-audit

"""

from flask_table import Table, Col


class OutputTable(Table):
    sample_size = Col('Sample Size')
    audit_stage = Col('Audit Stage')
    id = Col('ID')


class AuditTable(Table):
    sample_size = Col('Sample Size')
    audit_stage = Col('Audit Stage')
    id = Col('ID')


class SamplerTable(Table):
    sample_size = Col('Sample Size')
    audit_stage = Col('Audit Stage')
    id = Col('ID')