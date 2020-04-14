# -*- coding: utf-8 -*-
import logging,json,os,fc2,requests

POST_HEADER = {
    "Content-Type": "application/json; charset=utf-8"
}

# set env var DINGTALK_ROBOT_TOKEN to enable dingtalk robot notification
def send_dingtalk_msg(msg_json, atMobiles=None, isAtAll=False):
    payload = msg_json
    if not atMobiles or not isAtAll:
        payload.update({
            "at": {
                "atMobiles": atMobiles,
                "isAtAll": isAtAll
            }
        })

    token = os.getenv('DINGTALK_ROBOT_TOKEN', '')
    if token == '':
        return

    DINGTALK_ROBOT_URL = "https://oapi.dingtalk.com/robot/send?access_token=%s" % token
    r = requests.post(DINGTALK_ROBOT_URL, data=json.dumps(msg_json), headers=POST_HEADER)
    return r

def send_dingtalk_text(text, atMobiles=None, isAtAll=False):
    payload = {
        "msgtype": "text",
        "text": {
            "content": text
        },
    }
    return send_dingtalk_msg(payload, atMobiles, isAtAll)

# payload format in event:
# '{"functions":[{"serviceName":"service", "qualifier":"prod", "functionName":"foo", "target":5}]}'
def handler(event, context):
    logger = logging.getLogger()
    logger.info('going to update provision event: %s' % event)

    ev = json.loads(event)
    payloadStr = ev.get("payload", '{"functions":[]}')
    payload = json.loads(payloadStr)

    client = fc2.Client(
        endpoint='https://%s.%s.fc.aliyuncs.com' % (context.account_id, context.region),
        accessKeyID=context.credentials.access_key_id,
        accessKeySecret=context.credentials.access_key_secret,
        securityToken=context.credentials.security_token
    )

    functions = payload.get("functions", [])
    request_id = context.request_id
    for func in functions:
        service_name = func.get("serviceName", None)
        qualifier = func.get("qualifier", None)
        function_name = func.get("functionName", None)
        target = func.get("target", None)

        func_info = "services/%s.%s/function/%s, target:%d" % (service_name, qualifier, function_name, target)
        logger.info("going to put_provision_config for %s" % func_info)

        try:
            client.put_provision_config(service_name, qualifier, function_name, target)
            logger.info("put_provision_config for %s successfully" % func_info)
            send_dingtalk_text("put_provision_config for %s successfully, requestID:%s" % (func_info, request_id))
        except:
            logger.error("failed to put_provision_config for %s" % func_info)
            send_dingtalk_text("failed to put_provision_config for %s, requestID:%s" % (func_info, request_id))

    return 'finished'

