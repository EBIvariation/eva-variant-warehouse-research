#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import pymongo
import bson
import os
from bson.json_util import dumps


def mongo_replication_initiated(db):
    replication_status = {}
    try:
        replication_status = db.command("replSetGetStatus")
    except pymongo.errors.OperationFailure:
        return False, replication_status
    return replication_status[u'ok'] == 1.0, replication_status


def mongo_replication_set_initiate(data):
    replication_set_name, replication_set_members, port = data["replSetName"], data["replSetMembers"], data["port"]
    replication_set_members = replication_set_members.split(",")
    replication_set_first_member = replication_set_members[0]
    client = pymongo.MongoClient('mongodb://{0}:{1}/'.format(replication_set_first_member, port))
    db = client.admin

    already_initiated, result = mongo_replication_initiated(db)
    if already_initiated:
        return False, False, result

    members = [{"_id": i, "host": "{0}:{1}".format(replication_set_members[i], port)} for i in
               range(len(replication_set_members))]
    config = {"_id": replication_set_name, "members": members}
    replication_set_initiate_result = db.command("replSetInitiate", config)
    if replication_set_initiate_result[u'ok'] != 1.0:
        return True, False, repl_set_initiate_result

    replication_set_initiate_result = mongo_replication_initiated(db)
    client.close()

    return False, True, replication_set_initiate_result


def main():
    module_args = dict(state=dict(type='str', required=True), replSetName=dict(type='str', required=True),
                       replSetMembers=dict(type='str', required=True), port=dict(type='int', required=True))
    choice_map = {"initiated": mongo_replication_set_initiate}
    ansible_module = AnsibleModule(argument_spec=module_args)
    is_error, has_changed, result = choice_map.get(ansible_module.params['state'])(ansible_module.params)

    if not is_error:
        result = dict(msg="Successfully initiated", changed=has_changed, meta=dumps(result))
        ansible_module.exit_json(**result)
    else:
        result = dict(msg="Error initiating MongoDB replica set", meta=dumps(result))
        ansible_module.fail_json(**result)


if __name__ == '__main__':
    main()
