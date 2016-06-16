#!/usr/bin/python

from __future__ import print_function
from BeautifulSoup import BeautifulSoup
import json
from pprint import pprint
import sys, getopt
import re
import requests, requests.utils, pickle
from html2text import html2text
import urllib
import sys
import os
from urlparse import parse_qs, parse_qsl, urlparse
import json
import glob
import HTMLParser
import time
import getpass

html_parser = HTMLParser.HTMLParser()

def unescape(a):
    return html_parser.unescape(a).replace('&dsh;','-')

host = 'https://www.linkedin.com/'
reload(sys)
sys.setdefaultencoding('utf-8')

class linkedin_client():
    def __init__(self):
        self.csrfToken = None
        self.bcookie = None
        self.rs = requests.Session()
        try:
            with open('linkedin-session') as f:
                self.rs.cookies  = requests.utils.cookiejar_from_dict(pickle.load(f))
        except:
            pass
        if not 'bcookie' in self.rs.cookies:
            self.linkedin_login();

    def linkedin_login(self):
        mail=os.environ.get('LINKEDIN_LOGIN')
        if mail is None:
            mail = os.environ.get('EMAIL');
        if mail is None:
            mail = raw_input("E-mail for linkedin login: ")
        pw = getpass.getpass('Password for ' + mail + ' on ' + host + ' >');
        self.rs.get(host);
        self.bcookie = re.search('.*v=2\&([^"]+)', self.rs.cookies['bcookie']).group(1)
        resp = self.rs.post(host + 'uas/login-submit',
                allow_redirects=False,
                headers = {'Content-Type': 'application/x-www-form-urlencoded' },
                data = {'session_key': mail, 'session_password': pw, 'loginCsrfParam': self.bcookie}
                )
        #print(resp.status_code)
        assert(resp.status_code == 302)
        resp = self.rs.get(host);
        # ozidentity-templates/identity-content
        open('login.html', 'w').write(resp.content)
        soup = BeautifulSoup(resp.content)
        identity = soup.find('code', { 'id': 'ozidentity-templates/identity-content'})
        if identity is None:
            print("Login failed");
            return
        with open('linkedin-session', 'w') as f:
            pickle.dump(requests.utils.dict_from_cookiejar(self.rs.cookies), f)
        data = json.loads(identity.getText())
        print("Welcome", data["member"]["name"]["firstName"])

    def identity(self):
        #resp = self.rs.get(host);
        #open('identity.html', 'w').write(resp.content)
        soup = BeautifulSoup(resp.content)
        identity = soup.find('code', { 'id': 'ozidentity-templates/identity-content'})
        return json.loads(identity.getText())["member"]["name"]["firstName"]

    def inbox(self):
        resp = self.rs.get(host + 'messaging', verify=False, headers = {'csrf-token': self.csrfToken });
        if resp.status_code != 200:
            print(resp)
        soup = BeautifulSoup(resp.content)
        for c in soup.findAll('code', id="inbox-main-content"):
            data = json.loads(c.getText())
            for c in data['conversations']['conversationsBefore']:
                for m in c['messages']:
                    s = m['sender']
                    print("From:", unescape(s['firstName']), unescape(s['lastName']) + ',' , unescape(s['headline']));
                    # "recipients" 
                    print("Date: ", time.strftime('%c', time.localtime(int(m['timestamp'])/1000)))
                    print("Subject: ", unescape(m['subject']));
                    print("Read: ", unescape(str(m['read'])));
                    print('\n' + unescape(str(m['body'])) + '\n\n')

if __name__ == "__main__":
    li = linkedin_client();
    li.inbox()
