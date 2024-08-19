# -*- coding: utf-8 -*-
import os
import re
import time
import sys
import random
import requests
import json
import argparse
import traceback
from collections import OrderedDict
from bs4 import BeautifulSoup as bs
import urllib.parse

with open("cookie.txt","r") as f:
    COOKIE = f.read().strip()

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'cookie':COOKIE,
    'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Referer':'https://www.ssense.com/zh-us/women/clothing?page=416'
}

SSENSE_URL = 'https://www.ssense.com/zh-cn'
BASE_URL   = 'https://www.ssense.com/zh-cn/women/clothing?page=%d'


#Original: https://res.cloudinary.com/ssenseweb/image/upload/__IMAGE_PARAMS__/242477F107004_1.jpg
#Target:   https://img.ssensemedia.com/images/g_center,f_auto/242477F063004_1/jw-anderson.jpg
def parse_imgs(resp_text):
    soup = bs(resp_text, 'html.parser')


    # 找到包含 JSON 数据的 <script> 标签
    script_tags = soup.find_all('script')
    for script_tag in script_tags:
        if 'window.INITIAL_STATE=' in str(script_tag):
            # 提取 JSON 数据
            json_data = script_tag.string.replace('window.INITIAL_STATE=', '').strip()
            # 解析 JSON 数据
            data = json.loads(json_data)
            original_images = data['products']['current']['images']
            target_images = []
            brand_name = data['products']['current']['brand']['seoKeyword']['zh']
            for img_url in original_images:
                sku = img_url[img_url.rindex('/') + 1:-4]
                print(sku)
                target_image = f"https://img.ssensemedia.com/images/g_center,f_auto/{sku}/{brand_name}.jpg"
                target_images.append(target_image)
                print(img_url)
                print(target_image)
            return target_images

    return None


def get_product_info(product_url, product_id):
    """
    get a product's information from a single web page
    :param product_id
    :return: a result dict, containing sku, name, category, description, price, gender and image urls
    """
    print(product_id, product_url)

    response = requests.get(product_url, headers=HEADERS)

    if response.status_code == 200:
        print("Request successful!")
        resp = response.text
    else:
        print(f"Request failed with status code: {response.status_code}")
        resp = None

    imgs = parse_imgs(resp)
    download_img_urls = []
    for img in imgs:
        download_img_urls.append(f"{product_id},{img}")

    return resp,download_img_urls

def get_page_products(url, page, count = 1):
    '''
    get all products' urls in a web page
    :param url: web page url
    :return: product url list
    '''
    print(f"get product urls in page {page}, url {url}, for {count} time")

    #time.sleep(20)

    if count > 1:
        time.sleep(5)
    r = requests.get(url, headers=HEADERS)
    s = bs(r.text, 'html.parser')
    product_urls = []
    try:

        # 找到所有包含 JSON-LD 格式的 <script> 元素
        json_ld_scripts = s.find_all('script', type='application/ld+json')

        for script in json_ld_scripts:
            # 解析 JSON 数据
            data = json.loads(script.string)

            # 提取 url 字段
            url = data.get('url')
            #print(f"URL: {url}")

            product_urls.append(SSENSE_URL+url)
    except:
        print('Cannot find product links in this page')
        traceback.print_exc()
    return product_urls


def download_img(img_url,img_save_path,img_name):
    try:
        img_r = requests.get(img_url)
        with open(os.path.join(img_save_path, img_name), 'wb') as f:
            f.write(img_r.content)
        return True
    except:
        return False

def parse_id(product_url):
    pattern = r'/(\d+)$'

    product_id = re.search(pattern, product_url).group(1)
    #print(f"Product ID: {product_id}")
    return product_id

def get_outfit(product_id, pdt_file_path):

    url = f"https://www.ssense.com/zh-cn/api/product/related/women/{product_id}?sale=true"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        output = []
        resp = response.json()
        outfit = resp['styledWith']
        for product in outfit:
            product_url = product['url']
            if product['url'] is not None:
                product_url = SSENSE_URL + product_url
                output.append(product_url)
        if(len(output) > 0):
            output_file_path = os.path.join(pdt_file_path, f"outfit.json")
            with open(output_file_path, "w", encoding='utf-8') as f:
                f.write(json.dumps(resp))
        else:
            print(f"No items in outfit requests, pls check {product_id} ")
        return output
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None

def fetch_one_product(product_id, file_save_path, count, total_count, page, product_url):
    pdt_file_path = os.path.join(file_save_path, product_id)
    img_file_path = os.path.join(pdt_file_path, 'img_urls.txt')
    if os.path.exists(pdt_file_path) and os.path.exists(img_file_path):
        return
    try:
        print("[product:%d/%d, page:%d]"%(count,total_count, page))
        if not os.path.exists(pdt_file_path):
            os.makedirs(pdt_file_path)

        time.sleep(random.random())

        # r = requests.get(product_url, headers=HEADERS)
        # s = bs(r.text, 'html.parser')
        # #print(r.text)
        # with open(os.path.join(pdt_file_path, product_id+'.html'),'w',encoding='utf-8') as f:
        #     f.write(r.text)

        print(f'-----[step-1] get outfit json for {product_id}')
        product_urls = get_outfit(product_id, pdt_file_path)
        if product_urls is None:
            print(f"Outfit request Failed, skip {product_id} ")
            return

        product_urls.append(product_url)

        print('-----[step-2] get outfit products info')
        download_img_urls=[]
        for pdt_url in product_urls:
            time.sleep(random.random())
            pdt_id = parse_id(pdt_url)
            result,img_urls=get_product_info(pdt_url, pdt_id)
            with open(os.path.join(pdt_file_path, pdt_id+'.html'),'w',encoding='utf-8') as file:
                file.write(result)

            download_img_urls.extend(img_urls)
            #print(download_img_urls)

        if len(download_img_urls) > 0:
            with open(img_file_path, 'w') as f:
                for img_url in download_img_urls:
                    f.write(img_url+ '\n')

    except Exception as e:
        print('-----[wrong] %s'%(product_url))
        print(e)
        traceback.print_exc()
        with open(os.path.join(file_save_path,'wrong_url_list.txt'),'a') as f:
            f.write(product_url+'\n')

def dry_run_one_page(s_file_path, page):
    if os.path.exists(s_file_path):
        print(f"{s_file_path} exists, skip")
        return

    page_url = base_url % (page)
    product_urls = get_page_products(page_url, page)
    #RETRY 1 time
    if len(product_urls) == 0:
        product_urls = get_page_products(page_url, page,  count=2)
    total_count = len(product_urls)
    if total_count > 0:

        with open(s_file_path, "w") as s_file:

            for i,product_url in enumerate(product_urls):
                count = i + 1
                product_id = parse_id(product_url)

                s_file.write(f"{page},{i+1},{product_id},{product_url}\n")

def run_crawler(base_url,start_page,end_page,file_save_path, mode):
    if not os.path.exists(file_save_path):
        os.makedirs(file_save_path)

    for page in range(start_page, end_page):

        summary_file_name = f"summary_{page}_dry_run.csv"

        s_file_path = os.path.join(file_save_path, summary_file_name)

        if mode == "dry_run":
            dry_run_one_page(s_file_path, page)

        else: #mode fetch
            if os.path.exists(s_file_path):
                with open(s_file_path, "r") as f:
                    lines = f.readlines()

                total_count = len(lines)
                if total_count == 0:
                    print(f"Empty summary_file : {s_file_path}")
                    continue

                for line in lines:

                    #1,1,16287061,https://www.ssense.com/zh-cn/women/product/jw-anderson/red-and-navy-paneled-jacket/16287061
                    page, count, product_id, product_url = line.strip().split(',')
                    count = int(count)
                    page = int(page)
                    fetch_one_product(product_id, file_save_path, count, total_count, page, product_url)

            else:
                print(f"Lack of summary_file path: {s_file_path}")


if __name__ == '__main__':
    parse=argparse.ArgumentParser()
    parse.add_argument('--file_save_path',type=str,help='where to save crawled files',default='./output/')
    parse.add_argument('--start_page',type=int,help='start page index',default='1')
    parse.add_argument('--end_page',type=int,help='end page index',default='10')
    parse.add_argument('--mode', type=str, help='dry_run or fetch', default='dry_run')


    args=parse.parse_args()

    file_save_path = args.file_save_path
    start_page = args.start_page
    end_page = args.end_page
    mode=args.mode

    if start_page>end_page:
        print('start page must be less than end page')
        exit(0)

    if start_page<0 or end_page<0:
        print('page index must be greater than zero')

    base_url = BASE_URL
    run_crawler(base_url, start_page, end_page, file_save_path, mode)
