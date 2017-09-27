import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import db_configs_ggfinance as db
from pymongo import MongoClient


def init_driver():
    # driver = webdriver.Firefox()
    driver = webdriver.PhantomJS()
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


def lookup(driver, query):
    print("QUERY: %s" % query)
    ticker_code = query
    driver.get("http://www.google.com/finance/")
    try:
        box = driver.wait.until(EC.presence_of_element_located(
            (By.NAME, "q")))
        box.send_keys(query)
        find_button = driver.wait.until(EC.element_to_be_clickable(
            (By.ID, "gbqfb")))
        find_button.click()

        ticker_name = driver.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='appbar-center']" \
                           "/div[@class='appbar-snippet-primary']/span")
        ))
        name = ticker_name.text
        insert_article = mongo_connection().update(
            {
                "_id": ticker_code,
            },
            {
                '$set': {'crawled_name': name},
            }
        )
    except TimeoutException:
        print("Box or Button not found in google.com")
        mongodb_logging(query)
        return
    except:
        pass

    try:
        ticker_address = driver.wait.until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div/div/div[3]/div[2]/div/div[2]'
                           '/div/div/div[3]/div[1]/div/div[6]')
        ))
        address = ticker_address.text
        insert_article = mongo_connection().update(
            {
                "_id": ticker_code,
            },
            {
                '$set': {'address': address},
            }
        )
    except TimeoutException:
        mongodb_logging(query)
    except:
        pass
    try:
        ticker_descripton = driver.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='sfe-section']" \
                           "/div[@class='companySummary']")
        ))
        more_from_reuters = driver.find_element_by_xpath(
                "//div[@class='sfe-section']"
                "/div[@class='companySummary']"
                "/div[@class='sfe-break-top']")
        description = ticker_descripton.text
        description = description.replace(more_from_reuters.text, '').strip()
        insert_article = mongo_connection().update(
            {
                "_id": ticker_code,
            },
            {
                '$set': {'description': description},
            }
        )

    except TimeoutException:
        print("Box or Button not found in google.com")
        mongodb_logging(query)
    except:
        pass

    try:
        ticker_executives_existence = driver.wait.until(
                EC.presence_of_element_located(
                        (By.XPATH, "//td[@class='p linkbtn']")
                ))
        ticker_executives = driver.find_elements_by_xpath(
                "//td[@class='p linkbtn']")
        executives = []
        for executive in ticker_executives:
            executives.append(executive.text.strip())
        executives_name = "\n".join(executives)
        insert_article = mongo_connection().update(
            {
                "_id": ticker_code,
            },
            {
                '$set': {'executives': executives_name},
            }
        )

    except TimeoutException:
        print("Box or Button not found in google.com")
        mongodb_logging(query)
    except:
        pass

if __name__ == "__main__":
    driver = init_driver()

    tickers = []
    with open('9Aug2016_TSE_Google finance_crawl.csv', 'r') as input_file:
        reader = csv.reader(input_file, delimiter=',')
        print('okay')
        next(reader)
        num = 0
        for line in reader:
            print line
            num += 1

            insert_article = mongo_connection().save(
                {
                    "_id": line[3],
                    'name': line[0],
                    'exchange': line[1],
                    'root_ticker': line[2],
                    'GoogleFin_ticker': line[3]
                }
            )
            lookup(driver, line[3])

    driver.quit()
