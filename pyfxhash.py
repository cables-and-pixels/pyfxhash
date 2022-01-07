#!/usr/bin/env python3

import sys, os, argparse, json, requests, logging, shutil

# from pprint import pprint

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
        print(item['generationHash'])

def images(gtid):
    for item in entire_collection(gtid, 'iteration metadata'):
        ipfsid = item['metadata']['displayUri'][7:]
        iteration = int(item['iteration'])
        url = f'https://gateway.fxhash.xyz/ipfs/{ipfsid}'
        filename = f'./{gtid:d}-{iteration:04d}.png'
        if os.path.exists(filename):
            continue
        request = requests.get(url, stream=True)
        if request.status_code == 200:
            request.raw.decode_content = True
            with open(filename, 'wb') as f:
                shutil.copyfileobj(request.raw, f)
            print(filename)

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--id', nargs='+', required=True,
                        help='Generative token ID(s)')
    parser.add_argument('--hashes', action='store_true', default=False,
                        help='Get hashes')
    parser.add_argument('--images', action='store_true', default=False,
                        help='Get images')
    args = parser.parse_args()

    if not args.hashes and not args.images:
        parser.print_help()
        sys.exit(1)

    for gtid in args.id:
        print('#', gtid)
        if args.hashes:
            hashes(gtid)
        if args.images:
            images(gtid)
