# -*- coding: utf-8 -*-

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
test_delete_server
----------------------------------

Tests for the `delete_server` command.
"""

import mock
from novaclient import exceptions as nova_exc

from shade import OpenStackCloud
from shade.tests.unit import base


class TestDeleteServer(base.TestCase):

    def setUp(self):
        super(TestDeleteServer, self).setUp()
        self.cloud = OpenStackCloud("cloud", {})

    @mock.patch('shade.OpenStackCloud.nova_client')
    def test_delete_server(self, nova_mock):
        """
        Test that novaclient server delete is called when wait=False
        """
        server = mock.MagicMock(id='1234',
                                status='ACTIVE')
        server.name = 'daffy'
        nova_mock.servers.list.return_value = [server]
        self.cloud.delete_server('daffy', wait=False)
        nova_mock.servers.delete.assert_called_with(server=server)

    @mock.patch('shade.OpenStackCloud.nova_client')
    def test_delete_server_already_gone(self, nova_mock):
        """
        Test that we return immediately when server is already gone
        """
        nova_mock.servers.list.return_value = []
        self.cloud.delete_server('tweety', wait=False)
        self.assertFalse(nova_mock.servers.delete.called)

    @mock.patch('shade.OpenStackCloud.nova_client')
    def test_delete_server_already_gone_wait(self, nova_mock):
        self.cloud.delete_server('speedy', wait=True)
        self.assertFalse(nova_mock.servers.delete.called)

    @mock.patch('shade.OpenStackCloud.nova_client')
    def test_delete_server_wait_for_notfound(self, nova_mock):
        """
        Test that delete_server waits for NotFound from novaclient
        """
        server = mock.MagicMock(id='9999',
                                status='ACTIVE')
        server.name = 'wily'
        nova_mock.servers.list.return_value = [server]

        def _delete_wily(*args, **kwargs):
            self.assertIn('server', kwargs)
            self.assertEqual('9999', kwargs['server'].id)
            nova_mock.servers.list.return_value = []

            def _raise_notfound(*args, **kwargs):
                self.assertIn('server', kwargs)
                self.assertEqual('9999', kwargs['server'].id)
                raise nova_exc.NotFound(code='404')
            nova_mock.servers.get.side_effect = _raise_notfound

        nova_mock.servers.delete.side_effect = _delete_wily
        self.cloud.delete_server('wily', wait=True)
        nova_mock.servers.delete.assert_called_with(server=server)
