# -*- coding: utf-8 -*-
# Description: smart home power monitor
# Author: Moltenkore
# SPDX-License-Identifier: GPL-3.0-or-later

from bases.FrameworkServices.SimpleService import SimpleService
from pyHS100 import Discover
from threading import Thread, Lock

priority = 90000
update_every = 1

# Discovery new devices every 10 minutes
DISCOVERY_INTERVAL = 10 * 60
LOCK = Lock()

ORDER = [
    'current',
    'voltage',
    'power',
    'total'
]

CHARTS = {
    'current': {
        'options': [None, 'Current', 'amps', 'devices', 'smartplugpower.current', 'line'],
        'lines': [
            # ['current', 'apms', 'absolute', 1, 1000]
        ]
    },

    'voltage': {
        'options': [None, 'Voltage', 'volts', 'devices', 'smartplugpower.voltage', 'line'],
        'lines': [
            # ['voltage', 'volts', 'absolute', 1, 1000]
        ]
    },

    'power': {
        'options': [None, 'Power', 'watts', 'devices', 'smartplugpower.power', 'line'],
        'lines': [
            # ['power', 'watts', 'absolute', 1, 1000]
        ]
    },

}

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


def get_all_emeters(devices):
    arr = []
    for device in devices:
        device = devices.get(device)
        if (device.has_emeter):
            arr.append(device)
    return arr


def update_chart(obj, chart_name, dim_id, option, device, device_data, data):
    if dim_id not in obj.charts[chart_name]:
        obj.charts[chart_name].add_dimension([dim_id, "{0} ({1})".format(device.alias, device.host), 'absolute', 1, 1000])
    data[dim_id] = device_data.get(option) * 1000
    return data


def do_discovery(obj):
    obj.devices = Discover.discover()
    LOCK.acquire()
    obj.emeters = get_all_emeters(obj.devices)
    LOCK.release()


def do_async_discovery(obj):
    thread = Thread(target=do_discovery, args=[obj])
    thread.daemon = True
    thread.start()


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.fake_name = 'Power'
        self.order = ORDER
        self.definitions = CHARTS
        self.checked = False
        do_discovery(self)

    def check(self):
        if len(self.devices.keys()) < 1:
            self.error('No devices found.')
            return False
        if len(self.emeters) < 1:
            self.error('No devices with emeters found.')
            return False
        self.checked = True
        return True

    def get_data(self):
        if self.checked and self.runs_counter % DISCOVERY_INTERVAL == 0:
            do_async_discovery(self)

        data = dict()

        LOCK.acquire()
        if len(self.emeters) > 0:
            for device in self.emeters:
                try:
                    rt = device.get_emeter_realtime()
                    dim_id = device.host

                    update_chart(self, 'current', dim_id + '_current', 'current', device, rt, data)
                    update_chart(self, 'voltage', dim_id + '_voltage', 'voltage', device, rt, data)
                    update_chart(self, 'power', dim_id + '_power', 'power', device, rt, data)
                except Exception as e:
                    self.error('Something went wrong: ' + str(e))
                    do_discovery(self)
        LOCK.release()
        return data
