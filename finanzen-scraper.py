import time
import random
import csv
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import db_configs as db
from pymongo import MongoClient


def init_driver():
    driver = webdriver.Firefox()
    # driver = webdriver.Chrome()
    # driver = webdriver.PhantomJS()
    driver.wait = WebDriverWait(driver, 5)
    return driver

def mongo_connection():
    try:
        # logging.info('Connecting to MongoDB: %s port: %s' % (db.MONGO_HOST, db.MONGO_PORT))
        conn = MongoClient(db.MONGO_HOST, db.MONGO_PORT)
        return conn[db.MONGO_DB][db.MONGO_COLLECTION]
    except:
        raise

def mongo_log_connection():
    try:
        conn = MongoClient(db.MONGO_HOST, db.MONGO_PORT)
        return conn[db.MONGO_LOG_DB][db.MONGO_LOG_COLLECTION]
    except:
        raise

def mongodb_logging(ticker):
    try:
        mongo_log_connection().save(
                {
                    "_id": ticker
                }
        )
    except:
        raise

class Scraper(object):
    def __init__(self):
        self.current_page = 128
        self.stop = False

def lookup(driver, scraper):
    driver.get("http://www.finanzen-lexikon.de/cms/glossar-lexikon/23-lexikon-a.html?start=20")
    try:
        # Wait for the presence of checkboxes
        driver.wait.until(EC.presence_of_element_located(
            (By.NAME, "szkbuChkbx")))

        # Check the predefined checkboxes
        driver.find_elements_by_name('szkbuChkbx')[0].click()
        driver.find_elements_by_name('szkbuChkbx')[1].click()
        driver.find_elements_by_name('szkbuChkbx')[2].click()
        driver.find_elements_by_name('szkbuChkbx')[3].click()
        driver.find_elements_by_name('szkbuChkbx')[4].click()
        driver.find_elements_by_name('szkbuChkbx')[5].click()
        driver.find_elements_by_name('szkbuChkbx')[6].click()
        driver.find_elements_by_name('szkbuChkbx')[7].click()

        # Press search button
        find_button = driver.wait.until(EC.element_to_be_clickable(
            (By.NAME, "searchButton")))
        find_button.click()

        # Wait for the presence of first element
        driver.wait.until(EC.presence_of_element_located(
                (By.NAME, 'ccJjCrpSelKekkLst_st[0].eqMgrNm')
        ))

        current_chunk = scraper.current_page/10
        print current_chunk

        if current_chunk > 0:
            driver.find_element_by_link_text('...').click()
            if current_chunk >= 2:
                for i in range(0, current_chunk-1):
                    driver.find_elements_by_link_text('...')[1].click()
                    time.sleep(random.randrange(60))
                driver.find_element_by_link_text('128').click()

        current_page_str = driver.find_element_by_class_name('current').text
        scraper.current_page = int(current_page_str)

        # Iterate over the rows
        while True:
            for row_id in range(10):
                code = driver.find_element_by_name(
                        'ccJjCrpSelKekkLst_st[%s].eqMgrCd' % row_id
                ).get_attribute('value')
                issue_name = driver.find_element_by_name(
                        'ccJjCrpSelKekkLst_st[%s].eqMgrNm' % row_id
                ).get_attribute('value')
                address = driver.find_element_by_name(
                        'ccJjCrpSelKekkLst_st[%s].tdfkm' % row_id
                ).get_attribute('value')
                cat_industry = driver.find_element_by_name(
                        'ccJjCrpSelKekkLst_st[%s].gyshDspNm' % row_id
                ).get_attribute('value')

                issue_name = issue_name.encode('utf-8')

                print "current fow: {0}-{1}-{2}-{3}".format(
                        code, issue_name, address, cat_industry)

                mongo_connection().save(
                        {
                            '_id': code,
                            'name': issue_name,
                            'address': address,
                            'cat_industry': cat_industry
                        }
                )

            time.sleep(random.randrange(60))

            for i in range(random.randint(1, 5)):
                actions = ActionChains(driver)
                actions.move_by_offset(random.randrange(250), random.randrange(250))

            scroll_range = random.randrange(250)

            driver.execute_script("window.scrollTo(0, %s);" % scroll_range)

            next_button = driver.wait.until(EC.presence_of_element_located(
                    (By.CLASS_NAME, 'next_e')
            ))
            next_button.click()

        # insert_article = mongo_connection().update(
        #     {
        #         "_id": ticker_code,
        #     },
        #     {
        #         '$set': {'crawled_name': name},
        #     }
        # )
    except TimeoutException:
        print("Box or Button not found")
        return
    except Exception as e:
        scraper.stop = True
        print e
        # raise

if __name__ == "__main__":
    scraper = Scraper()
    print scraper.stop
    driver = init_driver()
    lookup(driver, scraper)
    while True:
        if not scraper.stop:
            pass
        else:
            driver = init_driver()
            lookup(driver, scraper)
            scraper.stop = False
        # driver.quit()
