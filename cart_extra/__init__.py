# -*- coding: utf-8 -*-
# The monkey patch belows exists to make it possible to override the
# cart page
from __future__ import unicode_literals
import frappe
from frappe.website import router
from frappe.website.router import get_start_folders, get_page_info
import os

__version__ = '0.0.1'


def get_page_info_from_template(path):
    '''Return page_info from path'''
    apps = frappe.get_installed_apps(frappe_last=True)
    if 'cart_extra' in apps:
        apps.remove('cart_extra')
        apps.insert(0, 'cart_extra')

    for app in apps:
        app_path = frappe.get_app_path(app)

        folders = get_start_folders()

        for start in folders:
            search_path = os.path.join(app_path, start, path)
            options = (search_path, search_path + '.html', search_path + '.md',
                search_path + '/index.html', search_path + '/index.md')
            for o in options:
                option = frappe.as_unicode(o)
                if os.path.exists(option) and not os.path.isdir(option):
                    return get_page_info(option, app, start, app_path=app_path)

    return None


router.get_page_info_from_template = get_page_info_from_template
