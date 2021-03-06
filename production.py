# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval

from trytond.modules.stock_number_of_packages.package import PackagedMixin

__all__ = ['BOMOutput', 'Production']


class BOMOutput(PackagedMixin,metaclass=PoolMeta):
    __name__ = 'production.bom.output'

    def get_rec_name(self, name):
        return self.product.rec_name

    @classmethod
    def validate(cls, boms):
        super(BOMOutput, cls).validate(boms)
        for bom in boms:
            bom.check_package(bom.quantity)


class Production(PackagedMixin,metaclass=PoolMeta):
    __name__ = 'production'

    package_required = fields.Function(fields.Boolean('Package required'),
        'on_change_with_package_required')

    @classmethod
    def __setup__(cls):
        super(Production, cls).__setup__()
        package_required = Eval('package_required', False)
        if cls.package.states.get('required'):
            cls.package.states['required'] = (
                cls.package.states['required'] | package_required)
            cls.number_of_packages.states['required'] = (
                cls.package.states['required'] | package_required)
        else:
            cls.package.states['required'] = package_required
            cls.number_of_packages.states['required'] = package_required
        if cls.quantity.states.get('readonly'):
            cls.package.states['readonly'] = cls.quantity.states['readonly']
            cls.number_of_packages.states['readonly'] = (
                cls.quantity.states['readonly'])

    @fields.depends('product', 'quantity')
    def on_change_with_package_required(self, name=None):
        if self.product and self.product.package_required:
            return True
        return False

    @fields.depends(methods=['on_change_quantity'])
    def on_change_number_of_packages(self):
        super(Production, self).on_change_number_of_packages()
        self.on_change_quantity()

    @classmethod
    def validate(cls, productions):
        super(Production, cls).validate(productions)
        for production in productions:
            production.check_package(production.quantity)

    def _explode_move_values(self, from_location, to_location, company,
            bom_io, quantity):
        move = super(Production, self)._explode_move_values(
            from_location, to_location, company, bom_io, quantity)
        package_factor = quantity / bom_io.quantity
        try:
            move.package = bom_io.package.id if bom_io.package else None
            move.number_of_packages = int(bom_io.number_of_packages
                * package_factor) if bom_io.number_of_packages else None
        except AttributeError:
            pass  # production.bom.output doesn't have package fields
        return move

    def _move(self, from_location, to_location, company, product, uom,
            quantity):
        move = super(Production, self)._move(from_location, to_location,
            company, product, uom, quantity)
        if product == self.product or product.package_required:
            package = product.default_package
            move.package = package
            move.number_of_packages = (int(quantity/package.qty) if package
                else None)
        return move

    @classmethod
    def compute_request(cls, product, warehouse, quantity, date, company):
        production = super(Production, cls).compute_request(product,
            warehouse, quantity, date, company)
        package = product.default_package
        number_packages = package.qty * quantity if package else quantity
        production.package = package
        production.number_of_packages = number_packages
        return production
