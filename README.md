# netdata-pyHS100-module
A module for [Netdata](https://github.com/netdata/netdata) that probes emeter smartplugs for realtime power data.

Uses the [pyHS100](https://github.com/GadgetReactor/pyHS100) library.

![screenshot](screenshot.png)

# Requirements
- Netdata installed
- Python 3
- A compatible TP-Link Smart Plug with an E-Meter such as the HS110

# Installation for Ubuntu 18.04
1. Install the phHS100 library using ``pip install pyHS100``
2. Install some additional pip stuff ``pip install pytest pytest-cov voluptuous typing``
3. Download ``smart-plug-power.chart.py`` and put it into ``/usr/libexec/netdata/python.d/``
4. Restart netdata ``service netdata restart``
5. After a few refreshes you should see a ``Power`` section appear in Netdata.
