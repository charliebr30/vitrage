# Copyright 2016 - Nokia
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

from oslo_log import log as logging

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EventAction
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.alarm_properties import AlarmProperties as AlarmProps
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.host.transformer import HostTransformer
from vitrage.datasources.transformer_base import TransformerBase
from vitrage.datasources.zabbix.driver import ZabbixDriver
from vitrage.datasources.zabbix.properties import ZabbixProperties
from vitrage.datasources.zabbix.properties import ZabbixTriggerStatus
from vitrage.datasources.zabbix.transformer import ZabbixTransformer
from vitrage.tests import base
from vitrage.tests.mocks import mock_driver as mock_sync


LOG = logging.getLogger(__name__)


# noinspection PyProtectedMember
class ZabbixTransformerTest(base.BaseTest):

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.transformers = {}
        host_transformer = HostTransformer(cls.transformers)
        cls.transformers[NOVA_HOST_DATASOURCE] = host_transformer

    def test_extract_key(self):
        LOG.debug('Test get key from nova instance transformer')

        # Test setup
        spec_list = mock_sync.simple_zabbix_alarm_generators(host_num=1,
                                                             events_num=1)
        zabbix_alarms = mock_sync.generate_sequential_events_list(spec_list)
        transformer = ZabbixTransformer(self.transformers)
        event = zabbix_alarms[0]

        # Test action
        observed_key = transformer._create_entity_key(event)

        # Test assertions
        observed_key_fields = observed_key.split(
            TransformerBase.KEY_SEPARATOR)

        self.assertEqual(EntityCategory.ALARM, observed_key_fields[0])
        self.assertEqual(event[DSProps.SYNC_TYPE], observed_key_fields[1])
        self.assertEqual(event[ZabbixProperties.RESOURCE_NAME],
                         observed_key_fields[2])
        self.assertEqual(event[ZabbixProperties.DESCRIPTION],
                         observed_key_fields[3])

    def test_zabbix_alarm_transform(self):
        LOG.debug('Zabbix alarm transformer test: transform entity event')

        # Test setup
        spec_list = mock_sync.simple_zabbix_alarm_generators(host_num=4,
                                                             events_num=10)
        zabbix_alarms = mock_sync.generate_sequential_events_list(spec_list)

        # convert to correct status
        for alar in zabbix_alarms:
            alar[ZabbixProperties.STATUS] = \
                ZabbixDriver._status_mapping()[alar[ZabbixProperties.SEVERITY]]

        for alarm in zabbix_alarms:
            # Test action
            wrapper = ZabbixTransformer(self.transformers).transform(alarm)
            self._validate_vertex(wrapper.vertex, alarm)

            neighbors = wrapper.neighbors
            self.assertEqual(1, len(neighbors))
            neighbor = neighbors[0]

            # Right now we are support only host as a resource
            if neighbor.vertex[VProps.TYPE] == NOVA_HOST_DATASOURCE:
                self._validate_host_neighbor(neighbors[0], alarm)

            self._validate_action(alarm, wrapper)

    def _validate_action(self, alarm, wrapper):
        sync_mode = alarm[DSProps.SYNC_MODE]
        if sync_mode in (SyncMode.SNAPSHOT, SyncMode.UPDATE):
            if alarm[ZabbixProperties.STATUS] == 'OK':
                self.assertEqual(EventAction.DELETE_ENTITY, wrapper.action)
            else:
                self.assertEqual(EventAction.UPDATE_ENTITY, wrapper.action)
        else:
            self.assertEqual(EventAction.CREATE_ENTITY, wrapper.action)

    def _validate_vertex(self, vertex, event):

        self.assertEqual(EntityCategory.ALARM, vertex[VProps.CATEGORY])
        self.assertEqual(event[DSProps.SYNC_TYPE], vertex[VProps.TYPE])
        self.assertEqual(event[ZabbixProperties.DESCRIPTION],
                         vertex[VProps.NAME])

        event_status = event[ZabbixProperties.STATUS]

        if event_status == ZabbixTriggerStatus.OK:
            self.assertEqual(AlarmProps.INACTIVE_STATE,
                             vertex[VProps.STATE])
        else:
            self.assertEqual(AlarmProps.ACTIVE_STATE,
                             vertex[VProps.STATE])

        self.assertEqual(event_status, vertex[VProps.SEVERITY])

        self.assertFalse(vertex[VProps.IS_DELETED])
        self.assertFalse(vertex[VProps.IS_PLACEHOLDER])

    def _validate_host_neighbor(self, neighbor, event):

        host_vertex = neighbor.vertex

        key_fields = host_vertex.vertex_id.split(TransformerBase.KEY_SEPARATOR)

        self.assertEqual(EntityCategory.RESOURCE, key_fields[0])
        self.assertEqual(NOVA_HOST_DATASOURCE, key_fields[1])
        self.assertEqual(event[ZabbixProperties.RESOURCE_NAME], key_fields[2])

        self.assertFalse(host_vertex[VProps.IS_DELETED])
        self.assertTrue(host_vertex[VProps.IS_PLACEHOLDER])

        self.assertEqual(EntityCategory.RESOURCE, host_vertex[VProps.CATEGORY])
        self.assertEqual(event[ZabbixProperties.RESOURCE_NAME],
                         host_vertex[VProps.ID])
        self.assertEqual(NOVA_HOST_DATASOURCE, host_vertex[VProps.TYPE])

        edge = neighbor.edge
        self.assertEqual(EdgeLabel.ON, edge.label)

        alarm_key = \
            ZabbixTransformer(self.transformers)._create_entity_key(event)
        self.assertEqual(alarm_key, edge.source_id)
        self.assertEqual(host_vertex.vertex_id, edge.target_id)
