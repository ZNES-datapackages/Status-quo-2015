# -*- coding: utf-8 -*-
"""
"""
import os
from datapackage import Package, Resource

descriptor = {}
descriptor['name'] = 'Status quo 2015'
descriptor['profile'] = 'tabular-data-package'

# create Package based on infer above
p = Package(descriptor)

for f in os.listdir('resources'):
    path = os.path.join('resources', f)

    r = Resource(path)

    p.add_resource(r.descriptor)

    p.commit()

p.save('datapackage.json')
