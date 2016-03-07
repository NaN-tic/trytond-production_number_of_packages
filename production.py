# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

from trytond.modules.stock_number_of_packages.package import PackagedMixin

__all__ = ['BOMOutput', 'Production']


class BOMOutput(PackagedMixin):
    __name__ = 'production.bom.output'
    __metaclass__ = PoolMeta

    @classmethod
    def __setup__(cls):
        super(BOMOutput, cls).__setup__()
        cls._error_messages.update({
                'package_required': 'Package required for BOM output "%s".',
                'number_of_packages_required': (
                    'Number of packages required for BOM output "%s".'),
                'package_qty_required': ('Quantity by Package is required '
                    'for package "%(package)s" of BOM output "%(record)s".'),
                'invalid_quantity_number_of_packages': ('The quantity of BOM '
                    'output "%s" do not correspond to the number of packages.')
                })

    def get_rec_name(self, name):
        return self.product.rec_name

    @classmethod
    def validate(cls, boms):
        super(BOMOutput, cls).validate(boms)
        for bom in boms:
            bom.check_package(bom.quantity)


class Production(PackagedMixin):
    __name__ = 'production'
    __metaclass__ = PoolMeta

    @classmethod
    def __setup__(cls):
        super(Production, cls).__setup__()
        if cls.quantity.states.get('required'):
            cls.package.states['required'] = cls.quantity.states['required']
        if cls.quantity.states.get('readonly'):
            cls.package.states['readonly'] = cls.quantity.states['readonly']
        if cls.quantity.states.get('required'):
            cls.number_of_packages.states['required'] = (
                cls.quantity.states['required'])
        if cls.quantity.states.get('readonly'):
            cls.number_of_packages.states['readonly'] = (
                cls.quantity.states['readonly'])

        cls._error_messages.update({
                'package_required': 'Package required for Production "%s".',
                'number_of_packages_required': (
                    'Number of packages required for Production "%s".'),
                'package_qty_required': ('Quantity by Package is required '
                    'for package "%(package)s" of Production "%(record)s".'),
                'invalid_quantity_number_of_packages': (
                    'The quantity of Production "%s" do not correspond to the '
                    'number of packages.')
                })

    @fields.depends(methods=['quantity'])
    def on_change_number_of_packages(self):
        res = super(Production, self).on_change_number_of_packages()
        self.quantity = res.get('quantity')
        res.update(self.on_change_quantity())
        return res

    @classmethod
    def validate(cls, productions):
        super(Production, cls).validate(productions)
        for production in productions:
            production.check_package(production.quantity)

    def _explode_move_values(self, from_location, to_location, company,
            bom_io, quantity):
        values = super(Production, self)._explode_move_values(
            from_location, to_location, company, bom_io, quantity)
        package_factor = quantity / bom_io.quantity
        try:
            values['package'] = bom_io.package.id if bom_io.package else None
            values['number_of_packages'] = int(bom_io.number_of_packages
                * package_factor) if bom_io.number_of_packages else None
        except AttributeError:
            pass  # production.bom.output doesn't have package fields
        return values
