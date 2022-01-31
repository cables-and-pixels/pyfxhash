#!/usr/bin/env python3

import sys, os, argparse, json, requests, logging, shutil
from pprint import pprint

# Sample API explorer:
# https://studio.apollographql.com/sandbox/explorer

fxhash_endpoint = 'https://api.fxhash.xyz/graphql/'

def entire_collection(gtid, fields):
    query = f"""{{
        generativeToken(id: {gtid}) {{
            entireCollection {{ {fields} }}
        }}
    }}"""
    r = requests.post(fxhash_endpoint, json={'query': query})
    if r.status_code != 200:
        return
    result = json.loads(r.content)
    if result['data'] is None or \
       result['data']['generativeToken'] is None:
        return
    collection = result['data']['generativeToken']['entireCollection']
    for item in collection:
        yield item

def hashes(gtid):
    for item in entire_collection(gtid, 'generationHash'):
        yield item['generationHash']

def images(gtid):
    for item in entire_collection(gtid, 'metadata'):
        yield item['metadata']['displayUri'][7:]

def attributes(gtid):
    for item in entire_collection(gtid, 'metadata'):
        if 'attributes' in item['metadata']:
            yield { a['name']: a['value']
                    for a in item['metadata']['attributes'] }
        else:
            yield {}

def owners(gtid):
    for item in entire_collection(gtid, 'owner { id name }'):
        if 'owner' in item:
            yield [
                item['owner']['id'],
                item['owner']['name'] or ''
            ]
        else:
            yield []

def download_images(gtid):
    dirname = f'./images/{gtid:d}'
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    iteration = 0
    for ipfsid in images(gtid):
        iteration += 1
        url = f'https://gateway.fxhash.xyz/ipfs/{ipfsid}'
        filename = f'{dirname}/{gtid:d}-{iteration:04d}.png'
        if os.path.exists(filename):
            continue
        request = requests.get(url, stream=True)
        if request.status_code == 200:
            request.raw.decode_content = True
            with open(filename, 'wb') as f:
                shutil.copyfileobj(request.raw, f)
            print(filename)

def output(data, fmt='default'):
    _data = list(data)
    _data.reverse()
    if fmt == 'default':
        for line in _data:
            if isinstance(line, list):
                print(' '.join(line))
            else:
                print(line)
    elif fmt == 'json':
        print(json.dumps(_data))

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--id', nargs='+', required=True,
                        help='Generative token ID(s)')
    parser.add_argument('--hashes', action='store_true', default=False,
                        help='Get hashes')
    parser.add_argument('--images', action='store_true', default=False,
                        help='Get images ipfs ids')
    parser.add_argument('--attributes', action='store_true', default=False,
                        help='Get attributes')
    parser.add_argument('--owners', action='store_true', default=False,
                        help='Get owners')
    parser.add_argument('--download_images', action='store_true', default=False,
                        help='Download images')
    parser.add_argument('--format', action='store', default='default',
                        help='Output format')
    args = parser.parse_args()

    if not args.hashes and \
       not args.images and \
       not args.attributes and \
       not args.owners and \
       not args.download_images:
        parser.print_help()
        sys.exit(1)

    for gtid in args.id:
        gtid = int(gtid)
        print(f'##', gtid)
        data = None
        if args.hashes:
            print('# hashes')
            output(hashes(gtid), args.format)
        if args.images:
            print('# images')
            output(images(gtid), args.format)
        if args.attributes:
            print('# attributes')
            output(attributes(gtid), args.format)
        if args.owners:
            print('# owners')
            output(owners(gtid), args.format)
        if args.download_images:
            download_images(gtid)
