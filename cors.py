#!/usr/bin/python3

import argparse, os
import requests
from urllib.parse import urlparse
from colored import fg, bg, attr
import queue, threading
import urllib3
urllib3.disable_warnings()

DEBUG = False

def init_args():
    parse = argparse.ArgumentParser(description='CORS Checker')
    parse.add_argument('-u', metavar='domain', help='Domain check CORS')
    parse.add_argument('-i', metavar='list-url', help='List domain check CORS')
    parse.add_argument('-x', metavar='method', default='get', help='Method check CORS')
    parse.add_argument('-c', metavar='cookies', help='Ex: ssid=...;name=...')
    parse.add_argument('-H', metavar='HTTPS headers', help='Ex: header1: ...\\nheader1: ...')
    parse.add_argument('-p', metavar='<IP>:<PORT>', help='Ex: 127.0.0.1:8080')
    parse.add_argument('-r', metavar='Burp request', help='Read file Burp request')
    parse.add_argument('-t', metavar='number threads', type=int, default=100, help='')
    return parse.parse_args()

def create_origin(domain=''):
    url_struc = urlparse(domain)
    if not url_struc.netloc:
        return ''

    if not url_struc.scheme:
        scheme = 'http'
    else:
        scheme = url_struc.scheme
    # root_domain = url_struc.netloc.split('.')
    # root_domain = root_domain[-2]+'.'+root_domain[-1]
    root_domain = domain

    list_origin = []
    list_origin.append('null')
    # list_origin.append(scheme+'://'+'evil'+root_domain)
    # list_origin.append(scheme+'://'+'evil-'+root_domain)
    list_origin.append(root_domain+'evil')
    list_origin.append(root_domain+'-evil')
    list_origin.append(root_domain+'.evil')
    return list_origin

def cookies_parser(cookies_in=''):
    cookies = {}
    if cookies_in:
        cookies_in = cookies_in.split(';')
        if '' in cookies_in:
            cookies_in.remove('')
        for cookie in cookies_in:
            i = cookie.index('=')
            cookies[cookie[:i]] = cookie[i+1:]
    return cookies

def headers_parser(headers_in=''):
    headers = {}
    if headers_in:
        headers_in = headers_in.split('\\n')
        if '' in headers_in:
            headers_in.remove('')
        for header in headers_in:
            print(header)
            i = header.index(':')
            headers[header[:i]] = header[i+2:]
    return headers

def process_burp(file_in=''):
    if not os.path.isfile(file_in):
        exit(f'{file_in} not exists')

    with open(file_in, 'r') as fp:
        headers = {}
        data = {}
        method = ''

        data = fp.read()
        data = data.split('\n')
        method = data[0].split(' ')[0]
        payload = data[data.index('')+1:len(data)-1]

        for line in range(1, data.index('')):
            i = data[line].index(':')
            headers[data[line][:i]] = data[line][i+2:]
        domain = headers['Host']+data[0].split(' ')[1]

        if method == 'POST':
            payload = payload[0].split('&')
            for item in payload:
                i = item.index('=')
                data[item[:i]] = item[i+1:]
        return method, domain, headers, data

def check_cors(domain='', method=[], cookies='', headers='', data='', proxies=''):
    if 'http://' not in domain and 'https://' not in domain:
        domain = 'https://'+domain

    list_origin = create_origin(domain)
    # print(fg(33)+'[*] Check CORS Domain: '+fg(222)+domain+attr('reset'))
    for m in method:
        for origin in list_origin:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'
            headers['Origin'] = origin
            try:
                if m.upper() == 'GET':
                    resp = requests.get(domain, headers=headers, proxies=proxies, cookies=cookies, verify=False)
                if m.upper() == 'POST':
                    resp = requests.post(domain, headers=headers, proxies=proxies, cookies=cookies, verify=False)
                if m.upper() == 'PUT':
                    resp = requests.put(domain, headers=headers, proxies=proxies, cookies=cookies, verify=False)
                if m.upper() == 'DELETE':
                    resp = requests.delete(domain, headers=headers, proxies=proxies, cookies=cookies, verify=False)
                    
                if 'Access-Control-Allow-Origin' in resp.headers.keys():
                    if resp.headers['Access-Control-Allow-Origin'] == '*' or origin in resp.headers['Access-Control-Allow-Origin']:
                        if 'Access-Control-Allow-Credentials' in resp.headers.keys() and resp.headers['Access-Control-Allow-Credentials'] == 'true':
                            if resp.headers['Access-Control-Allow-Origin'] != '*':
                                print(f'{fg("violet")}|->{attr("reset")} Domain: {fg("yellow")+domain+attr("reset")} - Method: {fg(82)+m.upper()+attr("reset")} - Origin: {fg("red")+origin+attr("reset")}', end='')
                                print(f' - Allow Cookie: {fg("red")}True{attr("reset")}')
                        elif 'Access-Control-Allow-Credentials' not in resp.headers.keys() or resp.headers['Access-Control-Allow-Credentials'] != 'true':
                            print(f'{fg("violet")}|->{attr("reset")} Domain: {fg("yellow")+domain+attr("reset")} - Method: {fg(82)+m.upper()+attr("reset")} - Origin: {fg("red")+origin+attr("reset")}', end='')
                            print(f' - Allow Cookie: {fg(142)}False{attr("reset")}')
            except:
                pass


def multi_thread(list_domain, method=[], cookies='', headers='', data='', proxies=''):
    while not list_domain.empty():
        domain = list_domain.get()
        check_cors(domain=domain, method=method, cookies=cookies, headers=headers, data=data, proxies=proxies)


def main():
    args = init_args()
    args.x = [args.x]
    proxies = {}
    if args.p:
        proxies = {
            'http': 'http://'+args.p,
            'https': 'https://'+args.p
        }

    if args.u:
        check_cors(domain=args.u, method=args.x, cookies=cookies_parser(args.c), headers=headers_parser(args.H), proxies=proxies)
    elif args.r:
        method, domain, headers, data = process_burp(args.r)
        method = [method]
        check_cors(domain=domain, method=method, cookies=cookies_parser(args.c), headers=headers, data=data, proxies=proxies)
    elif args.i:
        if not os.path.isfile(args.i):
            exit(f'{args.i} is not file')

        with open(args.i, 'r') as fp:
            que = queue.Queue()
            data = fp.read()
            data = data.split('\n')
            [que.put(domain) for domain in data]

            num_thread = args.t
            if args.t > que.qsize():
                num_thread = que.qsize()

            for i in range(num_thread):
                t = threading.Thread(target=multi_thread, args=(que, args.x, cookies_parser(args.c), headers_parser(args.H), '', proxies, ))
                t.start()

if __name__ == '__main__':
    main()