import logging
from odoo import fields, SUPERUSER_ID, api
from odoo.http import request, route
from odoo import http, tools, _
from xlrd.timemachine import xrange
from io import BytesIO
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


# My Portal Sell and Rent Contract Count
class RentalCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        sell_contract = request.env['property.vendor']
        rent_contract = request.env['tenancy.details']
        tenancy_domain = [('tenancy_id', '=', request.env.user.partner_id.id)]
        domain = [('customer_id', '=', request.env.user.partner_id.id)]
        # Maintenance Count
        tenancies = rent_contract.sudo().search(tenancy_domain).mapped('id')
        maintenance_count = request.env['maintenance.request'].sudo(
        ).search_count([('tenancy_id', 'in', tenancies)])
        values['sell_contract_count'] = sell_contract.sudo().search_count(domain)
        values['rent_contract_count'] = rent_contract.sudo(
        ).search_count(tenancy_domain)
        values['maintenance_count'] = maintenance_count
        return values


# Controllers
class RentalPortalWebsite(http.Controller):
    # Tree view sale Contract
    @http.route(['/my/sell-contract/'], type='http', auth="user", website=True)
    def rental_user_sell_contract(self):
        customer_id = request.env.user.partner_id.id
        sell_contracts = request.env['property.vendor'].sudo().search(
            [('customer_id', '=', customer_id)])
        values = {'contract': sell_contracts}
        return request.render('rental_management.rental_user_sell_contract_info', values)

    # Form View Sale Contract
    @http.route(['/my/sell-contract/information/<model("property.vendor"):b>'], type='http', auth="user",
                website=True)
    def rental_user_sell_contract_detail(self, b):
        if b.customer_id.id == request.env.user.partner_id.id:
            values = {
                'sell_contract': b.sudo(),
            }
            return request.render('rental_management.rental_user_sell_contract_details', values)
        else:
            return request.redirect('/')

    # Tree View Rent Contract
    @http.route(['/my/rent-contract/'], type='http', auth="user", website=True)
    def rental_user_rent_contract(self):
        rent_contracts = request.env['tenancy.details'].sudo().search(
            [('tenancy_id', '=', request.env.user.partner_id.id)])
        return request.render('rental_management.rental_user_rent_contract_info',  {'contract': rent_contracts})

    # Form View Rent Contract
    @http.route(['/my/rent-contract/information/<model("tenancy.details"):rc>'], type='http', auth="user",
                website=True)
    def rental_user_rent_contract_detail(self, rc):
        maintenance_rec = request.env['product.template'].sudo().search(
            [('is_maintenance', '=', True)])
        if rc.tenancy_id.id == request.env.user.partner_id.id:
            values = {
                'rent': rc.sudo(),
                'maintenance_type': maintenance_rec
            }
            return request.render('rental_management.rental_user_rent_contract_details', values)
        else:
            return request.redirect('/')

    # Maintenance Request Creation
    @http.route(['/my/rent-contract/information/maintenance-request'], type='http', auth="user",
                website=True)
    def rental_rent_maintenance_request(self, **kw):
        tenancy_id = request.env['tenancy.details'].sudo().browse(
            int(kw.get('rent')))
        name = kw.get('request') if kw.get('request') else (
            str(tenancy_id.tenancy_seq) + " Maintenance Request")
        maintenance_type_id = int(kw.get('maintenance_type_id'))
        maintenance_rec = {
            'maintenance_type_id': maintenance_type_id if maintenance_type_id else False,
            'name': name,
            'landlord_id': tenancy_id.property_landlord_id.id,
            'property_id': tenancy_id.property_id.id,
            'tenancy_id': tenancy_id.id,
            'description': kw.get('desc')
        }
        maintenance_id = request.env['maintenance.request'].sudo().create(
            maintenance_rec)
        return request.redirect('/my/maintenance-request/')

    # Tree View of Maintenance request
    @http.route(['/my/maintenance-request/'], type='http', auth="user", website=True)
    def rental_user_maintenance_request(self):
        tenancies = request.env['tenancy.details'].sudo().search(
            [('tenancy_id', '=', request.env.user.partner_id.id)]).mapped('id')
        maintenance_requests = request.env['maintenance.request'].sudo().search(
            [('tenancy_id', 'in', tenancies)])
        return request.render('rental_management.rental_user_maintenance_info',  {'maintenance_rec': maintenance_requests})

    # From Maintenance Request
    @http.route(['/my/maintenance-request/information/<model("maintenance.request"):mr>'], type='http', auth="user", website=True)
    def rental_user_maintenance_request_details(self, mr):
        return request.render('rental_management.rental_user_maintenance_details', {'mr': mr.sudo()})
