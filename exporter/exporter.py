#!/usr/bin/env python3

import http.server
import traceback
import sys
import time
import json
import urllib.request
import os
import logging


def get_config():
    '''Get configuration from ENV variables'''
    conf['url'] = 'https://api.statuspage.io/v1/pages/{}/components/{}'
   #conf['api_key'] = ''
    conf['log_level'] = 'INFO'
    conf['test_alerts_open'] = ''
    conf['test_alerts_close'] = ''
    conf['keys_to_exclude'] = list()
    env_lists_options = ['keys_to_exclude']
    for opt in env_lists_options:
        opt_val = os.environ.get(opt.upper())
        if opt_val:
            conf[opt] = opt_val.split()
    env_text_options = ['url', 'api_key', 'log_level', 'test_alerts_open', 'test_alerts_close']
    for opt in env_text_options:
        opt_val = os.environ.get(opt.upper())
        if opt_val:
            conf[opt] = opt_val
    conf['alert_to_statuspage_timeout'] = 10
    conf['main_loop_sleep_interval'] = 10
    conf['listen_port'] = 9647
    env_int_options = ['alert_to_statuspage_timeout', 'main_loop_sleep_interval', 'listen_port']
    for opt in env_int_options:
        opt_val = os.environ.get(opt.upper())
        if opt_val:
            conf[opt] = int(opt_val)

metrics = {
    'alertmanager_to_statuspage_up': {
        'help': '# HELP alertmanager_to_statuspage_up Health status. OK=1, Fail=0',
        'type': '# TYPE alertmanager_to_statuspage_up gauge',
        'value': 1,
    },
    'alertmanager_to_statuspage_errors_total': {
        'help': '# HELP alertmanager_to_statuspage_errors_total Number of errors',
        'type': '# TYPE alertmanager_to_statuspage_errors_total counter',
        'value': 0,
    },
}

def configure_logging():
    '''Configure logging module'''
    log = logging.getLogger(__name__)
    log.setLevel(conf['log_level'])
    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT)
    return log

class CustomHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    '''Create http server class'''
    def do_POST(self):
        '''Define reaction to http POST'''
        content_length = int(self.headers['Content-Length'])
        post_data_json = self.rfile.read(content_length)
        post_data = json.loads(post_data_json.decode('utf-8'))
        alert_to_statuspage(post_data)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

    def do_GET(self):
        if self.path == '/metrics':
            message = list()
            for metric in metrics:
                message.append(metrics[metric]['help'])
                message.append(metrics[metric]['type'])
                message.append('{} {}'.format(metric, metrics[metric]['value']))
            message = '\n'.join(message) + '\n'
        else:
            message = '<html><head><title>Custom Exporter</title></head><body><p>See /metrics</p></body></html>'
        message = message.encode()
        self.send_response(200)
        self.send_header('Content-Length', len(message))
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(message)

def create_allert_message(post_data):
    '''Convert web hook from alertmanager to statuspage data'''
    data_to_send = {
        'data': {
            'component': {
                'status': ''
            }
        }
    }
    log.debug('POST data: "{}"'.format(post_data))
    for alert in post_data['alerts']:
        if 'statuspage_page' not in alert['labels']:
            continue
        if 'statuspage_component' not in alert['labels']:
            continue
        data_to_send['component'] = alert['labels']['statuspage_component']
        data_to_send['page'] = alert['labels']['statuspage_page']
        if alert['status'] == 'firing':
            data_to_send['data']['component']['status'] = 'degraded_performance'
        elif alert['status'] == 'resolved':
            data_to_send['data']['component']['status'] = 'operational'
        else:
            log.error('Unknown alert status: {}'.format(alert['status']))
        log.debug('Data to push: "{}"'.format(data_to_send))
        return data_to_send

def alert_to_statuspage(post_data):
    '''Send alert message to statuspage'''
    data_to_send = create_allert_message(post_data)
    if not data_to_send:
        log.debug('No data to send')
        return
    url = conf['url'].format(data_to_send['page'], data_to_send['component'])
    url = 'https://api.statuspage.io/v1/pages/czvqghml1l09/components/r2zghv8rs17p'
    data = json.dumps(data_to_send['data']).encode('utf-8')
    method = 'PATCH'
    log.debug('HTTP request to URL: {} Method: {} Data: {}'.format(url, method, data))
    req = urllib.request.Request(url=url, method=method)
    req.add_header('Authorization', conf['api_key'])
    req.add_header('Content-Type', 'application/json')
   #log.debug('HTTP request to URL: {} Method: {} Data: {}'.format(url, method, data))
    response = urllib.request.urlopen(req, data, conf['alert_to_statuspage_timeout'])
    log.debug('HTTP code: {}, response: "{}"'.format(response.getcode(), response.read()))

def run(server_class=http.server.HTTPServer, handler_class=CustomHTTPRequestHandler):
    '''Run whole code'''
    server_address = ('', conf['listen_port'])
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ != 'main':
    conf = dict()
    get_config()
    log = configure_logging()
    log.debug('Config: "{}"'.format(conf))
    while True:
        try:
            run()
        except KeyboardInterrupt:
            break
        except:
            trace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            print(trace)
        time.sleep(conf['main_loop_sleep_interval'])
