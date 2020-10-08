#!/usr/bin/env python3

import dns.resolver
import argparse
import queue
import requests
import threading, os
from colored import fg, bg, attr
from lib.output import *
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

can_i_take_over_xyz = {
    "Anima": "If this is your website and you've just created it, try refreshing in a minute",
    "AWS/S3": "The specified bucket does not exist",
    "Bitbucket": "Repository not found",
    "Campaign Monitor": "Trying to access your account?",
    "Cargo Collective": "Cargo Collective",
    "Digital Ocean": "Domain uses DO name serves with no records in DO",
    "Fastly": "Fastly error: unknown domain",
    "Fly.io": "404 Not Found",
    "Gemfury": "404: This page could not be found",
    "Ghost": "The thing you were looking for is no longer here, or never was",
    "Github": "There isn't a Github Pages site here",
    "HatenaBlog": "404 Blog is not found",
    "Help Juice": "We could not find what you're looking for",
    "Help Scout": "No settings were found for this company",
    "Heroku": "No such app",
    "Intercom": "Uh oh. That page doesn't exist",
    "JetBrains": "is not a registered InCloud YouTrack",
    "Kinsta": "No Site For Domain",
    "LaunchRock": "It looks like you may have taken a wrong turn somewhere. Don't worry...it happens to all of us",
    "Mashery": "Unrecognized domain",
    "Ngrok": "Tunnel *.ngrok.io not found",
    "Pantheon": "404 error unknown site!",
    "Pingdom": "This public report page has not been activated by the user",
    "Readme.io": "Project doesnt exist... yet!",
    "Shopify": "Sorry, this shop is currently unavailable",
    "SmartJobBoard": "This job board website is either expired or its domain name is invalid",
    "Strikingly": "page not found",
    "Surge.sh": "project not found",
    "Tumblr": "Whatever you were looking for doesn't currently exist at this address",
    "Tilda": "Please renew your subscription",
    "Uberflip": "Non-hub domain, The URL you've accessed does not provide a hub",
    "Unbounce": "The requested URL was not found on this server",
    "Uptimerobot": "page not found",
    "UserVoice": "This UserVoice subdomain is currently available!",
    "Webflow": "The page you are looking for doesn't exist or has been moved",
    "Wordpress": "Do you want to register",
    "Worksites": "Hello! Sorry, but the website you&rsquo;re looking for doesn&rsquo;t exist"
}

dns_names = {
    "Anima": ["animaapp"],
    "AWS/S3": ["aws", "s3"],
    "Bitbucket": ["bitbucket"],
    "Campaign Monitor": ["createsend"],
    "Cargo Collective": ["cargocollective", "cargo"],
    "Digital Ocean": ["digitalocean"],
    "Fastly": ["fastly"],
    "Fly.io": ["fly"],
    "Gemfury": ["gemfury", "furyns"],
    "Ghost": ["ghost"],
    "Github": ["github"],
    "HatenaBlog": ["hatena"],
    "Help Juice": ["helpjuice"],
    "Help Scout": ["helpscout", "helpscoutdocs"],
    "Heroku": ["heroku"],
    "Intercom": ["intercom"],
    "JetBrains": ["jetbrains"],
    "Kinsta": ["kinsta"],
    "LaunchRock": ["launchrock"],
    "Mashery": ["mashery"],
    "Microsoft Azure": ["microsoft", "azure", "windows", "cloudapp", "visualstudio"],
    "Ngrok": ["ngrok"],
    "Pantheon": [],
    "Pingdom": [],
    "Readme.io": [],
    "Shopify": [],
    "SmartJobBoard": ["smartjobboard"],
    "Strikingly": ["strikinglydns"],
    "Surge.sh": ["surge"],
    "Tumblr": [],
    "Tilda": [],
    "Uberflip": ["uberflip"],
    "Unbounce": ["unbouncepages"],
    "Uptimerobot": ["uptimerobot"],
    "UserVoice": [],
    "Webflow": ["webflow"],
    "Wordpress": ["wordpress"],
    "Worksites": [],
}

def init_args():
    parser = argparse.ArgumentParser('Find subdomain takeover')
    parser.add_argument('-i', metavar='--file-domain', required=True, help='List file domains')
    parser.add_argument('-t', metavar='--threads', type=int, default=100, help='default thread is 100')
    return parser.parse_args()

def get_cname(domain=''):
    cnames = []
    que = queue.Queue()
    que.put(domain)
    
    domain = domain.replace('https://','')
    domain = domain.replace('http://','')
    while que:
        origin = que.get()
        try:
            result = dns.resolver.query(origin, 'CNAME')
            for cname in result:
                cname = str(cname)
                cnames.append(cname)
                que.put(cname)
        except:
            break
    return cnames

def multi_thread(que_domain=None, len_domain=0, output=None):
    while not que_domain.empty():
        domain = que_domain.get()
        output.checking(domain, len_domain-que_domain.qsize(), len_domain)
        if ('http://' not in domain) and ('https://' not in domain):
            domain = 'http://'+domain
        try:
            resp = requests.get(domain, verify=False, timeout=10)
            for engine in can_i_take_over_xyz:
                if can_i_take_over_xyz[engine] in resp.text:
                    cnames = get_cname(domain)
                    if not cnames and not dns_names[engine]:
                        output.newLine(attr('reset')+domain+' - Engine: '+fg('red')+engine+attr('reset'))
                    elif cnames:
                        for dns_name in dns_names[engine]:
                            if dns_name in cnames:
                                output.newLine(attr('reset')+domain+' - Engine: '+fg('red')+engine+attr('reset'))
        except:
            pass

def main():
    args = init_args()
    output = CLIOutput()
    with open(args.i, 'r') as fp:
        domains = fp.read().split('\n')
        domains.remove('')
        que_domain = queue.Queue()
        [que_domain.put(domain) for domain in domains]
        num_domain = que_domain.qsize()
        print(num_domain)
        list_thread = []
        
        if args.t > num_domain:
            num_thread = num_domain
        else:
            num_thread = args.t

        for i in range(num_thread):
            t = threading.Thread(target=multi_thread, args=(que_domain, num_domain, output))
            t.start()
            list_thread.append(t)
        for t in list_thread:
            t.join()
    s=''
    print(s.ljust(os.get_terminal_size().columns - 1), end="\r")
        
if __name__ == '__main__':
    main()