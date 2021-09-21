# -*- coding: utf-8 -*-
#!/usr/bin/python

from __future__ import print_function
import os
import os.path
import sys
import glob
import math
import getopt
import requests
import json
from tqdm import tqdm, trange
from config import BASE_URL, PRODUCTS_ENDPOINT, URL_BOOK_TYPES_ENDPOINT, URL_BOOK_ENDPOINT
from user import User
from os import path


#TODO: I should do a function that his only purpose is to request and return data
def book_request(user, offset=0, limit=10, verbose=False):
    data = []
    url = BASE_URL + PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
    if verbose:
        print(url)
    r = requests.get(url, headers=user.get_header())
    data += r.json().get('data', [])

    return url, r, data

def get_books(user, offset=0, limit=10, is_verbose=False, is_quiet=False):
    '''
        Request all your books, return json with info of all your books
        Params
        ...
        header : str
        offset : int
        limit : int
            how many book wanna get by request
    '''
    # TODO: given x time jwt expired and should refresh the header, user.refresh_header()

    user.build_auth()

    url, r, data = book_request(user, offset, limit)

    if r.status_code != 200:
        return None

    print(f'You have {str(r.json()["count"])} books')
    print("Getting list of books...")

    if not is_quiet:
        pages_list = trange(r.json()['count'] // limit, unit='Pages')
    else:
        pages_list = range(r.json()['count'] // limit)
    for i in pages_list:
        offset += limit
        data += book_request(user, offset, limit, is_verbose)[2]
    return data

def get_books_from_cache(user, outdir, offset=0, limit=10, is_verbose=False, is_quiet=False):
    '''
        Request all your books from cache file, or downloads book list and saves to cache;
        return json with info of all your books
        Params
        ...
        header : str
        offset : int
        limit : int
            how many book wanna get by request
    '''
    cachefile = path.join(outdir, 'packt_cache_file.json')
    if path.exists(cachefile):
        print('loading book list from cache[{}]'.format(cachefile))
        with open(cachefile, 'r') as infile:
            return json.load(infile)
    else:
        print('cache file not found [{}]'.format(cachefile))
        cachedata = get_books(user, offset, limit, is_verbose, is_quiet)
        if cachedata is None:
            return None
        print('saving book list to cache')
        with open(cachefile, 'w') as outfile:
            json.dump(cachedata, outfile)
        return cachedata

def get_url_book(user, book_id, format='pdf'):
    '''
        Return url of the book to download
    '''
    
    url = BASE_URL + URL_BOOK_ENDPOINT.format(book_id=book_id, format=format)
    r = requests.get(url, headers=user.get_header())

    if r.status_code == 200: # success
        return r.json().get('data', '')

    elif r.status_code == 401: # jwt expired 
        user.refresh_header() # refresh token 
        get_url_book(user, book_id, format)  # call recursive 
    
    print('ERROR (please copy and paste in the issue)')
    print(r.json())
    print(r.status_code)
    return ''


def get_book_file_types(user, book_id):
    '''
        Return a list with file types of a book
    '''

    url = BASE_URL + URL_BOOK_TYPES_ENDPOINT.format(book_id=book_id)
    r = requests.get(url, headers=user.get_header())

    if  (r.status_code == 200): # success
        return r.json()['data'][0].get('fileTypes', [])
    
    elif (r.status_code == 401): # jwt expired 
        user.refresh_header() # refresh token 
        get_book_file_types(user, book_id, format)  # call recursive 
    
    print('ERROR (please copy and paste in the issue)')
    print(r.json())
    print(r.status_code)
    return []


# TODO: i'd like that this functions be async and download faster
def download_book(filename, url):
    '''
        Download your book
    '''
    print('Starting to download ' + filename)

    with open(filename, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')
        if total is None:
            f.write(response.content)
        else:
            total = int(total)
            # TODO: read more about tqdm
            for chunk in tqdm(r.iter_content(chunk_size=1024), total=math.ceil(total//1024), unit='KB', unit_scale=True):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
            print('Finished ' + filename)


def make_zip(filename):
    if filename[-4:] == 'code':
        os.replace(filename, filename[:-4] + 'zip')


def move_current_files(root, book):
    sub_dir = f'{root}/{book}'
    does_dir_exist(sub_dir)
    for f in glob.iglob(sub_dir + '.*'):
        try:
            os.rename(f, f'{sub_dir}/{book}' + f[f.index('.'):])
        except OSError:
            os.rename(f, f'{sub_dir}/{book}' + '_1' + f[f.index('.'):])
        except ValueError as e:
            print(e)
            print('Skipping')


def does_dir_exist(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            print(e)
            sys.exit(2)


def main(argv):
    # thanks to https://github.com/ozzieperez/packtpub-library-downloader/blob/master/downloader.py
    email = None
    password = None
    root_directory =  os.path.abspath('media')
    book_file_types = ['pdf', 'mobi', 'epub', 'code']
    separate = None
    verbose = None
    quiet = None
    ask = None
    list = None
    usecache = None
    productids = None
    useragent = None
    errorMessage = 'Usage: main.py [-e <email> -p <password>] [-d <directory>] [-b <book file types>] [-i <book productid>,...] [-u <user agent>] [-s] [-v|-q] [-a] [-l] [-c]'
    errorMessage += '\n-e -email            login email'
    errorMessage += '\n-p -pass             login password'
    errorMessage += '\n-d -directory        output directory for books and cache files'
    errorMessage += '\n-b -books            comma separated file tipes to download (pdf,mobi,epub,code)'
    errorMessage += '\n-i -productids       product ids to downlod, get from -list'
    errorMessage += '\n-u -useragent        downloader HTTP user agent'
    errorMessage += '\n-s -separate         separate each book into a deifferent directory'
    errorMessage += '\n-v -verbose          show debug info (incompatible with -quiet)'
    errorMessage += '\n-q -quiet            show minimal info (incompatible with -verbose)'
    errorMessage += '\n-a -ask              ask before downloading each book'
    errorMessage += '\n-l -list             list all books in you account'
    errorMessage += '\n-c -cache            use cached information (if it exists) instead of requesting from the website\n'

    # get the command line arguments/options
    try:
        opts, args = getopt.getopt(
            argv, 'e:p:d:b:i:u:svqalc',
            ['email=', 'pass=', 'directory=', 'books=',
             'productids=', 'useragent=', 'separate',
             'verbose', 'quiet', 'ask', 'list', 'cache'])
    except getopt.GetoptError:
        print(errorMessage)
        sys.exit(2)

    # hold the values of the command line options
    for opt, arg in opts:
        if opt in ('-e', '--email'):
            email = arg
        elif opt in ('-p', '--pass'):
            password = arg
        elif opt in ('-d', '--directory'):
            root_directory = os.path.expanduser(
                arg) if '~' in arg else os.path.abspath(arg)
        elif opt in ('-b', '--books'):
            book_file_types = arg.split(',')
        elif opt in ('-s', '--separate'):
            separate = True
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-q', '--quiet'):
            quiet = True
        elif opt in ('-a', '--ask'):
            ask = True
        elif opt in ('-l', '--list'):
            list = True
        elif opt in ('-c', '--cache'):
            usecache = True
        elif opt in ('-i', '--productids'):
            productids = arg.split(',')
        elif opt in ('-u', '--useragent'):
            useragent = arg

    if verbose and quiet:
        print("Verbose and quiet cannot be used together.")
        sys.exit(2)

    tokencachefile = root_directory + "/tokencache.id"

    # do we have the minimum required info?
    if (not email or not password) and usecache != True and not os.path.exists(tokencachefile):
        print(errorMessage)
        sys.exit(2)

    if verbose:
        print('email={}'.format(email))
        print('password={}'.format(password))
        print('root_directory={}'.format(root_directory))
        print('book_file_types={}'.format(book_file_types))
        print('separate={}'.format(separate))
        print('verbose={}'.format(verbose))
        print('quiet={}'.format(quiet))
        print('ask={}'.format(ask))
        print('list={}'.format(list))
        print('usecache={}'.format(usecache))
        print('productids={}'.format(productids))
        print('useragent={}'.format(useragent))

    # check if not exists dir and create
    does_dir_exist(root_directory)

    # create user with his properly header
    user = User(email, password, tokencachefile, useragent)

    # get all your books
    if usecache:
        books = get_books_from_cache(user, root_directory, is_verbose=verbose, is_quiet=quiet)
    else:
        books = get_books(user, is_verbose=verbose, is_quiet=quiet)

    if books is None:
        print("Failed to get books. Is cached authentication token expired?")
        print("(delete " + tokencachefile + " to renew)")
        return

    books_iter = books

    if list == True:
        for book in books_iter:
            if (productids is not None and book['productId'] not in productids):
                continue
            print('{}: {}'.format(book['productId'], book['productName']))
        exit(0)

    user.build_auth()

    print('Downloading books...')
    for book in books_iter:
        if (productids is not None and book['productId'] not in productids):
            continue

        if ask == True:
            response = ''
            while response != 'y' and response != 'n':
                response = input('Download "{}"? [y/n] '.format(book['productName']))
            if response == 'n':
                continue

        # get the different file type of current book
        file_types = get_book_file_types(user, book['productId'])
        for file_type in file_types:
            if file_type in book_file_types:  # check if the file type entered is available by the current book
                book_name = book['productName'].replace(' ', '_').replace('.', '_').replace(':', '_').replace('/','')
                if separate:
                    filename = f'{root_directory}/{book_name}/{book_name}.{file_type}'
                    move_current_files(root_directory, book_name)
                else:
                    filename = f'{root_directory}/{book_name}.{file_type}'
                # get url of the book to download
                url = get_url_book(user, book['productId'], file_type)
                if not os.path.exists(filename) and not os.path.exists(filename.replace('.code', '.zip')):
                    download_book(filename, url)
                    make_zip(filename)
                else:
                    if verbose:
                        tqdm.write(f'{filename} already exists, skipping.')


if __name__ == '__main__':
    main(sys.argv[1:])
