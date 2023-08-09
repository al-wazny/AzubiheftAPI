import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import *

# Get login credentials from credentials file
with open('/home/ali/repos/AzubiheftAPI/credentials.json') as file:
    data = json.load(file)

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 3)

def fill_in_credentials():
    driver.get('https://www.azubiheft.de/Login.aspx')
    
    driver.find_element(By.XPATH, '//*[@id="txt_Benutzername"]').send_keys(data['azubiheft']['email'])
    driver.find_element(By.XPATH, '//*[@id="txt_Passwort"]').send_keys(data['azubiheft']['password'])
    driver.find_element(By.XPATH, '//*[@id="cmd_Login"]').click()

def logged_in():
    try:
        driver.find_element(By.XPATH, '//*[@id="Abmelden"]')
        return True
    except Exception:
        return False

def login():
    if not logged_in():
       fill_in_credentials()

def get_week(number):
    driver.get('https://www.azubiheft.de/Azubi/Ausbildungsnachweise.aspx?St=1')
    wait.until(EC.visibility_of_element_located((By.XPATH, f'//*[@id="Tab1"]/div[{number}]'))).click()

    return driver.find_elements(By.CSS_SELECTOR, '#divTB > .mo')

def week_days(week_number):
    days_in_week = 5
    for i in range(days_in_week):
        yield get_week(week_number)[i]

def get_entry_count(day):
    try:
        return len(day.find_elements(By.CLASS_NAME, 'table103'))
    except StaleElementReferenceException:
        return 0

def has_entries(day):
    return get_entry_count(day) > 0

def delete_entry():
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="GridViewTB"]/tbody/tr[3]/td/div'))).click()
        wait.until(EC.visibility_of_element_located((By.ID, 'cmdDel'))).click()
        wait.until(EC.visibility_of_element_located((By.ID, 'cmdConfirmBoxOK'))).click()
        time.sleep(1)
    except TimeoutException:
        driver.refresh()
        delete_entry()

def delete_all_entries(day, entry_count):
    day.click()
    for _ in range(entry_count):
        delete_entry()

def goto_week_overview():
    wait.until(EC.element_to_be_clickable((By.ID, 'navOpt'))).click()

def main(week_number):
    login()

    for day in week_days(week_number):
        if has_entries(day):
            delete_all_entries(day, get_entry_count(day))
            goto_week_overview()

    main(week_number+1)

main(1)
