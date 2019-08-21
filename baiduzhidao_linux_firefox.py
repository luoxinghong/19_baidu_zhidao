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
from pyvirtualdisplay import Display
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import NoSuchElementException
import time
import datetime
import os
import emoji
import pymysql
import glob
import json
import re


config = {'host': '106.12.8.109', 'port': 3306, 'user': 'root', 'passwd': 'lxh123', 'charset': 'utf8mb4',
          'cursorclass': pymysql.cursors.DictCursor, 'db': 'spider_data'}


def get_info():
    question_info = {"url": None, "keyword": None, "title": None, "question": None, "best_answer": None,
                     "best_name": None, "best_date": None, "answers": None, "second_questions": None}
    return question_info


def get_second_info():
    second_question_info = {"url": None, "title": None, "question": None, "best_answer": None,
                            "best_name": None, "best_date": None, "answers": None}
    return second_question_info


def start_chrome():
    display = Display(visible=0, size=(800, 600))
    display.start()
    binary = FirefoxBinary('/opt/selen_firefox/firefox/firefox')
    driver = webdriver.Firefox(firefox_binary=binary)
    return driver, display


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


def page_url(origi_url, page_num):
    pages_urls = []
    for i in range(page_num):
        link = origi_url + "&ie=gbk&site=-1&sites=0&date=0&pn={}".format(i * 10)
        pages_urls.append(link)
    return pages_urls


def parse_url(url):
    print("①parse_url  ", url)
    # 加载网页，获取问题title
    try:
        driver, display = start_chrome()
        driver.get(url)
        time.sleep(3)
        title = driver.find_element_by_class_name("ask-title").text
        print("②title  ", title)
    except Exception as e:
        driver.quit()
        display.stop()
        return "", "", "", "", "", "", "", ""

    # 爬取问题内容
    try:
        question = driver.find_element_by_class_name("conReal").text
    except:
        question = ""

    # 爬取最佳回复
    try:
        best = driver.find_element_by_css_selector('div.best-text').text
        bs1 = best.lstrip('展开全部\n')
        bs2 = bs1.replace('\n\n', '')
        answer = bs2.replace('\n', '')
        best_answer = emoji.demojize(answer)

        best_name = driver.find_element_by_css_selector('span.wgt-replyer-all-uname').text
        best_date = driver.find_element_by_css_selector('span.wgt-replyer-all-time').text.replace("推荐于", "")
    except:
        print("that have no best answer")
        best_answer, best_name, best_date = "", "", ""
    finally:
        print("③最佳回复：", best_answer)

    # 展开隐藏回复
    try:
        if driver.find_element_by_id('show-answer-hide').is_enabled():
            driver.find_element_by_id('show-answer-hide').click()
            time.sleep(1)
    except NoSuchElementException:
        pass
    try:
        if driver.find_element_by_css_selector('div.show-hide-dispute').is_enabled():
            driver.find_element_by_css_selector('div.show-hide-dispute').click()
            time.sleep(1)
    except NoSuchElementException:
        pass

    # 普通回复爬取
    other_answers_sels = driver.find_elements_by_class_name('answer-text')
    other_answers_names = driver.find_elements_by_class_name('wgt-replyer-all-uname')
    other_answers_dates = driver.find_elements_by_class_name('wgt-replyer-all-time')
    answers = []
    if len(other_answers_sels) > 0:
        for index_number, other in enumerate(other_answers_sels):
            ordinary_answer = {"name": None, "date": None, "content": None}
            other_ans = other.text
            other_ans_t1 = other_ans.lstrip('展开全部\n')
            other_ans_t2 = other_ans_t1.replace('\n\n', '')
            other_answer = other_ans_t2.replace('\n', '').replace(u'\u3000', '').replace(u'\xa0', '')
            other_answer = emoji.demojize(other_answer) if len(other_answer) > 0 else ""
            ordinary_answer["content"] = other_answer
            if best_answer == "":
                ordinary_answer["name"] = other_answers_names[index_number].text
                ordinary_answer["date"] = other_answers_dates[index_number].text.replace("推荐于", "")
            else:
                ordinary_answer["name"] = other_answers_names[index_number + 1].text
                ordinary_answer["date"] = other_answers_dates[index_number + 1].text.replace("推荐于", "")
            answers.append(ordinary_answer)
            print("④普通回复", ordinary_answer)

    related_urls1 = driver.find_elements_by_css_selector('a.related-link.related-link-zd')
    related_urls2 = driver.find_elements_by_css_selector('a.related-link.related-link-qy')
    related_urls = related_urls1 + related_urls2
    related_urls = [i.get_attribute("href") for i in related_urls]
    related_urls = [i for i in related_urls if "zhidao.baidu.com" in i]
    driver.quit()
    display.stop()
    print("⑤关联的url", related_urls)
    print("_" * 50)
    return url, title, question, best_answer, best_name, best_date, answers, related_urls


def handle_url(url, keyword):
    url, title, question, best_answer, best_name, best_date, answers, related_urls = parse_url(url)
    if title != "":
        second_questions = []
        if len(related_urls) > 0:
            for related_url in related_urls:
                second_question_info = get_second_info()
                s_url, s_title, s_question, s_best_answer, s_best_name, s_best_date, s_answers, s_related_urls = parse_url(
                    related_url)
                second_question_info["url"] = s_url
                second_question_info["title"] = s_title
                second_question_info["question"] = s_question
                second_question_info["best_answer"] = s_best_answer
                second_question_info["best_name"] = s_best_name
                second_question_info["best_date"] = s_best_date
                second_question_info["answers"] = s_answers
                second_questions.append(second_question_info)

        question_info = get_info()
        question_info["url"] = url
        question_info["title"] = title
        question_info["question"] = question
        question_info["best_answer"] = best_answer
        question_info["best_name"] = best_name
        question_info["best_date"] = best_date
        question_info["answers"] = answers
        question_info["second_questions"] = second_questions

        # total_file_number = glob.glob(pathname='./data/*.json')
        # file_id = len(total_file_number)
        # with open('data/{:0>4}.json'.format(file_id), 'w', encoding='utf-8') as f:
        #     f.write(json.dumps(question_info))
        #     f.close()


        try:
            sql = """insert into baiduzhidao(url,title,keyword,question,best_answer,best_name,best_date,answers,second_questions) values ("{url}","{title}","{keyword}","{question}","{best_answer}","{best_name}","{best_date}","{answers}","{second_questions}");""".format(
                url=pymysql.escape_string(url),
                title=pymysql.escape_string(title),
                keyword=pymysql.escape_string(keyword),
                question=pymysql.escape_string(question),
                best_answer=pymysql.escape_string(best_answer),
                best_name=pymysql.escape_string(best_name),
                best_date=pymysql.escape_string(best_date),
                answers=pymysql.escape_string(str(answers)),
                second_questions=pymysql.escape_string(json.dumps(second_questions, ensure_ascii=False))
            )
            conn = pymysql.connect(**config)
            conn.autocommit(1)
            cursor = conn.cursor()
            cursor.execute(sql)
        except:
            import traceback
            traceback.print_exc()
            # 发生错误时会滚
            conn.rollback()
        finally:
            # 关闭游标连接
            cursor.close()
            # 关闭数据库连接
            conn.close()


def crawler(keywords):
    page_num = 2
    for keyword in keywords:
        cur_url = prefix_url(keyword)
        page_urls = page_url(cur_url, page_num)
        for pageurl in page_urls:
            driver, display = start_chrome()
            driver.get(pageurl)
            links = driver.find_elements_by_css_selector('a.ti')
            links = [i.get_attribute('href') for i in links]
            links = [i for i in links if "zhidao.baidu.com" in i]
            for url in links:
                handle_url(url, keyword)
            driver.quit()
            display.stop()

if __name__ == "__main__":
    keywords = keywords()
    crawler(keywords)
