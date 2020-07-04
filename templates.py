#!/usr/bin/env python3

from util import prompt, base64, ensure_dir, random_token
from jinja2 import Environment, FileSystemLoader
import subprocess
import shutil
import re
import os

dirname = os.path.dirname(__file__)
jinja_env.filters['b64encode'] = base64
clusters_dir = os.path.join(dirname, 'clusters')
template_dir = os.path.join(dirname, 'templates')
template_secrets_dir = os.path.join(template_dir, 'secrets')
jinja_env = Environment(loader=FileSystemLoader(template_dir))

data_node_configs = {
  'minikube': {
    'replicas': '2',
    'heap_size': '512m',
    'memory_limit': '1Gi',
    'storage_class': 'standard'
  },
  '4cpu X N': {
    'heap_size': '4g',
    'memory_limit': '8Gi',
    'storage_class': 'ssd'
  },
  '8cpu X N': {
    'heap_size': '8g',
    'memory_limit': '16Gi',
    'storage_class': 'ssd'
  },
  '16cpu X N': {
    'heap_size': '20g',
    'memory_limit': '40Gi',
    'storage_class': 'ssd'
  }
}

def check_cert_presence(cert_dir):
  files = ['ca.crt', 'ca.key', 'logstash.crt', 'logstash.key']
  for file in files:
    fname = os.path.join(cert_dir, file)
    if not os.path.isfile(fname):
      return False
  return True
