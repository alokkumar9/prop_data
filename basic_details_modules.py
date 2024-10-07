from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import pandas as pd
from selenium_helper import *

def get_element_info(elements):
  projects_in_page_list=[]
  for element in elements:
    reg_number= element.find_element(By.CLASS_NAME,"p-0").text.split("#")[1].strip()
    project_name= element.find_element(By.CLASS_NAME,"title4").text.strip()
    builder=element.find_element(By.CLASS_NAME,"darkBlue.bold").text.strip()
    locations = element.find_elements(By.CSS_SELECTOR, ".listingList > li")
    try:
      location_geo=locations[0].find_element(By.CSS_SELECTOR, "a[href*='maps']").get_attribute('href').strip()
    except NoSuchElementException:
      location_geo=''

    location_name=locations[0].text.strip()

    try:
      route=locations[1].find_element(By.CSS_SELECTOR, "a[href*='maps']").get_attribute('href').strip()
    except NoSuchElementException:
      route=''

    state_pin_cert_dist_last_ext=element.find_elements(By.CSS_SELECTOR,".col-xl-6 > .row")
    state_pin_cert=state_pin_cert_dist_last_ext[0].find_elements(By.CSS_SELECTOR,".col-xl-4 > p")
    state=state_pin_cert[0].text.strip()
    pin=state_pin_cert[1].text.strip()

    dist_last_ext=state_pin_cert_dist_last_ext[1].find_elements(By.CSS_SELECTOR,".col-xl-4 > p")
    district= dist_last_ext[0].text.strip()
    last_modified=dist_last_ext[1].text.strip()
    extension_cert=state_pin_cert_dist_last_ext[1].find_element(By.CSS_SELECTOR,".col-xl-4 > a").text.strip()

    visit_details_url=element.find_element(By.CSS_SELECTOR,".col-xl-2.divider a").get_attribute('href').strip()

    projects_in_page_list.append(
        {
          'reg_number':reg_number,
          'project_name':project_name,
          'builder':builder,
          'location_geo':location_geo,
          'location_name':location_name,
          'route':route,
          'state':state,
          'pin':int(pin),
          'district':district,
          'last_modified': date_standizer(last_modified),
          'extension_cert':extension_cert,
          'visit_details_url':visit_details_url,
          'project_details_extracted': False,
          'building_details_extracted': False
        }
    )
  return projects_in_page_list


def add_most_basic_info(project):
  complete_project_info={}
  complete_project_info['reg_number']=project['reg_number']
  complete_project_info['project_name']=project['project_name']
  complete_project_info['builder']=project['builder']
  complete_project_info['location_geo']=project['location_geo']
  complete_project_info['location_name']=project['location_name']
  complete_project_info['state']=project['state']
  complete_project_info['pin']=project['pin']
  complete_project_info['district']=project['district']
  complete_project_info['last_modified']=project['last_modified']
  complete_project_info['route']=project['route']
  complete_project_info['extension_cert']=project['extension_cert']
  complete_project_info['visit_details_url']=project['visit_details_url']
  complete_project_info['project_details_extracted']= project['project_details_extracted']
  complete_project_info['building_details_extracted']= project['building_details_extracted']
  return complete_project_info