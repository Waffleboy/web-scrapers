# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 18:28:50 2016

@author: waffle
"""

import threading
import datetime,os,shutil,time
import single_link_scraper as backend
import format_and_download
import http
import pandas as pd #ONLY IF RESUME IS NEEDED

lst = []
http.client._MAXHEADERS = 1000

BASE_LINK= 'http://www.todayonline.com'

BASE_FOLDER_NAME = 'Articles' #change if you want.
PRINT_PAGE_NUM   = True # set to False if you dont want to see the current page the scraper is on.

CURRENT_DATE = datetime.date.today()
HTML_SAVE_FOLDER = BASE_FOLDER_NAME+'/'+ 'HTML_2016-09-03' #BASE_FOLDER_NAME +'/'+ 'HTML_'+str(CURRENT_DATE)
CSV_NAME         = BASE_FOLDER_NAME + '/' + '2016-09-03.csv' #str(CURRENT_DATE) + '.csv'

def getURLFromArticle(BASE_LINK,article):
    if article.name == 'h2':
        return BASE_LINK + article.a.get('href')

def getArticleDivsOnPage(link):
    soup = backend.scrapeLink(link)
    inner = soup.find('div',{'class':'inner'})
    articles = inner.findAll('h2',{'class':['node__title','node-title']})
    return articles
    
def stripURLSFromAllArticles(BASE_LINK,articles):
    URLS = []
    for article in articles:
        URLS.append(getURLFromArticle(BASE_LINK,article))
    return URLS

def f(link):
    global BASE_LINK
    articles = getArticleDivsOnPage(link)
    URLS = stripURLSFromAllArticles(BASE_LINK,articles)
    return URLS
    
for i in range(1,10):
    lst.append(f('http://www.todayonline.com/business?page=' + str(i)))

lst = [item for sublist in lst for item in sublist]


def storeHTML(URL,date,title,category):
    global CURRENT_DATE,HTML_SAVE_FOLDER
    saveFolder = HTML_SAVE_FOLDER+'/'+category
    if not os.path.exists(saveFolder):
        os.mkdir(saveFolder)
    title = title.replace('/', '_')
    ob = backend.getHTMLText(URL)
    filename = title + '.html'
    # if already have, dont add again
    if os.path.exists(saveFolder+'/'+filename):
        return False
    Html_file = open(saveFolder+'/'+filename,"w")
    Html_file.write(ob)
    Html_file.close()
    return True
    
def runtest(entry):
    infoHash = backend.run(entry)
    format_and_download.formatInputsToCSV(infoHash,'test.csv','business')
    storeHTML(entry,infoHash['date'],infoHash['title'],'business')

for entry in lst:
    t = threading.Thread(target=runtest, args = (entry,))
    t.daemon = True
    t.start()