# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 22:12:24 2016

@author: waffleboy
"""
# meant to quickly find beginning and ending dates

import main
import single_link_scraper as backend
import datetime

def quickSearchStarting(page_URL,date):
    MARGIN_OF_ERROR = 2
    first_article_on_page_date = getFirstArticleDateOnPage(page_URL)
    REPEAT_500,REPEAT_100,REPEAT_50,REPEAT_10 = False,False,False,False
    dayDifference = (first_article_on_page_date - date).days
    while dayDifference >= MARGIN_OF_ERROR:
        if dayDifference > 500 and REPEAT_500 == False:
             REPEAT_500 = True
             page_URL,first_article_on_page_date = difference(date,page_URL,first_article_on_page_date,1000)
             continue
        if dayDifference > 100 and REPEAT_100 == False:
             REPEAT_100 = True
             page_URL,first_article_on_page_date = difference(date,page_URL,first_article_on_page_date,500)
             continue
        if dayDifference > 50 and REPEAT_50 == False:
             REPEAT_50 = True
             page_URL,first_article_on_page_date = difference(date,page_URL,first_article_on_page_date,50)
             continue
        if dayDifference > 10 and REPEAT_10 == False:
             REPEAT_10 = True
             page_URL,first_article_on_page_date = difference(date,page_URL,first_article_on_page_date,20)
             continue
        dayDifference2 = (first_article_on_page_date - date).days
        if dayDifference2 < dayDifference:
            dayDifference = dayDifference2
        else:
            break
        page_URL,first_article_on_page_date = difference(date,page_URL,first_article_on_page_date,1)
        
    page_URL = backTrackUntilHit(date,page_URL)
    return page_URL

def difference(date,page_URL,first_article_on_page_date,skipAmount):
    currentURL = page_URL
    dayDifference = (first_article_on_page_date - date).days
    while dayDifference > 0:
        pageNum = main.getPageNumberFromURL(currentURL)
        newPageCounter = pageNum + skipAmount
        newURL = makeNewURL(page_URL,newPageCounter)
        try:
            first_article_on_page_date2 = getFirstArticleDateOnPage(newURL)
        except:
            break
        dayDifference = (first_article_on_page_date2 - date).days
        if dayDifference < 0:
            break
        currentURL = newURL
        first_article_on_page_date = first_article_on_page_date2
    return currentURL,first_article_on_page_date

#dont miss out any articles
def backTrackUntilHit(date,page_URL):
    currentURL = page_URL
    first_article_on_page_date = getFirstArticleDateOnPage(currentURL)
    if first_article_on_page_date > date:
        return page_URL
    
    prevPage = currentURL
    while first_article_on_page_date <= date:
        prevPage = main.getPreviousArticlePage(prevPage)
        first_article_on_page_date = getFirstArticleDateOnPage(prevPage)
    return prevPage

def getFirstArticleDateOnPage(page_URL):
    articles = backend.scrapeLink(page_URL)
    first_article = articles.find('li',{'class':'first-item'})
    first_article_date = first_article.find('span',{'class':'date'}).text
    first_article_date_object = datetime.datetime.strptime(first_article_date,'%d %b %Y').date()
    return first_article_date_object
    
def makeNewURL(page_URL,newPageCounter):
    LAST_WORD = 'latest/'
    idx = page_URL.find(LAST_WORD) + len(LAST_WORD)
    return page_URL[:idx] + str(newPageCounter)
