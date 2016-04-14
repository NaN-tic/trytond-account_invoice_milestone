# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

try:
    from trytond.modules.acconnt_invoice_milestone.tests.test_account_invoice_milestone  import suite
except ImportError:
    from .test_account_invoice_milestone import suite

__all__ = ['suite']
