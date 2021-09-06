# -*- coding: utf-8 -*-

from __future__ import print_function
from genericpath import exists
import sys
import requests
from config import BASE_URL, AUTH_ENDPOINT

class User:
    """
        User object that contain his header 
    """
    username = ""
    password = ""
    # need to fill Authoritazion with current token provide by api
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        "Authorization":""
        }
    authorized = False
    tokenFilePath = None
    
    def __init__(self, username, password, tokenFileDir, useragent = None):
        self.username = username
        self.password = password
        self.tokenFilePath = tokenFileDir + 'tokencache.id'
        if useragent is not None:
            self.header["User-Agent"] = useragent

    def build_auth(self):
        if self.authorized == True:
            return
        
        self.header["Authorization"] = self.get_token()
        self.authorized = True
    
    def get_token(self, force = False):
        """
            Request auth endpoint and return user token  
        """
        if not force and self.tokenFilePath is not None and exists(self.tokenFilePath):
            f = open(self.tokenFilePath, "r")
            token = f.read()
            f.close()
            return token

        url = BASE_URL+AUTH_ENDPOINT
        # use json paramenter because for any reason they send user and pass in plain text :'(
        r = requests.post(url, json={'username':self.username, 'password':self.password})
        if r.status_code == 200:
            print("You are in!")
            token = 'Bearer ' + r.json()['data']['access']
            if self.tokenFilePath is not None:
                print("saving token")
                f = open(self.tokenFilePath, "w")
                f.write(token)
                f.close()
            return token
    
        # except should happend when user and pass are incorrect 
        print("Error login,  check user and password")
        print("Status code {}".format(r.status_code))
        sys.exit(2)

    def get_header(self):
        return self.header

    def refresh_header(self):
        """
            Refresh jwt because it expired and returned
        """
        self.header["Authorization"] = self.get_token(True)

        return self.header

