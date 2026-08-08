# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
from odoo.addons.html_editor.tools import get_video_embed_code, get_video_thumbnail


class PropertyDetails(models.Model):
    _name = 'property.details'
    _description = 'Property Details and for registration new Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'property_seq, name, id'
    _check_company_auto = True

    # Property Details
    name = fields.Char(string='Name', required=True, translate=True)
    image = fields.Binary(string='Image')
    type = fields.Selection([('land', 'Land'),
                             ('residential', 'Residential'),
                             ('commercial', 'Commercial'),
                             ('industrial', 'Industrial')
                             ], string='Property Type',
                            required=True,
                            default="residential")
    sale_lease = fields.Selection([
        ('for_sale', 'Sale'),
        ('for_tenancy', 'Rent')],
        string='Property For',
        default='for_tenancy',
        required=True)
    property_seq = fields.Char(string='Property Code',
                               required=True,
                               readonly=False,
                               copy=False,
                               default=lambda self: '')
    stage = fields.Selection([('draft', 'Draft'),
                              ('available', 'Available'),
                              ('booked', 'In Booking'),
                              ('on_lease', 'On Rent'),
                              ('sale', 'In Sale'),
                              ('sold', 'Sold')],
                             group_expand='_expand_groups',
                             string='Status',
                             default='draft',
                             required=True,
                             tracking=True,
                             index=True)

    # Multi Companies
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 required=True,
                                 index=True,
                                 default=lambda self: self.env.company)
    responsible_id = fields.Many2one('res.users', string='Responsible', required=True,
                                     default=lambda self: self.env.user, index=True, tracking=True)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')

    # Property Sub Type
    property_subtype_id = fields.Many2one('property.sub.type',
                                          string="Property Sub Type",
                                          domain="[('type','=',type)]")

    # Project & Sub Project & Region
    region_id = fields.Many2one('property.region', string="Region")
    property_project_id = fields.Many2one('property.project',
                                          string="Project",
                                          check_company=True)
    subproject_id = fields.Many2one('property.sub.project',
                                    string="Sub Project",
                                    check_company=True)

    # Address
    zip = fields.Char(string='Zip')
    street = fields.Char(string='Street1', translate=True)
    street2 = fields.Char(string='Street2', translate=True)
    city = fields.Char(string='City  ', translate=True)
    city_id = fields.Many2one('property.res.city', string='City')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one(
        "res.country.state", string='State', store=True,
        domain="[('country_id', '=?', country_id)]")

    # Lat Long
    longitude = fields.Char(string='Longitude')
    latitude = fields.Char(string='Latitude')

    # Owner Details
    landlord_id = fields.Many2one(
        'res.partner', string='LandLord', index=True, check_company=True,
        domain=[('user_type', '=', 'landlord')],
    )
    landlord_phone = fields.Char(string="Phone", related="landlord_id.phone")
    landlord_email = fields.Char(string="Email", related="landlord_id.email")
    website = fields.Char(string='Website', translate=True)

    # Property Tags
    tag_ids = fields.Many2many('property.tag', string='Tags')

    # Availability
    amenities = fields.Boolean(string="Amenities")
    is_facilities = fields.Boolean(string="Specifications")
    is_images = fields.Boolean(string="Images")
    is_floor_plan = fields.Boolean(string="Floor Plans")
    nearby_connectivity = fields.Boolean(string="Nearby Connectivities")

    # Area Measurement
    is_section_measurement = fields.Boolean(
        string="Is Section Area Measurement")
    measure_unit = fields.Selection([('sq_ft', 'ft²'),
                                     ('sq_m', 'm²'),
                                     ('sq_yd', 'yd²'),
                                     ('cu_ft', 'ft³'),
                                     ('cu_m', 'm³')],
                                    default='sq_ft',
                                    string="Area Measurement Unit")
    room_measurement_ids = fields.One2many('property.room.measurement',
                                           'room_measurement_id',
                                           string='Area Measurement')
    total_room_measure = fields.Integer(compute='compute_room_measure',
                                        store=True)
    total_area = fields.Float(string="Total Area")
    usable_area = fields.Float(string="Usable Area")
    sq_ft = fields.Float(string="Total Ft²")
    sq_m = fields.Float(string="Total M²")
    sq_yd = fields.Float(string="Total Yd²")
    cu_ft = fields.Float(string="Total Ft³")
    cu_m = fields.Float(string="Total M³")

    # Pricing
    price = fields.Monetary(string="Price")
    rent_unit = fields.Selection([('Day', "Day"),
                                  ('Month', "Month"),
                                  ('Year', "Year")],
                                 default='Month',
                                 string="Rent Unit")
    pricing_type = fields.Selection([('fixed', 'Fixed'),
                                     ('area_wise', 'Area Wise')],
                                    string="Pricing Type",
                                    default='fixed')
    price_per_area = fields.Monetary(string="Price / Area")

    # Utility Service
    is_extra_service = fields.Boolean(string="Utility Services")
    extra_service_ids = fields.One2many('extra.service.line',
                                        'property_id',
                                        string="Services")
    extra_service_cost = fields.Monetary(string="Utility Cost",
                                         compute="_compute_extra_service_cost")

    # Maintenance Service
    is_maintenance_service = fields.Boolean(string="Is Any Maintenance")
    maintenance_rent_type = fields.Selection([('once', 'Once'),
                                              ('recurring', 'Recurring')],
                                             string="Maintenance Type",
                                             default="once")
    maintenance_type = fields.Selection([('fixed', 'Fixed'),
                                         ('area_wise', 'Area Wise')],
                                        string="Charges Type")
    per_area_maintenance = fields.Monetary(string="Maintenance / Area")
    total_maintenance = fields.Monetary(string="Total Maintenance")

    #  Property Documents
    document_ids = fields.One2many('property.documents',
                                   'property_id',
                                   string="Documents")

    # Property Amities
    amenities_ids = fields.Many2many('property.amenities',
                                     string="Property Amenities")

    # Property Specification
    property_specification_ids = fields.Many2many('property.specification',
                                                  string='Property Specifications')

    # Image
    property_images_ids = fields.One2many('property.images',
                                          'property_id',
                                          string='Property Images')
    # Floor Plan
    floreplan_ids = fields.One2many('floor.plan',
                                    'property_id',
                                    string='Property Floor Plans')
    # Nearby Connectivity
    connectivity_ids = fields.One2many('property.connectivity.line',
                                       'property_id',
                                       string="Property Nearby Conductivities")

    # Maintenance History
    maintenance_ids = fields.One2many('maintenance.request',
                                      'property_id',
                                      string='Maintenance Histories')

    # Property Broker And Tenancies
    tenancy_broker_count = fields.Integer(string="Rent Broker Count",
                                          compute="compute_count")
    tenancy_ids = fields.One2many('tenancy.details',
                                  'property_id',
                                  string='Rent Contracts')
    broker_ids = fields.One2many('tenancy.details',
                                 'property_id',
                                 string='Broker History',
                                 domain=[('is_any_broker', '=', True)])

    # Property Broker and Selling
    property_vendor_ids = fields.One2many('property.vendor',
                                          'property_id',
                                          string='Booking Details')
    sold_booking_id = fields.Many2one(
        'property.vendor', string="Booking", check_company=True, ondelete="restrict"
    )
    sale_broker_count = fields.Integer(string="Sale Broker Count",
                                       compute="compute_count")

    #  Enquiry
    tenancy_inquiry_ids = fields.One2many('tenancy.inquiry',
                                          'property_id',
                                          string="Rent Enquiry")
    sale_inquiry_ids = fields.One2many('sale.inquiry',
                                       'property_id',
                                       string="Sale Enquiry")

    # CRM Lead
    lead_count = fields.Integer(string="Lead Count",
                                compute="_compute_lead")
    lead_opp_count = fields.Integer(string="Opportunity Count",
                                    compute="_compute_lead")

    # Property Type wise Details
    total_floor = fields.Integer(string='No of Floors')
    floor = fields.Integer(string='Floor')
    bed = fields.Integer(string='Rooms', default=1)
    bathroom = fields.Integer(string='Bathrooms', default=1)
    parking = fields.Integer(string='Parking', default=1)
    facing = fields.Selection([('N', 'North(N)'),
                               ('E', 'East(E)'),
                               ('S', 'South(S)'),
                               ('W', 'West(W)'),
                               ('NE', 'North-East(NE)'),
                               ('SE', 'South-East(SE)'),
                               ('SW', 'South-West(SW)'),
                               ('NW', 'North-West(NW)'), ],
                              string='Facing', default='N')
    furnishing_id = fields.Many2one('property.furnishing', string="Furnishing")
    unit_type = fields.Integer(string="Unit Type", default=1)

    # Smart Button Count
    document_count = fields.Integer(string='Document Count',
                                    compute='_compute_document_count')
    request_count = fields.Integer(string='Request Count',
                                   compute='_compute_request_count')
    booking_count = fields.Monetary(string='Booking Amount',
                                    compute='_compute_booking_count')
    tenancy_count = fields.Integer(string='Rent Count',
                                   compute='_compute_booking_count')

    # Legacy compatibility fields retained for existing databases
    # Pricing
    token_amount = fields.Monetary(string='Book Price')
    sale_price = fields.Monetary(string='Sale Price')
    tenancy_price = fields.Monetary(string='Rent')
    # Property Details
    property_licence_no = fields.Char(string='License No.',
                                      translate=True)

    # Parent Property
    is_parent_property = fields.Boolean(string='Main Property')
    parent_property_id = fields.Many2one(
        'parent.property', check_company=True,
        domain="[('company_id', '=', company_id)]",
    )

    # Nearby Connectivity
    airport = fields.Char()
    national_highway = fields.Char()
    metro_station = fields.Char()
    metro_city = fields.Char()
    school = fields.Char()
    hospital = fields.Char()
    shopping_mall = fields.Char()
    park = fields.Char()
    # ---
    towers = fields.Boolean()
    no_of_towers = fields.Integer()
    facilities = fields.Text()
    # --
    parent_airport = fields.Char()
    parent_national_highway = fields.Char()
    parent_metro_station = fields.Char()
    parent_metro_city = fields.Char()
    parent_school = fields.Char()
    parent_hospital = fields.Char()
    parent_shopping_mall = fields.Char()
    parent_park = fields.Char()
    # --
    parent_zip = fields.Char()
    parent_street = fields.Char()
    parent_street2 = fields.Char()
    parent_city = fields.Char()
    parent_city_id = fields.Many2one(related='parent_property_id.city_id',
                                     string="Parent Cities")
    parent_country_id = fields.Many2one(related='parent_property_id.country_id',
                                        string="Parent Country")
    parent_state_id = fields.Many2one(related='parent_property_id.state_id',
                                      string="Parent State")
    parent_website = fields.Char()
    # --
    parent_amenities_ids = fields.Many2many(string="Parent Amentias",
                                            related='parent_property_id.amenities_ids')
    parent_specification_ids = fields.Many2many(string="Parent Specifications",
                                                related='parent_property_id.property_specification_ids')
    parent_landlord_id = fields.Many2one(string="Parent Landlord",
                                         related='parent_property_id.landlord_id')
    # --
    construct_year = fields.Char(string="Construct Year",
                                 size=4)
    buying_year = fields.Char()
    address = fields.Char()
    sold_invoice_id = fields.Many2one('account.move', check_company=True)
    sold_invoice_state = fields.Boolean()
    certificate_ids = fields.One2many('property.certificate',
                                      'property_id',
                                      string='Certificates')
    # --
    nearby_connectivity_ids = fields.Many2many('property.connectivity')
    room_no = fields.Char(string='Flat No./House No.')
    total_square_ft = fields.Char(string='Total Area Ft')
    usable_square_ft = fields.Char(string='Usable Area Ft')
    residence_type = fields.Selection([('apartment', 'Apartment'),
                                       ('bungalow', 'Bungalow'),
                                       ('vila', 'Vila'),
                                       ('raw_house', 'Raw House'),
                                       ('duplex', 'Duplex House'),
                                       ('single_studio', 'Single Studio')],
                                      string='Type of Residence')

    # Industrial
    industry_name = fields.Char()
    industry_location = fields.Selection([('inside', 'Inside City'),
                                          ('outside', 'Outside City')], )
    industrial_used_for = fields.Selection([('company', 'Company'),
                                            ('warehouses', 'Warehouses'),
                                            ('factories', 'Factories'),
                                            ('other', 'Other')])
    other_usages = fields.Char()
    industrial_facilities = fields.Text()
    # Land
    land_name = fields.Char()
    area_hector = fields.Char()
    land_facilities = fields.Text()
    # Commercial
    commercial_name = fields.Char()
    commercial_type = fields.Selection([('full_commercial', 'Full Commercial'),
                                        ('shops', 'Shops'),
                                        ('big_hall', 'Big Hall')])
    used_for = fields.Selection([('offices', 'Offices'),
                                 ('retail_stores', 'Retail Stores'),
                                 ('shopping_centres', 'Shopping Centres'),
                                 ('hotels', 'Hotels'),
                                 ('restaurants', 'Restaurants'),
                                 ('pubs', 'Pubs'),
                                 ('cafes', 'Cafes'),
                                 ('sport_facilities', 'Sport Facilities'),
                                 ('medical_centres', 'Medical Centres'),
                                 ('hospitals', 'Hospitals'),
                                 ('nursing_homes', 'Nursing Homes'),
                                 ('other', 'Other Use')
                                 ])
    floor_commercial = fields.Integer()
    total_floor_commercial = fields.Char()
    commercial_facilities = fields.Text()
    other_use = fields.Char()
    # Measurement
    commercial_measurement_ids = fields.One2many(
        'property.commercial.measurement', 'commercial_measurement_id')
    industrial_measurement_ids = fields.One2many(
        'property.industrial.measurement', 'industrial_measurement_id')
    total_commercial_measure = fields.Integer(
        string='Total Commercial Area', compute='compute_commercial_measure', store=True
    )
    total_industrial_measure = fields.Integer(
        string='Total Industrial Area', compute='compute_industrial_measure', store=True
    )
    furnishing = fields.Selection([('fully_furnished', 'Fully Furnished'),
                                   ('only_kitchen', 'Only Kitchen Furnished'),
                                   ('only_bed', 'Only BedRoom Furnished'),
                                   ('not_furnished', 'Not Furnished'),
                                   ], string='Furnishing Property', default='fully_furnished')

    # End legacy compatibility fields

    # Create, Constrain, Write, Scheduler, Name get
    # Create
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('property_seq'):
                vals['property_seq'] = self.env['ir.sequence'].next_by_code(
                    'property.details') or ''
        res = super(PropertyDetails, self).create(vals_list)
        return res

    # Stage Expand
    @api.model
    def _expand_groups(self, states, domain):
        return ['draft', 'available', 'booked', 'on_lease', 'sale', 'sold']

    # Unlink
    def unlink(self):
        blocked = self.filtered(lambda rec: rec.stage not in ('draft', 'available'))
        if blocked:
            raise ValidationError(
                _("Only draft or available properties can be deleted: %s")
                % ", ".join(blocked.mapped("display_name"))
            )
        rental_history = self.env["tenancy.details"].search_count(
            [("property_id", "in", self.ids)]
        )
        sale_history = self.env["property.vendor"].search_count(
            [("property_id", "in", self.ids)]
        )
        if rental_history or sale_history:
            raise ValidationError(
                _("A property with rental or sale history cannot be deleted. Archive or keep the property for audit history instead.")
            )
        return super().unlink()

    @api.constrains("stage", "sale_lease", "sold_booking_id")
    def _check_stage_business_consistency(self):
        """Prevent lifecycle corruption through direct RPC writes.

        Contract lookups are batched for the whole recordset so multi-record writes
        do not trigger one query per property.
        """
        if not self:
            return
        today = fields.Date.context_today(self)
        running_contracts = self.env["tenancy.details"].search(
            [
                ("property_id", "in", self.ids),
                ("contract_type", "=", "running_contract"),
                ("end_date", ">=", today),
            ]
        )
        reserved_property_ids = set(running_contracts.mapped("property_id").ids)
        current_property_ids = set(
            running_contracts.filtered(
                lambda contract: contract.start_date
                and contract.start_date <= today
                and contract.end_date >= today
            ).mapped("property_id").ids
        )

        for property_record in self:
            has_running = property_record.id in reserved_property_ids
            has_current = property_record.id in current_property_ids
            sale_booking = property_record.sold_booking_id.filtered(lambda sale: sale.stage == "booked")

            if property_record.stage in ("sale", "sold") and property_record.sale_lease != "for_sale":
                raise ValidationError(_("Only a property configured For Sale can use a sale status."))
            if property_record.stage == "on_lease" and property_record.sale_lease != "for_tenancy":
                raise ValidationError(_("A rented property must remain configured For Rent."))
            if property_record.stage == "sold" and (
                not property_record.sold_booking_id
                or property_record.sold_booking_id.stage != "sold"
            ):
                raise ValidationError(_("A property can be marked Sold only by a completed property sale."))
            if property_record.stage == "booked":
                if not sale_booking and not has_running:
                    raise ValidationError(_("Reserved status requires an active sale booking or rental contract."))
                if sale_booking and property_record.sale_lease != "for_sale":
                    raise ValidationError(_("A property with an active sale booking must remain configured For Sale."))
            if property_record.stage == "on_lease" and not has_current:
                raise ValidationError(_("Rented status requires a currently running rental contract."))
            if property_record.stage in ("draft", "available", "sale"):
                if has_running:
                    raise ValidationError(
                        _("A property with a current or future running rental contract cannot be moved to this status.")
                    )
                if sale_booking:
                    raise ValidationError(_("A property with an active sale booking must remain Reserved."))

    @api.depends("name", "type", "is_parent_property", "parent_property_id.name")
    def _compute_display_name(self):
        type_labels = dict(self._fields["type"]._description_selection(self.env))
        for record in self:
            parts = [record.name]
            if record.is_parent_property and record.parent_property_id:
                parts.append(record.parent_property_id.display_name)
            if record.type:
                parts.append(type_labels.get(record.type, record.type))
            record.display_name = " - ".join(filter(None, parts)) or _("Property")

    # Scheduler
    @api.model
    def update_property_address(self):
        """Refresh inherited address data for units linked to a parent property."""
        properties = self.search(
            [('is_parent_property', '=', True), ('parent_property_id', '!=', False)]
        )
        properties._sync_parent_property_address()
        return len(properties)

    def _parent_property_address_vals(self):
        self.ensure_one()
        parent = self.parent_property_id
        if not parent:
            return {}
        if parent.company_id and parent.company_id != self.company_id:
            raise ValidationError(_("Parent property and unit must belong to the same company."))
        return {
            "zip": parent.zip,
            "street": parent.street,
            "street2": parent.street2,
            "city": parent.city,
            "city_id": parent.city_id.id,
            "country_id": parent.country_id.id,
            "state_id": parent.state_id.id,
            "website": parent.website,
            "landlord_id": parent.landlord_id.id,
        }

    def _sync_parent_property_address(self):
        """Persist address/contact values inherited from the selected parent property."""
        for property_record in self.filtered(lambda rec: rec.is_parent_property and rec.parent_property_id):
            property_record.write(property_record._parent_property_address_vals())
        return True

    @api.onchange('is_parent_property', 'parent_property_id')
    def onchange_parent_property_address(self):
        """Legacy onchange entry point retained because older views/data call it."""
        for property_record in self:
            if property_record.is_parent_property and property_record.parent_property_id:
                property_record.update(property_record._parent_property_address_vals())

    @api.model
    def update_property_measurement(self):
        """Refresh legacy stored measurement totals in recordset batches."""
        properties = self.search([])
        properties.filtered(lambda rec: rec.type == "residential").compute_room_measure()
        properties.filtered(lambda rec: rec.type == "commercial").compute_commercial_measure()
        properties.filtered(lambda rec: rec.type == "industrial").compute_industrial_measure()
        return len(properties)

    # Compute
    # Total Measurement
    @api.depends('room_measurement_ids.carpet_area', 'type', 'measure_unit', 'is_section_measurement')
    def compute_room_measure(self):
        for rec in self:
            total = 0
            if rec.room_measurement_ids:
                for data in rec.room_measurement_ids:
                    total = total + data.carpet_area
            rec.total_room_measure = total
            if rec.is_section_measurement:
                rec.total_area = total

    @api.depends('commercial_measurement_ids.carpet_area', 'is_section_measurement', 'type')
    def compute_commercial_measure(self):
        for property_record in self:
            total = sum(property_record.commercial_measurement_ids.mapped('carpet_area'))
            property_record.total_commercial_measure = total
            if property_record.type == 'commercial' and property_record.is_section_measurement:
                property_record.total_area = total

    @api.depends('industrial_measurement_ids.carpet_area', 'is_section_measurement', 'type')
    def compute_industrial_measure(self):
        for property_record in self:
            total = sum(property_record.industrial_measurement_ids.mapped('carpet_area'))
            property_record.total_industrial_measure = total
            if property_record.type == 'industrial' and property_record.is_section_measurement:
                property_record.total_area = total

    # CRM Leads
    @api.depends('sale_lease')
    def _compute_lead(self):
        lead_model = self.env['crm.lead']
        if not self.ids or not lead_model.browse().has_access("read"):
            for property_record in self:
                property_record.lead_count = 0
                property_record.lead_opp_count = 0
            return
        groups = lead_model._read_group(
            [('property_id', 'in', self.ids)], ['property_id', 'type'], ['__count']
        )
        count_map = {(property_record.id, lead_type): count for property_record, lead_type, count in groups}
        for property_record in self:
            property_record.lead_count = count_map.get((property_record.id, 'lead'), 0)
            property_record.lead_opp_count = count_map.get((property_record.id, 'opportunity'), 0)

    # Utility Service Total
    @api.depends('extra_service_ids.price')
    def _compute_extra_service_cost(self):
        for rec in self:
            amount = 0.0
            if rec.extra_service_ids:
                for data in rec.extra_service_ids:
                    amount = amount + data.price
            rec.extra_service_cost = amount

    # Counts
    # Document Count
    def _compute_document_count(self):
        groups = self.env['property.documents']._read_group(
            [('property_id', 'in', self.ids)], ['property_id'], ['__count']
        ) if self.ids else []
        count_map = {property_record.id: count for property_record, count in groups}
        for property_record in self:
            property_record.document_count = count_map.get(property_record.id, 0)

    # Booking Count
    def _compute_booking_count(self):
        groups = self.env['tenancy.details']._read_group(
            [('property_id', 'in', self.ids)], ['property_id'], ['__count']
        ) if self.ids else []
        count_map = {property_record.id: count for property_record, count in groups}
        for property_record in self:
            property_record.booking_count = property_record.sold_booking_id.book_price
            property_record.tenancy_count = count_map.get(property_record.id, 0)

    # Maintenance Request Count
    def _compute_request_count(self):
        groups = self.env['maintenance.request']._read_group(
            [('property_id', 'in', self.ids)], ['property_id'], ['__count']
        ) if self.ids else []
        count_map = {property_record.id: count for property_record, count in groups}
        for property_record in self:
            property_record.request_count = count_map.get(property_record.id, 0)

    # Count
    def compute_count(self):
        sale_groups = self.env['property.vendor']._read_group(
            [('property_id', 'in', self.ids), ('is_any_broker', '=', True)],
            ['property_id'],
            ['broker_id:count_distinct'],
        ) if self.ids else []
        sale_map = {property_record.id: count for property_record, count in sale_groups}
        tenancy_groups = self.env['tenancy.details']._read_group(
            [('property_id', 'in', self.ids), ('is_any_broker', '=', True)],
            ['property_id'],
            ['broker_id:count_distinct'],
        ) if self.ids else []
        tenancy_map = {property_record.id: count for property_record, count in tenancy_groups}
        for property_record in self:
            property_record.sale_broker_count = sale_map.get(property_record.id, 0)
            property_record.tenancy_broker_count = tenancy_map.get(property_record.id, 0)

    # Onchange
    # Area Wise Price
    @api.onchange('pricing_type', 'price_per_area', 'measure_unit', 'room_measurement_ids', 'is_section_measurement',
                  'total_area')
    def onchange_fix_area_price(self):
        for rec in self:
            if rec.pricing_type == 'area_wise':
                rec.price = rec.total_area * rec.price_per_area

    # Maintenance Area wise Price
    @api.onchange('is_maintenance_service', 'maintenance_type', 'per_area_maintenance')
    def onchange_maintenance_type_charges(self):
        for rec in self:
            if rec.is_maintenance_service and rec.maintenance_type == 'area_wise':
                rec.total_maintenance = rec.per_area_maintenance * rec.total_area

    # Total Area
    @api.onchange('room_measurement_ids', 'is_section_measurement')
    def onchange_area_measure(self):
        for rec in self:
            total = 0.0
            if rec.is_section_measurement and rec.room_measurement_ids:
                for data in rec.room_measurement_ids:
                    total = total + data.carpet_area
                rec.total_area = total

    # Property Sub Type Domain
    @api.onchange('type')
    def onchange_property_sub_type(self):
        for rec in self:
            rec.property_subtype_id = False

    # State And Country Onchange
    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    # Buttons
    # Stage Buttons
    def action_in_available(self):
        active_contracts = self.env["tenancy.details"].search(
            [("property_id", "in", self.ids), ("contract_type", "=", "running_contract")]
        )
        if active_contracts:
            blocked = ", ".join(active_contracts.mapped("property_id.display_name"))
            raise UserError(
                _("Properties with an active rental contract cannot be made available: %s") % blocked
            )
        self.write({"stage": "available"})
        return True

    def action_in_booked(self):
        self.write({"stage": "booked"})
        return True

    def action_sold(self):
        if not self.env.user.has_group("rental_management.property_rental_manager"):
            raise UserError(_("Only a Rental Manager can confirm a property as sold."))
        for property_record in self:
            if not property_record.sold_booking_id or property_record.sold_booking_id.stage != "sold":
                raise UserError(
                    _("Complete the property sale workflow before marking the property as Sold.")
                )
        self.write({"stage": "sold"})
        return True

    def action_draft_property(self):
        self.write({"stage": "draft"})
        return True

    def action_in_sale(self):
        self.ensure_one()
        if self.sale_lease != "for_sale":
            raise UserError(_("Set Property For to Sale before moving the property to For Sale."))
        self.write({"stage": "sale"})
        return True

    # G-map Location
    def action_gmap_location(self):
        self.ensure_one()
        if self.longitude and self.latitude:
            longitude = self.longitude
            latitude = self.latitude
            http_url = 'https://maps.google.com/maps?q=loc:' + latitude + ',' + longitude
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': http_url,
            }
        else:
            raise ValidationError(
                "! Enter Proper Longitude and Latitude Values")

    # Smart Button
    def action_maintenance_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request',
            'res_model': 'maintenance.request',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
            'view_mode': 'kanban,list,form',
            'target': 'current'
        }

    def action_property_document(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document',
            'res_model': 'property.documents',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
            'view_mode': 'list',
            'target': 'current'
        }

    def action_sale_booking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Booking Information',
            'res_model': 'property.vendor',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_crm_lead(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Leads',
            'res_model': 'crm.lead',
            'domain': [('property_id', '=', self.id), ('type', '=', 'lead')],
            'context': {'default_property_id': self.id, 'default_type': 'lead'},
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_crm_lead_opp(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Opportunity',
            'res_model': 'crm.lead',
            'domain': [('property_id', '=', self.id), ('type', '=', 'opportunity')],
            'context': {'default_property_id': self.id, 'default_type': 'opportunity'},
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_view_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rent Contracts',
            'res_model': 'tenancy.details',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id, 'default_company_id': self.company_id.id},
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_property_tenancy_broker(self):
        self.ensure_one()
        ids = self.env['tenancy.details'].search(
            [('property_id', '=', self.id), ('is_any_broker', '=', True)]).mapped('broker_id').mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Brokers',
            'res_model': 'res.partner',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_property_sale_broker(self):
        self.ensure_one()
        ids = self.env['property.vendor'].search(
            [('property_id', '=', self.id), ('is_any_broker', '=', True)]).mapped('broker_id').mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Brokers',
            'res_model': 'res.partner',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_create_rental_contract(self):
        self.ensure_one()
        if self.sale_lease != "for_tenancy":
            raise UserError(_("Only a property configured for rent can be used to create a rental contract."))
        if self.stage != "available":
            raise UserError(_("Only an available property can be used to create a rental contract."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Rental Contract"),
            "res_model": "tenancy.details",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_property_id": self.id,
                "default_company_id": self.company_id.id,
                "default_contract_type": "new_contract",
            },
        }


    def action_view_rent_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Rental Invoices"),
            "res_model": "account.move",
            "domain": [
                ("tenancy_id.property_id", "=", self.id),
                ("move_type", "=", "out_invoice"),
            ],
            "view_mode": "list,form",
            "context": {"default_move_type": "out_invoice"},
        }

    def action_view_active_contract(self):
        self.ensure_one()
        contract = self.env["tenancy.details"].search(
            [("property_id", "=", self.id), ("contract_type", "=", "running_contract")],
            order="start_date desc, id desc",
            limit=1,
        )
        if not contract:
            raise UserError(_("No active rental contract exists for this property."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "tenancy.details",
            "res_id": contract.id,
            "view_mode": "form",
            "target": "current",
        }

    # Server Action
    def action_available_property(self):
        active_ids = self._context.get('active_ids')
        property_rec = self.env['property.details'].browse(active_ids).exists()
        for data in property_rec:
            if data.stage == 'draft':
                data.write({
                    'stage': 'available'
                })

    # Dashboard
    @api.model
    def get_property_stats(self):
        """Return permission-aware, company-scoped dashboard data without sudo."""
        allowed_company_ids = [self.env.company.id]
        company_domain = [("company_id", "in", allowed_company_ids)]
        property_model = self.env["property.details"]
        contract_model = self.env["tenancy.details"]
        sale_model = self.env["property.vendor"]
        move_model = self.env["account.move"]
        today = fields.Date.context_today(self)

        def grouped_counts(model, group_field, domain=None):
            return {
                key: count
                for key, count in model._read_group(
                    (domain or []) + company_domain,
                    groupby=[group_field],
                    aggregates=["__count"],
                )
                if key
            }

        stage_counts = grouped_counts(property_model, "stage")
        type_counts = grouped_counts(property_model, "type")
        contract_counts = grouped_counts(contract_model, "contract_type")
        sale_counts = grouped_counts(sale_model, "stage")

        rent_moves_domain = company_domain + [
            ("tenancy_id", "!=", False),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
        ]
        if move_model.browse().has_access("read"):
            rent_aggregates = move_model._read_group(
                rent_moves_domain,
                groupby=[],
                aggregates=["amount_total:sum", "amount_residual:sum"],
            )
            amount_total, amount_residual = rent_aggregates[0] if rent_aggregates else (0.0, 0.0)
            collected_amount = (amount_total or 0.0) - (amount_residual or 0.0)
            outstanding_amount = amount_residual or 0.0
            overdue_invoice = move_model.search_count(
                rent_moves_domain
                + [("invoice_date_due", "<", today), ("amount_residual", ">", 0)]
            )
            pending_invoice = move_model.search_count(
                rent_moves_domain + [("amount_residual", ">", 0)]
            )
        else:
            collected_amount = 0.0
            outstanding_amount = 0.0
            overdue_invoice = 0
            pending_invoice = 0
        running_contracts = contract_model.search(
            company_domain + [("contract_type", "=", "running_contract")]
        )
        monthly_rent = sum(
            contract.total_rent
            if contract.rent_unit == "Month"
            else contract.total_rent / 12.0
            if contract.rent_unit == "Year"
            else contract.total_rent * 30.0
            for contract in running_contracts
        )
        total_rentable = sum(
            stage_counts.get(stage, 0) for stage in ("available", "booked", "on_lease")
        )
        occupancy_rate = (
            round(stage_counts.get("on_lease", 0) * 100.0 / total_rentable, 2)
            if total_rentable
            else 0.0
        )

        sold_total_group = sale_model._read_group(
            company_domain + [("stage", "=", "sold")],
            groupby=[],
            aggregates=["sale_price:sum"],
        )
        sold_total = (sold_total_group[0][0] if sold_total_group else 0.0) or 0.0
        pending_invoice_sale = (
            move_model.search_count(
                company_domain
                + [("sold_id", "!=", False), ("state", "=", "posted"), ("amount_residual", ">", 0)]
            )
            if move_model.browse().has_access("read")
            else 0
        )

        partner_company_domain = [
            "|",
            ("company_id", "=", False),
            ("company_id", "in", allowed_company_ids),
        ]
        currency_symbol = self.env.company.currency_id.symbol or ""
        stats = {
            "avail_property": stage_counts.get("available", 0),
            "booked_property": stage_counts.get("booked", 0),
            "lease_property": stage_counts.get("on_lease", 0),
            "sale_property": stage_counts.get("sale", 0),
            "sold_property": stage_counts.get("sold", 0),
            "draft_contract": contract_counts.get("new_contract", 0),
            "running_contract": contract_counts.get("running_contract", 0),
            "expire_contract": contract_counts.get("expire_contract", 0),
            "extend_contract": contract_model.search_count(company_domain + [("is_extended", "=", True)]),
            "close_contract": contract_counts.get("close_contract", 0),
            "cancel_contract": contract_counts.get("cancel_contract", 0),
            "pending_invoice": pending_invoice,
            "rent_total": f"{collected_amount:.2f} {currency_symbol}".strip(),
            "monthly_rent": monthly_rent,
            "collected_amount": collected_amount,
            "outstanding_amount": outstanding_amount,
            "overdue_invoice": overdue_invoice,
            "occupancy_rate": occupancy_rate,
            "maintenance_request": self.env["maintenance.request"].search_count(company_domain),
            "booked": sale_counts.get("booked", 0),
            "sale_sold": sale_counts.get("sold", 0),
            "refund": sale_counts.get("refund", 0),
            "sold_total": f"{sold_total:.2f} {currency_symbol}".strip(),
            "pending_invoice_sale": pending_invoice_sale,
            "customer_count": self.env["res.partner"].search_count(
                partner_company_domain + [("user_type", "=", "customer")]
            ),
            "landlord_count": self.env["res.partner"].search_count(
                partner_company_domain + [("user_type", "=", "landlord")]
            ),
            "region_count": self.env["property.region"].search_count([]),
            "project_count": self.env["property.project"].search_count(company_domain),
            "subproject_count": self.env["property.sub.project"].search_count(company_domain),
            "total_property": sum(stage_counts.values()),
            "property_type": [
                ["Land", "Residential", "Commercial", "Industrial"],
                [
                    type_counts.get("land", 0),
                    type_counts.get("residential", 0),
                    type_counts.get("commercial", 0),
                    type_counts.get("industrial", 0),
                ],
            ],
            "property_stage": [
                ["Available Properties", "Sold Properties", "Booked Properties", "On Sale", "On Lease"],
                [
                    stage_counts.get("available", 0),
                    stage_counts.get("sold", 0),
                    stage_counts.get("booked", 0),
                    stage_counts.get("sale", 0),
                    stage_counts.get("on_lease", 0),
                ],
            ],
        }
        stats.update(
            {
                "property_map_data": self.get_property_map_data(),
                "due_paid_amount": self.due_paid_amount(),
                "tenancy_top_broker": self.get_top_broker(),
            }
        )
        return stats

    @api.model
    def get_top_broker(self):
        company_domain = [("company_id", "=", self.env.company.id)]

        def broker_data(model, extra_domain):
            groups = model._read_group(
                company_domain + extra_domain,
                groupby=["broker_id"],
                aggregates=["__count"],
                limit=5,
                order="__count desc",
            )
            names, values = [], []
            for broker, count in groups:
                if broker:
                    names.append(broker.display_name)
                    values.append(count)
            return names, values

        tenancy_names, tenancy_values = broker_data(
            self.env["tenancy.details"], [("is_any_broker", "=", True)]
        )
        sold_names, sold_values = broker_data(
            self.env["property.vendor"], [("is_any_broker", "=", True), ("stage", "=", "sold")]
        )
        return [tenancy_names, tenancy_values, sold_names, sold_values]

    @api.model
    def due_paid_amount(self):
        company_domain = [("company_id", "=", self.env.company.id)]
        move_model = self.env["account.move"]
        if not move_model.browse().has_access("read"):
            empty = {"Due": 0.0, "Paid": 0.0}
            return [
                list(empty.keys()),
                list(empty.values()),
                list(empty.keys()),
                list(empty.values()),
            ]

        def totals(domain):
            groups = move_model._read_group(
                company_domain + domain + [("state", "=", "posted")],
                groupby=["payment_state"],
                aggregates=["amount_total:sum", "amount_residual:sum"],
            )
            total = sum((amount_total or 0.0) for _payment_state, amount_total, _amount_residual in groups)
            due = sum((amount_residual or 0.0) for _payment_state, _amount_total, amount_residual in groups)
            return {"Due": due, "Paid": total - due}

        sold = totals([("sold_id", "!=", False)])
        tenancy = totals([("tenancy_id", "!=", False), ("move_type", "=", "out_invoice")])
        return [list(sold.keys()), list(sold.values()), list(tenancy.keys()), list(tenancy.values())]

    @api.model
    def get_property_map_data(self):
        data = []
        properties = self.search(
            [
                ("company_id", "=", self.env.company.id),
                ("stage", "=", "available"),
                ("latitude", "!=", False),
                ("longitude", "!=", False),
            ]
        )
        for property_record in properties:
            location_parts = [_("Property: %s") % property_record.display_name]
            if property_record.region_id:
                location_parts.append(_("Region: %s") % property_record.region_id.display_name)
            if property_record.city_id:
                location_parts.append(_("City: %s") % property_record.city_id.display_name)
            data.append(
                {
                    "title": "\n".join(location_parts),
                    "latitude": property_record.latitude,
                    "longitude": property_record.longitude,
                }
            )
        return data


# Area Measurement
class PropertyRoomMeasurement(models.Model):
    _name = 'property.room.measurement'
    _description = 'Room Property Measurement Details'

    type_room = fields.Selection([('hall', 'Hall'),
                                  ('bed_room', 'Bed Room'),
                                  ('kitchen', 'Kitchen'),
                                  ('drawing_room', 'Drawing Room'),
                                  ('bathroom', 'Bathroom'),
                                  ('store_room', 'Store Room'),
                                  ('balcony', 'Balcony'),
                                  ('wash_area', 'Wash Area'), ],
                                 string='House Section')
    section_id = fields.Many2one('property.area.type', string="Section")
    length = fields.Integer(string='Length')
    width = fields.Integer(string='Width')
    height = fields.Integer(string='Height', default=1)
    no_of_unit = fields.Integer(string="No of Unit", default=1)
    carpet_area = fields.Integer(string='Total Area',
                                 compute='_compute_carpet_area')
    measure = fields.Char(string='ft²',
                          default='ft²',
                          readonly=True,
                          translate=True)
    room_measurement_id = fields.Many2one(
        'property.details', string='Room Details', ondelete='cascade', index=True
    )
    measure_unit = fields.Selection(related="room_measurement_id.measure_unit",
                                    store=True)
    sq_ft = fields.Float(string="Total Square Feet")
    sq_m = fields.Float(string="Total Square Meters")
    sq_yd = fields.Float(string="Total Square Yards")
    cu_ft = fields.Float(string="Total Cubic Feet")
    cu_m = fields.Float(string="Total Cubic Meters")

    @api.depends('length', 'width', 'height', 'measure_unit', 'no_of_unit')
    def _compute_carpet_area(self):
        for rec in self:
            total = 0.0
            if rec.measure_unit in ['sq_ft', 'sq_m', 'sq_yd']:
                total = rec.length * rec.width * rec.no_of_unit
            elif rec.measure_unit in ['cu_ft', 'cu_m']:
                total = rec.length * rec.width * rec.height * rec.no_of_unit
            rec.carpet_area = total


# Property Documents
class PropertyDocuments(models.Model):
    _name = 'property.documents'
    _description = 'Document related to Property'
    _rec_name = 'doc_type'

    property_id = fields.Many2one(
        'property.details', string='Property Name', readonly=True,
        ondelete='cascade', index=True,
    )
    document_date = fields.Date(string='Date', default=fields.Date.today)
    doc_type = fields.Selection([('photos', 'Photo'),
                                 ('brochure', 'Brochure'),
                                 ('certificate', 'Certificate'),
                                 ('insurance_certificate',
                                  'Insurance Certificate'),
                                 ('utilities_insurance', 'Utilities Certificate')],
                                string='Document Type', required=True)
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name', translate=True)


# Property Amentias
class PropertyAmenities(models.Model):
    _name = 'property.amenities'
    _description = 'Details About Property Amenities'
    _rec_name = 'title'

    sequence = fields.Integer()
    image = fields.Binary(string='Image')
    title = fields.Char(string='Title', translate=True)


# Property Specification
class PropertySpecification(models.Model):
    _name = 'property.specification'
    _description = 'Details About Property Specification'
    _rec_name = 'title'

    image = fields.Image(string='Image')
    title = fields.Char(string='Title', translate=True)
    description = fields.Text(string="Description", translate=True)
    description_line1 = fields.Char(string='Description ', translate=True)
    description_line2 = fields.Char(string='Description Line 2',
                                    translate=True)
    description_line3 = fields.Char(string='Description Line 3',
                                    translate=True)


# Property Floor Plan
class FloorPlan(models.Model):
    _name = 'floor.plan'
    _description = 'Details About Floor Plan'
    _inherit = ["image.mixin"]
    _order = "sequence, id"

    title = fields.Char(string='Title', translate=True)
    sequence = fields.Integer(default=10)
    property_id = fields.Many2one(
        'property.details', string='Property', ondelete='cascade', index=True
    )
    image = fields.Image(string='Image ')
    video_url = fields.Char("Video URL",
                            help="URL of a video for showcasing your property.")
    embed_code = fields.Html(compute="_compute_embed_code",
                             sanitize=False)
    can_image_1024_be_zoomed = fields.Boolean(string="Can Image 1024 be zoomed",
                                              compute="_compute_can_image_1024_be_zoomed",
                                              store=True)

    @api.depends("image", "image_1024")
    def _compute_can_image_1024_be_zoomed(self):
        for image in self:
            image.can_image_1024_be_zoomed = (
                    image.image and tools.is_image_size_above(image.image, image.image_1024))

    @api.onchange("video_url")
    def _onchange_video_url(self):
        if not self.image:
            thumbnail = get_video_thumbnail(self.video_url)
            self.image = thumbnail and base64.b64encode(thumbnail) or False

    @api.depends("video_url")
    def _compute_embed_code(self):
        for image in self:
            image.embed_code = get_video_embed_code(image.video_url) or False

    @api.constrains("video_url")
    def _check_valid_video_url(self):
        for image in self:
            if image.video_url and not image.embed_code:
                raise ValidationError(
                    _(
                        "Provided video URL for '%s' is not valid. Please enter a valid video URL.",
                        image.display_name,
                    )
                )


# Property Images
class PropertyImages(models.Model):
    _name = 'property.images'
    _description = 'Property Images'
    _inherit = ["image.mixin"]
    _order = "sequence, id"

    title = fields.Char(string='Title', translate=True)
    sequence = fields.Integer(default=10)
    property_id = fields.Many2one(
        'property.details', string='Property Name', readonly=True,
        ondelete='cascade', index=True,
    )
    image = fields.Image(string='Images')
    video_url = fields.Char("Video URL",
                            help="URL of a video for showcasing your property.")
    embed_code = fields.Html(compute="_compute_embed_code",
                             sanitize=False)
    can_image_1024_be_zoomed = fields.Boolean(string="Can Image 1024 be zoomed",
                                              compute="_compute_can_image_1024_be_zoomed",
                                              store=True)

    @api.depends("image", "image_1024")
    def _compute_can_image_1024_be_zoomed(self):
        for image in self:
            image.can_image_1024_be_zoomed = (
                    image.image and tools.is_image_size_above(image.image, image.image_1024))

    @api.onchange("video_url")
    def _onchange_video_url(self):
        if not self.image:
            thumbnail = get_video_thumbnail(self.video_url)
            self.image = thumbnail and base64.b64encode(thumbnail) or False

    @api.depends("video_url")
    def _compute_embed_code(self):
        for image in self:
            image.embed_code = get_video_embed_code(image.video_url) or False

    @api.constrains("video_url")
    def _check_valid_video_url(self):
        for image in self:
            if image.video_url and not image.embed_code:
                raise ValidationError(
                    _(
                        "Provided video URL for '%s' is not valid. Please enter a valid video URL.",
                        image.display_name,
                    )
                )


# Property Tags
class PropertyTag(models.Model):
    _name = 'property.tag'
    _description = 'Property Tags'
    _rec_name = 'title'

    title = fields.Char(string='Title', translate=True)
    color = fields.Integer(string='Color')


# Utility Service
class TenancyExtraService(models.Model):
    _inherit = 'product.product'

    is_extra_service_product = fields.Boolean(string="Is Extras Service")


# Utility Service Line
class ExtraServiceLine(models.Model):
    _name = 'extra.service.line'
    _description = "Tenancy Extras Service"

    service_id = fields.Many2one('product.product',
                                 string="Service",
                                 domain=[('is_extra_service_product', '=', True)])
    price = fields.Float(string="Cost")
    service_type = fields.Selection([('once', 'Once'),
                                     ('monthly', 'Recurring')],
                                    string="Type",
                                    default="once")
    property_id = fields.Many2one(
        'property.details', string="Property", ondelete='cascade', index=True
    )

    @api.onchange('service_id')
    def _onchange_service_id_price(self):
        for rec in self:
            if rec.service_id:
                rec.price = rec.service_id.lst_price


# City
class PropertyResCity(models.Model):
    _name = 'property.res.city'
    _description = 'Cities'

    color = fields.Integer('Color')
    name = fields.Char(string="City Name", required=True, translate=True)


# Property Connectivity
class PropertyConnectivity(models.Model):
    _name = 'property.connectivity'
    _description = "Property Nearby Connectivity"

    name = fields.Char(string="Title", translate=True)
    distance = fields.Char(string="Distance", translate=True)
    image = fields.Image(string='Images')


# Property Connectivity Line
class PropertyConnectivityLine(models.Model):
    _name = 'property.connectivity.line'
    _description = "Property Connectivity Line"

    property_id = fields.Many2one(
        'property.details', ondelete='cascade', index=True
    )
    connectivity_id = fields.Many2one('property.connectivity',
                                      string="Nearby Connectivity")
    name = fields.Char(string="Name", translate=True)
    image = fields.Image(related="connectivity_id.image", string='Images')
    distance = fields.Char(string="Distance", translate=True)


# Tenancy Inquiry
class TenancyInquiry(models.Model):
    _name = 'tenancy.inquiry'
    _description = "Rent Inquiry"
    _rec_name = 'lead_id'
    _check_company_auto = True

    property_id = fields.Many2one('property.details', string="Property Details", check_company=True)
    company_id = fields.Many2one(
        'res.company', related='property_id.company_id', string='Company', store=True, index=True
    )
    note = fields.Text(string="Note", translate=True)
    duration_id = fields.Many2one('contract.duration', string='Duration')
    customer_id = fields.Many2one('res.partner', string="Customer", check_company=True)
    lead_id = fields.Many2one('crm.lead', string="Lead", check_company=True)

    @api.depends("customer_id.name", "lead_id.name")
    def _compute_display_name(self):
        for record in self:
            parts = [record.customer_id.display_name, record.lead_id.display_name]
            record.display_name = " - ".join(filter(None, parts)) or _("Rent Inquiry")


# Sale Inquiry
class SaleInquiry(models.Model):
    _name = 'sale.inquiry'
    _description = "Sale Inquiry"
    _rec_name = 'lead_id'
    _check_company_auto = True

    property_id = fields.Many2one('property.details', string="Property Details", check_company=True)
    company_id = fields.Many2one(
        'res.company', related='property_id.company_id', string='Company', store=True, index=True
    )
    note = fields.Text(string="Note", translate=True)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    ask_price = fields.Monetary(string="Ask Price")
    customer_id = fields.Many2one('res.partner', string="Customer", check_company=True)
    lead_id = fields.Many2one('crm.lead', string="Lead", check_company=True)

    @api.depends("customer_id.name", "lead_id.name")
    def _compute_display_name(self):
        for record in self:
            parts = [record.customer_id.display_name, record.lead_id.display_name]
            record.display_name = " - ".join(filter(None, parts)) or _("Sale Inquiry")


# Property Area Type
class PropertyAreaType(models.Model):
    _name = 'property.area.type'
    _description = "Property Area Type"

    name = fields.Char(string="Title")
    type = fields.Selection([('room', 'Rooms'),
                             ('bathroom', 'Bathrooms'),
                             ('parking', 'Parking'),
                             ('hall', 'Hall'),
                             ('kitchen', 'Kitchen'),
                             ('other', 'Other')], string="Type")


# Property Sub Type
class PropertySubType(models.Model):
    _name = 'property.sub.type'
    _description = "Property Sub Type"

    name = fields.Char(string="Title")
    type = fields.Selection([('land', 'Land'),
                             ('residential', 'Residential'),
                             ('commercial', 'Commercial'),
                             ('industrial', 'Industrial')],
                            string="Type")
    sequence = fields.Integer()


# Furnishing Type
class PropertyFurnishing(models.Model):
    _name = 'property.furnishing'
    _description = "Property Furnishing"

    name = fields.Char(string="Title")


# Legacy compatibility models retained for existing databases
class PropertyCommercialMeasurement(models.Model):
    _name = 'property.commercial.measurement'
    _description = 'Commercial Property Measurement Details'

    shops = fields.Char(string='Section', translate=True)
    length = fields.Integer(string='Length')
    width = fields.Integer(string='Width')
    height = fields.Integer(string='Height')
    carpet_area = fields.Integer(string='Area', compute='_compute_carpet_area')
    measure = fields.Char(string='ft²', default='ft²',
                          readonly=True, translate=True)
    commercial_measurement_id = fields.Many2one(
        'property.details', string='Commercial Details', ondelete='cascade', index=True
    )
    no_of_unit = fields.Integer(string="No of Unit", default=1)
    measure_unit = fields.Selection(
        related="commercial_measurement_id.measure_unit", store=True)
    sq_ft = fields.Float(string="Total Square Feet",
                         compute='_compute_carpet_area')
    sq_m = fields.Float(string="Total Square Meters",
                        compute='_compute_carpet_area')
    sq_yd = fields.Float(string="Total Square Yards",
                         compute='_compute_carpet_area')
    cu_ft = fields.Float(string="Total Cubic Feet",
                         compute='_compute_carpet_area')
    cu_m = fields.Float(string="Total Cubic Meters",
                        compute='_compute_carpet_area')

    @api.depends('length', 'width', 'height', 'measure_unit', 'no_of_unit')
    def _compute_carpet_area(self):
        for rec in self:
            total = 0
            sq_ft = 0
            sq_m = 0
            sq_yd = 0
            cu_ft = 0
            cu_m = 0
            if rec.length and rec.width:
                total = rec.length * rec.width * rec.no_of_unit
            if rec.measure_unit == 'sq_ft':
                sq_ft = total
                sq_m = total * 0.092903
                sq_yd = total * 0.111111
                cu_ft = total * rec.height
                cu_m = cu_ft * 0.0283168
            elif rec.measure_unit == 'sq_m':
                sq_ft = total * 10.764
                sq_m = total
                sq_yd = total * 1.19599
                cu_ft = total * rec.height * 35.3147
                cu_m = total * rec.height
            elif rec.measure_unit == 'sq_yd':
                sq_ft = total * 9
                sq_m = total * 0.836127
                sq_yd = total
                cu_ft = total * rec.height * 27
                cu_m = cu_ft / 35.3147
            elif rec.measure_unit == 'cu_ft' and rec.height > 0:
                cu_ft = total * rec.height
                sq_ft = cu_ft / rec.height
                sq_m = (cu_ft / rec.height) * 0.092903
                sq_yd = sq_ft / 9.0
                cu_m = cu_ft * 0.0283168
            elif rec.measure_unit == 'cu_m' and rec.height > 0:
                cu_m = total * rec.height
                sq_ft = (cu_m / rec.height) * 10.764
                sq_m = cu_m / rec.height
                sq_yd = sq_m * 1.19599
                cu_ft = cu_m * 35.315
            rec.carpet_area = total
            rec.sq_ft = sq_ft
            rec.sq_m = sq_m
            rec.sq_yd = sq_yd
            rec.cu_ft = cu_ft
            rec.cu_m = cu_m


class PropertyIndustrialMeasurement(models.Model):
    _name = 'property.industrial.measurement'
    _description = 'Industrial Property Measurement Details'

    asset = fields.Char(string='industrial Asset', translate=True)
    length = fields.Integer(string='Length')
    width = fields.Integer(string='Width')
    height = fields.Integer(string='Height')
    carpet_area = fields.Integer(string='Area', compute='_compute_carpet_area')
    measure = fields.Char(string='ft²', default='ft²',
                          readonly=True, translate=True)
    industrial_measurement_id = fields.Many2one(
        'property.details', string='Industrial Details', ondelete='cascade', index=True
    )
    no_of_unit = fields.Integer(string="No of Unit", default=1)
    measure_unit = fields.Selection(
        related="industrial_measurement_id.measure_unit", store=True)
    sq_ft = fields.Float(string="Total Square Feet",
                         compute='_compute_carpet_area')
    sq_m = fields.Float(string="Total Square Meters",
                        compute='_compute_carpet_area')
    sq_yd = fields.Float(string="Total Square Yards",
                         compute='_compute_carpet_area')
    cu_ft = fields.Float(string="Total Cubic Feet",
                         compute='_compute_carpet_area')
    cu_m = fields.Float(string="Total Cubic Meters",
                        compute='_compute_carpet_area')

    @api.depends('length', 'width', 'height', 'measure_unit', 'no_of_unit')
    def _compute_carpet_area(self):
        for rec in self:
            total = 0
            sq_ft = 0
            sq_m = 0
            sq_yd = 0
            cu_ft = 0
            cu_m = 0
            if rec.length and rec.width:
                total = rec.length * rec.width * rec.no_of_unit
            if rec.measure_unit == 'sq_ft':
                sq_ft = total
                sq_m = total * 0.092903
                sq_yd = total * 0.111111
                cu_ft = total * rec.height
                cu_m = cu_ft * 0.0283168
            elif rec.measure_unit == 'sq_m':
                sq_ft = total * 10.764
                sq_m = total
                sq_yd = total * 1.19599
                cu_ft = total * rec.height * 35.3147
                cu_m = total * rec.height
            elif rec.measure_unit == 'sq_yd':
                sq_ft = total * 9
                sq_m = total * 0.836127
                sq_yd = total
                cu_ft = total * rec.height * 27
                cu_m = cu_ft / 35.3147
            elif rec.measure_unit == 'cu_ft' and rec.height > 0:
                cu_ft = total * rec.height
                sq_ft = cu_ft / rec.height
                sq_m = (cu_ft / rec.height) * 0.092903
                sq_yd = sq_ft / 9.0
                cu_m = cu_ft * 0.0283168
            elif rec.measure_unit == 'cu_m' and rec.height > 0:
                cu_m = total * rec.height
                sq_ft = (cu_m / rec.height) * 10.764
                sq_m = cu_m / rec.height
                sq_yd = sq_m * 1.19599
                cu_ft = cu_m * 35.315
            rec.carpet_area = total
            rec.sq_ft = sq_ft
            rec.sq_m = sq_m
            rec.sq_yd = sq_yd
            rec.cu_ft = cu_ft
            rec.cu_m = cu_m


class CertificateType(models.Model):
    _name = 'certificate.type'
    _description = 'Type Of Certificate'
    _rec_name = 'type'

    type = fields.Char(string='Type', translate=True)


class PropertyCertificate(models.Model):
    _name = 'property.certificate'
    _description = 'Property Related All Certificate'
    _rec_name = 'type_id'

    type_id = fields.Many2one('certificate.type', string='Type')
    expiry_date = fields.Date(string='Expiry Date')
    responsible = fields.Char(string='Responsible', translate=True)
    note = fields.Char(string='Note', translate=True)
    property_id = fields.Many2one(
        'property.details', string='Property', ondelete='cascade', index=True
    )


class ParentProperty(models.Model):
    _name = 'parent.property'
    _description = 'Parent Property Details'
    _check_company_auto = True

    name = fields.Char(string='Name', translate=True)
    image = fields.Binary(string='Image')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, index=True
    )
    amenities_ids = fields.Many2many('property.amenities', string='Amenities')
    property_specification_ids = fields.Many2many('property.specification',
                                                  string='Specification')
    zip = fields.Char(string='Zip')
    street = fields.Char(string='Street1', translate=True)
    street2 = fields.Char(string='Street2', translate=True)
    city = fields.Char(string='City ', translate=True)
    city_id = fields.Many2one('property.res.city', string='City')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one("res.country.state",
                               string='State',
                               readonly=False, store=True,
                               domain="[('country_id', '=?', country_id)]")
    landlord_id = fields.Many2one(
        'res.partner', string='LandLord', check_company=True,
        domain=[('user_type', '=', 'landlord')],
    )
    website = fields.Char(string='Website', translate=True)
    airport = fields.Char(string='Airport')
    national_highway = fields.Char(string='National Highway', translate=True)
    metro_station = fields.Char(string='Metro Station', translate=True)
    metro_city = fields.Char(string='Metro City', translate=True)
    school = fields.Char(string="School", translate=True)
    hospital = fields.Char(string="Hospital", translate=True)
    shopping_mall = fields.Char(string="Mall", translate=True)
    park = fields.Char(string="Park", translate=True)
    nearby_connectivity_ids = fields.Many2many('property.connectivity',
                                               string="Nearby Connectivity ")
    type = fields.Selection([('residential', 'Residential'),
                             ('commercial', 'Commercial'),
                             ('industrial', 'Industrial')],
                            string='Property Type',
                            default="residential")
    property_count = fields.Integer(string="Property Count",
                                    compute="_compute_properties")

    # Residential
    residence_type = fields.Selection([('apartment', 'Apartment'),
                                       ('bungalow', 'Bungalow'),
                                       ('vila', 'Vila'),
                                       ('raw_house', 'Raw House'),
                                       ('duplex', 'Duplex House'),
                                       ('single_studio', 'Single Studio')],
                                      string='Type of Residence')
    total_floor = fields.Integer(string='Total Floor')
    towers = fields.Boolean(string='Tower Building')
    no_of_towers = fields.Integer(string='No. of Towers')

    # Commercial
    commercial_type = fields.Selection([('full_commercial', 'Full Commercial'),
                                        ('shops', 'Shops'),
                                        ('big_hall', 'Big Hall')],
                                       string='Commercial Type')

    # Industrial
    industry_location = fields.Selection([('inside', 'Inside City'),
                                          ('outside', 'Outside City')],
                                         string='Location')

    def _compute_properties(self):
        groups = self.env['property.details']._read_group(
            [('parent_property_id', 'in', self.ids), ('is_parent_property', '=', True)],
            ['parent_property_id'],
            ['__count'],
        ) if self.ids else []
        count_map = {parent.id: count for parent, count in groups}
        for property_record in self:
            property_record.property_count = count_map.get(property_record.id, 0)

    def action_properties_parent(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Properties',
            'res_model': 'property.details',
            'domain': [('parent_property_id', '=', self.id), ('is_parent_property', '=', True)],
            'context': {'default_parent_property_id': self.id, 'default_is_parent_property': True},
            'view_mode': 'kanban,list,form',
            'target': 'current'
        }

# End legacy compatibility models
