# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import fields, http
import json


class PortalUser(http.Controller):
	@http.route(['/update-image'], type='json', auth="user")
	def action_update_image(self,**post):
		datas_file = str(post['img_attachment']).split(',')
		datas_file = datas_file[1]
		user_id = request.env.user
		datas_file = ''
		if 'img_attachment' in post and post['img_attachment']:
			datas_file = str(post['img_attachment']).split(',')
			datas_file = datas_file[1]
			user_id.write({'image_1920':datas_file})
		values = {'user_id':user_id}
		return request.env['ir.ui.view'].render_template("website_portal_design.update_user_image",values)

	@http.route(['/address-view'], type='http', auth="public", website=True)
	def partner_address(self,**post):
		partner_id = request.env.user.partner_id
		values = {}
		countries = request.env['res.country'].sudo().search([])
		shippings = partner_id.search([('id', 'child_of', partner_id.commercial_partner_id.ids),('is_removed','!=',True)])
		values = {'countries':countries,'shippings':shippings,'billing':partner_id}
		return request.render('website_portal_design.address_list',values)

	@http.route(['/update-addres/<model("res.partner"):partner>'], type='http', auth="public", website=True)
	def update_shipping_addres(self,partner,**post):
		partner_id = request.env.user.partner_id
		shipping_partner_id = request.env['res.partner'].sudo().browse(int(partner))
		if shipping_partner_id:
			partner_id.sudo().write({'default_shipping_id':shipping_partner_id.id})
		return request.redirect("/address-view")

	@http.route(['/delete-address/<model("res.partner"):partner>'], type='http', auth="public", website=True)
	def delete_shipping_addres(self,partner,**post):
		partner_id = request.env.user.partner_id
		shipping_partner_id = request.env['res.partner'].sudo().browse(int(partner))
		if shipping_partner_id:
			shipping_partner_id.is_removed = True
		return request.redirect("/address-view")

	@http.route(['/add-address'], type='http', auth="public", website=True)
	def add_new_address(self,**post):
		required_fields = []
		predefine_data = {}
		user_id = request.env.user
		company_id = user_id.company_id
		values = {}
		partner_id = False
		error_message = ""
		if 'data' in post and post['data']:
			predefine_data = json.loads(post['data'].replace("'", '"'))
		if 'error' in post and post['error']:
			required_fields = post['error'].strip().split(',')
			error_message = "Update required fields!"		
		countries = request.env['res.country'].sudo().search([])
		state_ids = request.env['res.country.state'].sudo().search([])
		if 'edit-mode' in  post and post['edit-mode']:
			partner_id = request.env['res.partner'].sudo().browse(int(post['edit-mode']))
			values.update({
				'mode':'edit-mode',		
			})
		elif 'new-address' in post and post['new-address']:
			values.update({
				'mode':'new-address',		
			})
		if 'submitted' in post and post['submitted']:
			required_fields = ['name','city','street','phone','state_id']
			values = {}
			update_partner_id = False
			rfields = []
			if 'partner_id' in post and post['partner_id']:
				partner = ''.join(x for x in post['partner_id'] if x.isdigit())
				update_partner_id = request.env['res.partner'].sudo().browse(int(partner))
			error_message = ''
			for require_field in required_fields:
				if require_field in post and not post[require_field]:
					rfields.append(require_field)
			if rfields:
				error_message = ','.join(rfields)
			if  error_message:		
				return request.redirect("/add-address?data=%s&error=%s" % (post, error_message))
			partner_id = request.env.user.partner_id
			partner_vals = {}
			if 'name' in post and post['name']:
				partner_vals.update({'name':post['name']})
			if 'email' in post and post['email']:
				partner_vals.update({'email':post['email']})
			if 'phone' in post and post['phone']:
				partner_vals.update({'phone':post['phone']})
			if 'street' in post and post['street']:
				partner_vals.update({'street':post['street']})
			if 'street2' in post and post['street2']:
				partner_vals.update({'street2':post['street2']})
			if 'zip' in post and post['zip']:
				partner_vals.update({'zip':post['zip']})
			if 'city' in post and post['city']:
				partner_vals.update({'city':post['city']})
			if 'state_id' in post and post['state_id']:
				state_id = request.env['res.country.state'].sudo().browse(int(post['state_id']))
			if state_id:
				partner_vals.update({'state_id':state_id.id,'country_id':state_id.country_id.id})
			if 'mode' in  post and post['mode']:
				if post['mode'] == 'edit-mode' and update_partner_id:
					delivery_partner_id = update_partner_id.sudo().write(partner_vals)
				elif post['mode'] == 'new-address':
					partner_vals.update({'parent_id':partner_id.id,'type':'delivery'})
					delivery_partner_id = request.env['res.partner'].sudo().create(partner_vals)
			return request.redirect('/address-view')
		else:
			values.update({
				'partner_id':partner_id,
				'required_fields':required_fields,
				'error_message':error_message,
				'countries':countries,
				'predefine_data':predefine_data,
				'state_ids':state_ids,			
			})
		return request.render('website_portal_design.add_address',values)