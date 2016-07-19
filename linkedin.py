#!/usr/bin/python

from __future__ import print_function
from BeautifulSoup import BeautifulSoup
import json
from pprint import pprint
import sys, getopt
import re
import requests, requests.utils, pickle
from html2text import html2text
import os
from urlparse import parse_qs, parse_qsl, urlparse
import glob
import HTMLParser
import time
import getpass
import termios
import fcntl
from datetime import datetime
import ago
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--verbose",  action='store_true', help="output raw json")
#ap.add_argument("groups_admin")
ap.add_argument("command", nargs='*', help='groups_admin, groups, inbox')
args = ap.parse_args()

html_parser = HTMLParser.HTMLParser()

def unescape(a):
    return html_parser.unescape(a).replace('&dsh; ', '-')

def filename(a):
    return re.sub(r'[ /?=&]+', '_', a)

host = 'https://www.linkedin.com/'
reload(sys)
sys.setdefaultencoding('utf-8')

def getch():
    # http://love-python.blogspot.co.il/2010/03/getch-in-python-get-single-character.html
    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    try:
        while 1:
            try:
                c = sys.stdin.read(1)
                break
            except IOError: pass
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    return c

def print_resp(resp):
        pprint(resp.url)
        pprint(resp.request)
        pprint(resp.request.url)
        pprint(resp.request.headers)
        print('resp.request.body:')
        pprint(resp.request.body)
        pprint(resp)
        pprint(resp.headers)
        #pprint(resp.text)
        open('resp.html', 'w').write(resp.content)
        open('resp.txt', 'w').write((html2text(resp.content.decode('utf-8'))))

class linkedin_client():
    def __init__(self):
        self.csrfToken = None
        self.bcookie = None
        self.rs = requests.Session()
        resp = None
        try:
            with open('linkedin-session') as f:
                self.rs.cookies  = requests.utils.cookiejar_from_dict(pickle.load(f))
        except:
            pass
        if not 'bcookie' in self.rs.cookies:
            self.linkedin_login();

    def verbose(self, data):
        if args.verbose:
            print(json.dumps(data, indent=4, sort_keys = True))

    def linkedin_login(self):
        mail=os.environ.get('LINKEDIN_LOGIN')
        if mail is None:
            mail = os.environ.get('EMAIL');
        if mail is None:
            mail = raw_input('E-mail for linkedin login: ')
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
        open('login.html', 'w').write(resp.content)
        soup = BeautifulSoup(resp.content)
        identity = soup.find('code', { 'id': 'ozidentity-templates/identity-content'})
        if identity is None:
            print('Login failed');
            return
        with open('linkedin-session', 'w') as f:
            pickle.dump(requests.utils.dict_from_cookiejar(self.rs.cookies), f)
        data = json.loads(identity.getText())
        print('Welcome', data['member']['name']['firstName'])

    def identity(self):
        resp = self.rs.get(host);
        open('identity.html', 'w').write(resp.content)
        soup = BeautifulSoup(resp.content)
        identity = soup.find('code', { 'id': 'ozidentity-templates/identity-content'})
        #print(json.dumps(json.loads(identity.getText()), indent=4))
        identity2 = soup.find('code', { 'id': 'sharebox-static/templates/share-content'})
        #print(json.dumps(json.loads(identity2.getText()), indent=4))
        self.id = json.loads(identity2.getText())['memberInfo']['id'];
        print(json.dumps(json.loads(identity2.getText())['memberInfo']))
        #pprint(soup);
        if self.csrfToken is None:
            self.csrfToken = json.loads(soup.find('code', { 'id': '__pageContext__'}).getText())['csrfToken']
        return json.loads(identity.getText())['member']['name']['firstName']

    def inbox(self):
        resp = self.rs.get(host + 'messaging', headers = {'csrf-token': self.csrfToken });
        if resp.status_code != 200:
            print(resp)
        soup = BeautifulSoup(resp.content)
        for c in soup.findAll('code', id='inbox-main-content'):
            inbox = json.loads(c.getText())
            fn='inbox.json'
            open(fn, 'w').write(json.dumps(inbox, indent=4, sort_keys=True))
            for c in inbox['conversations']['conversationsBefore']:
                #print('Conversation: ', unescape(c['subject']));
                #fn = filename(unescape(c['subject'])) + '.json'
                #if glob.glob(fn):
                #   continue
                #print(fn)
                #open(fn, 'w').write(json.dumps(c, indent=4, sort_keys=True))
                self.verbose(c)
                continue # don't separate message
                for m in c['messages']:
                    s = m['sender']
                    #print(time.strftime('%c', time.localtime(int(m['timestamp'])/1000)), unescape(s['firstName']), unescape(s['lastName']) + ', ', unescape(m['subject']));
                    #print('From:', unescape(s['firstName']), unescape(s['lastName']) + ', ', unescape(s['headline']));
                    # 'recipients'
                    #print('Date: ', time.strftime('%c', time.localtime(int(m['timestamp'])/1000)))
                    #print('Subject: ', unescape(m['subject']));
                    #print('Read: ', unescape(str(m['read'])));
                    #print('\n' + unescape(str(m['body'])) + '\n\n')
                    #fn = filename(unescape(s['firstName']) + ' ' +  unescape(s['lastName']) + ', ' + unescape(m['subject'])) + '.json'
                    #print(fn)
                    #open(fn, 'w').write(json.dumps(m, indent=4, sort_keys=True))
                    self.verbose(m)

    def accept(self, gid):
        resp = self.rs.get(host + 'communities-api/v1/memberships/community/' + str(gid) + '?membershipStatus=PENDING',
                headers = {'csrf-token': self.csrfToken });
        pending = resp.json()
        self.verbose(pending)
        for p in pending['data']:
            while True:
                print(p['mini']['id'], p['mini']['name'], '-', p['mini']['headline'], p['mini']['profileUrl'])
                self.verbose(p['mini'])
                print('Accept, Reject?')
                c = getch();
                if ord(c) == 27: break
                if c in ['a', 'y']: a = 'accept'
                elif c in ['r', 'n']: a = 'reject'
                else: continue
                try:
                    print(a)
                    resp = self.rs.post(host + 'communities-api/v1/membership/request/' + a,
                            data = json.dumps({'communityId': str(gid),
                                'requesterMembershipId': p['mini']['id'], # for accept
                                'requesterMemberId': p['mini']['id'], # for reject
                                }),
                            headers = {'csrf-token': self.csrfToken, 'content-type': 'application/json'})
                    if resp.status_code != 200:
                        print('failed')
                        print_resp(resp)
                    break
                except KeyError:
                    pass

    def group_posts(self, gid, cat, count = 10):
        print(cat)
        resp = self.rs.get(host + 'communities-api/v1/activities/community/' + gid + '?activityType=' + cat +
            '&sort=RECENT&count=' + str(count) + '&start=0',
            headers = {'csrf-token': self.csrfToken });
        #print('resp.content', resp.content)
        #pprint(json.loads(resp.content))
        for d in json.loads(resp.content)['data']:
            #print(time.strftime('%y-%m-%d %H:%M', time.localtime(int(d['datePosted'])/1000)), d['title']);
            print(ago.human(datetime.fromtimestamp(int(d['datePosted'])/1000), precision=1, abbreviate=True), '\t', d['author']['name'] + ':', d['title']);
            #print(humanize.naturalday(time.localtime(int(d['datePosted'])/1000)), d['title']);

    def highlights(self, cat = 'DISCUSSION', count = 10):
        resp = self.rs.get(host +
            'communities-api/v1/discussion/highlights/' + self.id + '?type=' + cat + '&sort=RECENT&count=' + str(count) + '&start=0',
            headers = {'csrf-token': self.csrfToken });
        #print('resp.content', resp.content)
        #pprint(json.loads(resp.content))
        print('\nHighlights\n')
        for d in json.loads(resp.content)['data']:
            #print(time.strftime('%y-%m-%d %H:%M', time.localtime(int(d['datePosted'])/1000)), d['title']);
            print(ago.human(datetime.fromtimestamp(int(d['discussion']['datePosted'])/1000), precision=1, abbreviate=True), '\t',
                    d['community']['name'] + ':',
                    d['discussion']['title']);
            #print(humanize.naturalday(time.localtime(int(d['datePosted'])/1000)), d['title']);

    def approve(self, gid, cat):
        resp = self.rs.get(host + 'manageGroup?dispModQueue=&gid=' + gid + '&category=' + cat)
        soup = BeautifulSoup(resp.content)
        for c in soup.findAll('td'):
            if c.has_key('data-li-itemkey'):
                item = c._getAttrMap()['data-li-itemkey']
                print(item)
                print(c.find('span', { 'class': 'stamp'}).getText())
                n = c.find('a', { 'class': 'full-name'})
                print(n.getText('\n'), parse_qs(urlparse(n['href']).query)['memberID'][0])
                less = c.find('a', { 'class': 'showLess'})
                if less: less.extract()
                print('Title:', c.find('span', { 'class': 'title'}).getText())
                f = c.find('p', { 'class': 'discussion details full hide'})
                if not f:
                    f = c.find('p', { 'class': 'article details'})
                if f:
                    print(unescape(f.getText('\n')))
                else:
                    print('\nall:\n', c)
                l = c.find('a', { 'title': 'View link'})
                if l: print('Link ', l['href'])
                print('--\n');
                while True:
                    if cat == 'SD':
                        print('Move to Jobs, ', end="")
                    print('Approve, Delete?');
                    c = getch();
                    if ord(c) == 27: break
                    try:
                        if c in ['a', 'y']: a = 'approveModItems'
                        elif c in ['d', 'n']: a = 'deleteModItems'
                        elif c in ['j', 'm']: a = 'moveModItemsToJobs'
                        else: continue
                        print(a);
                        resp = self.rs.post(host + 'manageGroup',
                            data = 'ajax=ajax&' + a + '=' + a + '&trk=sbq-ap-l&csrfToken=' + self.csrfToken +
                                '&gid=' + str(gid) + '&category=' + cat + '&split_page=1&allItemKeys=' + item + '&items=' + item + '&',
                            #data = {'ajax':'ajax', a:a, 'csrfToken':self.csrfToken, 'gid': gid, 'category':cat, 'allItemKeys':item, 'items':item },
                            headers = {'csrf-token': self.csrfToken, 'content-type': 'application/x-www-form-urlencoded' })
                        if resp.status_code != 200:
                            print('failed')
                            print_resp(resp)
                        break
                    except KeyError:
                        pass

    def groups(self, with_posts = True, dump_metadata = False):
        resp = self.rs.get(host + 'communities-api/v1/communities/memberships/' + self.id + '?' +
                #+ '?projection=FULL&sortBy=RECENTLY_JOINED',
                '&count=500',
                headers = {'csrf-token': self.csrfToken });
        try:
            data = json.loads(resp.content)
            #pprint(data);
            for g in data['data']:
                print(g['group']['mini']['name'])
                if with_posts:
                    li.group_posts(g['group']['id'], 'DISCUSSION');
                    li.group_posts(g['group']['id'], 'JOB');
                    print('\n')
                    self.verbose(g)
                #if dump_metadata:
                    #fn = filename(g['group']['mini']['name']) + '.json'
                    #if glob.glob(fn):
                    #    continue
                    #print(fn)
                    #open(fn, 'w').write(json.dumps(g, indent=4, sort_keys=True))
            #pprint(g['group'])
        except (ValueError):
            raise(Exception(resp.content))

    def groups_admin(self, with_posts = True):
        resp = self.rs.get(host + 'communities-api/v1/communities/memberships/' + self.id + '?' +
                #+ '?projection=FULL&sortBy=RECENTLY_JOINED',
                '&count=500',
                headers = {'csrf-token': self.csrfToken });
        try:
            data = json.loads(resp.content)
            #pprint(data);
            for g in data['data']:
                if g.has_key('adminMetadata'):
                    print(g['group']['mini']['name'])
                    #print(json.dumps(g['adminMetadata']))
                    self.accept(g['group']['id'])
                    if with_posts:
                        li.group_posts(g['group']['id'], 'DISCUSSION');
                    self.approve(g['group']['id'], 'SD');
                    if with_posts:
                        li.group_posts(g['group']['id'], 'JOB');
                    self.approve(g['group']['id'], 'SJ');
                    print('\n')
            #pprint(g['group'])
        except (ValueError):
            raise(Exception(resp.content))

    def eval(self, cmd):
        eval('self.' + cmd + '()')

    def help(self):
        print('highlights');
        print('groups_admin');
        print('groups');
        print('inbox');

if __name__ == '__main__':
    if args.verbose:
            print("verbose turned on")
    for c in args.command:
        li = linkedin_client();
        li.identity()
        li.eval(c)
