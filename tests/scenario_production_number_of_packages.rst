=============================
Production Number of Packages
=============================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax, set_tax_code
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install production_number_of_packages Module::

    >>> Module = Model.get('ir.module')
    >>> modules = Module.find([('name', '=', 'production_number_of_packages')])
    >>> Module.install([x.id for x in modules], config.context)
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()
    >>> party = company.party

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Configuration production location::

    >>> Location = Model.get('stock.location')
    >>> warehouse, = Location.find([('code', '=', 'WH')])
    >>> production_location, = Location.find([('code', '=', 'PROD')])
    >>> warehouse.production_location = production_location
    >>> warehouse.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal(30)
    >>> template.cost_price = Decimal(20)
    >>> package = template.packagings.new()
    >>> package.name = 'Package 1'
    >>> package.qty = 6
    >>> package.weight = 0.3
    >>> package = template.packagings.new()
    >>> package.name = 'Package 2'
    >>> package.qty = 10
    >>> package.weight = 0.5
    >>> template.save()
    >>> package1 = template.packagings[0]
    >>> package1.qty
    6.0
    >>> template.package_required = True
    >>> template.default_package = package1
    >>> template.save()
    >>> product, = template.products
    >>> product.save()

Create Components::

    >>> component1 = Product()
    >>> template1 = ProductTemplate()
    >>> template1.name = 'component 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal(5)
    >>> template1.cost_price = Decimal(1)
    >>> template1.save()
    >>> component1, = template1.products
    >>> component1.save()

    >>> meter, = ProductUom.find([('name', '=', 'Meter')])
    >>> centimeter, = ProductUom.find([('name', '=', 'centimeter')])
    >>> component2 = Product()
    >>> template2 = ProductTemplate()
    >>> template2.name = 'component 2'
    >>> template2.default_uom = meter
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal(7)
    >>> template2.cost_price = Decimal(5)
    >>> template2.save()
    >>> component2, = template2.products
    >>> component2.save()

Create Bill of Material::

    >>> BOM = Model.get('production.bom')
    >>> BOMInput = Model.get('production.bom.input')
    >>> BOMOutput = Model.get('production.bom.output')
    >>> bom = BOM(name='product')
    >>> input1 = BOMInput()
    >>> bom.inputs.append(input1)
    >>> input1.product = component1
    >>> input1.quantity = 5
    >>> input2 = BOMInput()
    >>> bom.inputs.append(input2)
    >>> input2.product = component2
    >>> input2.quantity = 150
    >>> input2.uom = centimeter
    >>> output = BOMOutput()
    >>> bom.outputs.append(output)
    >>> output.product = product
    >>> output.package == package1
    True
    >>> output.number_of_packages = 1
    >>> output.quantity
    6.0
    >>> bom.save()

    >>> ProductBom = Model.get('product.product-production.bom')
    >>> product.boms.append(ProductBom(bom=bom))
    >>> product.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line1 = InventoryLine()
    >>> inventory.lines.append(inventory_line1)
    >>> inventory_line1.product = component1
    >>> inventory_line1.quantity = 20
    >>> inventory_line2 = InventoryLine()
    >>> inventory.lines.append(inventory_line2)
    >>> inventory_line2.product = component2
    >>> inventory_line2.quantity = 10
    >>> inventory.save()
    >>> Inventory.confirm([inventory.id], config.context)
    >>> inventory.state
    u'done'

Create a production of product::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.product = product
    >>> production.package == package1
    True
    >>> production.bom = bom
    >>> production.number_of_packages = 2
    >>> production.quantity
    12.0
    >>> sorted([i.quantity for i in production.inputs])
    [10.0, 300.0]
    >>> output, = production.outputs
    >>> output.quantity
    12.0
    >>> production.cost
    Decimal('25.0000')
    >>> output.unit_price
    Decimal('2.0833')
    >>> production.save()

Make the production::

    >>> Production.wait([production.id], config.context)
    >>> production.state
    u'waiting'
    >>> Production.assign_try([production.id], config.context)
    True
    >>> production.reload()
    >>> all(i.state == 'assigned' for i in production.inputs)
    True
    >>> Production.run([production.id], config.context)
    >>> production.reload()
    >>> all(i.state == 'done' for i in production.inputs)
    True
    >>> Production.done([production.id], config.context)
    >>> production.reload()
    >>> output, = production.outputs
    >>> output.state
    u'done'
