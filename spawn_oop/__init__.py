# -*- coding: utf-8 -*-
"""OpenObject Process Spawner.
"""
import os
import socket
import sys
import time
import tempfile
from datetime import datetime
from hashlib import sha1
from collections import namedtuple
from multiprocessing import Lock

import psutil
from ooop import OOOP, Manager

import ir_cron
import netsvc
import pooler
from tools import config
from tools.translate import _
from osv.osv import except_osv

__version__ = '0.8.1'

RUNNING_INSTANCES = {}


def compute_hash_instance(dbname, osv_object, method, *args):
    if args:
        args = '-'.join([str(x) for x in args])
    return sha1('%s-%s-%s-%s' % (dbname, osv_object, method, args)).hexdigest()

SpawnProc = namedtuple('SpawnProc', ['pid', 'startup', 'user'])


class spawn(object):
    """Spawn decorator.
    """

    hash_lock = Lock()

    def __init__(self, *args, **kwargs):
        self.uniq = kwargs.get('uniq', False)
        self.n_args = int(kwargs.get('n_args', -1))
        self.link = kwargs.get('link', False)

    def __call__(self, f):
        def f_spawned(*args, **kwargs):
            if not os.getenv('SPAWNED', False):
                spawn.hash_lock.acquire()
                logger = netsvc.Logger()
                # self, cursor, uid, *args
                osv_object = args[0]
                cursor = args[1]
                uid = args[2]
                if self.n_args < 0:
                    self.n_args = len(args)
                if not self.link:
                    self.link = f.__name__
                hash_instance = compute_hash_instance(
                    cursor.dbname, osv_object, self.link, args[3:self.n_args]
                )
                spawn_proc = RUNNING_INSTANCES.get(hash_instance,
                                                   SpawnProc(0, 0, 0))
                try:
                    if psutil.Process(spawn_proc.pid) and self.uniq:
                        if isinstance(args[-1], dict):
                            context = args[-1]
                        spawn.hash_lock.release()
                        raise except_osv("Error",
                            _(u"Already running pid: %s by user: %s at: %s")
                            % (spawn_proc.pid, spawn_proc.user,
                               spawn_proc.startup)
                        )
                except psutil.NoSuchProcess:
                    pass
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', 0))
                child_port = sock.getsockname()[1]
                sock.listen(1)
                sock.shutdown(socket.SHUT_RDWR)
                user_obj = osv_object.pool.get('res.users')
                # Aquí hem de fer l'spawn
                env = os.environ.copy()
                env['SPAWNED'] = '1'
                command = sys.argv[:]
                command[0] = os.path.join(config['root_path'],
                                          'openerp-server.py')
                command += ['--port=%i' % child_port, '--no-netrpc',
                            '--update=False',
                            '--database=%s' % cursor.dbname,
                            '--logfile=%s' % tempfile.mkstemp()[1],
                            '--pidfile=%s' % os.devnull]

                start = datetime.now()
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO, 'Spawned '
                                     'new process: %s' % ' '.join(command))
                p = psutil.Popen(command, env=env)
                user = user_obj.browse(cursor, uid, uid).login
                name = user_obj.browse(cursor, uid, uid).name
                pwd = user_obj.browse(cursor, uid, uid).password
                uri = 'http://localhost'
                if config['secure']:
                    uri = 'https://localhost'
                is_listen = False
                timeout = int(os.getenv('SPAWN_OOP_TIMEOUT', 20))
                while not is_listen:
                    if timeout <= 0:
                        raise Exception(
                            _('Error timeout starting spawned instance.')
                        )
                    try:
                        OOOP(dbname=cursor.dbname, port=child_port, user=user,
                             pwd=pwd, uri=uri)
                        is_listen = True
                    except:
                        time.sleep(0.1)
                        timeout -= 0.1
                        is_listen = False
                startup = datetime.now() - start
                if self.uniq:
                    RUNNING_INSTANCES[hash_instance] = SpawnProc(p.pid, start,
                                                                 name)
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO,
                    'Server started in %s. PID: %s. Listening on %s. '
                    'Hash instance: %s ' % (startup, p.pid, child_port,
                                            hash_instance)
                )
                spawn.hash_lock.release()
                start = datetime.now()
                O = OOOP(dbname=cursor.dbname, port=child_port, user=user,
                         pwd=pwd, uri=uri)
                obj = Manager(osv_object._name, O)
                method = f.__name__
                newargs = args[3:]
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO,
                    'Calling %s.%s(%s)' % (
                        osv_object._name, method,
                        ', '.join([str(x) for x in newargs])
                    )
                )

                res = getattr(obj, method)(*newargs)
                duration = datetime.now() - start
                po = psutil.Process(p.pid)
                for child in po.get_children():
                    try:
                        child.kill()
                        child.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        child.send_signal(psutil.signal.SIGKILL)
                po.kill()
                po.wait()
                if self.uniq:
                    del RUNNING_INSTANCES[hash_instance]
                logger.notifyChannel('spawn_oop', netsvc.LOG_INFO, 'Server '
                                     'stopped. PID: %s. Duration %s.'
                                     % (p.pid, duration))
                return res
            else:
                return f(*args, **kwargs)
        return f_spawned
