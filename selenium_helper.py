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
from captcha_modules import *
from more_details_modules import *
import time
def setup_driver():
  chrome_options = Options()
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  return webdriver.Chrome(options=chrome_options)

def take_screenshot(driver):
  driver.save_screenshot("screenshot.png")

def property_not_added_file(l):
  with open('property_not_added.txt', 'a') as f:
    for item in l:
      f.write("%s\n" % item)

def clean_text(t):
  t=t.replace("\n","").replace("\t","").replace(":","").replace("*","").strip()
  return t

def well_formated_dict(df_dict):
  for record in df_dict:
    for key, value in record.items():
      if isinstance(value, str):
        try:
          # Try converting to integer
          record[key] = int(value)
        except ValueError:
          try:
            # If integer conversion fails, try converting to float
            record[key] = float(value)
          except ValueError:
            # If both conversions fail, leave the value as it is
            pass
  return df_dict


def date_standizer(text_with_date, failed_dates=None):
  dformat = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
  if failed_dates is None:
      failed_dates = []  # Initialize the list if not provided

  if isinstance(text_with_date, str):
      text_with_date = text_with_date.strip()
      if len(text_with_date) == 0:
          return text_with_date
      else:
          for i, d in enumerate(dformat):
              try:
                  standard_date = pd.to_datetime(text_with_date, format=d)
                  return standard_date  # Return the standardized date
              except ValueError:
                  continue
          # If all formats fail, log the original text
          failed_dates.append(text_with_date)
          return text_with_date  # Return the original text if conversion fails
  return text_with_date

def date_standizer_for_table(df):
  for col in df.columns:
    df[col]=df[col].apply(date_standizer)
  return df

def manage_captcha_logic(driver):
    attempt = 1
    while attempt <= 3:
        try:
            time.sleep(2)
            wait = WebDriverWait(driver, 10)

        # Wait for the page to load completely
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            captcha_canvas_img = get_captcha_canvas_image(driver)
            if captcha_canvas_img is None:
                print("captcha_canvas_img is None")
                return False

            new_image = replace_multiple_colors_rgba(captcha_canvas_img, color_map)
            optimized_image = optimize_image_for_ocr(new_image)
            recognized_text = recognize_captcha(optimized_image)
            captcha_alpha_num = get_all_recognized_alpha_num(recognized_text)

            if is_captcha_length_valid(captcha_alpha_num):
                type_captcha_to_input(driver, captcha_alpha_num)
                submit_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit']"))
                )
                submit_button.click()

                if is_invalid_captcha_dialog(driver):
                    print(f"Invalid CAPTCHA. Attempt: {attempt}")  # Moved here
                    print(captcha_alpha_num)
                    ok_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[text()='Ok']"))
                    )
                    ok_button.click()
                    # No return False here, allowing the loop to continue
                else:
                    print(f"CAPTCHA solved in attempt: {attempt}")
                    print(captcha_alpha_num)

                    return True
            else:
               print("Captcha not valid: ", captcha_alpha_num, ",  attempt: ",attempt)
               refresh_captcha(driver)

        except Exception as e:
            print(f"Error in attempt {attempt}: {str(e)}")

        attempt += 1
        # Uncomment the following line if you want a delay between attempts
        # time.sleep(2)
    return False


def switch_tab(driver, reg_num, visit_details_url):
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        load_captcha_website(driver, visit_details_url)

        if manage_captcha_logic(driver):
            wait = WebDriverWait(driver, 15)
            take_screenshot(driver)
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')

            wait.until(EC.all_of(
                EC.visibility_of_element_located((By.TAG_NAME, "select")),
                EC.visibility_of_element_located((By.TAG_NAME, "input")),
                EC.visibility_of_element_located((By.TAG_NAME, "table"))
            ))
            
            # Check if jQuery is available before using it
            if driver.execute_script("return typeof jQuery !== 'undefined'"):
                wait.until(lambda d: d.execute_script('return jQuery.active == 0'))

            try:
                property_details_dict = extract_property_details(driver)
            except Exception as e:
                print(f"Error in property data extraction: {str(e)}")
                property_details_dict = None

            try:
                building_details = extract_building_details(driver, wait)
            except Exception as e:
                print(f"Error in building data extraction: {str(e)}")
                building_details = None

            try:
               parking_details=get_all_parking_details(driver)
            except Exception as e:
               print(f"Error in parking details extraction: {str(e)}")
               parking_details=None

            return property_details_dict, building_details, parking_details
        else:
            print("Captcha not solved")
            property_not_added_file([reg_num+"  "+visit_details_url])
            return None, None
    except Exception as e:
        print(f"An error occurred in selenium helper: {str(e)}")
        return None, None
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

def extract_property_details(driver):
    df1 = data1_extraction_df(driver)
    df2 = data2_extraction_df(driver)
    combined_df = pd.concat([df1, df2], ignore_index=True)
    combined_df_after_date_standardization = date_standizer_for_table(combined_df)
    df_dict = combined_df_after_date_standardization.to_dict(orient="records")
    return well_formated_dict(df_dict)

def extract_building_details(driver, wait):
    building_title_element = wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'summary of building details')]")))
    table_element = building_title_element.find_element(By.XPATH, "./following::table[1]")
    return get_building_details(table_element)