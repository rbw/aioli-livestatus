# -*- coding: utf-8 -*-

from aioli import Package
from .service import LivestatusService

__version__ = '0.1.0'

export = Package(
    name='aioli-livestatus',
    description='Livestatus support for the Aioli framework',
    controllers=[],
    services=[LivestatusService],
)
