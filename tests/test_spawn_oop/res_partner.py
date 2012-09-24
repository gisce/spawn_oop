# -*- coding: utf-8 -*-
from osv import osv
from spawn_oop import spawn
import time


class ResPartner(osv.osv):
    _inherit = 'res.partner'

    @spawn(uniq=True, n_args=0)
    def read(self, cr, user, ids, fields=None, context=None,
             load='_classic_read'):
        time.sleep(1)
        res = super(ResPartner, self).read(cr, user, ids, fields, context)
        return res

    @spawn(uniq=True, n_args=0, link='read')
    def search(self, cr, user, args, offset=0, limit=None, order=None,
               context=None, count=False):
        time.sleep(1)
        res = super(ResPartner, self).search(cr, user, args, offset, limit,
                                             order, context, count)
        return res

ResPartner()
