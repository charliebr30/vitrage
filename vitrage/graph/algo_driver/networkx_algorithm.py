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

from networkx.algorithms import components
from networkx.algorithms import simple_paths

from oslo_log import log as logging

from vitrage.graph.algo_driver.algorithm import GraphAlgorithm
from vitrage.graph.algo_driver.sub_graph_matching import subgraph_matching
from vitrage.graph.driver import Direction
from vitrage.graph.driver import NXGraph
from vitrage.graph.filter import check_filter
from vitrage.graph.query import create_predicate

LOG = logging.getLogger(__name__)


class NXAlgorithm(GraphAlgorithm):

    def __init__(self, graph):
        """Create a new GraphAlgorithm

        :param graph: graph instance
        :type graph: driver.Graph
        """
        super(NXAlgorithm, self).__init__(graph)

    def graph_query_vertices(self,
                             query_dict=None,
                             root_id=None,
                             depth=None,
                             direction=Direction.BOTH,
                             edge_query_dict=None):

        graph = NXGraph('graph')

        if not root_id:
            root_id = self.graph.root_id
        root_data = self.graph._g.node[root_id]

        if not query_dict:
            match_func = lambda item: True
        else:
            match_func = create_predicate(query_dict)

        if not edge_query_dict:
            edge_match_func = lambda item: True
        else:
            edge_match_func = create_predicate(edge_query_dict)

        if not match_func(root_data):
            LOG.info('graph_query_vertices: root %s does not match filter %s',
                     str(root_id), str(query_dict))
            return graph

        n_result = []
        visited_nodes = set()
        n_result.append(root_id)
        nodes_q = [(root_id, 0)]
        while nodes_q:
            node_id, curr_depth = nodes_q.pop(0)
            if (node_id in visited_nodes) or (depth and curr_depth >= depth):
                continue
            visited_nodes.add(node_id)
            (n_list, e_list) = self.graph._neighboring_nodes_edges_query(
                node_id,
                direction=direction,
                vertex_predicate=match_func,
                edge_predicate=edge_match_func)
            n_result.extend([v_id for v_id, data in n_list])
            nodes_q.extend([(v_id, curr_depth + 1) for v_id, data in n_list])

        graph._g = self.graph._g.subgraph(n_result)
        LOG.debug('graph_query_vertices: find graph: nodes %s, edges %s',
                  str(graph._g.nodes(data=True)),
                  str(graph._g.edges(data=True)))
        LOG.debug('graph_query_vertices: real graph: nodes %s, edges %s',
                  str(self.graph._g.nodes(data=True)),
                  str(self.graph._g.edges(data=True)))
        return graph

    def sub_graph_matching(self, subgraph, known_matches, validate=False):
        return subgraph_matching(self.graph, subgraph, known_matches, validate)

    def create_graph_from_matching_vertices(self,
                                            vertex_attr_filter=None,
                                            query_dict=None,
                                            edge_attr_filter=None):
        if query_dict:
            vertices = self.graph.get_vertices(query_dict=query_dict)
        elif vertex_attr_filter:
            vertices = self.graph.get_vertices(
                vertex_attr_filter=vertex_attr_filter)
        else:
            vertices = self.graph.get_vertices()

        vertices_ids = [vertex.vertex_id for vertex in vertices]

        graph = NXGraph('graph')
        graph._g = self.graph._g.subgraph(vertices_ids)

        # delete non matching edges
        if edge_attr_filter:
            for source, target, edge_data in graph._g.edges_iter(data=True):
                if not check_filter(edge_data, edge_attr_filter):
                    graph.remove_edge(u=source, v=target)

        LOG.debug('match query, find graph: nodes %s, edges %s',
                  str(graph._g.nodes(data=True)),
                  str(graph._g.edges(data=True)))
        LOG.debug('match query, real graph: nodes %s, edges %s',
                  str(self.graph._g.nodes(data=True)),
                  str(self.graph._g.edges(data=True)))
        return graph

    def subgraph(self, entities):
        subgraph = NXGraph('graph')
        subgraph._g = self.graph._g.subgraph(entities)
        return subgraph

    def connected_component_subgraphs(self, subgraph):
        return components.connected_component_subgraphs(
            subgraph._g.to_undirected(), copy=False)

    def all_simple_paths(self, source, target):
        return simple_paths.all_simple_paths(self.graph._g,
                                             source=source,
                                             target=target)
