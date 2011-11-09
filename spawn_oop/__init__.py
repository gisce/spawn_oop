# -*- coding: utf-8 -*-
"""OpenObject Process Spawner.
"""
import os
import sys
from datetime import datetime

import psutil
from ooop import OOOP, Manager

import ir_cron
import netsvc
from tools import config

__version__ = '0.3.2'

def spawn(port=8069):
    """Spawn decorator.
    """
    def wrapper(f):
        def f_spawned(*args, **kwargs):
            if not os.getenv('SPAWNED', False):
                logger = netsvc.Logger()
                # self, cursor, uid, *args
                osv_object = args[0]            
                cursor = args[1]
                uid = args[2]
                user_obj = osv_object.pool.get('res.users')
                # Aquí hem de fer l'spawn
                env = os.environ.copy()
                env['SPAWNED'] = '1'
                command = sys.argv[:]
                command += ['--port=0', '--no-netrpc', '--update=False',
                            '--database=%s' % cursor.dbname,
                            '--logfile=%s' % os.devnull,
                            '--pidfile=False']
                child_port = port
                start = datetime.now()
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO, 'Spawned new '
                                     'process: %s' % ' '.join(command))
                p = psutil.Popen(command, env=env)
                po = psutil.Process(p.pid)
                while (child_port == port):
                    for connection in po.get_connections():
                        if (connection.status == 'LISTEN'
                                and not connection.remote_address):
                            child_port = connection.local_address[1]
                startup = datetime.now() - start
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO, 'Server '
                                     'started in %s. PID: %s. Listening on %s.'
                                     % (startup, p.pid, child_port))
                user = user_obj.browse(cursor, uid, uid).login
                pwd = user_obj.browse(cursor, uid, uid).password
                start = datetime.now()
                uri = 'http://localhost'
                if config['secure']:
                    uri = 'https://localhost'
                O = OOOP(dbname=cursor.dbname, port=child_port, user=user,
                         pwd=pwd, uri=uri)
                obj = Manager(osv_object._name, O)
                method = f.__name__
                newargs = args[3:]
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO, 'Calling '
                                     '%s.%s(%s)' % (osv_object._name, method,
                                                ', '.join(map(str, newargs))))

                res = getattr(obj, method)(*newargs)
                duration = datetime.now() - start
                for child in po.get_children():
                    child.kill()
                po.kill()
                po.wait()
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO, 'Server '
                                     'stopped. PID: %s. Duration %s.'
                                     % (p.pid, duration))
                return res
            else:
                return f(*args, **kwargs)
        return f_spawned
    return wrapper
