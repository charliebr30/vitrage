#!/usr/bin/env bash
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

export DEVSTACK_GATE_NEUTRON=1
export DEVSTACK_GATE_HEAT=1
export DEVSTACK_GATE_INSTALL_TESTONLY=1
export DEVSTACK_GATE_TEMPEST=1
export DEVSTACK_GATE_TEMPEST_NOTESTS=1
export KEEP_LOCALRC=1


if [ -z ${DEVSTACK_LOCAL_CONFIG+x} ]; then
    DEVSTACK_LOCAL_CONFIG="enable_plugin vitrage git://git.openstack.org/openstack/vitrage"
fi
DEVSTACK_LOCAL_CONFIG+=$'\nenable_plugin ceilometer git://git.openstack.org/openstack/ceilometer'
DEVSTACK_LOCAL_CONFIG+=$'\nenable_plugin aodh git://git.openstack.org/openstack/aodh'
DEVSTACK_LOCAL_CONFIG+=$'\ndisable_service ceilometer-alarm-evaluator,ceilometer-alarm-notifier'
DEVSTACK_LOCAL_CONFIG+=$'\ndisable_service n-net'

export DEVSTACK_LOCAL_CONFIG

if [ -z ${ENABLED_SERVICES+x} ]; then
    ENABLED_SERVICES=tempest
fi
ENABLED_SERVICES+=,q-svc,q-dhcp,q-meta,q-agt,q-l3
ENABLED_SERVICES+=,h-eng h-api h-api-cfn h-api-cw
ENABLED_SERVICES+=,vitrage-api,vitrage-graph
ENABLED_SERVICES+=,key,aodi-api,aodh-notifier,aodh-evaluator
ENABLED_SERVICES+=,ceilometer-alarm-evaluator,ceilometer-alarm-notifier
ENABLED_SERVICES+=,ceilometer-api
export ENABLED_SERVICES


GATE_DEST=$BASE/new
DEVSTACK_PATH=$GATE_DEST/devstack

cat > $DEVSTACK_PATH/local.conf <<EOF
[[post-config|\$NOVA_CONF]]
[DEFAULT]
notification_topics = notifications,vitrage_notifications
notification_driver = messagingv2

[[post-config|\$NEUTRON_CONF]]
[DEFAULT]
notification_topics = notifications,vitrage_notifications
notification_driver = messagingv2

[[post-config|\$CINDER_CONF]]
[DEFAULT]
notification_topics = notifications,vitrage_notifications
notification_driver = messagingv2

[[post-config|\$HEAT_CONF]]
[DEFAULT]
notification_topics = notifications,vitrage_notifications
notification_driver = messagingv2
policy_file = /etc/heat/policy.json-tempest

[[post-config|\$VITRAGE_CONF]]
[static_physical]
changes_interval = 5

[datasources]
snapshots_interval = 120
EOF

$GATE_DEST/devstack-gate/devstack-vm-gate.sh
