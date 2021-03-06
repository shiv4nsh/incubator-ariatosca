# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from aria import workflow

from .workflows import execute_operation_on_instance


@workflow
def execute_operation(
        context,
        graph,
        operation,
        operation_kwargs,
        allow_kwargs_override,
        run_by_dependency_order,
        type_names,
        node_ids,
        node_instance_ids,
        **kwargs):
    subgraphs = {}
    # filtering node instances
    filtered_node_instances = list(_filter_node_instances(
        context=context,
        node_ids=node_ids,
        node_instance_ids=node_instance_ids,
        type_names=type_names))

    if run_by_dependency_order:
        filtered_node_instances_ids = set(node_instance.id
                                          for node_instance in filtered_node_instances)
        for node_instance in context.node_instances:
            if node_instance.id not in filtered_node_instances_ids:
                subgraphs[node_instance.id] = context.task_graph(
                    name='execute_operation_stub_{0}'.format(node_instance.id))

    # registering actual tasks to sequences
    for node_instance in filtered_node_instances:
        node_instance_sub_workflow = execute_operation_on_instance(
            workflow_id=node_instance.id,
            context=context,
            graph=graph,
            node_instance=node_instance,
            operation=operation,
            operation_kwargs=operation_kwargs,
            allow_kwargs_override=allow_kwargs_override)
        subgraphs[node_instance.id] = node_instance_sub_workflow

    for _, node_instance_sub_workflow in subgraphs.items():
        graph.add_task(node_instance_sub_workflow)

    # adding tasks dependencies if required
    if run_by_dependency_order:
        for node_instance in context.node_instances:
            for relationship_instance in node_instance.relationship_instances:
                graph.dependency(source_task=subgraphs[node_instance.id],
                                 after=[subgraphs[relationship_instance.target_id]])


def _filter_node_instances(context, node_ids=(), node_instance_ids=(), type_names=()):
    for node_instance in context.node_instances:
        if ((not node_instance_ids or node_instance.id in node_instance_ids) and
                (not node_ids or node_instance.node.id in node_ids) and
                (not type_names or node_instance.node.type_hierarchy in type_names)):
            yield node_instance
