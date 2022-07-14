# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request
from .res_config_settings import BearerAuth

class ProductProduct(models.Model):
    _inherit = 'product.template'

    goflow_id = fields.Char('Goflow ID')
    goflow_item_no = fields.Char('Goflow Item Number')


    def sync_product_goflow(self):
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')
        url = 'https://%s.api.goflow.com/v1/products' % goflow_subdomain
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }
        try:
            result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers)
            goflow_api = result.json()
            products = goflow_api["data"]
            while goflow_api["next"]:
                goflow_api = requests.get(goflow_api["next"], auth=BearerAuth(goflow_token), headers=headers).json()
                products.extend(goflow_api["data"])

            for product in products:
                prod_name = product['details']['name']
                if prod_name:
                    goflow_id = product['id']
                    check_if_product_exists = self.search([('goflow_id','=',goflow_id)])
                    goflow_item_no = product['item_number']
                    goflow_tags_json = product["tags"]
                    allowed_tags = self.env['goflow.product.tag'].search([('sync_products','=',True)]).mapped('goflow_id')
                    goflow_tags = []

                    for tag in goflow_tags_json:
                        goflow_tags.append(tag['id'])
                    if not set(allowed_tags).isdisjoint(goflow_tags):

                        if not check_if_product_exists:
                            self.create({'name':prod_name,'goflow_id':goflow_id,'goflow_item_no':goflow_item_no})
        except:
            pass



# import requests #to make TMDB API calls
#
# #Discover API url filtered to movies >= 2004 and containing Drama genre_ID: 18
# discover_api = 'https://api.themoviedb.org/3/discover/movie?
# api_key=['my api key']&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&primary_release_year=>%3D2004&with_genres=18'
#
# discover_api = requests.get(discover_api).json()
# most_popular_films = discover_api["results"]
# while discover_api["next_url"]:
#     discover_api = requests.get(discover_api["next_url"]).json()
#     most_popular_films.extend(discover_api["results"])
#
# #printing movie_id and movie_title by popularity desc
# for i, film in enumerate(most_popular_films):
#     print(i, film['id'], film['title'])