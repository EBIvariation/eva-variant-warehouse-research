#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import pymongo
import bson
import os
from bson.json_util import dumps


def mongo_add_shard(data):
    primary_query_router, query_router_port, shard_name = data["primaryQueryRouter"], data["queryRouterPort"], \
                                                          data["shardName"]
    client = pymongo.MongoClient('mongodb://{0}:{1}/'.format(primary_query_router, query_router_port))
    db = client.admin

    add_shard_result = db.command("addShard", shard_name)
    if add_shard_result[u'ok'] != 1.0:
        return True, False, add_shard_result

    client.close()

    return False, True, add_shard_result


def main():
    module_args = dict(state=dict(type='str', required=True), primaryQueryRouter=dict(type='str', required=True),
                       queryRouterPort=dict(type='str', required=True), shardName=dict(type='str', required=True))
    choice_map = {"added": mongo_add_shard}
    ansible_module = AnsibleModule(argument_spec=module_args)
    is_error, has_changed, result = choice_map.get(ansible_module.params['state'])(ansible_module.params)

    if not is_error:
        result = dict(msg="Shards successfully added", changed=has_changed, meta=dumps(result))
        ansible_module.exit_json(**result)
    else:
        result = dict(msg="Error adding shards", meta=dumps(result))
        ansible_module.fail_json(**result)


if __name__ == '__main__':
    main()
