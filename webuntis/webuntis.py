import requests
import json
import base64
import asyncio

# Class Webuntis
#
# This class contains various data and functions for
# interacting with the Webuntis API
#
# Keep in mind that before executing any functions you have to log in
#
# Keep in mind that after executing any functions you have to log out
# You will be automatically logged out in less than 10 minutes by webuntis itself
class Webuntis:
    def __init__(self, username, password, baseurl, school, elemid, identity = 'Awesome'):
        self.school = school
        self.schoolbase64 = base64.b64encode(school.encode('ascii'))
        self.username = username
        self.password = password
        self.baseurl = "https://" + baseurl + ".webuntis.com"
        self.id = identity
        self.sessionInformation = {}
        self.elemid = elemid
        self.anonymous = False
        self.userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36"
        self.request = requests
        self.headers = {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'x-Requested-With': 'XMLHttpRequest',
            'User-Agent': self.userAgent
        }

    # Connects the client to the specified webuntis server
    async def login(self):
        # print("The user " + self.username + " has been successfully logged in!")
        url = self.baseurl + "/WebUntis/jsonrpc.do"
        data = {
            'id': self.id,
            'method': 'authenticate',
            'params': {
                'user': self.username,
                'password': self.password,
                'client': self.id
            },
            'jsonrpc': '2.0',
        }
        params = {
            'school': self.school
        }
        self.sessionInformation = self.request.post(url = url, data = data, params = params, headers = self.headers, allow_redirects = False)

    # Disconnects the client from the specified webuntis server
    async def logout(self):
        # print("The user " + self.username + " has been successfully logged out!")
        url = self.baseurl + "/WebUntis/jsonrpc.do"
        data = {
            'id': self.id,
            'method': 'logout',
            'params': {},
            'jsonrpc': '2.0',
        }
        params = {
            'school': self.school
        }
        self.request.post(url = url, data = data, params = params, headers = self.headers, allow_redirects = False)
        self.sessionInformation = None

    # Builds needed headers for requests
    def buildcookies(self):
        cookies = [
            'JSESSIONID=' + self.sessionInformation.sessionId,
            'schoolname=' + str(self.schoolbase64)
        ]
        return "; ".join(cookies)

    # Get you own timetable for the current day
    async def generalrequest(self, method, url = '/WebUntis/jsonrpc.do', parameter=None):
        if parameter is None:
            parameter = {}
        data = {
            'id': self.id,
            'method': method,
            'params': parameter,
            'jsonrpc': '2.0',
        }
        params = {
            'school': self.school
        }
        headers = {
            'Cookie': self.buildcookies()
        }
        self.request.post(url = self.baseurl + url, data = data, params = params, headers = headers)

    # Get all teachers of the current user
    async def getteachers(self):
        return await self.generalrequest('getTeachers')
