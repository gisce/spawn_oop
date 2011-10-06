# -*- coding: utf-8 -*-
"""IrCron modification.
"""
import os

from osv import osv
from base.ir.ir_cron import ir_cron

class IrCron(ir_cron, osv.osv):
    """Check that ir.cron isn't started on child process.
    """
    _inherit = 'ir.cron'

    def _poolJobs(self, db_name, check=False):
        """Check if is a spawnded process.
        """
        if not os.getenv('SPAWNED', False):
            super(IrCron, self)._poolJobs(db_name, check)
IrCron()
