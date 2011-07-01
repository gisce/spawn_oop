# -*- coding: utf-8 -*-
"""OpenObject Process Spawner.
"""
import os
import sys

import psutil
from ooop import OOOP, Manager

__version__ = '0.1.0'


def spawn(port=8069):
    """Spawn decorator.
    """
    def wrapper(f):
        def f_spawned(*args, **kwargs):
            if not os.getenv('SPAWNED', False):
                # self, cursor, uid, *args
                osv_object = args[0]            
                cursor = args[1]
                uid = args[2]
                user_obj = osv_object.pool.get('res.users')
                # Aquí hem de fer l'spawn
                env = os.environ.copy()
                env['SPAWNED'] = '1'
                command = sys.argv[:]
                command += ['--port=0', '--no-netrpc', '--update=False']
                child_port = port
                p = psutil.Popen(command, env=env)
                po = psutil.Process(p.pid)
                while (child_port == port):
                    for connection in po.get_connections():
                        if connection.status == 'LISTEN':
                            child_port = connection.local_address[1]
                            break
                user = user_obj.browse(cursor, uid, uid).login
                pwd = user_obj.browse(cursor, uid, uid).password
                O = OOOP(dbname=cursor.dbname, port=child_port, user=user,
                         pwd=pwd)
                obj = Manager(osv_object._name, O)
                method = f.__name__
                newargs = args[3:]
                res = None
                res = getattr(obj, method)(*newargs)
                for child in po.get_children():
                    child.kill()
                po.kill()
                po.wait()
                return res
            else:
                return f(*args, **kwargs)
        return f_spawned
    return wrapper
