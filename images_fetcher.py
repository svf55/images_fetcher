#!/usr/bin/env python
"""
Obtaining images and metadata from a web page.
"""


import time
import argparse
import logging
import re
import urllib.request
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


logger = logging.getLogger(__name__)


def process_main_page(driver):
    base_url = 'https://images.nasa.gov'
    logger.info('Process main page %s', base_url)
    driver.get(base_url)
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.ID, 'landing-assets'))
    )
    time.sleep(3)
    image_urls = [
        a.get_attribute('href')
        for a in driver.find_elements_by_xpath('//div[@id="landing-assets"]/div/a')
    ]
    logger.info('Found {} images on main page'.format(len(image_urls)))
    for url in image_urls:
        try:
            process_image_page(driver, url)
        except Exception as e:
            logger.exception('Error during processing %s', url)


def process_image_page(driver, url):
    logger.info('Process page %s', url)
    driver.get(url)
    detail_info = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.ID, 'details-info'))
    )
    time.sleep(3) # wait angular
    nasa_id = detail_info.find_element_by_xpath('//span[@data-ng-bind="media.NASAID"]').text
    img_url = driver.find_element_by_xpath('//img[@id="details_img"]').get_attribute('src')

    # save image
    img_ext = re.search(r'\.[^\.]+$', img_url).group()
    img_file_name = '{}{}'.format(nasa_id, img_ext)
    logger.info('Save %s', img_file_name)
    urllib.request.urlretrieve(img_url, img_file_name)

    # collect metadata
    metadata = {
        'NASA ID': nasa_id,
        'Image url': img_url,
        'Keywords': ', '.join(get_keywords(detail_info)),
        'Center': get_center(detail_info),
        'Date Created': get_date_created(detail_info),
        'Center Website': get_center_website(detail_info),
        'Description': get_description(detail_info)
    }
    # save metadata
    metadata_file_name = '{}.txt'.format(nasa_id)
    logger.info('Save %s', metadata_file_name)
    with open(metadata_file_name, 'w') as w:
        for k, v in metadata.items():
            w.write('{}:\t{}\n'.format(k, v))


def if_exists(f):
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except NoSuchElementException as e:
            return None
    return wrap

@if_exists
def get_keywords(detail_info):
    return [span.text for span in detail_info.find_elements_by_xpath('//li[@id="detail-keywords"]/span[not(@class="detail-lbl")]')]

@if_exists
def get_center(detail_info):
    return detail_info.find_element_by_xpath('//span[text()="Center:"]/following-sibling::span').text

@if_exists
def get_date_created(detail_info):
    return detail_info.find_element_by_xpath('//span[text()="Date Created:"]/following-sibling::span').text

@if_exists
def get_center_website(detail_info):
    return detail_info.find_element_by_xpath('//li[@data-ng-if="media.Center.website"]/a').get_attribute('href')

@if_exists
def get_description(detail_info):
    return detail_info.find_element_by_xpath('//span[@id="editDescription"]').text


if __name__ == '__main__':

    # configure logigng
    rootLogger = logging.getLogger()
    ch = logging.StreamHandler()
    rootLogger.setLevel(logging.INFO)
    rootLogger.addHandler(ch)

    parser = argparse.ArgumentParser(description='Nasa images fetcher')
    parser.add_argument('--chrome-driver-path', type=str, help='Selenium driver path for Google Chrome', required=True)
    args = parser.parse_args()

    # run parsing
    driver = webdriver.Chrome(args.chrome_driver_path)
    process_main_page(driver)
    driver.quit()

