# -*- coding: utf-8 -*-
# Description: smart home power monitor
# Author: Moltenkore
# SPDX-License-Identifier: GPL-3.0-or-later

from bases.FrameworkServices.SimpleService import SimpleService
from pyHS100 import Discover, EmeterStatus
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
        'options': [None, 'Power', 'watts', 'devices', 'smartplugpower.power', 'area'],
        'lines': [
            # ['power', 'watts', 'absolute', 1, 1000]
        ]
    },

    'total': {
        'options': [None, 'Total consumed', 'watt-hours', 'devices', 'smartplugpower.total', 'line'],
        'lines': [
            # ['total', 'watt-hours', 'absolute', 1, 1]
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


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.fake_name = 'Power'
        self.order = ORDER
        self.definitions = CHARTS
        self.checked = False
        self.config_devices = configuration.get('devices')
        self.devices = None
        self.emeters = None
        self.do_discovery()

    def do_discovery(self):
        devices = {}
        if self.config_devices:
            for host in self.config_devices:
                try:
                    device = Discover.discover_single(host)
                    if device:
                        devices[host] = device
                except Exception as e:
                    self.error('`discover_single()` has failed for {}: {}'.format(host, str(e)))
        else:
            try:
                devices = Discover.discover()
            except Exception as e:
                self.error('`discover()` has failed: ' + str(e))

        LOCK.acquire()
        self.devices = devices
        if self.devices:
            self.emeters = []
            for device in self.devices.values():
                try:
                    if device.has_emeter:
                        self.emeters.append(device)
                except Exception as e:
                    self.error('`has_emeter()` has failed for {}: {}'.format(device.host, str(e)))
        LOCK.release()

    def do_async_discovery(self):
        thread = Thread(target=self.do_discovery)
        thread.daemon = True
        thread.start()

    def check(self):
        if not self.devices:
            self.error('No devices found.')
        elif not self.emeters:
            self.error('No devices with emeters found.')
        else:
            self.checked = True

        return self.checked

    def update_chart(self, chart_data, measured_value, device, device_data):
        chart_name = measured_value.split('_')[0]
        divisor = (1, 1000)[measured_value.split('_')[-1][0] == 'm']
        dim_id = '{}_{}'.format(device.host, chart_name)
        friendly_hostname = '{} ({})'.format(device.alias, device.host)

        if dim_id not in self.charts[chart_name]:
            self.charts[chart_name].add_dimension([dim_id, friendly_hostname, 'absolute', 1, divisor])

        chart_data[dim_id] = device_data[measured_value]

    def get_data(self):
        if self.checked and (self.runs_counter * self.update_every) % DISCOVERY_INTERVAL < self.update_every and self.config_devices is None:
            self.do_async_discovery()

        LOCK.acquire()
        if not self.emeters:
            LOCK.release()
            self.do_discovery()
        else:
            LOCK.release()

        chart_data = {}
        LOCK.acquire()
        for emeter in self.emeters:
            try:
                emeter_data = EmeterStatus(emeter.get_emeter_realtime())

                self.update_chart(chart_data, 'current_ma', emeter, emeter_data)
                self.update_chart(chart_data, 'voltage_mv', emeter, emeter_data)
                self.update_chart(chart_data, 'power_mw',   emeter, emeter_data)
                self.update_chart(chart_data, 'total_wh',   emeter, emeter_data)
            except Exception as e:
                self.error('`get_emeter_realtime()` has failed for {}: {}'.format(emeter.host, str(e)))
        LOCK.release()

        return chart_data
