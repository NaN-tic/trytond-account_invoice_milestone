# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .configuration import *
from .milestone import *
from .sale import *
from .invoice import *


def register():
    Pool.register(
        AccountConfiguration,
        AccountConfigurationCompany,
        AccountInvoiceMilestoneGroupType,
        AccountInvoiceMilestoneType,
        AccountInvoiceMilestoneGroup,
        AccountInvoiceMilestone,
        AccountInvoiceMilestoneSaleLine,
        AccountInvoiceMilestoneRemainderSale,
        StockMove,
        SaleConfiguration,
        Sale,
        SaleLine,
        Invoice,
        InvoiceLine,
        InvoiceMilestoneRelation,
        module='account_invoice_milestone', type_='model')
