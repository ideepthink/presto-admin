# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
product tests for presto-admin plugin commands
"""
from tests.product.base_product_case import BaseProductTestCase

TMP_JAR_PATH = '/opt/prestoadmin/pretend.jar'
STD_REMOTE_PATH = '/usr/lib/presto/lib/plugin/hive-cdh5/pretend.jar'


class TestPlugin(BaseProductTestCase):
    def setUp(self):
        super(TestPlugin, self).setUp()
        self.setup_cluster()
        self.install_presto_admin(self.cluster)

    def deploy_jar_to_master(self):
        self.cluster.write_content_to_host('A PRETEND JAR', TMP_JAR_PATH,
                                           self.cluster.master)

    def test_basic_add_jars(self):
        self.upload_topology()
        self.deploy_jar_to_master()
        # no plugin dir argument
        output = self.run_prestoadmin(
            'plugin add_jar %s hive-cdh5' % TMP_JAR_PATH)
        self.assertEqualIgnoringOrder(output, '')
        for host in self.cluster.all_hosts():
            self.assert_path_exists(host, STD_REMOTE_PATH)

        # supply plugin directory
        output = self.run_prestoadmin(
            'plugin add_jar %s hive-cdh5 /etc/presto/plugin' % TMP_JAR_PATH)
        self.assertEqual(output, '')
        for host in self.cluster.all_hosts():
            self.assert_path_exists(host,
                                    '/etc/presto/plugin/hive-cdh5/pretend.jar')

    def test_lost_coordinator(self):
        internal_bad_host = self.cluster.internal_slaves[0]
        bad_host = self.cluster.slaves[0]
        good_hosts = [self.cluster.internal_master,
                      self.cluster.internal_slaves[1],
                      self.cluster.internal_slaves[2]]
        topology = {'coordinator': internal_bad_host,
                    'workers': good_hosts}
        self.upload_topology(topology)
        self.cluster.stop_host(bad_host)
        self.deploy_jar_to_master()
        output = self.run_prestoadmin(
            'plugin add_jar %s hive-cdh5' % TMP_JAR_PATH)
        self.assertRegexpMatches(output, self.down_node_connection_error %
                                 {'host': internal_bad_host})
        self.assertEqual(len(output.splitlines()), self.len_down_node_error)
        for host in good_hosts:
            self.assert_path_exists(host, STD_REMOTE_PATH)

    def test_lost_worker(self):
        internal_bad_host = self.cluster.internal_slaves[0]
        bad_host = self.cluster.slaves[0]
        good_hosts = [self.cluster.internal_master,
                      self.cluster.internal_slaves[1],
                      self.cluster.internal_slaves[2]]
        topology = {'coordinator': self.cluster.internal_master,
                    'workers': self.cluster.internal_slaves}
        self.upload_topology(topology)
        self.cluster.stop_host(bad_host)
        self.deploy_jar_to_master()
        output = self.run_prestoadmin(
            'plugin add_jar %s hive-cdh5' % TMP_JAR_PATH)
        self.assertRegexpMatches(output, self.down_node_connection_error %
                                 {'host': internal_bad_host})
        self.assertEqual(len(output.splitlines()), self.len_down_node_error)
        for host in good_hosts:
            self.assert_path_exists(host, STD_REMOTE_PATH)