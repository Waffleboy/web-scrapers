# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 22:12:24 2016

@author: waffleboy
"""
# meant to quickly find beginning and ending dates
# TO BE REFACTORED

import main
import single_link_scraper as backend

def quickSearchStarting(page_URL,date):
    MARGIN_OF_ERROR = 2
    first_article_on_page_date = getFirstArticleDateOnPage(page_URL)
    if not first_article_on_page_date:
        return page_URL
    REPEAT_500,REPEAT_100,REPEAT_50,REPEAT_10,REPEAT_5 = False,False,False,False,False
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
        if dayDifference > 5 and REPEAT_5 == False:
             REPEAT_5 = True
             page_URL,first_article_on_page_date = difference(date,page_URL,first_article_on_page_date,5)
             continue
        if not first_article_on_page_date:
            return page_URL
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
        pageNum = main.getPageNumberFromURL(currentURL) # may break for 0
        newPageCounter = pageNum + skipAmount
        newURL = makeNewURL(currentURL,newPageCounter)
        try:
            first_article_on_page_date2 = getFirstArticleDateOnPage(newURL)
        except:
            break
        if not first_article_on_page_date2:
            return currentURL,first_article_on_page_date
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

## these functions should be modified for new news websites
def getFirstArticleDateOnPage(page_URL):
    articles = backend.scrapeLink(page_URL)
    article = articles.find('div',{'id':['content-main']})
    first_article = article.find('h2',{'class':['node__title', 'node-title']})
    if not first_article:
        return None
    article_link = first_article.a.get('href')
    if 'todayonline.com' in article_link:
        first_article_url = article_link
    else:
        first_article_url  = 'http://www.todayonline.com'+article_link
    first_article_soup = backend.scrapeLink(first_article_url)
    first_article_date = backend.getDatePublished(first_article_url,first_article_soup)
    first_article_date_object = main.parseDate(first_article_date)
    return first_article_date_object
    
def makeNewURL(page_URL,newPageCounter):
    nextPageNum = newPageCounter
    if 'page' in page_URL:
        currPageIdx = page_URL.find('=')
        return page_URL[:currPageIdx + 1] + str(nextPageNum)
    return page_URL + '?page=' + str(nextPageNum - 1) #cause theres page 0 also
