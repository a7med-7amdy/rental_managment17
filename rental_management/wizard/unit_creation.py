# -*- coding: utf-8 -*-
# Copyright 2023-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.fields import Command
from odoo.exceptions import UserError, ValidationError


# Unit Create from Project
class UnitCreation(models.TransientModel):
    _name = 'unit.creation'
    _description = 'Project Unit Creation'

    total_floors = fields.Integer(string="Total Floors", default=1)
    units_per_floor = fields.Integer(string="Units per Floor", default=1)
    property_code_prefix = fields.Char(string="Prefix",
                                       help="Prefix for Property Code")
    floor_start_from = fields.Integer(string="Floor Start From")

    @api.model
    def default_get(self, fields):
        res = super(UnitCreation, self).default_get(fields)
        active_id = self._context.get("active_id", False)
        unit_from = self._context.get('unit_from')
        if unit_from == 'project':
            project_id = self.env["property.project"].browse(active_id).exists()
            if project_id:
                res['property_code_prefix'] = project_id.project_sequence
                res['floor_start_from'] = project_id.floor_created + 1
        elif unit_from == 'sub_project':
            project_id = self.env["property.sub.project"].browse(active_id).exists()
            if project_id:
                res['property_code_prefix'] = project_id.project_sequence
                res['total_floors'] = project_id.total_floors
                res['units_per_floor'] = project_id.units_per_floor
                res['floor_start_from'] = project_id.floor_created + 1
        return res

    def action_create_property_unit(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        unit_from = self.env.context.get("unit_from")
        if self.total_floors <= 0:
            raise ValidationError(_("Total floors must be greater than zero."))
        if self.units_per_floor <= 0:
            raise ValidationError(_("Units per floor must be greater than zero."))
        if self.floor_start_from < 0:
            raise ValidationError(_("Floor start must not be negative."))
        if unit_from not in ("project", "sub_project") or not active_id:
            raise UserError(_("Open the unit creation wizard from a project or sub-project."))

        if unit_from == "project":
            project_id = self.env["property.project"].browse(active_id).exists()
            if not project_id:
                raise UserError(_("The source project no longer exists."))
            self.env.cr.execute(
                "SELECT id FROM property_project WHERE id = %s FOR UPDATE",
                (project_id.id,),
            )
            parent_project = project_id
            property_rec = {"property_project_id": project_id.id}
        else:
            project_id = self.env["property.sub.project"].browse(active_id).exists()
            if not project_id or not project_id.property_project_id:
                raise UserError(_("The source sub-project or its parent project no longer exists."))
            self.env.cr.execute(
                "SELECT id FROM property_sub_project WHERE id = %s FOR UPDATE",
                (project_id.id,),
            )
            parent_project = project_id.property_project_id
            property_rec = {
                "property_project_id": parent_project.id,
                "subproject_id": project_id.id,
            }

        company = project_id.company_id
        if not company or company not in self.env.companies:
            raise UserError(_("The project company is not one of your currently allowed companies."))
        property_rec.update(
            {
                "company_id": company.id,
                "sale_lease": "for_tenancy" if project_id.project_for == "rent" else "for_sale",
                "total_floor": self.total_floors,
                "property_subtype_id": project_id.property_subtype_id.id,
                "landlord_id": project_id.landlord_id.id,
                "type": project_id.property_type,
                "street": project_id.street,
                "street2": project_id.street2,
                "city_id": project_id.city_id.id,
                "zip": project_id.zip,
                "state_id": project_id.state_id.id,
                "country_id": project_id.country_id.id,
                "region_id": project_id.region_id.id,
                "website": project_id.website,
                "longitude": project_id.longitude,
                "latitude": project_id.latitude,
            }
        )

        prefix = (self.property_code_prefix or project_id.project_sequence or "").strip()
        if not prefix:
            raise ValidationError(_("A property code prefix is required."))
        property_data = []
        for floor in range(self.floor_start_from, self.floor_start_from + self.total_floors):
            for unit in range(1, self.units_per_floor + 1):
                code = "%s%s-%s" % (prefix, str(floor).zfill(2), str(unit).zfill(2))
                name = "%s-%s" % (project_id.name, str(floor) + str(unit).zfill(2))
                property_data.append({"name": name, "property_seq": code, "floor": floor})

        duplicate = self.env["property.details"].with_company(company).search(
            [("property_seq", "in", [item["property_seq"] for item in property_data])],
            limit=1,
        )
        if duplicate:
            raise ValidationError(
                _("Property code %(code)s already exists. Adjust the prefix or floor range.")
                % {"code": duplicate.property_seq}
            )

        unit_amenities, unit_images, unit_specification, unit_connectivity = self.get_property_availability(
            unit_from=unit_from, project_id=project_id
        )
        property_rec.update(
            self.get_property_availability_info(
                project_id=project_id,
                unit_amenities=unit_amenities,
                unit_specification=unit_specification,
                unit_images=unit_images,
                unit_connectivity=unit_connectivity,
            )
        )
        vals_list = []
        for data in property_data:
            vals = dict(property_rec)
            vals.update(data)
            vals_list.append(vals)

        created_properties = self.env["property.details"].with_company(company).create(vals_list)
        project_id.write(
            {
                "total_floors": self.total_floors,
                "units_per_floor": self.units_per_floor,
                "floor_created": max(project_id.floor_created, self.floor_start_from + self.total_floors - 1),
            }
        )
        if unit_from == "sub_project" and parent_project:
            parent_project.invalidate_recordset(["property_unit_ids"])
        return {
            "name": _("Properties"),
            "type": "ir.actions.act_window",
            "domain": [("id", "in", created_properties.ids)],
            "view_mode": "list,form",
            "context": {"create": False},
            "res_model": "property.details",
            "target": "current",
        }

    def get_property_availability(self, unit_from, project_id):
        unit_amenities = False
        unit_images = False
        unit_specification = False
        unit_connectivity = False
        if unit_from == 'project':
            unit_amenities = project_id.property_amenity_ids.ids
            unit_images = project_id.project_image_ids
            unit_specification = project_id.property_specification_ids.ids
            unit_connectivity = project_id.project_connectivity_ids
        if unit_from == 'sub_project':
            unit_amenities = project_id.subproject_amenity_ids.ids
            unit_images = project_id.subproject_image_ids
            unit_specification = project_id.subproject_specification_ids.ids
            unit_connectivity = project_id.subproject_connectivity_ids
        return unit_amenities, unit_images, unit_specification, unit_connectivity

    def get_property_availability_info(self, project_id, unit_amenities, unit_specification, unit_images, unit_connectivity):
        info_rec = {}
        images = []
        nearby = []
        # Amenities
        if project_id.avail_amenity:
            info_rec['amenities'] = project_id.avail_amenity
            info_rec['amenities_ids'] = [Command.set(unit_amenities)]
        # Specifications
        if project_id.avail_specification:
            info_rec['is_facilities'] = project_id.avail_specification
            info_rec['property_specification_ids'] = [Command.set(unit_specification)]
        # Images
        if project_id.avail_image:
            info_rec['is_images'] = project_id.avail_image
            for image in unit_images:
                images.append(Command.create({
                    'title': image.title,
                    'sequence': image.sequence,
                    'image': image.image,
                    'video_url': image.video_url,
                }))
            info_rec['property_images_ids'] = images
        # Connectivity
        if project_id.avail_nearby_connectivity:
            info_rec['nearby_connectivity'] = project_id.avail_nearby_connectivity
            for n in unit_connectivity:
                nearby.append(Command.create({
                    'connectivity_id': n.connectivity_id.id,
                    'name': n.name,
                    'image': n.image,
                    'distance': n.distance
                }))
            info_rec['connectivity_ids'] = nearby
        return info_rec
