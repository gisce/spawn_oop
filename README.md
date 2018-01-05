### :warning: This module is replaced with the combination of [OORQ](https://github.com/gisce/oorq) and [Autoworker](https://github.com/gisce/autoworker) :warning:


# Spawn Open Object Processes

Spawns OpenERP instances for functions that consumes a lot of cpu.
You can lock calls to one instance only by `uniq` param.


# Requirements

Tested on OpenERP 5.0.X

 * psutil
 * Erppeek

# Example

```python
from spawn_oop import spawn


class ResPartner(osv.osv):
    """Inherit class from res.partner.
    """
    _inherit = 'res.partner'

    @spawn()
    def consumes_lot_of_cpu(self, cursor, uid, ids, context=None):
        """Some hard function.
        """
        y = 0
        for x in range(0, 10000000000):
            y += x
        return y

ResPartner()
```

When `ResPartner.consumes_lot_of_cpu()` is called, another OpenERP instance is 
started, then via xmlrpc we call `consumes_lot_of_cpu()` in that new instance,
so the main openerp process doesn't get overloaded.


# Example for `uniq`

```python
from spawn_oop import spawn


class ResPartner(osv.osv)
    """Inherit class from res.partner
    """
    _inherit = 'res.partner'

    @spawn(uniq=True)
    def consumes_lot_of_cpu(self, cursor, uid, ids, context=None):
        """Some hard function.
        """
        y = 0
        for x in range(0, 10000000000):
            y += x
        return y

ResPartner()
```

Now `consumes_lot_of_cpu()` is locked when is running.


