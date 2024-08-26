from odoo import api, fields, models

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    tier_ids = fields.One2many(
        "tier.list",
        "pricelist_item_id",
        string="Pricing Tiers",
    )
    compute_price = fields.Selection(
        selection=[
            ('fixed', "Fixed Price"),
            ('percentage', "Discount"),
            ('formula', "Formula"),
            ('tiered', "Tiered")
        ],
        index=True, default='fixed', required=True
    )
    product_variant_id = fields.Many2one("product.product", string="Product Variant")


class TierList(models.Model):
    _name = "tier.list"
    _description = "Pricing Tiers"

    product_id = fields.Many2one("product.product", string="Product")
    pricelist_item_id = fields.Many2one("product.pricelist.item", string="Pricelist Item")
    tier_number = fields.Integer(string="Tier Number", required=True)
    quantity_from = fields.Float(string="Quantity From", required=True)
    quantity_to = fields.Float(string="Quantity To", required=True)
    list_price = fields.Float(string="List Price", required=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty', 'order_id.pricelist_id')
    def _apply_tiered_pricing(self):
        for line in self:
            pricelist = line.order_id.pricelist_id
            if not pricelist:
                continue
            pricelist_item = self.env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('compute_price', '=', 'tiered'),
                ('product_variant_id', '=', line.product_id.id)
            ], limit=1)
            if pricelist_item:
                applicable_tier = next(
                    (tier for tier in pricelist_item.tier_ids
                     if tier.quantity_from <= line.product_uom_qty <= tier.quantity_to),
                    None
                )
                if applicable_tier:
                    line.price_unit = applicable_tier.list_price
