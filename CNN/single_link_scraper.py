# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 08:15:42 2016

@author: waffleboy
"""

from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent

# This file will scrape a single URL.

def randomUserAgentGenerator():
    ua = UserAgent()
    return ua.random
    
def scrapeLink(link):
    ob   = getHTMLText(link)
    soup = BeautifulSoup(ob, 'html.parser')
    return soup
    
def getHTMLText(link):
    headers = { 'User-Agent': randomUserAgentGenerator() }
    ob = requests.get(link,headers=headers).text
    return ob

def getAuthors(soup):
    by = soup.find("li",{'class':'news_byline'})
    if not by:
        return None,None
    try:
        authors = by.findAll('a')
        if authors:
            author1 = authors[0].text
            if len(authors) == 2:
                author2 = authors[1].text
            else:
                author2 = None
    except:
        return None,None
    return author1,author2
    
def getDatePublished(link,soup):
    dates = soup.findAll("li",{"class":"news_posttime"})
    if dates:
        return dates[0].contents[1].strip().rstrip()
    print("WARNING: No date for "+link)
    
def getTitle(link,soup):
    titles = soup.findAll("meta", {"property" : "og:title"})
    if titles:
        if len(titles) != 1:
            print('WARNING: more than one link found for '+link)
            print('Returning first one found...')
        return titles[0].get("content")
    
def getContent_PTags(link,soup):
    content = soup.findAll("div",{"class":"news_detail"})
    if len(content) != 1:
         print('WARNING: more than one content tag found for '+link)
         print('Using first one found...')
    content = content[0]
    tags = content.findAll('p')
    tags = [str(x) for x in tags]
    return tags

#main function. input: string link.
def run(link):
    soup    = scrapeLink(link)
    author1,author2 = getAuthors(soup)
    infoHash = {'author1' : author1,
                'author2' : author2,
                'date'   : getDatePublished(link,soup),
                #'email'  : getAuthorEmail(link,soup),
                'title'  : getTitle(link,soup),
                'content': getContent_PTags(link,soup) # change to text only if you want text only.
                }
    return infoHash
   
