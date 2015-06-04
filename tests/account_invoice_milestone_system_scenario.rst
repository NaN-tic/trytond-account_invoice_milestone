=============================================
Account Invoice Milestone - Manual Milestones
=============================================

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
    >>> product, = template.products

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
    >>> consumable, = template.products

    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.list_price = Decimal('50')
    >>> template.cost_price = Decimal('20')
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> service, = template.products

    >>> template = ProductTemplate()
    >>> template.name = 'Advancement'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.list_price = Decimal('0')
    >>> template.cost_price = Decimal('0')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> advancement, = template.products

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
    >>> inventory_line.quantity = 2000.0
    >>> inventory_line.expected_quantity = 0.0
    >>> inventory.save()
    >>> inventory.click('confirm')
    >>> inventory.state
    u'done'


Fixed Amount + Remainder Milestones
===================================

Create Milestone Group Type::

    >>> MileStoneType = Model.get('account.invoice.milestone.type')
    >>> MileStoneGroupType = Model.get('account.invoice.milestone.group.type')
    >>> group_type = MileStoneGroupType(name='Test')
    >>> fixed_type = group_type.lines.new()
    >>> fixed_type.kind = 'system'
    >>> fixed_type.trigger = 'confirmed_sale'
    >>> fixed_type.invoice_method = 'fixed'
    >>> fixed_type.amount = Decimal('100.0')
    >>> fixed_type.currency = currency
    >>> remainder = group_type.lines.new()
    >>> remainder.invoice_method = 'remainder'
    >>> remainder.trigger = 'sent_sale'
    >>> remainder.kind = 'system'
    >>> group_type.save()


One sale invoice order quantities - Normal workflow
----------------------------------------------------

Create a Sale with lines with service products and goods products::

    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'order'
    >>> sale.milestone_group_type = group_type
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
    >>> service_line = sale.lines.new()
    >>> service_line.product = service
    >>> service_line.quantity = 2.0
    >>> service_line.amount
    Decimal('100.00')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> len(sale.invoices)
    0
    >>> group = sale.milestone_group
    >>> group.reload()
    >>> len(group.milestones)
    2
    >>> fixed_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'amount']
    >>> fixed_milestone.state
    u'processing'
    >>> remainder_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'remainder']
    >>> remainder_milestone.state
    u'confirmed'
    >>> fixed_milestone.amount
    Decimal('100.00')
    >>> invoice = fixed_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> group.total_amount
    Decimal('480.00')
    >>> group.merited_amount
    Decimal('100.00')
    >>> group.amount_to_assign
    Decimal('0.00')
    >>> group.assigned_amount
    Decimal('480.00')
    >>> group.invoiced_amount
    Decimal('100.000')

Confirm advancement invoice::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> fixed_milestone.reload()
    >>> fixed_milestone.state
    u'succeeded'

Make shipments serving less quantity than expected::

    >>> shipment, = sale.shipments
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 15
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> len(sale.shipments)
    2
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> shipment.click('cancel')
    >>> sale.reload()
    >>> sale.shipment_state
    u'exception'
    >>> shipment_exception = Wizard('sale.handle.shipment.exception', [sale])
    >>> while shipment_exception.form.recreate_moves:
    ...     _ = shipment_exception.form.recreate_moves.pop()
    >>> shipment_exception.execute('handle')
    >>> sale.reload()
    >>> len(sale.shipments)
    2
    >>> sale.shipment_state
    u'sent'

Check remainder milestone::

    >>> group.reload()
    >>> len(group.milestones)
    2
    >>> remainder_milestone.reload()
    >>> invoice = remainder_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('380.00')

Confirm remainder invoice and check group is completed::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> group.reload()
    >>> group.state
    'completed'

Pay invoices and check group is paid::

    >>> for invoice in [m.invoice for m in group.milestones]:
    ...     pay_invoice = Wizard('account.invoice.pay', [invoice])
    ...     pay_invoice.form.journal = cash_journal
    ...     pay_invoice.form.date = today
    ...     pay_invoice.execute('choice')
    ...     invoice.reload()
    ...     invoice.state
    u'paid'
    u'paid'
    >>> group.reload()
    >>> group.state
    'paid'


One sale invoice shipped quantities - Normal workflow
-----------------------------------------------------

Create a Sale with lines with service products and goods products::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'shipment'
    >>> sale.milestone_group_type = group_type
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
    >>> service_line = sale.lines.new()
    >>> service_line.product = service
    >>> service_line.quantity = 2.0
    >>> service_line.amount
    Decimal('100.00')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> len(sale.invoices)
    0
    >>> group = sale.milestone_group
    >>> group.reload()
    >>> len(group.milestones)
    2
    >>> fixed_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'amount']
    >>> fixed_milestone.state
    u'processing'
    >>> remainder_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'remainder']
    >>> remainder_milestone.state
    u'confirmed'

Confirm advancement invoice::

    >>> invoice = fixed_milestone.invoice
    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> fixed_milestone.reload()
    >>> fixed_milestone.state
    u'succeeded'

Make shipments serving less quantity than expected::

    >>> shipment, = sale.shipments
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 15
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> shipment.click('cancel')
    >>> sale.reload()
    >>> sale.shipment_state
    u'exception'
    >>> shipment_exception = Wizard('sale.handle.shipment.exception', [sale])
    >>> while shipment_exception.form.recreate_moves:
    ...     _ = shipment_exception.form.recreate_moves.pop()
    >>> shipment_exception.execute('handle')
    >>> sale.reload()
    >>> sale.shipment_state
    u'sent'

Check remainder milestone::

    >>> group.reload()
    >>> len(group.milestones)
    2
    >>> remainder_milestone.reload()
    >>> invoice = remainder_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('330.00')

Confirm remainder invoice and check group is completed::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> group.reload()
    >>> group.state
    'completed'

Pay invoices and check group is paid::

    >>> for invoice in [m.invoice for m in group.milestones]:
    ...     pay_invoice = Wizard('account.invoice.pay', [invoice])
    ...     pay_invoice.form.journal = cash_journal
    ...     pay_invoice.form.date = today
    ...     pay_invoice.execute('choice')
    ...     invoice.reload()
    ...     invoice.state
    u'paid'
    u'paid'
    >>> group.reload()
    >>> group.state
    'paid'


Percentage Amount + Shipped Amount and invoice Sale Lines Milestones
====================================================================

Create Milestone Group Type::

    >>> group_type = MileStoneGroupType(name='Test 2')
    >>> percent_type = group_type.lines.new()
    >>> percent_type.kind = 'system'
    >>> percent_type.trigger = 'confirmed_sale'
    >>> percent_type.invoice_method = 'percent_on_total'
    >>> percent_type.percentage = Decimal('0.30')
    >>> shipped_amount_type = group_type.lines.new()
    >>> shipped_amount_type.kind = 'system'
    >>> shipped_amount_type.trigger = 'shipped_amount'
    >>> shipped_amount_type.trigger_shipped_amount = Decimal('0.50')
    >>> shipped_amount_type.invoice_method = 'sale_lines'
    >>> remainder = group_type.lines.new()
    >>> remainder.invoice_method = 'remainder'
    >>> remainder.trigger = 'sent_sale'
    >>> remainder.kind = 'system'
    >>> group_type.save()


One sale invoice order quantities - Normal workflow
----------------------------------------------------

Create a Sale with lines with service products and goods products::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'order'
    >>> sale.milestone_group_type = group_type
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
    >>> service_line = sale.lines.new()
    >>> service_line.product = service
    >>> service_line.quantity = 2.0
    >>> service_line.amount
    Decimal('100.00')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.untaxed_amount
    Decimal('480.00')
    >>> len(sale.invoices)
    0
    >>> group = sale.milestone_group
    >>> group.reload()
    >>> len(group.milestones)
    3
    >>> advancement_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'amount']
    >>> advancement_milestone.state
    u'processing'
    >>> advancement_milestone.amount
    Decimal('144.00')
    >>> sale_lines_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'sale_lines']
    >>> sale_lines_milestone.state
    u'confirmed'
    >>> len(sale_lines_milestone.sale_lines_to_invoice)
    3
    >>> remainder_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'remainder']
    >>> remainder_milestone.state
    u'confirmed'

Confirm advancement invoice::

    >>> invoice = advancement_milestone.invoice
    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> advancement_milestone.reload()
    >>> advancement_milestone.state
    u'succeeded'

Make shipments serving less than 50% of total amount::

    >>> shipment, = sale.shipments
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 10
    ...     else:
    ...         move.quantity = 0
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> group.reload()
    >>> group.merited_amount
    Decimal('200.00')
    >>> group.invoiced_amount
    Decimal('144.000')
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'confirmed'

Make shipments serving more than 50% but less than expected::

    >>> sale.reload()
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 5
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> group.reload()
    >>> group.merited_amount
    Decimal('430.00')
    >>> group.invoiced_amount
    Decimal('480.000')
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'processing'
    >>> invoice = sale_lines_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('336.00')

Confirm sale lines invoice::

    >>> invoice = sale_lines_milestone.invoice
    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'succeeded'

Cancel quantities not delivered and check nothing else invoiced::

    >>> sale.reload()
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> shipment.click('cancel')
    >>> sale.reload()
    >>> sale.shipment_state
    u'exception'
    >>> shipment_exception = Wizard('sale.handle.shipment.exception', [sale])
    >>> while shipment_exception.form.recreate_moves:
    ...     _ = shipment_exception.form.recreate_moves.pop()
    >>> shipment_exception.execute('handle')
    >>> sale.reload()
    >>> sale.shipment_state
    u'sent'
    >>> group.reload()
    >>> len(group.milestones)
    3
    >>> group.state
    'completed'
    >>> remainder_milestone.reload()
    >>> remainder_milestone.state
    u'cancel'

Pay invoices and check group is paid::

    >>> for invoice in [m.invoice for m in group.milestones if m.invoice]:
    ...     pay_invoice = Wizard('account.invoice.pay', [invoice])
    ...     pay_invoice.form.journal = cash_journal
    ...     pay_invoice.form.date = today
    ...     pay_invoice.execute('choice')
    ...     invoice.reload()
    ...     invoice.state
    u'paid'
    u'paid'
    >>> group.reload()
    >>> group.state
    'paid'


One sale invoice shipped quantities - Normal workflow
----------------------------------------------------

Create a Sale with lines with service products and goods products::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'shipment'
    >>> sale.milestone_group_type = group_type
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
    >>> service_line = sale.lines.new()
    >>> service_line.product = service
    >>> service_line.quantity = 2.0
    >>> service_line.amount
    Decimal('100.00')
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.untaxed_amount
    Decimal('480.00')
    >>> len(sale.invoices)
    0
    >>> group = sale.milestone_group
    >>> group.reload()
    >>> len(group.milestones)
    3
    >>> advancement_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'amount']
    >>> advancement_milestone.state
    u'processing'
    >>> advancement_milestone.amount
    Decimal('144.00')
    >>> sale_lines_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'sale_lines']
    >>> sale_lines_milestone.state
    u'confirmed'
    >>> len(sale_lines_milestone.sale_lines_to_invoice)
    3
    >>> remainder_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'remainder']
    >>> remainder_milestone.state
    u'confirmed'

Confirm advancement invoice::

    >>> invoice = advancement_milestone.invoice
    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> advancement_milestone.reload()
    >>> advancement_milestone.state
    u'succeeded'

Make shipments serving more than 50% but less than expected::

    >>> sale.reload()
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 15
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> group.reload()
    >>> group.merited_amount
    Decimal('430.00')
    >>> group.invoiced_amount
    Decimal('430.000')
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'processing'
    >>> invoice = sale_lines_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('286.00')

Confirm sale lines invoice::

    >>> invoice = sale_lines_milestone.invoice
    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'succeeded'

Cancel quantities not delivered and check nothing else invoiced::

    >>> sale.reload()
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> shipment.click('cancel')
    >>> sale.reload()
    >>> sale.shipment_state
    u'exception'
    >>> shipment_exception = Wizard('sale.handle.shipment.exception', [sale])
    >>> while shipment_exception.form.recreate_moves:
    ...     _ = shipment_exception.form.recreate_moves.pop()
    >>> shipment_exception.execute('handle')
    >>> sale.reload()
    >>> sale.shipment_state
    u'sent'
    >>> group.reload()
    >>> len(group.milestones)
    3
    >>> group.state
    'completed'
    >>> remainder_milestone.reload()
    >>> remainder_milestone.state
    u'cancel'

Pay invoices and check group is paid::

    >>> for invoice in [m.invoice for m in group.milestones if m.invoice]:
    ...     pay_invoice = Wizard('account.invoice.pay', [invoice])
    ...     pay_invoice.form.journal = cash_journal
    ...     pay_invoice.form.date = today
    ...     pay_invoice.execute('choice')
    ...     invoice.reload()
    ...     invoice.state
    u'paid'
    u'paid'
    >>> group.reload()
    >>> group.state
    'paid'


Shipped Amount and invoice Sale Lines and Shipped Goods Milestones
==================================================================

Create Milestone Group Type::

    >>> group_type = MileStoneGroupType(name='Test 3')
    >>> sale_lines_type = group_type.lines.new()
    >>> sale_lines_type.kind = 'system'
    >>> sale_lines_type.trigger = 'shipped_amount'
    >>> sale_lines_type.trigger_shipped_amount = Decimal('1.00')
    >>> sale_lines_type.invoice_method = 'sale_lines'
    >>> shipped_goods_type = group_type.lines.new()
    >>> shipped_goods_type.kind = 'system'
    >>> shipped_goods_type.trigger = 'shipped_amount'
    >>> shipped_goods_type.trigger_shipped_amount = Decimal('0.50')
    >>> shipped_goods_type.invoice_method = 'shipped_goods'
    >>> remainder = group_type.lines.new()
    >>> remainder.invoice_method = 'remainder'
    >>> remainder.trigger = 'sent_sale'
    >>> remainder.kind = 'system'
    >>> group_type.save()


One sale invoice order quantities - Normal workflow
----------------------------------------------------

Create a Sale with lines with service products and goods products::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'order'
    >>> sale.milestone_group_type = group_type
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
    >>> service_line = sale.lines.new()
    >>> service_line.product = service
    >>> service_line.quantity = 2.0
    >>> service_line.amount
    Decimal('100.00')
    >>> sale.save()
    >>> sale.untaxed_amount
    Decimal('480.00')

Process sale::

    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> len(sale.invoices)
    0
    >>> group = sale.milestone_group
    >>> group.reload()
    >>> len(group.milestones)
    3
    >>> sale_lines_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'sale_lines']
    >>> sale_lines_milestone.state
    u'confirmed'
    >>> len(sale_lines_milestone.sale_lines_to_invoice)
    3
    >>> shipped_goods_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'shipped_goods']
    >>> shipped_goods_milestone.state
    u'confirmed'
    >>> len(shipped_goods_milestone.sale_lines_to_invoice)
    3
    >>> remainder_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'remainder']
    >>> remainder_milestone.state
    u'confirmed'

Modify milestone group to invoice service lines by line and material lines by
shipped goods::

    >>> sale_lines_milestone.click('cancel')
    >>> sale_lines_milestone.click('draft')
    >>> sale_lines_milestone.reload()
    >>> i = 0
    >>> for trigger_line in sale_lines_milestone.trigger_lines[:]:
    ...     if trigger_line.product != service:
    ...         _ = sale_lines_milestone.trigger_lines.pop(i)
    ...     else:
    ...         i += 1
    >>> i = 0
    >>> for line_to_inv in sale_lines_milestone.sale_lines_to_invoice[:]:
    ...     if line_to_inv.product != service:
    ...         _ = sale_lines_milestone.sale_lines_to_invoice.pop(i)
    ...     else:
    ...         i += 1
    >>> sale_lines_milestone.save()
    >>> len(sale_lines_milestone.trigger_lines)
    1
    >>> len(sale_lines_milestone.sale_lines_to_invoice)
    1
    >>> sale_lines_milestone.click('confirm')
    >>> shipped_goods_milestone.click('cancel')
    >>> shipped_goods_milestone.click('draft')
    >>> shipped_goods_milestone.reload()
    >>> i = 0
    >>> for trigger_line in shipped_goods_milestone.trigger_lines[:]:
    ...     if trigger_line.product == service:
    ...         _ = shipped_goods_milestone.trigger_lines.pop(i)
    ...     else:
    ...         i += 1
    >>> i = 0
    >>> for line_to_inv in shipped_goods_milestone.sale_lines_to_invoice[:]:
    ...     if line_to_inv.product == service:
    ...         _ = shipped_goods_milestone.sale_lines_to_invoice.pop(i)
    ...     else:
    ...         i += 1
    >>> shipped_goods_milestone.save()
    >>> len(shipped_goods_milestone.trigger_lines)
    2
    >>> len(shipped_goods_milestone.sale_lines_to_invoice)
    2
    >>> shipped_goods_milestone.click('confirm')

Execute Check triggers to generate services invoice::

    >>> group.click('check_triggers')
    >>> group.reload()
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'processing'
    >>> invoice = sale_lines_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> sale.reload()
    >>> len(sale.invoices)
    1
    >>> invoice in sale.invoices
    True

Confirm services invoice::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'succeeded'

Make shipments serving 50% but only one line and less than expected::

    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 19
    ...     else:
    ...         move.quantity = 0
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> len(sale.shipments)
    2
    >>> group.reload()
    >>> group.merited_amount
    Decimal('290.00')
    >>> group.invoiced_amount
    Decimal('300.000')
    >>> len(group.milestones)
    4
    >>> shipped_goods_milestone2, = [x for x in group.milestones
    ...     if x.invoice_method == 'shipped_goods' and x.state == 'confirmed']
    >>> len(shipped_goods_milestone2.trigger_lines)
    2
    >>> len(shipped_goods_milestone2.sale_lines_to_invoice)
    1
    >>> shipped_goods_milestone.reload()
    >>> shipped_goods_milestone.state
    u'processing'
    >>> invoice = shipped_goods_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('200.00')
    >>> sale.reload()
    >>> len(sale.invoices)
    2
    >>> invoice in sale.invoices
    True

Confirm shipped sale lines invoice::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> shipped_goods_milestone.reload()
    >>> shipped_goods_milestone.state
    u'succeeded'

Make shipments serving the other sale line but less than expected::

    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 0
    ...     else:
    ...         move.quantity = 5
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> len(sale.shipments)
    3
    >>> group.reload()
    >>> group.merited_amount
    Decimal('440.00')
    >>> group.invoiced_amount
    Decimal('480.000')
    >>> len(group.milestones)
    4
    >>> shipped_goods_milestone2.reload()
    >>> shipped_goods_milestone2.state
    u'processing'
    >>> invoice = shipped_goods_milestone2.invoice
    >>> invoice.untaxed_amount
    Decimal('180.00')
    >>> sale.reload()
    >>> len(sale.invoices)
    3
    >>> invoice in sale.invoices
    True

Confirm shipped sale lines invoice::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> shipped_goods_milestone2.reload()
    >>> shipped_goods_milestone2.state
    u'succeeded'

Cancel quantities not delivered and check nothing else invoiced::

    >>> sale.reload()
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> len(shipment.inventory_moves)
    2
    >>> shipment.click('cancel')
    >>> sale.reload()
    >>> sale.shipment_state
    u'exception'
    >>> shipment_exception = Wizard('sale.handle.shipment.exception', [sale])
    >>> while shipment_exception.form.recreate_moves:
    ...     _ = shipment_exception.form.recreate_moves.pop()
    >>> shipment_exception.execute('handle')
    >>> sale.reload()
    >>> sale.shipment_state
    u'sent'
    >>> group.reload()
    >>> len(group.milestones)
    4
    >>> group.invoiced_amount
    Decimal('480.000')
    >>> group.state
    'completed'
    >>> remainder_milestone.reload()
    >>> remainder_milestone.state
    u'cancel'

Pay invoices and check group is paid::

    >>> for invoice in [m.invoice for m in group.milestones if m.invoice]:
    ...     pay_invoice = Wizard('account.invoice.pay', [invoice])
    ...     pay_invoice.form.journal = cash_journal
    ...     pay_invoice.form.date = today
    ...     pay_invoice.execute('choice')
    ...     invoice.reload()
    ...     invoice.state
    u'paid'
    u'paid'
    u'paid'
    >>> group.reload()
    >>> group.state
    'paid'


One sale invoice shipped quantities - Normal workflow
-----------------------------------------------------

Create a Sale with lines with service products and goods products::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'shipment'
    >>> sale.milestone_group_type = group_type
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
    >>> service_line = sale.lines.new()
    >>> service_line.product = service
    >>> service_line.quantity = 2.0
    >>> service_line.amount
    Decimal('100.00')
    >>> sale.save()
    >>> sale.untaxed_amount
    Decimal('480.00')

Process sale::

    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> len(sale.invoices)
    0
    >>> group = sale.milestone_group
    >>> group.reload()
    >>> len(group.milestones)
    3
    >>> sale_lines_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'sale_lines']
    >>> sale_lines_milestone.state
    u'confirmed'
    >>> len(sale_lines_milestone.sale_lines_to_invoice)
    3
    >>> shipped_goods_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'shipped_goods']
    >>> shipped_goods_milestone.state
    u'confirmed'
    >>> len(shipped_goods_milestone.sale_lines_to_invoice)
    3
    >>> remainder_milestone, = [x for x in group.milestones
    ...     if x.invoice_method == 'remainder']
    >>> remainder_milestone.state
    u'confirmed'

Modify milestone group to invoice service lines by line and material lines by
shipped goods::

    >>> sale_lines_milestone.click('cancel')
    >>> sale_lines_milestone.click('draft')
    >>> sale_lines_milestone.reload()
    >>> i = 0
    >>> for trigger_line in sale_lines_milestone.trigger_lines[:]:
    ...     if trigger_line.product != service:
    ...         _ = sale_lines_milestone.trigger_lines.pop(i)
    ...     else:
    ...         i += 1
    >>> i = 0
    >>> for line_to_inv in sale_lines_milestone.sale_lines_to_invoice[:]:
    ...     if line_to_inv.product != service:
    ...         _ = sale_lines_milestone.sale_lines_to_invoice.pop(i)
    ...     else:
    ...         i += 1
    >>> sale_lines_milestone.save()
    >>> len(sale_lines_milestone.trigger_lines)
    1
    >>> len(sale_lines_milestone.sale_lines_to_invoice)
    1
    >>> sale_lines_milestone.click('confirm')
    >>> shipped_goods_milestone.click('cancel')
    >>> shipped_goods_milestone.click('draft')
    >>> shipped_goods_milestone.reload()
    >>> i = 0
    >>> for trigger_line in shipped_goods_milestone.trigger_lines[:]:
    ...     if trigger_line.product == service:
    ...         _ = shipped_goods_milestone.trigger_lines.pop(i)
    ...     else:
    ...         i += 1
    >>> i = 0
    >>> for line_to_inv in shipped_goods_milestone.sale_lines_to_invoice[:]:
    ...     if line_to_inv.product == service:
    ...         _ = shipped_goods_milestone.sale_lines_to_invoice.pop(i)
    ...     else:
    ...         i += 1
    >>> shipped_goods_milestone.save()
    >>> len(shipped_goods_milestone.trigger_lines)
    2
    >>> len(shipped_goods_milestone.sale_lines_to_invoice)
    2
    >>> shipped_goods_milestone.click('confirm')

Execute Check triggers to generate services invoice::

    >>> group.click('check_triggers')
    >>> group.reload()
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'processing'
    >>> invoice = sale_lines_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> sale.reload()
    >>> len(sale.invoices)
    1
    >>> invoice in sale.invoices
    True

Confirm services invoice::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> sale_lines_milestone.reload()
    >>> sale_lines_milestone.state
    u'succeeded'

Make shipments serving 50% but only one line and less than expected::

    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 19
    ...     else:
    ...         move.quantity = 0
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> len(sale.shipments)
    2
    >>> group.reload()
    >>> group.merited_amount
    Decimal('290.00')
    >>> group.invoiced_amount
    Decimal('290.000')
    >>> len(group.milestones)
    4
    >>> shipped_goods_milestone2, = [x for x in group.milestones
    ...     if x.invoice_method == 'shipped_goods' and x.state == 'confirmed']
    >>> len(shipped_goods_milestone2.trigger_lines)
    2
    >>> len(shipped_goods_milestone2.sale_lines_to_invoice)
    2
    >>> shipped_goods_milestone.reload()
    >>> shipped_goods_milestone.state
    u'processing'
    >>> invoice = shipped_goods_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('190.00')
    >>> sale.reload()
    >>> len(sale.invoices)
    2
    >>> invoice in sale.invoices
    True

Confirm shipped sale lines invoice::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> shipped_goods_milestone.reload()
    >>> shipped_goods_milestone.state
    u'succeeded'

Make shipments serving the other sale line but less than expected::

    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> for move in shipment.inventory_moves:
    ...     if move.product == product:
    ...         move.quantity = 0
    ...     else:
    ...         move.quantity = 5
    >>> shipment.save()
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> len(sale.shipments)
    3
    >>> group.reload()
    >>> group.merited_amount
    Decimal('440.00')
    >>> group.invoiced_amount
    Decimal('440.000')
    >>> len(group.milestones)
    5
    >>> shipped_goods_milestone3, = [x for x in group.milestones
    ...     if x.invoice_method == 'shipped_goods' and x.state == 'confirmed']
    >>> len(shipped_goods_milestone3.trigger_lines)
    2
    >>> len(shipped_goods_milestone3.sale_lines_to_invoice)
    2
    >>> shipped_goods_milestone2.reload()
    >>> shipped_goods_milestone2.state
    u'processing'
    >>> invoice = shipped_goods_milestone2.invoice
    >>> invoice.untaxed_amount
    Decimal('150.00')
    >>> sale.reload()
    >>> len(sale.invoices)
    3
    >>> invoice in sale.invoices
    True

Confirm shipped sale lines invoice::

    >>> invoice.click('post')
    >>> invoice.state
    u'posted'
    >>> shipped_goods_milestone2.reload()
    >>> shipped_goods_milestone2.state
    u'succeeded'

Cancel quantities not delivered and check nothing else invoiced::

    >>> sale.reload()
    >>> shipment, = [s for s in sale.shipments if s.state == 'waiting']
    >>> len(shipment.inventory_moves)
    2
    >>> shipment.click('cancel')
    >>> sale.reload()
    >>> sale.shipment_state
    u'exception'
    >>> shipment_exception = Wizard('sale.handle.shipment.exception', [sale])
    >>> while shipment_exception.form.recreate_moves:
    ...     _ = shipment_exception.form.recreate_moves.pop()
    >>> shipment_exception.execute('handle')
    >>> sale.reload()
    >>> sale.shipment_state
    u'sent'
    >>> group.reload()
    >>> len(group.milestones)
    5
    >>> group.invoiced_amount
    Decimal('440.000')
    >>> group.state
    'completed'
    >>> shipped_goods_milestone3.reload()
    >>> shipped_goods_milestone3.state
    u'cancel'
    >>> remainder_milestone.reload()
    >>> remainder_milestone.state
    u'cancel'

Pay invoices and check group is paid::

    >>> for invoice in [m.invoice for m in group.milestones if m.invoice]:
    ...     pay_invoice = Wizard('account.invoice.pay', [invoice])
    ...     pay_invoice.form.journal = cash_journal
    ...     pay_invoice.form.date = today
    ...     pay_invoice.execute('choice')
    ...     invoice.reload()
    ...     invoice.state
    u'paid'
    u'paid'
    u'paid'
    >>> group.reload()
    >>> group.state
    'paid'

