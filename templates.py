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

def prompt_for_logstash_certs(context, cert_dir):
  if check_cert_presence(cert_dir):
    print(f"Using keys and certs for Logstash found in {cert_dir}.")
    context['skip_logstash'] = False
  else:
    do_logstash = prompt("Would you like to set up Logstash (with SSL beats input)? (Y/n)",
      "^[yYnN]?$"
    )
    if do_logstash and do_logstash.lower() != 'y':
      context['skip_logstash'] = True
      return
    else:
      context['skip_logstash'] = False
    print("Provide the following information to generate self-signed certificates: ")
    ca_name = prompt("Certificate Authority Name", default='Logstash CA')
    url = prompt("CN - Common Name for Logstash",
      regex='^[a-zA-Z.-0-9]+$',
      default='logstash.my-domain.com'
    )
    country = prompt("C - Country Code",
      regex='[A-Z]{1,4}',
      default='BR'
    )
    state = prompt("ST - State",
      regex='[A-Z]{1,4}',
      default='SP'
    )
    loc = prompt("L - Location",
      regex='[A-Za-z 0-9-_.]+',
      default='Santos'
    )
    org = prompt("O - Org",
      regex='[A-Za-z 0-9-_.]+',
      default='Acme'
    )
    org_unit = prompt("OU - Org Unit",
      regex='[A-Za-z 0-9-_.]+',
      default='Computers'
    )
    ensure_dir(os.path.join(cert_dir,'afile'))
    subprocess.run([
      os.path.join(dirname, 'templates', '6_logstash', 'ssl-gen.sh'),
      ca_name, url, country, state, loc, org, org_unit, cert_dir
    ], check=True)
    if not check_cert_presence(cert_dir):
      raise RuntimeError('certs failed to generate')
  try:
    shutil.rmtree(template_secrets_dir)
  except:
    pass
  shutil.copytree(cert_dir, template_secrets_dir)
  context['logstash_beats_port'] = '8751'

def prompt_for_oauth_config(context):
  do_oauth = prompt("Would you like to configure oauth2_proxy to authorize a GitHub team??? (y/N)",
    "^[yYnN]?$"
  )
  if not do_oauth or do_oauth.lower() != 'y':
    context['skip_oauth'] = True
    return
  else:
    context['skip_oauth'] = False
    context['github_org'] = prompt('Enter the GitHub org', '^[a-z0-9-_]+$')
    context['github_team'] = prompt('Enter the GitHub team (optional)', '^[a-z0-9-_]*$')
    context['oauth_client_id'] = prompt('Enter the OAuth Client ID', '^[a-z0-9-]+$')
    context['oauth_client_secret'] = prompt('Enter the OAuth Client Secret', '^[a-z0-9-]+$')
    context['oauth_cookie_name'] = '_ghoauth'
    context['oauth_cookie_secret'] = random_token()
    context['ssl_crt'] = prompt('Enter the path to the SSL certificate', readFile=True)
    context['ssl_key'] = prompt('Enter the path to the SSL private key', readFile=True)

def do_prompts():
  context = {}
  context['namespace'] = prompt(
    'Enter with your kubernetes namespace for the elasticsearch cluster',
    '^[a-z][-a-z0-9]{1,19}$',
    'default'
  )
  context['cluster_name'] = prompt(
    'Enter with your name for the elasticsearch cluster',
    '^[a-z][-a-z0-9]{1,19}$',
    'my-es-cluster'
  )
  print('Select the node size: ')
  for i, key in enumerate(data_node_configs):
    print(f'{i+1}: {key}')
  config_count = len(data_node_configs)  # Will break regex if > 9 configs
  node_size_choice = int(prompt(
    f'[1-{config_count}]: ',
    f'^[1-{config_count}]$',
    '2'
  ))
  context['data_node'] = data_node_configs[list(data_node_configs.keys())[node_size_choice-1]]
  if node_size_choice != 1:
    context['data_node']['replicas'] = int(prompt(
      'Enter the number of nodes (2-9)',
      '^[2-9]$',
      '2'
    ))
  context['data_node']['volume_size'] = prompt(
    'Enter the data volume size in GB [10-9999]',
    '^[1-9][0-9]{1,3}$',
    '250'
  )
  prompt_for_logstash_certs(context, os.path.join(clusters_dir, context['namespace'], "logstash-ssl-keys"))
  prompt_for_oauth_config(context)
  return context

def main():
  print('These scripts will create configuration files to set up an Elasticsearch cluster in Kubernetes.')

  context = do_prompts()
  cluster_dir = os.path.join(clusters_dir, context['namespace'])
  do_logstash = '' if context['skip_logstash'] else '6'
  do_oauth_proxy = '' if context['skip_oauth'] else '7'
  for template in jinja_env.list_templates(filter_func=(lambda x:re.match(f'^[1-5{do_logstash}{do_oauth_proxy}]_.+\.yml$', x))):
    if context['namespace'] is 'default' and template.endswith('/namespace.yml'):
      continue
    if context['data_node']['storage_class'] is 'standard' and template.endswith('-storage.yml'):
      continue
    output = jinja_env.get_template(template).render(context)
    out_path = os.path.join(cluster_dir, template)
    ensure_dir(out_path)
    with open(out_path, 'w') as output_file:
      print(output, file=output_file)
  try:
    shutil.rmtree(template_secrets_dir)
  except:
    pass
  print('\nSuccessfully generated cluster files. :D')
  print(f'configuration files have been saved to => {cluster_dir}')

if __name__ == "__main__":
  main()
