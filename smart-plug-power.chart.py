# -*- coding: utf-8 -*-
# Description: smart home power monitor
# Author: Moltenkore
# SPDX-License-Identifier: GPL-3.0-or-later

from bases.FrameworkServices.SimpleService import SimpleService
from pyHS100 import Discover

priority = 90000
update_every = 1

ORDER = [
    'current',
    'voltage',
    'power',
    'total'
]

CHARTS = {
    'current': {
        'options': [None, 'Current', 'amps', 'devices', 'power.current', 'line'],
        'lines': [
            # ['current', 'apms', 'absolute', 1, 1000]
        ]
    },

    'voltage': {
        'options': [None, 'Voltage', 'volts', 'devices', 'power.voltage', 'line'],
        'lines': [
            # ['voltage', 'volts', 'absolute', 1, 1000]
        ]
    },

    'power': {
        'options': [None, 'Power', 'watts', 'devices', 'power.power', 'line'],
        'lines': [
            # ['power', 'watts', 'absolute', 1, 1000]
        ]
    },

}


def get_all_emeters(devices):
    arr = []
    for device in devices:
        device = devices.get(device)
        if (device.has_emeter):
            arr.append(device)
    return arr

# >>> d = Discover.discover()

# >>> d.keys()
# dict_keys(['10.1.1.239'])

# >>>plug = d.get("10.1.1.239")

# >>> plug.has_emeter
# True

# >>> plug.alias
# 'Server'

# >>> plug.get_emeter_realtime()
# {'current': 0.416283, 'voltage': 236.242586, 'power': 87.890383, 'total': 11.353}

# >>> plug.get_emeter_realtime().get("power")
# 87.715957


def update_chart(obj, chart_name, dim_id, option, device, device_data, data):
    if dim_id not in obj.charts[chart_name]:
        obj.charts[chart_name].add_dimension([dim_id, "{0} ({1})".format(device.alias, device.host), 'absolute', 1, 1000])
    data[dim_id] = device_data.get(option) * 1000
    return data


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.fake_name = 'Power'
        self.order = ORDER
        self.definitions = CHARTS
        self.devices = Discover.discover()
        self.emeters = get_all_emeters(self.devices)

    def check(self):
        if len(self.devices.keys()) < 1:
            self.error('No devices found.')
            return False
        if len(self.emeters) < 1:
            self.error('No devices with emeters found.')
            return False
        return True

    def get_data(self):
        data = dict()

        for device in self.emeters:
            rt = device.get_emeter_realtime()
            dim_id = device.host

            data = update_chart(self, 'current', dim_id + '_current', 'current', device, rt, data)
            data = update_chart(self, 'voltage', dim_id + '_voltage', 'voltage', device, rt, data)
            data = update_chart(self, 'power', dim_id + '_power', 'power', device, rt, data)

        return data
