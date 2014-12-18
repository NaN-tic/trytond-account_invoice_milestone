==================================
Account Invoice Milestone Scenario
==================================

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
    >>> fixed_type.kind = 'manual'
    >>> fixed_type.type = 'fixed'
    >>> fixed_type.amount = Decimal('100.0')
    >>> fixed_type.currency = currency
    >>> fixed_type.days = 5
    >>> remainder = group_type.lines.new()
    >>> remainder.months = 1
    >>> group_type.save()
    >>> remainder, = MileStoneType.find([
    ...     ('milestone_group', '=', group_type.id),
    ...     ('type', '=', 'fixed'),
    ...     ], limit=1)

Create Milestone Group with a Milestone of Kind Manual and Amount Type::

    >>> MileStoneGroup = Model.get('account.invoice.milestone.group')
    >>> group = MileStoneGroup(party=customer)
    >>> first_milestone = group.lines.new()
    >>> first_milestone.party == customer
    True
    >>> first_milestone.invoice_method = 'amount'
    >>> first_milestone.type = remainder
    >>> first_milestone.trigger
    u'manual'
    >>> first_milestone.amount = Decimal('100.0')
    >>> group.save()
    >>> group.state
    'to_assign'
    >>> group.amount
    Decimal('0.0')
    >>> group.amount_to_assign
    Decimal('-100.00')
    >>> group.amount_assigned
    Decimal('100.00')

Create Sale and Associate to Milestone Group::

    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.invoice_method = 'milestone'
    >>> sale.milestone_group = group
    >>> sale.party = customer
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
    >>> group.reload()
    >>> milestone, = group.lines
    >>> milestone.click('confirm')
    >>> group.reload()
    >>> group.amount
    Decimal('380.00')
    >>> group.amount_to_assign
    Decimal('280.00')
    >>> group.amount_assigned
    Decimal('100.00')
    >>> group.amount_invoiced
    Decimal('0.0')
    >>> group.amount_invoiced_advancement
    Decimal('0.0')
    >>> group.state
    'pending'

Create a Invoice for the milestone::

    >>> milestone.click('_invoice')
    >>> milestone.state
    u'processing'
    >>> invoice = milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> group.reload()
    >>> group.amount_invoiced
    Decimal('100.00')
    >>> group.amount_invoiced_advancement
    Decimal('0.0')
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
    >>> milestone.reload()
    >>> milestone.state
    u'succeeded'

Process the sale and no invoice created::

    >>> sale.click('process')
    >>> len(sale.invoices)
    0

Create a second milestone based on the shipment of goods::

    >>> consumable_line, goods_line = sale.lines
    >>> second_milestone = group.lines.new()
    >>> second_milestone.invoice_method = 'goods'
    >>> second_milestone.trigger = 'manual'
    >>> second_milestone.moves_to_invoice.append(
    ...     SaleLine(goods_line.moves[0].id))
    >>> group.save()
    >>> group.reload()
    >>> group.amount_to_assign
    Decimal('80.00')
    >>> group.state
    'pending'
    >>> group.amount_assigned
    Decimal('300.00')
    >>> _, second_milestone = group.lines
    >>> second_milestone.click('confirm')

Test it can not be invoiced until the goods are sent::

    >>> second_milestone.click('_invoice')
    Traceback (most recent call last):
        ...
    UserError: ('UserError', (u'Milestone "2" can not be invoiced because its move "20.0u product is not done.', ''))
    >>> shipment, = sale.shipments
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> second_milestone.click('_invoice')
    >>> second_milestone.state
    u'processing'
    >>> invoice = second_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('200.00')
    >>> group.reload()
    >>> group.amount_invoiced
    Decimal('300.00')
    >>> group.amount_invoiced_advancement
    Decimal('0.0')
    >>> len(group.lines)
    2

Create a third milestone to fill the sale::

    >>> third_milestone = group.lines.new()
    >>> third_milestone.invoice_method = 'amount'
    >>> third_milestone.trigger = 'manual'
    >>> third_milestone.amount = Decimal('80.0')
    >>> group.save()
    >>> group.reload()
    >>> group.amount_to_assign
    Decimal('0.00')
    >>> group.state
    'pending'
    >>> group.amount_assigned
    Decimal('380.00')
    >>> group.amount_invoiced
    Decimal('300.00')
    >>> third_milestone.click('confirm')
    >>> third_milestone.click('_invoice')
    >>> invoice = third_milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('80.00')
    >>> group.reload()
    >>> group.amount_invoiced
    Decimal('380.00')
    >>> group.state
    'completed'

When confirming a sale with a group type a new milestone group is created::

    >>> sale = Sale()
    >>> sale.invoice_method = 'milestone'
    >>> sale.milestone_group_type = group_type
    >>> sale.party = customer
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
    >>> sale.milestone_group
    >>> sale.click('confirm')
    >>> group = sale.milestone_group
    >>> first_milestone, second_milestone = group.lines
    >>> first_milestone.trigger
    u'manual'
    >>> first_milestone.amount
    Decimal('100.00')
    >>> second_milestone.trigger
    u'manual'

Create Milestone Group with a fixed amount milestone::

    >>> MileStoneGroup = Model.get('account.invoice.milestone.group')
    >>> group = MileStoneGroup(party=customer)
    >>> first_milestone = group.lines.new()
    >>> first_milestone.party == customer
    True
    >>> first_milestone.invoice_method = 'amount'
    >>> first_milestone.trigger = 'system'
    >>> first_milestone.amount = Decimal('100.0')
    >>> group.save()
    >>> first_milestone, = group.lines

Create a sale and assign it to the group::

    >>> sale = Sale()
    >>> sale.invoice_method = 'milestone'
    >>> sale.milestone_group = group
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> goods_line = sale.lines.new()
    >>> goods_line.product = product
    >>> goods_line.quantity = 30.0
    >>> goods_line.amount
    Decimal('300.00')
    >>> sale.save()
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> first_milestone.trigger_lines.append(SaleLine(sale.lines[0].id))
    >>> first_milestone.save()
    >>> first_milestone.click('confirm')
    >>> first_milestone.state
    u'confirmed'

When the sale is processed a new advancement invoice is created::

    >>> sale.click('process')
    >>> first_milestone.reload()
    >>> first_milestone.state
    u'processing'
    >>> invoice, = sale.advancement_invoices
    >>> invoice.state
    u'draft'
    >>> invoice_line, = invoice.lines
    >>> invoice_line.product == advancement
    True
    >>> invoice_line.quantity
    1.0
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> group.reload()
    >>> group.amount_invoiced_advancement
    Decimal('100.00')

When the goods are sent, the new invoice takes in account the already invoiced
amount::

    >>> shipment, = sale.shipments
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> invoice, = sale.invoices
    >>> invoice.untaxed_amount
    Decimal('200.00')
    >>> compensation_line, product_line = invoice.lines
    >>> compensation_line.product == advancement
    True
    >>> compensation_line.quantity
    -1.0
    >>> compensation_line.amount
    Decimal('-100.00')
    >>> product_line.product == product
    True
    >>> product_line.quantity
    30.0
    >>> product_line.amount
    Decimal('300.00')

Make a partial sale with milestone and close the milestone::

    >>> MileStoneGroup = Model.get('account.invoice.milestone.group')
    >>> Move = Model.get('stock.move')
    >>> group = MileStoneGroup(party=customer)
    >>> first_milestone = group.lines.new()
    >>> first_milestone.invoice_method = 'amount'
    >>> first_milestone.trigger = 'system'
    >>> first_milestone.amount = Decimal('100.0')
    >>> group.save()
    >>> first_milestone, = group.lines
    >>> sale = Sale()
    >>> sale.invoice_method = 'milestone'
    >>> sale.milestone_group = group
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> line = sale.lines.new()
    >>> line.product = consumable
    >>> line.quantity = 2.0
    >>> line.unit_price = Decimal('0.0')
    >>> line = sale.lines.new()
    >>> line.product = product
    >>> line.quantity = 20.0
    >>> sale.save()
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> first_milestone.trigger_lines.append(SaleLine(sale.lines[0].id))
    >>> first_milestone.save()
    >>> first_milestone.click('confirm')
    >>> sale.click('process')
    >>> group.reload()
    >>> group.amount_invoiced
    Decimal('100.00')
    >>> shipment, = sale.shipments
    >>> shipment.click('draft')
    >>> for move in shipment.outgoing_moves:
    ...     if move.product == product:
    ...         move.quantity = 10.0
    >>> shipment.click('wait')
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> sale.invoice_state
    u'waiting'
    >>> invoice, = sale.invoices
    >>> invoice.untaxed_amount
    Decimal('0.00')
    >>> group.reload()
    >>> len(group.lines)
    2
    >>> group.amount_invoiced
    Decimal('100.00')
    >>> group.click('close')
    >>> _, _, new_milestone = group.lines
    >>> new_milestone.invoice_method
    u'goods'
    >>> new_milestone.trigger
    u'system'
    >>> stock_move, = new_milestone.moves_to_invoice
    >>> stock_move.state
    u'draft'
    >>> stock_move.quantity
    10.0

Make a partial sale with milestone and check invoices are correctly linked
to stock moves::

    >>> group = MileStoneGroup(party=customer)
    >>> milestone = group.lines.new()
    >>> milestone.invoice_method = 'amount'
    >>> milestone.trigger = 'system'
    >>> milestone.amount = Decimal('100.0')
    >>> milestone = group.lines.new()
    >>> milestone.invoice_method = 'goods'
    >>> milestone.trigger = 'system'
    >>> group.save()
    >>> first_milestone, second_milestone = group.lines
    >>> sale = Sale()
    >>> sale.invoice_method = 'milestone'
    >>> sale.milestone_group = group
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> line = sale.lines.new()
    >>> line.product = consumable
    >>> line.quantity = 2.0
    >>> line = sale.lines.new()
    >>> line.product = product
    >>> line.quantity = 20.0
    >>> sale.save()
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> first_milestone.trigger_lines.append(SaleLine(sale.lines[0].id))
    >>> first_milestone.save()
    >>> first_milestone.click('confirm')
    >>> sale.click('process')
    >>> invoice, = sale.advancement_invoices
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> group.reload()
    >>> group.amount_invoiced
    Decimal('100.00')
    >>> shipment, = sale.shipments
    >>> shipment.click('draft')
    >>> for move in shipment.outgoing_moves:
    ...     if move.product == product:
    ...         move.quantity = 5.0
    >>> shipment.click('wait')
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> sale.reload()
    >>> sale.invoice_state
    u'waiting'
    >>> invoice, = sale.invoices
    >>> invoice.untaxed_amount
    Decimal('10.00')
    >>> group.reload()
    >>> group.amount_invoiced
    Decimal('110.00')
    >>> group.amount_invoiced_advancement
    Decimal('0.00')
    >>> sorted([m.state for m in group.lines])
    [u'processing', u'processing']
    >>> _, second_milestone = group.lines
    >>> len(second_milestone.moves_to_invoice)
    2
    >>> _, new_shipment = sale.shipments
    >>> new_shipment.click('wait')
    >>> new_shipment.click('assign_try')
    True
    >>> new_shipment.click('pack')
    >>> new_shipment.click('done')
    >>> group.reload()
    >>> group.amount_invoiced
    Decimal('260.00')
    >>> sale.reload()
    >>> _, new_invoice = sale.invoices
    >>> new_invoice.untaxed_amount
    Decimal('150.00')
    >>> _, _, new_milestone = group.lines
    >>> new_milestone.trigger
    u'system'
    >>> new_milestone.invoice_method
    u'goods'
    >>> new_milestone.invoice == new_invoice
    True
    >>> move, = new_milestone.moves_to_invoice
    >>> move.quantity
    15.0
    >>> move.product == product
    True
    >>> move.state
    u'done'

Create a milestone group type with there diferent milestone types::

    >>> group_type = MileStoneGroupType(name='Three milestones')
    >>> milestone_type = group_type.lines.new()
    >>> milestone_type.type = 'fixed'
    >>> milestone_type.kind = 'system'
    >>> milestone_type.trigger = 'accept'
    >>> milestone_type.currency = currency
    >>> milestone_type.days = 2
    >>> milestone_type.amount = Decimal('100.0')
    >>> milestone_type = group_type.lines.new()
    >>> milestone_type.type = 'fixed'
    >>> milestone_type.kind = 'system'
    >>> milestone_type.trigger = 'percentage'
    >>> milestone_type.trigger_shipped_amount = Decimal('50.0')
    >>> milestone_type.currency = currency
    >>> milestone_type.amount = Decimal('200.0')
    >>> milestone_type = group_type.lines.new()
    >>> milestone_type.kind = 'system'
    >>> milestone_type.trigger = 'finish'
    >>> group_type.save()

Create a sale for with the milestone type::

    >>> sale = Sale()
    >>> sale.invoice_method = 'milestone'
    >>> sale.milestone_group_type = group_type
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> goods_line = sale.lines.new()
    >>> goods_line.product = product
    >>> goods_line.quantity = 50.0
    >>> goods_line.amount
    Decimal('500.00')
    >>> sale.click('quote')
    >>> sale_line, = sale.lines

When the sale is confirmed the accept milestone is triggered but not invoiced::

    >>> sale.click('confirm')
    >>> group = sale.milestone_group
    >>> accept, percent, remainder = group.lines
    >>> accept.amount
    Decimal('100.00')
    >>> accept.invoice
    >>> accept_trigger_date = today + relativedelta(days=2)
    >>> accept.trigger_date == accept_trigger_date
    True
    >>> accept.state
    u'confirmed'


Create the accept milestone invoice::

    >>> Milestone = Model.get('account.invoice.milestone')
    >>> accept.click('_invoice')
    >>> accept.invoice
    >>> config._context['trigger_date'] = accept_trigger_date
    >>> accept.reload()
    >>> accept.click('_invoice')
    >>> del config._context['trigger_date']
    >>> invoice = accept.invoice
    >>> invoice.untaxed_amount
    Decimal('100.00')

Process the sale and check group amounts::

    >>> sale.click('process')
    >>> group.reload()
    >>> group.amount
    Decimal('500.00')
    >>> group.amount_assigned
    Decimal('500.00')
    >>> group.amount_to_assign
    Decimal('0.00')
    >>> group.amount_invoiced
    Decimal('100.00')
    >>> group.amount_invoiced_advancement
    Decimal('100.00')

Second line is computed when sending 50% of the goods::

    >>> accept, percent, remainder = group.lines
    >>> percent.trigger_shipped_amount
    Decimal('50.0')
    >>> trigger_line, = percent.trigger_lines
    >>> trigger_line.id == sale_line.id
    True
    >>> percent.state
    u'confirmed'
    >>> shipment, = sale.shipments
    >>> stock_inventory_move, = shipment.inventory_moves
    >>> stock_inventory_move.quantity
    50.0
    >>> stock_inventory_move.quantity = 10.0
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> shipment.state
    u'done'
    >>> percent.reload()
    >>> percent.invoice
    >>> sale.reload()
    >>> _, shipment = sorted(sale.shipments, key=lambda a: int(a.code))
    >>> inventory_move, = shipment.inventory_moves
    >>> inventory_move.quantity
    40.0
    >>> inventory_move.quantity = 15.0
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> shipment.state
    u'done'
    >>> percent.reload()
    >>> percent.state
    u'processing'
    >>> invoice = percent.invoice
    >>> invoice.untaxed_amount
    Decimal('200.00')
    >>> group.reload()
    >>> group.amount
    Decimal('500.00')
    >>> group.amount_assigned
    Decimal('500.00')
    >>> group.amount_to_assign
    Decimal('0.00')
    >>> group.amount_invoiced
    Decimal('300.00')
    >>> group.amount_invoiced_advancement
    Decimal('300.00')

When we finish the shipment the third milestone is computed::

    >>> sale.reload()
    >>> _, _, shipment = sorted(sale.shipments, key=lambda a: int(a.code))
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> shipment.state
    u'done'
    >>> group.reload()
    >>> accept, percent, remainder = group.lines
    >>> invoice = remainder.invoice
    >>> invoice.untaxed_amount
    Decimal('200.00')
    >>> group.amount
    Decimal('500.00')
    >>> group.amount_assigned
    Decimal('500.00')
    >>> group.amount_to_assign
    Decimal('0.00')
    >>> group.amount_invoiced
    Decimal('500.00')
    >>> group.state
    'completed'

Create a sale to return one product::

    >>> return_sale = Sale()
    >>> return_sale.invoice_method = 'milestone'
    >>> return_sale.party = customer
    >>> return_sale.milestone_group = group
    >>> return_sale.payment_term = payment_term
    >>> return_sale_line = return_sale.lines.new()
    >>> return_sale_line.product = product
    >>> return_sale_line.quantity = -1
    >>> return_sale.click('quote')
    >>> return_sale.untaxed_amount
    Decimal('-10.00')
    >>> return_sale.click('confirm')
    >>> return_sale.click('process')

Test it's reflected on milestone group::

    >>> group.reload()
    >>> len(group.sales)
    2
    >>> group.amount_to_assign
    Decimal('-10.00')
    >>> group.amount
    Decimal('490.00')

Create a new milestone to invoice it::

    >>> milestone = group.lines.new()
    >>> milestone.kind = 'manual'
    >>> milestone.invoice_method = 'goods'
    >>> milestone.moves_to_invoice.extend([Move(x.id)
    ...     for x in return_sale.moves])
    >>> group.save()
    >>> _, _, _, milestone = group.lines
    >>> milestone.click('confirm')

Recieve the goods and create a new invoice::

    >>> shipment_return, = return_sale.shipment_returns
    >>> shipment_return.click('receive')
    >>> shipment_return.click('done')
    >>> milestone.reload()
    >>> milestone.click('_invoice')
    >>> invoice = milestone.invoice
    >>> invoice.untaxed_amount
    Decimal('10.00')
    >>> invoice.type
    u'out_credit_note'
    >>> group.reload()
    >>> group.state
    'completed'
