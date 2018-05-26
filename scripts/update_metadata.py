# -*- coding: utf-8 -*-
"""
"""
import os
from datapackage import Package, Resource

p = Package()

for f in os.listdir('resources'):
    path = os.path.join('resources', f)

    r = Resource(path)

    p.add_resource(r.descriptor)

    p.commit()

p.save('datapackage.json')
