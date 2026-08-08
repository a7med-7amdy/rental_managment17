# -*- coding: utf-8 -*-
# Copyright 2023-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.addons.html_editor.tools import get_video_embed_code, get_video_thumbnail


class PropertyProject(models.Model):
    _name = "property.project"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Property Project Details"
    _check_company_auto = True

    # Project Details
    name = fields.Char(string="Name", required=True, translate=True)
    project_sequence = fields.Char(string="Code", required=True)
    image_1920 = fields.Image(string="Image")
    is_sub_project = fields.Boolean(default=True)
    project_for = fields.Selection([("rent", "Rent"),
                                    ("sale", "Sale")],
                                   string="Project For",
                                   required=True)
    property_type = fields.Selection([("residential", "Residential"),
                                      ("commercial", "Commercial"),
                                      ("industrial", "Industrial"),
                                      ("land", "Land"),],
                                     string="Property Type",
                                     required=True)
    property_subtype_id = fields.Many2one("property.sub.type",
                                          string="Property Subtype",
                                          required=True,
                                          domain="[('type','=',property_type)]")
    status = fields.Selection([("draft", "Draft"),
                               ("available", "Available"),
                               ("cancel", "Cancel"),
                               ("closed", "Closed"),],
                              default="draft")
    landlord_id = fields.Many2one(
        "res.partner",
        string="Landlord",
        domain="[('user_type','=','landlord')]",
        check_company=True,
    )
    # Company & Currency
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one("res.currency",
                                  related="company_id.currency_id",
                                  string="Currency",
                                  store=True)

    # Additional Details
    date_of_project = fields.Date(string="Date of Project", required=True)
    construction_year = fields.Char(string="Construction Year")
    property_brochure = fields.Binary(string="Brochure")
    brochure_name = fields.Char(string="Brochure Name")
    website = fields.Char(string='Website')

    # Address
    region_id = fields.Many2one("property.region", string="Region")
    street = fields.Char(string="Street", translate=True)
    street2 = fields.Char(string="Street2", translate=True)
    city_id = fields.Many2one('property.res.city')
    zip = fields.Char(string="Zip", translate=True)
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country',
                                 string='Country',
                                 ondelete='restrict')

    # Lat Long
    longitude = fields.Char(string='Longitude')
    latitude = fields.Char(string='Latitude')

    # Documents
    document_ids = fields.One2many("project.document.line",
                                   "project_id", string="Docs")

    # Availability
    avail_description = fields.Boolean(string="Descriptions")
    avail_amenity = fields.Boolean(string="Amenities")
    avail_specification = fields.Boolean(string="Specifications")
    avail_image = fields.Boolean(string="Images")
    avail_nearby_connectivity = fields.Boolean(string="Nearby Connectivity")

    # SubProject
    sub_project_ids = fields.One2many(
        "property.sub.project", "property_project_id")

    # Basic Details
    sale_lease = fields.Selection([("rent", "Rent"),
                                   ("sale", "Sale")],
                                  string="Sale Lease", default="rent")
    total_floors = fields.Integer(string="Total Floors")
    units_per_floor = fields.Integer(string="Units per Floor")
    total_subproject = fields.Integer(string="Total Sub Project",
                                      compute="_compute_sub_project_count")
    total_area = fields.Float(string="Total Property Area",
                              compute="compute_properties_statics")
    available_area = fields.Float(string="Available Area",
                                  compute="compute_properties_statics")
    total_values = fields.Monetary(string="Total Value of Project",
                                   compute="compute_properties_statics")
    total_maintenance = fields.Monetary(string="Total Maintenance",
                                        compute="compute_properties_statics")
    total_collection = fields.Monetary(string="Total Collection",
                                       compute="compute_properties_statics")
    scope_of_collection = fields.Monetary(string="Scope of Collection",
                                          compute="compute_properties_statics")

    # Description
    description = fields.Html(string="Description")

    # Amenities
    property_amenity_ids = fields.Many2many("property.amenities")

    # Specifications
    property_specification_ids = fields.Many2many("property.specification")

    # Images
    project_image_ids = fields.One2many("project.images.line", "project_id",
                                        string="images")
    # Connectivity
    project_connectivity_ids = fields.One2many("project.connectivity.line",
                                               "project_id")

    # Other Details
    license_number = fields.Char(string="License No.")
    date_of_license = fields.Date(string="Date of License")

    # Count
    document_count = fields.Integer(compute="compute_count")
    sub_project_count = fields.Integer()
    unit_count = fields.Integer(compute="compute_count")
    available_unit_count = fields.Integer(compute="compute_count")
    sold_count = fields.Integer(compute="compute_count")
    rent_count = fields.Integer(compute="compute_count")

    # Units
    property_unit_ids = fields.One2many("property.details",
                                        "property_project_id")
    floor_created = fields.Integer()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("project_for"):
                vals["sale_lease"] = vals["project_for"]
            elif vals.get("sale_lease"):
                vals["project_for"] = vals["sale_lease"]
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if "project_for" in vals:
            vals["sale_lease"] = vals["project_for"]
        elif "sale_lease" in vals:
            vals["project_for"] = vals["sale_lease"]
        return super().write(vals)

    # Unlink
    def unlink(self):
        for project in self:
            if project.is_sub_project and project.sub_project_ids:
                raise ValidationError(
                    _("Cannot delete project, please delete corresponding subproject before deletion")
                )
            if not project.is_sub_project and project.property_unit_ids:
                raise ValidationError(
                    _("Cannot delete project, please delete corresponding units before deletion")
                )
        return super().unlink()

    # Compute
    # Smart Button Count
    @api.depends('is_sub_project', 'property_unit_ids.stage')
    def compute_count(self):
        document_groups = self.env['project.document.line']._read_group(
            [('project_id', 'in', self.ids)], ['project_id'], ['__count']
        ) if self.ids else []
        document_map = {project.id: count for project, count in document_groups}
        property_groups = self.env['property.details']._read_group(
            [('property_project_id', 'in', self.ids)],
            ['property_project_id', 'stage'],
            ['__count'],
        ) if self.ids else []
        totals = {}
        stages = {}
        for project, stage, count in property_groups:
            totals[project.id] = totals.get(project.id, 0) + count
            stages[(project.id, stage)] = count
        for project in self:
            project.document_count = document_map.get(project.id, 0)
            project.unit_count = totals.get(project.id, 0)
            project.available_unit_count = stages.get((project.id, 'available'), 0)
            project.sold_count = (
                stages.get((project.id, 'sale'), 0)
                + stages.get((project.id, 'sold'), 0)
            )
            project.rent_count = stages.get((project.id, 'on_lease'), 0)

    @api.depends("sub_project_ids")
    def _compute_sub_project_count(self):
        groups = self.env['property.sub.project']._read_group(
            [('property_project_id', 'in', self.ids)], ['property_project_id'], ['__count']
        ) if self.ids else []
        count_map = {project.id: count for project, count in groups}
        for project in self:
            project.total_subproject = count_map.get(project.id, 0)

    @api.depends('sale_lease', 'is_sub_project')
    def compute_properties_statics(self):
        if not self:
            return
        property_model = self.env["property.details"]
        properties = property_model.search([("property_project_id", "in", self.ids)])
        property_ids = properties.ids
        sales = self.env["property.vendor"].search([("property_id", "in", property_ids)]) if property_ids else self.env["property.vendor"].browse()
        contracts = self.env["tenancy.details"].search([("property_id", "in", property_ids)]) if property_ids else self.env["tenancy.details"].browse()

        properties_by_parent = {}
        for prop in properties:
            parent = prop.property_project_id
            if parent:
                properties_by_parent.setdefault(parent.id, self.env["property.details"].browse())
                properties_by_parent[parent.id] |= prop
        sales_by_property = {}
        for sale in sales:
            sales_by_property.setdefault(sale.property_id.id, self.env["property.vendor"].browse())
            sales_by_property[sale.property_id.id] |= sale
        contracts_by_property = {}
        for contract in contracts:
            contracts_by_property.setdefault(contract.property_id.id, self.env["tenancy.details"].browse())
            contracts_by_property[contract.property_id.id] |= contract

        for rec in self:
            purpose = "for_sale" if rec.sale_lease == "sale" else "for_tenancy"
            rec_properties = properties_by_parent.get(rec.id, property_model.browse()).filtered(
                lambda prop: prop.sale_lease == purpose
            )
            rec.total_area = sum(rec_properties.mapped("total_area"))
            rec.available_area = sum(
                rec_properties.filtered(lambda prop: prop.stage == "available").mapped("total_area")
            )
            rec.total_values = sum(rec_properties.mapped("price"))
            rec.total_maintenance = sum(
                rec_properties.filtered("is_maintenance_service").mapped("total_maintenance")
            )
            if rec.sale_lease == "sale":
                rec_sales = self.env["property.vendor"].browse()
                for prop in rec_properties:
                    rec_sales |= sales_by_property.get(prop.id, self.env["property.vendor"].browse())
                rec.total_collection = sum(rec_sales.mapped("paid_amount"))
                rec.scope_of_collection = sum(rec_sales.mapped("remaining_amount"))
            else:
                rec_contracts = self.env["tenancy.details"].browse()
                for prop in rec_properties:
                    rec_contracts |= contracts_by_property.get(prop.id, self.env["tenancy.details"].browse())
                rec.total_collection = sum(rec_contracts.mapped("paid_tenancy"))
                rec.scope_of_collection = sum(rec_contracts.mapped("remain_tenancy"))
    # Onchange
    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    # Property Sub Type Domain
    @api.onchange('property_type')
    def onchange_property_sub_type(self):
        for rec in self:
            rec.property_subtype_id = False

    # Default Valuation
    @api.onchange('project_for')
    def onchange_valuation_sale_lease(self):
        for rec in self:
            rec.sale_lease = rec.project_for

    # Button
    # Smart Button

    def action_document_count(self):
        self.ensure_one()
        action = {
            "name": "Documents",
            "type": "ir.actions.act_window",
            "view_mode": "kanban,list,form",
            "domain": [("project_id", "=", self.id)],
            "res_model": "project.document.line",
            "target": "current",
        }
        if self.status == "draft":
            action['context'] = {'default_project_id': self.id}
            return action
        else:
            action['context'] = {'create': False, 'edit': False}
            return action

    def action_sub_project_count(self):
        self.ensure_one()
        return {
            "name": "Sub Projects",
            "type": "ir.actions.act_window",
            "domain": [("property_project_id", "=", self.id)],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.sub.project",
            "target": "current",
        }

    def action_view_unit(self):
        self.ensure_one()
        return {
            "name": "Units",
            "type": "ir.actions.act_window",
            "domain": [("property_project_id", "=", self.id)],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.details",
            "target": "current",
        }

    def action_view_available_unit(self):
        self.ensure_one()
        return {
            "name": "Available Units",
            "type": "ir.actions.act_window",
            "domain": [("property_project_id", "=", self.id), ('stage', '=', 'available')],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.details",
            "target": "current",
        }

    def action_view_sold_unit(self):
        self.ensure_one()
        return {
            "name": "Sold / Sale Units",
            "type": "ir.actions.act_window",
            "domain": [("property_project_id", "=", self.id), ('stage', 'in', ['sold', 'sale'])],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.details",
            "target": "current",
        }

    def action_view_rent_unit(self):
        self.ensure_one()
        return {
            "name": "Rent Units",
            "type": "ir.actions.act_window",
            "domain": [("property_project_id", "=", self.id), ('stage', '=', 'on_lease')],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.details",
            "target": "current",
        }

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

    def action_status_draft(self):
        self.status = 'draft'

    def action_status_available(self):
        self.status = 'available'


# Project Document
class ProjectDocumentLine(models.Model):
    _name = "project.document.line"
    _description = "Documents for Project"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    document_name = fields.Char(string="Document Name")
    document_file = fields.Binary(string="Document", required=True)
    user_id = fields.Many2one("res.users", string="Added by", required=True, default=lambda self: self.env.user)
    project_id = fields.Many2one("property.project", ondelete="cascade", index=True)


# Project Connectivity Line
class ProjectConnectivityLine(models.Model):
    _name = 'project.connectivity.line'
    _description = "Project Connectivity Line"

    project_id = fields.Many2one('property.project', ondelete='cascade', index=True)
    connectivity_id = fields.Many2one('property.connectivity',
                                      string="Nearby Connectivity")
    name = fields.Char(string="Name", translate=True)
    image = fields.Image(related="connectivity_id.image", string='Images')
    distance = fields.Char(string="Distance", translate=True)


# Property Images
class ProjectImagesLine(models.Model):
    _name = 'project.images.line'
    _description = 'Project Image Line'
    _inherit = ["image.mixin"]
    _order = "sequence, id"

    title = fields.Char(string='Title', translate=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one('property.project', ondelete='cascade', index=True)
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
