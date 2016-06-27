=============================================
Account Invoice Milestone - Manual Milestones
=============================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax, set_tax_code
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account_invoice_milestone::

    >>> Module = Model.get('ir.module')
    >>> module, = Module.find([('name', '=', 'account_invoice_milestone')])
    >>> Module.install([module.id], config.context)
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> currency = get_currency()
    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> account_tax = accounts['tax']
    >>> account_cash = accounts['cash']

Set Cash journal::

    >>> Journal = Model.get('account.journal')
    >>> cash_journal, = Journal.find([('type', '=', 'cash')])
    >>> cash_journal.credit_account = account_cash
    >>> cash_journal.debit_account = account_cash
    >>> cash_journal.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create products::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product.template = template
    >>> product.save()

    >>> consumable = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'consumable'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.consumable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('30')
    >>> template.cost_price = Decimal('10')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> consumable.template = template
    >>> consumable.save()

    >>> advancement = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'Advancment'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.list_price = Decimal('0')
    >>> template.cost_price = Decimal('0')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> advancement.template = template
    >>> advancement.save()


Use advancement product for advancement invoices::

    >>> AccountConfiguration = Model.get('account.configuration')
    >>> Sequence = Model.get('ir.sequence')
    >>> milestone_sequence, = Sequence.find([
    ...     ('code', '=', 'account.invoice.milestone'),
    ...     ], limit=1)
    >>> milestone_group_sequence, = Sequence.find([
    ...     ('code', '=', 'account.invoice.milestone.group'),
    ...     ], limit=1)
    >>> account_config = AccountConfiguration(1)
    >>> account_config.milestone_advancement_product = advancement
    >>> account_config.milestone_sequence = milestone_sequence
    >>> account_config.milestone_group_sequence = milestone_group_sequence
    >>> account_config.save()

Create payment term::

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')
    >>> payment_term = PaymentTerm(name='Direct')
    >>> payment_term_line = PaymentTermLine(type='remainder')
    >>> payment_term.lines.append(payment_term_line)
    >>> payment_term.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory.save()
    >>> inventory_line = inventory.lines.new()
    >>> inventory_line.product=product
    >>> inventory_line.quantity = 200.0
    >>> inventory_line.expected_quantity = 0.0
    >>> inventory.save()
    >>> inventory.click('confirm')
    >>> inventory.state
    u'done'


Create Milestone Group Type::

    >>> MileStoneType = Model.get('account.invoice.milestone.type')
    >>> MileStoneGroupType = Model.get('account.invoice.milestone.group.type')
    >>> group_type = MileStoneGroupType(name='Test')
    >>> fixed_type = group_type.lines.new()
    >>> fixed_type.kind = 'manual'
    >>> fixed_type.invoice_method = 'fixed'
    >>> fixed_type.amount = Decimal('100.0')
    >>> fixed_type.days = 5
    >>> fixed_type.description = 'Advancement'
    >>> fixed_type.currency = currency
    >>> remainder = group_type.lines.new()
    >>> remainder.invoice_method = 'remainder'
    >>> remainder.kind = 'manual'
    >>> remainder.months = 1
    >>> remainder.description = 'Once finished'
    >>> group_type.save()




Manual Amount based Milestones
==============================

One Sale One Amount Milestone - Normal workflow
-----------------------------------------------

Create a Sale with lines with service products and goods products::

    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.milestone_group_type = group_type
    >>> sale.payment_term = payment_term
    >>> consumable_line = sale.lines.new()
    >>> consumable_line.product = consumable
    >>> consumable_line.quantity = 6.0
    >>> consumable_line.amount
    Decimal('180.00')
    >>> goods_line = sale.lines.new()
    >>> goods_line.product = product
    >>> goods_line.quantity = 20.0
    >>> goods_line.amount
    Decimal('200.00')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')

    >>> group = sale.milestone_group
    >>> group.reload()
    >>> reminder, = [x for x in group.milestones if x.invoice_method == 'remainder']
    >>> fixed_milestone, = [x for x in group.milestones if x.invoice_method == 'amount']
    >>> fixed_milestone.invoice_method
    u'amount'
    >>> fixed_milestone.description
    u'Advancement'
    >>> fixed_milestone.amount
    Decimal('100.00')
    >>> fixed_milestone.click('confirm')
    >>> remainder.description
    'Once finished'
    >>> reminder.click('confirm')
    >>> group.reload()
    >>> group.total_amount
    Decimal('380.00')
    >>> group.amount_to_assign
    Decimal('0.00')
    >>> group.assigned_amount
    Decimal('380.00')
    >>> group.invoiced_amount
    Decimal('0.00')
    >>> group.merited_amount
    Decimal('0.00')
    >>> group.state
    'pending'

Create a Invoice for the milestone::

    >>> fixed_milestone.click('do_invoice')
    >>> fixed_milestone.state
    u'processing'
    >>> invoice = fixed_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> invoice_line, = invoice.lines
    >>> invoice_line.description
    u'Advancement'
    >>> group.reload()
    >>> group.invoiced_amount
    Decimal('100.00')
    >>> group.merited_amount
    Decimal('0.00')
    >>> group.state
    'pending'

Test that invoice_amount can not be modified::

    >>> invoice_line, = invoice.lines
    >>> invoice_line.unit_price = Decimal('110.0')
    >>> invoice.save()
    Traceback (most recent call last):
        ...
    UserError: ('UserError', (u'Amount of invoice "1 Customer" must be equal than its milestone "1" amount', ''))
    >>> invoice.reload()

Pay the invoice and check that the milestone is marked as succeeded::

    >>> invoice.click('post')
    >>> pay = Wizard('account.invoice.pay', [invoice])
    >>> pay.form.journal = cash_journal
    >>> pay.execute('choice')
    >>> invoice.reload()
    >>> invoice.state
    u'paid'
    >>> fixed_milestone.reload()
    >>> fixed_milestone.state
    u'succeeded'
