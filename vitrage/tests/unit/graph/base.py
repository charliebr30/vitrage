# Copyright 2016 - Alcatel-Lucent
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

"""
test_vitrage graph
----------------------------------

Tests for `vitrage` graph driver
"""

import random
import time

from oslo_log import log as logging

from vitrage.common.constants import EdgeLabel as ELabel
from vitrage.common.constants import EntityCategory
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.datasources.static_physical import SWITCH
from vitrage.graph import create_graph
from vitrage.graph import utils as graph_utils
from vitrage.tests import base

LOG = logging.getLogger(__name__)

ENTITY_GRAPH_HOSTS_PER_CLUSTER = 8
ENTITY_GRAPH_VMS_PER_HOST = 8
ENTITY_GRAPH_ALARMS_PER_HOST = 8
ENTITY_GRAPH_TESTS_PER_HOST = 20
ENTITY_GRAPH_ALARMS_PER_VM = 8

RESOURCE = EntityCategory.RESOURCE
ALARM = EntityCategory.ALARM

TEST = 'TEST'
ALARM_ON_VM = 'ALARM_ON_VM'
ALARM_ON_HOST = 'ALARM_ON_HOST'
TEST_ON_HOST = 'TEST_ON_HOST'

v_node = graph_utils.create_vertex(
    vitrage_id=EntityCategory.RESOURCE + ':' + OPENSTACK_CLUSTER,
    entity_id='111111111111',
    entity_type=OPENSTACK_CLUSTER,
    entity_category=RESOURCE)
v_host = graph_utils.create_vertex(
    vitrage_id=NOVA_HOST_DATASOURCE + '222222222222',
    entity_id='222222222222',
    entity_type=NOVA_HOST_DATASOURCE,
    entity_category=RESOURCE)
v_instance = graph_utils.create_vertex(
    vitrage_id=NOVA_INSTANCE_DATASOURCE + '333333333333',
    entity_id='333333333333',
    entity_type=NOVA_INSTANCE_DATASOURCE,
    entity_category=RESOURCE)
v_alarm = graph_utils.create_vertex(
    vitrage_id=ALARM + '444444444444',
    entity_id='444444444444',
    entity_type=ALARM_ON_VM,
    entity_category=ALARM)
v_switch = graph_utils.create_vertex(
    vitrage_id=SWITCH + '1212121212',
    entity_id='1212121212',
    entity_type=SWITCH,
    entity_category=RESOURCE)

e_node_to_host = graph_utils.create_edge(
    source_id=v_node.vertex_id,
    target_id=v_host.vertex_id,
    relationship_type=ELabel.CONTAINS,
    update_timestamp='123')

e_node_to_switch = graph_utils.create_edge(
    source_id=v_node.vertex_id,
    target_id=v_switch.vertex_id,
    relationship_type=ELabel.CONTAINS)


def add_connected_vertex(graph, entity_type, entity_subtype, entity_id,
                         edge_type, other_vertex, reverse=False):
    vertex = graph_utils.create_vertex(
        vitrage_id=entity_subtype + str(entity_id),
        entity_id=entity_id,
        entity_category=entity_type,
        entity_type=entity_subtype)
    edge = graph_utils.create_edge(
        source_id=other_vertex.vertex_id if reverse else vertex.vertex_id,
        target_id=vertex.vertex_id if reverse else other_vertex.vertex_id,
        relationship_type=edge_type)
    graph.add_vertex(vertex)
    graph.add_edge(edge)
    return vertex


def rand_vertex_id(entity_type, items_count, max_id):
    random_vm_entity_id = random.randint(
        max_id - items_count, max_id - 1)
    vertex_id = entity_type + str(random_vm_entity_id)
    return vertex_id


class GraphTestBase(base.BaseTest):

    def __init__(self, *args, **kwds):
        super(GraphTestBase, self).__init__(*args, **kwds)

        self.vm_id = 10000000
        self.vm_alarm_id = 30000000
        self.vms = []
        self.host_alarm_id = 20000000
        self.host_test_id = 40000000
        self.entity_graph = self._create_entity_graph(
            'entity_graph',
            num_of_hosts_per_node=ENTITY_GRAPH_HOSTS_PER_CLUSTER,
            num_of_vms_per_host=ENTITY_GRAPH_VMS_PER_HOST,
            num_of_alarms_per_host=ENTITY_GRAPH_ALARMS_PER_HOST,
            num_of_alarms_per_vm=ENTITY_GRAPH_ALARMS_PER_VM,
            num_of_tests_per_host=ENTITY_GRAPH_TESTS_PER_HOST)

    def _assert_set_equal(self, d1, d2, message):
        super(GraphTestBase, self).assert_dict_equal(
            dict.fromkeys(d1, 0), dict.fromkeys(d2, 0), message)

    def _create_entity_graph(self, name, num_of_alarms_per_host,
                             num_of_alarms_per_vm,
                             num_of_hosts_per_node,
                             num_of_vms_per_host,
                             num_of_tests_per_host):

        start = time.time()
        g = create_graph(name, EntityCategory.RESOURCE + ':' +
                         OPENSTACK_CLUSTER)
        g.add_vertex(v_node)
        g.add_vertex(v_switch)
        g.add_edge(e_node_to_switch)

        # Add Hosts
        for host_id in range(num_of_hosts_per_node):
            host_to_add = add_connected_vertex(g,
                                               RESOURCE,
                                               NOVA_HOST_DATASOURCE,
                                               host_id,
                                               ELabel.CONTAINS,
                                               v_node,
                                               True)

            g.add_edge(graph_utils.create_edge(host_to_add.vertex_id,
                                               v_switch.vertex_id, 'USES'))

            # Add Host Alarms
            for j in range(num_of_alarms_per_host):
                add_connected_vertex(g, ALARM, ALARM_ON_HOST,
                                     self.host_alarm_id, ELabel.ON,
                                     host_to_add)
                self.host_alarm_id += 1

            # Add Host Tests
            for j in range(num_of_tests_per_host):
                add_connected_vertex(g, TEST, TEST_ON_HOST, self.host_test_id,
                                     ELabel.ON, host_to_add)
                self.host_test_id += 1

            # Add Host Vms
            for j in range(num_of_vms_per_host):
                vm_to_add = add_connected_vertex(g,
                                                 RESOURCE,
                                                 NOVA_INSTANCE_DATASOURCE,
                                                 self.vm_id,
                                                 ELabel.CONTAINS,
                                                 host_to_add,
                                                 True)
                self.vm_id += 1
                self.vms.append(vm_to_add)

                # Add Instance Alarms
                for k in range(num_of_alarms_per_vm):
                    add_connected_vertex(g, ALARM, ALARM_ON_VM,
                                         self.vm_alarm_id, ELabel.ON,
                                         vm_to_add)
                    self.vm_alarm_id += 1

        end = time.time()
        LOG.debug('Graph creation took ' + str(end - start) +
                  ' seconds, size is: ' + str(len(g)))
        expected_graph_size = \
            2 + num_of_hosts_per_node + num_of_hosts_per_node * \
            num_of_alarms_per_host + num_of_hosts_per_node * \
            num_of_vms_per_host + num_of_hosts_per_node * \
            num_of_vms_per_host * num_of_alarms_per_vm + \
            num_of_tests_per_host * num_of_hosts_per_node
        assert expected_graph_size == len(g), 'Graph size'
        return g
