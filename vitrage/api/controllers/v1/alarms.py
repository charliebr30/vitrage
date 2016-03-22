# Copyright 2016 - Nokia Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import pecan

from oslo_log import log
from pecan.core import abort

from vitrage.api.controllers.rest import RootRestController
from vitrage.api.policy import enforce
# noinspection PyProtectedMember
from vitrage.i18n import _LI


LOG = log.getLogger(__name__)


class AlarmsController(RootRestController):

    @pecan.expose('json')
    def index(self, vitrage_id=None):
        return self.post(vitrage_id)

    @pecan.expose('json')
    def post(self, vitrage_id):
        enforce("list alarms", pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received list alarms with vitrage id %s') %
                 vitrage_id)

        try:
            if pecan.request.cfg.use_mock_file:
                return self.get_mock_data('alarms.sample.json')
            else:
                return self.get_alarms(vitrage_id)
        except Exception as e:
            LOG.exception('failed to get alarms %s', e)
            abort(404, str(e))

    @staticmethod
    def get_alarms(vitrage_id=None):
        alarms_json = pecan.request.client.call(pecan.request.context,
                                                'get_alarms',
                                                arg=vitrage_id)
        LOG.info(alarms_json)

        try:
            alarms_list = json.loads(alarms_json)['alarms']
            return alarms_list

        except Exception as e:
            LOG.exception('failed to open file %s ', e)
            abort(404, str(e))
