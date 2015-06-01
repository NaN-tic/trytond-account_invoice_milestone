=============================================
Account Invoice Milestone - Manual Milestones
=============================================

.. Set the Planned Invoice Date in some miletones. It is used as Invoice Date
   without any other consequence
Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account_invoice_milestone::

    >>> Module = Model.get('ir.module.module')
    >>> module, = Module.find([('name', '=', 'account_invoice_milestone')])
    >>> Module.install([module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])



Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name=str(today.year))
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_seq = Sequence(name=str(today.year), code='account.move',
    ...     company=company)
    >>> post_move_seq.save()
    >>> fiscalyear.post_move_sequence = post_move_seq
    >>> invoice_seq = SequenceStrict(name=str(today.year),
    ...     code='account.invoice', company=company)
    >>> invoice_seq.save()
    >>> fiscalyear.out_invoice_sequence = invoice_seq
    >>> fiscalyear.in_invoice_sequence = invoice_seq
    >>> fiscalyear.out_credit_note_sequence = invoice_seq
    >>> fiscalyear.in_credit_note_sequence = invoice_seq
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> Journal = Model.get('account.journal')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> revenue, = Account.find([
    ...         ('kind', '=', 'revenue'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')
    >>> cash, = Account.find([
    ...         ('kind', '=', 'other'),
    ...         ('name', '=', 'Main Cash'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> cash_journal, = Journal.find([('type', '=', 'cash')])
    >>> cash_journal.credit_account = cash
    >>> cash_journal.debit_account = cash
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
    >>> payment_term_line = PaymentTermLine(type='remainder', days=0)
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
    >>> fixed_type.kind = 'system'
    >>> fixed_type.invoice_method = 'fixed'
    >>> fixed_type.trigger = 'confirmed_sale'
    >>> fixed_type.amount = Decimal('100.0')
    >>> fixed_type.currency = currency
    >>> remainder = group_type.lines.new()
    >>> remainder.invoice_method = 'remainder'
    >>> remainder.trigger = 'sent_sale'
    >>> remainder.kind = 'system'
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
    >>> len(sale.invoices)
    0
    >>> group = sale.milestone_group
    >>> group.reload()
    >>> len(group.milestones)
    2
    >>> remainder_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'remainder']
    >>> fixed_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'amount']
    >>> fixed_milestone.amount
    Decimal('100.00')
    >>> invoice = fixed_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> group.total_amount
    Decimal('380.00')
    >>> group.amount_to_assign
    Decimal('0.00')
    >>> group.assigned_amount
    Decimal('380.00')
    >>> group.invoiced_amount
    Decimal('100.000')

Make shipments::

    >>> shipment, = sale.shipments
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')

Check remainder_milestone Milestone::

    >>> group.reload()
    >>> len(group.milestones)
    2
    >>> remainder_milestone.reload()
    >>> invoice = remainder_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('280.00')
