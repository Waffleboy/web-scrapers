# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 08:15:42 2016

@author: waffleboy
"""

from bs4 import BeautifulSoup
import requests, string,time,pickle,os,csv,re
import pandas as pd
from unidecode import unidecode
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
    by = soup.find(lambda elm: elm.name == "span" and "By" in elm.text)
    if not by:
        return None,None
    try:
        authorstag = by.findNext('h2')
        authorshref = authorstag.find('a')
        authors = authorshref.text
    except:
        return None,None
    
    author1 = authors
    author2 = None
    authorSplit = authors.split()
    if 'and' in authorSplit:
        andIdx  = authorSplit.index('and')
        author1 = ' '.join(authorSplit[:andIdx])
        author2 = ' '.join(authorSplit[andIdx+1:])
    return author1,author2
    
def getAuthorEmail(link,soup):
    emails = soup.find_all('a', href=re.compile('mailto'))
    if emails:
        if len(emails) != 1:
            print('WARNING: more than one email found for '+link)
            print('Returning first one found...')
        return emails[0].text
    
def getDatePublished(link,soup):
    dates = soup.findAll("div",{"class":["authoring","full-date"]})
    if dates:
        return dates[0].findAll("span")[1].text
    print("WARNING: No date for "+link)
    
def getTitle(link,soup):
    titles = soup.findAll("meta", {"property" : "twitter:title"})
    if titles:
        if len(titles) != 1:
            print('WARNING: more than one link found for '+link)
            print('Returning first one found...')
        return titles[0].get("content")
    
def getContent_PTags(link,soup):
    content = soup.findAll("div",{"class":"content"})
    if len(content) != 1:
         print('WARNING: more than one content tag found for '+link)
         print('Using first one found...')
    content = content[0]
    tags = content.findAll('p')
    return tags
    
def getContent_TextOnly(link,soup):
    tags = getContent_PTags(link,soup)
    text = ''
    for entry in tags:
        text += entry.text
    return text

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
   
