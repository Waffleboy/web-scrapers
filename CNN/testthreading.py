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

from multiprocessing import Pool  # This is a thread-based Pool
from multiprocessing import cpu_count

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

pool = Pool(cpu_count() * 2)
GOAL = 6837+1
for i in range(6300,GOAL):
    lst.append('http://www.todayonline.com/world?page=' + str(i))

lst2 = []
results = pool.map(f, lst)
results = [item for sublist in results for item in sublist]

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
    storeHTML(entry,infoHash['date'],infoHash['title'],'world')
    return infoHash
    
pool.close()

n=150
chunks = [results[i:i + n] for i in range(0, len(results), n)]
chunkCounter = 1
for chunk in chunks:
    print('Doing chunk '+ str(chunkCounter) +' Out of ' + str(len(chunks)))
    chunkCounter += 1
    pool = Pool(cpu_count() * 2)
    counter = 0
    all_Infohashes = pool.map(runtest,chunk)
    pool.close()
    print('putting to CSV')
    for infoHash in all_Infohashes:
        if counter % 100 == 0:
            print('Putting file '+str(counter)+' of '+str(len(all_Infohashes)))
        counter += 1
        format_and_download.formatInputsToCSV(infoHash,CSV_NAME,'world')
