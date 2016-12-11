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
import pandas as pd # for resuming

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
TIME_DELAY       = 60*20 # time to pause after every 4 chunks downloaded. decreasing makes it faster, but might get disconnected.

# Important: if you're disconnected for any reason (internet problems etc), comment out finished
#           categories in CATEGORIES_TO_SCRAPE, and run again. Then, run
#           dropDuplicatedRows(path_to_csv) to remove  duplicated rows from the CSV file.

# If you're resuming, comment out the categories that you've already downloaded.

CATEGORIES_TO_SCRAPE = {'commentary'     :'http://www.todayonline.com/commentary',
                         'voices'       :'http://www.todayonline.com/voices',
                         'singapore'    :'http://www.todayonline.com/singapore',
                          'daily focus'  :'http://www.todayonline.com/daily-focus',
                          'china & india':'http://www.todayonline.com/chinaindia',
                          'world'        :'http://www.todayonline.com/world',
                          'business'     :'http://www.todayonline.com/business',
                          'tech'         :'http://www.todayonline.com/tech',
                          'sports'       :'http://www.todayonline.com/sports',
                          'entertainment':'http://www.todayonline.com/entertainment',
                         'lifestyle'    :'http://www.todayonline.com/lifestyle',
                          'blogs'        :'http://www.todayonline.com/blogs'
                         }
                       
## DO NOT TOUCH THE FOLLOWING ##
http.client._MAXHEADERS = 1000
BASE_LINK = 'http://www.todayonline.com'
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
            print('Beginning URL found! - '+ beginURL)
        endURL   = quicksearcher.quickSearchStarting(category_URL,DATE_FROM - datetime.timedelta(2))
        if VERBOSE:
            print('Ending URL found! - '+ endURL)
        articlePageURLs = getAllArticlePageURLSInRange(beginURL,endURL)
        if VERBOSE:
            print('Getting all article URLs from page range...')
        articleURLs     = getArticleURLsFromArticlePageURLS(articlePageURLs)
        if VERBOSE:
            print('Raw article count: '+str(len(articleURLs)))
            print('Filtering excess articles not in date range...')
        articleURLs     = filterDateRange(articleURLs,DATE_FROM,DATE_END)
        if VERBOSE:
            print('Actual Count after filtering: '+str(len(articleURLs)))
        n = 150 #chunk size for pool-ed scraping
        chunks = [articleURLs[i:i + n] for i in range(0, len(articleURLs), n)]
        if not chunks:
            print('No articles found for category ' + category + ' in specified date range! Skipping..')
        scrapeChunksUsingPooling(chunks,category)

    print('Scraping complete!')
    return

def scrapeChunksUsingPooling(chunks,category):
    global VERBOSE,TIME_DELAY
    chunkCounter = 1
    for chunk in chunks:
        if chunkCounter % 4 == 0:
            delay(TIME_DELAY)
        print('Doing chunk '+ str(chunkCounter) +' Out of ' + str(len(chunks)))
        chunkCounter += 1
        try:
            pool = Pool(cpu_count() * 2)
            all_Infohashes = pool.map(downloadURL,chunk)
            pool.close()
        except ConnectionError as e:
            print(e) #temp hack
            pool.close()
            url = 'http://' + e[e.find('www.'):e.find('(Caused')].rstrip().strip()
            new_Chunk = [x for x in chunk if url not in x]
            print('Resting for 10 minutes and trying again..')
            time.sleep(600)
            pool = Pool(cpu_count() * 2)
            all_Infohashes = pool.map(downloadURL,new_Chunk)
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
    lastWord = 'page='
    skip = len(lastWord)
    if lastWord in url:
        return url[:url.find(lastWord)+skip]
    return url
    
#==============================================================================
#               Get and Strip All articles on a specific page.
#==============================================================================
def getArticleTagsOnPage(link):
    global BASE_LINK
    soup = backend.scrapeLink(link)
    inner = soup.find('div',{'id':'content-main'})
    articles = inner.findAll('h2',{'class':['node__title','node-title']})
    return articles
    
def stripURLSFromAllArticles(articles):
    global BASE_LINK
    URLS = [BASE_LINK + x.a.get('href') if (x.a.get('href').count('todayonline') == 0) else x.a.get('href') for x in articles] #hack
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
    lastWord = 'page='
    if lastWord in link:
         currPageIdx = link.find(lastWord)
         skip = len(lastWord)
         currPageNum = link[currPageIdx + skip:]
         return int(currPageNum)
    return 0
            
        
def getPreviousArticlePage(link):
    lastWord = 'page='
    if lastWord not in link:
        return link
    skip = len(lastWord)
    pageNum = getPageNumberFromURL(link)
    pageNum = str( int(pageNum) - 1 )
    newURL = link[:link.find(lastWord) + skip] + pageNum
    return newURL
    
def getNextArticlePage(link):
     if 'page' in link:
        currPageIdx = link.find('=')
        currPageNum = link[currPageIdx+1:]
        nextPageNum = str( int(currPageNum) + 1 )
        return link[:currPageIdx + 1] + nextPageNum
     return link + '?page=1'

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
    endIdx   = len(articleURLs)
    if endIdx > 30:
        delay(600)
    # filter out everything earlier than the DATE_END
    for i in range(len(articleURLs)):
        currArticle = articleURLs[i]
        soup = backend.scrapeLink(currArticle)
        date = backend.getDatePublished(currArticle,soup)
        date = parseDate(date)
        if date <= DATE_END:
            beginIdx = i
            break
        
    for i in range(len(articleURLs)-1,-1,-1):
        currArticle = articleURLs[i]
        soup = backend.scrapeLink(currArticle)
        date = backend.getDatePublished(currArticle,soup)
        date = parseDate(date)
        if i == len(articleURLs)-1: # first
            if date >= DATE_FROM:
                endIdx = i
                break
        if date <= DATE_FROM:
            endIdx = i
            break
        
    return articleURLs[beginIdx:endIdx+1]

def parseDate(date):
    return datetime.datetime.strptime(date, '%I:%M %p, %B %d, %Y').date()

def delay(n):
    print('Pausing to avoid being disconnected..')
    time.sleep(n)
    return

def dropDuplicatedRows(filePath):
    df = pd.read_csv(filePath)
    df = df.drop_duplicates()
    df.to_csv(filePath,index=False)
    
if __name__ == '__main__':
    run()