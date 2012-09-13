# -*- coding: utf-8 -*-
from osv import osv
from spawn_oop import spawn
import time


class ResPartner(osv.osv):
    _inherit = 'res.partner'

    @spawn(uniq=True)
    def read(self, cr, user, ids, fields=None, context=None,
             load='_classic_read'):
        time.sleep(3)
        res = super(ResPartner, self).read(cr, user, ids, fields, context)
        return res

ResPartner()
