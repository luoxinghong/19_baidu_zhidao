#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: 罗兴红
@contact: EX-LUOXINGHONG001@pingan.com.cn
@file: demo1.py
@time: 2019/3/29 13:45
@desc:
'''
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import datetime
import os
import emoji
import pymysql

connection = pymysql.connect(
    host='localhost',  # 数据库地址，本地一般写127.0.0.1或者localhost
    user='root',  # 数据库账户
    password='lxh123',  # 数据库密码
    db='spider_data',  # 使用的数据库名称
    charset='utf8mb4',  # 字符集
)


def start_chrome():
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    driver = webdriver.Chrome(executable_path='chromedriver', chrome_options=option)
    driver.start_client()
    return driver


def keywords():
    filename = 'keywords.txt'
    keywords = []
    with open(filename, 'r', encoding='UTF-8') as file_object:
        for line in file_object:
            kw_cn = line.strip()
            keywords.append(kw_cn)
    return keywords


def prefix_url(keyword):
    kw_gbk = str(keyword.encode('gbk')).lstrip("b'").rstrip("'")
    kw = kw_gbk.replace(r'\x', '%')
    base_url = 'https://zhidao.baidu.com/search?lm=0&rn=10&pn=0&fr=search&ie=gbk&word='
    origi_url = base_url + kw
    return origi_url


def page_url(origi_url):
    pages_urls = []
    for i in range(1):
        link = origi_url + "&ie=gbk&site=-1&sites=0&date=0&pn={}".format(i * 10)
        pages_urls.append(link)
    return pages_urls


def sub_urls(page_urls):
    urls = []
    for pageurl in page_urls:
        driver.get(pageurl)
        links = driver.find_elements_by_css_selector('a.ti')
        for link in links:
            sub_url = link.get_attribute('href')
            urls.append(sub_url)

    return urls


def get_answers(url):
    driver.get(url)
    time.sleep(1)
    try:
        title = driver.find_element_by_class_name("ask-title").text
        title = emoji.demojize(title)
        best = driver.find_element_by_css_selector('div.best-text').text
        bs1 = best.lstrip('展开全部\n')
        bs2 = bs1.replace('\n\n', '')
        answer = bs2.replace('\n', '')
        answer = emoji.demojize(answer)


    except NoSuchElementException:
        pass

    answers = []

    try:
        qiye_answer = driver.find_element_by_css_selector('div.ec-answer').text
        qy1 = qiye_answer.lstrip('展开全部\n')
        qy2 = qy1.replace('\n\n', '')
        qy_ans = qy2.replace('\n', '')
        answers.append(qy_ans)
    except NoSuchElementException:
        pass
    try:
        if driver.find_element_by_id('show-answer-hide').is_enabled():
            driver.find_element_by_id('show-answer-hide').click()
        if driver.find_element_by_css_selector('div.show-hide-dispute'):
            driver.find_element_by_css_selector('div.show-hide-dispute').click()
    except NoSuchElementException:
        pass
    other_answers_sels = driver.find_elements_by_class_name('answer-text')
    for other in other_answers_sels:
        other_ans = other.text
        other_ans_t1 = other_ans.lstrip('展开全部\n')
        other_ans_t2 = other_ans_t1.replace('\n\n', '')
        other_answer = other_ans_t2.replace('\n', '').replace(u'\u3000', '').replace(u'\xa0', '')
        answers.append(other_answer)
    answers = [emoji.demojize(a) for a in answers if len(a) > 0]

    print("title", title)
    print("answer", answer)
    print("=" * 50)
    print("answers", answers)
    print("*" * 100)

    return title, answer, answers


def crawler(keywords):
    for keyword in keywords:
        print("keyword：", keyword)
        cur_url = prefix_url(keyword)
        page_urls = page_url(cur_url)
        urls = sub_urls(page_urls)
        for url in urls:
            try:
                print("URL：", url)
                title, answer, answers = get_answers(url)
                print("title", title)
                # print("answer", answer)

                # with connection.cursor() as cursor:
                #
                #     sql = """insert into baiduzhidao(keyword,question,answer,url,answers) values ("{keyword}","{question}","{answer}","{url}","{answers}");""".format(
                #         keyword=pymysql.escape_string(keyword),
                #         question=pymysql.escape_string(title),
                #         answer=pymysql.escape_string(answer),
                #         url=pymysql.escape_string(url),
                #         answers=pymysql.escape_string(str(answers))
                #     )
                #     cursor.execute(sql)
                #
                #     connection.commit()
            except Exception as e:
                print(e)
            finally:
                pass
        continue


driver = start_chrome()
keywords = keywords()
crawler(keywords)
driver.quit()
