from selenium_helper import *
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

def clean_text(t):
  t=t.replace("\n","").replace("\t","").replace(":","").replace("*","").strip()
  return t

def nearest_title(element):
  nearest_b = element.find_element(By.XPATH, "./preceding::b[1]")
  # Find nearest previous <h5> tag
  try:
    nearest_h5 = element.find_element(By.XPATH, "./preceding::h5[1]")
  except NoSuchElementException:
    return clean_text(nearest_b.text)
  # Get the positions of the elements
  element_position = element.location['y']
  b_position = nearest_b.location['y']
  h5_position = nearest_h5.location['y']

  # Calculate distances
  distance_to_b = element_position - b_position
  distance_to_h5 = element_position - h5_position

  # Determine which is closer
  if distance_to_b < distance_to_h5:
    return clean_text(nearest_b.text)
  else:
    return clean_text(nearest_h5.text)

def nearest_table_title(element):
  nearest_b = element.find_element(By.XPATH, "./preceding::b[1]")
  # Find nearest previous <h5> tag
  try:
    nearest_label = element.find_element(By.XPATH, "./preceding::label[1]")
  except NoSuchElementException:
    return clean_text(nearest_b.text)
  # Get the positions of the elements
  element_position = element.location['y']
  b_position = nearest_b.location['y']
  label_position = nearest_label.location['y']

  # Calculate distances
  distance_to_b = element_position - b_position
  distance_to_label = element_position - label_position

  # Determine which is closer
  if distance_to_b < distance_to_label:
    return clean_text(nearest_b.text)
  else:
    return clean_text(nearest_label.text)


def html_table_to_df(html_table):
  table_io = StringIO(str(html_table))
  df = pd.read_html(table_io,flavor='bs4')[0]
  return df

def data1_extraction_df(driver):
  input_and_select_elements = driver.find_elements(By.XPATH, "//input | //select")

  data1 = []
  for element in input_and_select_elements:

      # Get the preceding label and title elements
      label_element = element.find_element(By.XPATH, "./preceding::label[1]")
      previous_title = nearest_title(element)
      if label_element.text.strip() == "Excavation":
          break
      # Handle select elements
      if element.tag_name == 'select':
          select_element = Select(element)
          try:
              element_text = select_element.first_selected_option.text
          except NoSuchElementException:
              element_text = ""
      else:
          element_text = element.get_attribute("value")

      # Append the data
      data1.append({
          "label": clean_text(label_element.text),
          # "element_tag": clean_text(element.tag_name),
          "element_text": clean_text(element_text),
          "title": previous_title
      })

  df1 = pd.DataFrame(data1)
  return df1

def data2_extraction_df(driver):
  elements = driver.find_elements(By.XPATH, "//div[@class='col-sm-12 col-md-6 col-lg-6 mb-1']")

  data2 = []
  for element in elements:
    try:
      element_with_labels = element.find_elements(By.TAG_NAME, "label")
      label_element1 = element_with_labels[0]
      label_element2 = element_with_labels[1]
      label=clean_text(label_element1.text)
      element_text=clean_text(label_element2.text)
      previous_title = nearest_title(element)
      data2.append({
          "label": label,
          # "element_tag": label_element1.tag_name,
          "element_text": element_text,
          "title": previous_title
      })  # l1=element_label[0].text
    except IndexError:
      continue
    # Create a DataFrame from the collected data
  df2 = pd.DataFrame(data2)
  return df2


def get_building_details(table_element):
  building_details = []
  tbody_element = table_element.find_elements(By.CSS_SELECTOR, ":scope>tbody")[0]
  rows=tbody_element.find_elements(By.CSS_SELECTOR, ":scope>tr")
  for row in rows:
    cols = row.find_elements(By.CSS_SELECTOR, ":scope>td")
    building_name=cols[1].text.strip()
    inner_table=cols[2].find_element(By.CSS_SELECTOR, ":scope>table")
    inner_table_tbody = inner_table.find_elements(By.CSS_SELECTOR, ":scope>tbody")[0]
    inner_table_rows = inner_table_tbody.find_elements(By.CSS_SELECTOR, ":scope>tr")[0]
    inner_table_rtds = inner_table_rows.find_elements(By.CSS_SELECTOR, ":scope>td")
    info={
        "building_name": building_name,
        "apartment_type": inner_table_rtds[1].text.strip(),
        "carpet_area_sqmts": float(inner_table_rtds[2].text.strip()),
        "number_of_apartments": int(inner_table_rtds[3].text.strip()),
        "number_of_booked_apartment": int(inner_table_rtds[4].text.strip())
    }
    building_details.append(info)
  return building_details

def get_single_parking_details(mt4):
  parking_details = {}
  class_ml2_elements = mt4.find_elements(By.XPATH, ".//b[contains(@class, 'ml-2')]")
  parking_details["building_name"]=class_ml2_elements[0].text.strip()
  parking_details["wing_name"]=class_ml2_elements[1].text.strip()
  t_head=mt4.find_element(By.TAG_NAME, "thead")
  t_head_rows=t_head.find_elements(By.TAG_NAME, "th")
  parking_details["head"]=[th.text.strip() for th in t_head_rows[2:]]


  t_body=mt4.find_element(By.TAG_NAME, "tbody")
  all_rows=t_body.find_elements(By.TAG_NAME, "tr")
  total_details_row_element=all_rows[-1]
  td_total=total_details_row_element.find_elements(By.TAG_NAME, "td")
  p_type_list=[]
  p_type_list.append({
      "parking_type": td_total[0].text.strip(),
      "info": [int(td.text.strip()) for td in td_total[1:]]
  })

  other_rows=all_rows[:-1]
  for row in other_rows:
    td_other=row.find_elements(By.TAG_NAME, "td")
    p_type_list.append({
        "parking_type": td_other[1].text.strip(),
        "info": [int(td.text.strip()) for td in td_other[2:]]
    })
    
  parking_details["parking_details"]=p_type_list
  return parking_details

def get_parking_elements(driver):
  try:
    parking_details = driver.find_element(By.XPATH, "//b[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'parking details')]")
    mt4_elements = parking_details.find_elements(By.XPATH, "./following::div[@class='mt-4']")
    return mt4_elements
  except NoSuchElementException:
    return None
  
def get_all_parking_details(driver):
  mt4_elements=get_parking_elements(driver)
  if mt4_elements is None:
    return None
  building_details=[get_single_parking_details(mt4) for mt4 in mt4_elements]
  return building_details

