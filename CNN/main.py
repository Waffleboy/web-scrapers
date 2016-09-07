# -*- coding: utf-8 -*-
"""
Created on Mon Sep 5 20:42:50 2016

@author: waffleboy
"""
import datetime,os,time
import single_link_scraper as backend
import format_and_download as formatter
import quicksearcher
import http

from multiprocessing import Pool
from multiprocessing import cpu_count

#==============================================================================
#                               Settings
#==============================================================================
DATE_FROM        = datetime.date(2014,7,1)
DATE_END         = datetime.date(2014,11,30)
BASE_FOLDER_NAME = 'Articles' #change if you want.
VERBOSE   = True # set to False if you dont want to see the current page the scraper is on.

CURRENT_DATE = datetime.date.today()
HTML_SAVE_FOLDER = BASE_FOLDER_NAME+'/'+ 'HTML_'+str(CURRENT_DATE)
CSV_NAME         = BASE_FOLDER_NAME + '/' + str(CURRENT_DATE) + '.csv'
# Dont touch below if not resuming from existing session
RESUME_FROM_PREVIOUS = False #Set to true if some error occured previously and run again
RESUME_CATEGORY = '' # Last category that it was scraping. will delete and restart from there.

# If you're resuming, comment out the categories that you've already downloaded.

CATEGORIES_TO_SCRAPE = { 'ASIA PACIFIC' :'http://www.channelnewsasia.com/archives/4760/Asia%20Pacific/fouryears/latest/0',
                         'SINGAPORE'    :'http://www.channelnewsasia.com/archives/3636/Singapore/fouryears/latest/0',
                         'WORLD'        :'http://www.channelnewsasia.com/archives/3032/World/fouryears/latest/0',
                         'BUSINESS'     :'http://www.channelnewsasia.com/archives/3638/Business/fouryears/latest/0',
                         'SPORT'        :'http://www.channelnewsasia.com/archives/4650/Sport/fouryears/latest/0',
                         'ENTERTAINMENT':'http://www.channelnewsasia.com/archives/3640/Entertainment/fouryears/latest/0',
                         'TECHNOLOGY'   :'http://www.channelnewsasia.com/archives/4616/Technology/fouryears/latest/0',
                         'HEALTH'       :'http://www.channelnewsasia.com/archives/4772/Health/fouryears/latest/0',
                         'LIFESTYLE'    :'http://www.channelnewsasia.com/archives/4810/Lifestyle/fouryears/latest/0'
                         }
                       
## DO NOT TOUCH THE FOLLOWING ##
http.client._MAXHEADERS = 1000
BASE_LINK = 'http://www.channelnewsasia.com'
CURRENT_CATEGORY = ''
#==============================================================================

def run():
    global DATE_FROM,DATE_END,CATEGORIES_TO_SCRAPE,RESUME_FROM_PREVIOUS,RESUME_CATEGORY,VERBOSE, CURRENT_CATEGORY
    initializeOrResume(RESUME_FROM_PREVIOUS)
    for category in CATEGORIES_TO_SCRAPE:
        CURRENT_CATEGORY = category
        print('Scraping category: ' + category)
        category_URL = CATEGORIES_TO_SCRAPE[category]
        beginURL  = quicksearcher.quickSearchStarting(category_URL,DATE_END)
        if VERBOSE:
            print('Beginning URL found! - '+beginURL)
        endURL   = quicksearcher.quickSearchStarting(category_URL,DATE_FROM - datetime.timedelta(1))
        if VERBOSE:
            print('Ending URL found! - '+ endURL)
        articlePageURLs = getAllArticlePageURLSInRange(beginURL,endURL)
        articleURLs     = getArticleURLsFromArticlePageURLS(articlePageURLs)
        articleURLs     = filterDateRange(articleURLs,DATE_FROM,DATE_END)
        n = 150 #chunk size for pool-ed scraping
        chunks = [articleURLs[i:i + n] for i in range(0, len(articleURLs), n)]
        if not chunks:
            print('No articles found for category ' + category + ' in specified date range! Skipping..')
        scrapeChunksUsingPooling(chunks,category)

    print('Scraping complete!')
    return

def scrapeChunksUsingPooling(chunks,category):
    global VERBOSE
    chunkCounter = 1
    for chunk in chunks:
        print('Doing chunk '+ str(chunkCounter) +' Out of ' + str(len(chunks)))
        chunkCounter += 1
        pool = Pool(cpu_count() * 2)
        all_Infohashes = pool.map(downloadURL,chunk)
        pool.close()
        print('putting to CSV')
        for infoHash in all_Infohashes:
            formatter.formatInputsToCSV(infoHash,CSV_NAME,category)

def downloadURL(current_url):
    global CURRENT_CATEGORY
    category = CURRENT_CATEGORY
    infoHash = backend.run(current_url)
    storeHTML(current_url,infoHash['date'],infoHash['title'],category)
    return infoHash
    
    
###############################################################################
#                              HELPER FUNCTIONS
###############################################################################

#==============================================================================
#               generate all article urls to scrape
#==============================================================================

def getAllArticlePageURLSInRange(beginURL,endURL):
    beginPageNum = getPageNumberFromURL(beginURL)
    endPageNum   = getPageNumberFromURL(endURL)
    base         = getBaseLink(beginURL)
    lst = []
    for i in range(beginPageNum,endPageNum+1):
        lst.append(base+str(i))
    return lst
    
def getArticleURLsFromArticlePageURLS(articlePageURLs):
    pool = Pool(cpu_count() * 2)
    # maps over the entire list
    results = pool.map(getURLSFromSingleArticlePage, articlePageURLs)
    results = [item for sublist in results for item in sublist]
    pool.close()
    return results

def getURLSFromSingleArticlePage(link):
    articles = getArticleTagsOnPage(link)
    URLS = stripURLSFromAllArticles(articles)
    return URLS
    
def getBaseLink(url):
    lastWord = 'latest/'
    skip = len(lastWord)
    return url[:url.find(lastWord)+skip]
    
#==============================================================================
#               Get and Strip All articles on a specific page.
#==============================================================================
def getArticleTagsOnPage(link):
    soup = backend.scrapeLink(link)
    inner = soup.find('div',{'class':'archive-section'})
    articles = inner.findAll('h2')
    return articles
    
def stripURLSFromAllArticles(articles):
    global BASE_LINK
    URLS = [BASE_LINK + x.a.get('href') for x in articles]
    return URLS
    
#==============================================================================
#                   Miscellaneous  functions
#==============================================================================

def initializeOrResume(RESUME_FROM_PREVIOUS):
    if not RESUME_FROM_PREVIOUS:    
        initialize() #prepare directory
    else:
        pass
    return
    
# initialize csv
def initialize():
    print('Creating folders..')
    global BASE_FOLDER_NAME,HTML_SAVE_FOLDER
    if not os.path.exists(BASE_FOLDER_NAME):
        os.mkdir(BASE_FOLDER_NAME)
    if not os.path.exists(HTML_SAVE_FOLDER):
        os.mkdir(HTML_SAVE_FOLDER)
    return


def getPageNumberFromURL(link):
    lastWord = 'latest/'
    currPageIdx = link.find(lastWord)
    skip = len(lastWord)
    currPageNum = link[currPageIdx + skip:]
    return int(currPageNum)
            
        
def getPreviousArticlePage(link):
    lastWord = 'latest/'
    skip = len(lastWord)
    pageNum = getPageNumberFromURL(link)
    pageNum = str( int(pageNum) - 1 )
    newURL = link[:link.find(lastWord) + skip] + pageNum
    return newURL
    
def getNextArticlePage(link):
    lastWord = 'latest/'
    skip = len(lastWord)
    pageNum = getPageNumberFromURL(link)
    pageNum = str( int(pageNum) + 1 )
    newURL = link[:link.find(lastWord) + skip] + pageNum
    return newURL


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

# is there a better way of doing this?
def filterDateRange(articleURLs,DATE_FROM,DATE_END):
    beginIdx = 0
    endIdx   = 0
    # filter out everything earlier than the DATE_END
    for i in range(len(articleURLs)):
        currArticle = articleURLs[i]
        soup = backend.scrapeLink(currArticle)
        date = backend.getDatePublished(currArticle,soup)
        date = parseDate(date)
        if date <= DATE_END:
            beginIdx = i
            break
        
    for i in range(0,len(articleURLs),-1):
        currArticle = articleURLs[i]
        soup = backend.scrapeLink(currArticle)
        date = backend.getDatePublished(currArticle,soup)
        date = parseDate(date)
        if date <= DATE_FROM:
            endIdx = i
            break
        
    return articleURLs[beginIdx:endIdx+1]

def parseDate(date_string):
    return datetime.datetime.strptime(date_string,'%d %b %Y %H:%M').date()
    
def randomDelay():
    time.sleep(30)
    return

if __name__ == '__main__':
    run()