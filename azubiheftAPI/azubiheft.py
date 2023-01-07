from bs4 import BeautifulSoup
from datetime import date
import requests
import numpy as np


class AzubiheftAPI:

    def __init__(self):
        self.session = requests.Session()
        self.login_page = 'https://www.azubiheft.de/Login.aspx'

    def get_page_content(self, url) -> BeautifulSoup:
        '''
        :@param url {str}:
        Pull all the HTML of a given page
        '''
        response = self.session.get(url)

        return BeautifulSoup(response.text, "html.parser")

    def get_missing_inputfield_values(self):
        '''
        Pull all the data inside of the hidden inputfields that is needed to login 
        '''
        page_content = self.get_page_content(self.login_page)

        state = page_content.find(id="__VIEWSTATE")['value']
        generator = page_content.find(id="__VIEWSTATEGENERATOR")['value']
        validation = page_content.find(id="__EVENTVALIDATION")['value']

        return state, generator, validation

    def login(self, email, password) -> None:
        '''
        :@param email {str}:
        :@param password {str}:
        '''
        state, generator, validation = self.get_missing_inputfield_values()
        
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        login_data = {
            '__VIEWSTATE': state,
            '__VIEWSTATEGENERATOR': generator,
            '__EVENTVALIDATION': validation,
            'ctl00$ContentPlaceHolder1$txt_Benutzername': email,
            'ctl00$ContentPlaceHolder1$txt_Passwort': password,
            'ctl00$ContentPlaceHolder1$chk_Persistent': 'on',
            'ctl00$ContentPlaceHolder1$cmd_Login': 'Anmelden',
            'ctl00$ContentPlaceHolder1$HiddenField_isMobile': 'false' 
        }

        self.session.post(self.login_page, headers=headers, data=login_data)

    def get_week_number(self, entryDate) -> int:
        """
        :@param entryDate {str}:
        Get the amount of weeks that have been passed since the 01.08.2021
        which is needed for the payload to create an entry at a given date in azubiheft
        """
        entryDate = entryDate.split('-')
        year, month, day = list(np.int16(entryDate))

        start_date = date(2021,8,1)
        end_date = date(year,month,day)

        days = abs(start_date-end_date).days
        
        return int((days/7)+2)

    def create_entry(self, date, message, art) -> None:
        '''
        send a payload to azubiheft with all the data needed to create an entry
        '''
        art = art if art else '1'
        week = self.get_week_number(date)
        date = date.replace('-', '')

        site = f'https://www.azubiheft.de/Azubi/XMLHttpRequest.ashx?Datum={date}&BrNr={week}'
        data = {
            'disablePaste': '0',
            'Seq': '0',
            'Art_ID': art,
            'Abt_ID': '0',
            'Dauer': '00:00',
            'Inhalt': message,
            'jsVer': '11',
        }                 

        self.session.post(site, data=data)
