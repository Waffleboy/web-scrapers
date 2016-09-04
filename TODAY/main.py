# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 22:47:51 2016

@author: waffleboy
"""
import datetime,os,shutil,time
import single_link_scraper as backend
import format_and_download as formatter
import http
import pandas as pd #ONLY IF RESUME IS NEEDED
#==============================================================================
#                               Settings
#==============================================================================
DATE_FROM        = datetime.date(2014,7,1)
DATE_END         = datetime.date(2014,11,30)
BASE_FOLDER_NAME = 'Articles' #change if you want.
PRINT_PAGE_NUM   = True # set to False if you dont want to see the current page the scraper is on.

CURRENT_DATE = datetime.date.today()
HTML_SAVE_FOLDER = BASE_FOLDER_NAME+'/'+ 'HTML_2016-09-03' #BASE_FOLDER_NAME +'/'+ 'HTML_'+str(CURRENT_DATE)
CSV_NAME         = BASE_FOLDER_NAME + '/' + '2016-09-03.csv' #str(CURRENT_DATE) + '.csv'
# Dont touch below if not resuming from existing session
RESUME_FROM_PREVIOUS = False #Set to true if some error occured previously and run again
RESUME_CATEGORY = '' # Last category that it was scraping. will delete and restart from there.

# If you're resuming, comment out the categories that you've already downloaded.

CATEGORIES_TO_SCRAPE = {#'commentary'     :'http://www.todayonline.com/commentary',
                         # 'voices'       :'http://www.todayonline.com/voices',
                          #'singapore'    :'http://www.todayonline.com/singapore',
                          #'daily focus'  :'http://www.todayonline.com/daily-focus',
                          #'china & india':'http://www.todayonline.com/chinaindia',
                          #'world'        :'http://www.todayonline.com/world',
                          #'business'     :'http://www.todayonline.com/business',
                          'tech'         :'http://www.todayonline.com/tech',
                          #'sports'       :'http://www.todayonline.com/sports',
                          #'entertainment':'http://www.todayonline.com/entertainment',
                         # 'lifestyle'    :'http://www.todayonline.com/lifestyle',
                         # 'blogs'        :'http://www.todayonline.com/blogs'
                         }
                       
## DO NOT TOUCH THE FOLLOWING ##
http.client._MAXHEADERS = 1000
BASE_LINK = 'http://www.todayonline.com'

#==============================================================================
def initialize():
    print('Creating folders..')
    global BASE_FOLDER_NAME,HTML_SAVE_FOLDER
    if not os.path.exists(BASE_FOLDER_NAME):
        os.mkdir(BASE_FOLDER_NAME)
    if not os.path.exists(HTML_SAVE_FOLDER):
        os.mkdir(HTML_SAVE_FOLDER)
    return
    
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

def getURLFromArticle(BASE_LINK,article):
    if article.name == 'h2':
        return BASE_LINK + article.a.get('href')

def downloadOrSkip(URL,category):
    global HTML_SAVE_FOLDER,CSV_NAME
    soup = backend.scrapeLink(URL)
    date = backend.getDatePublished(URL,soup)
    BREAK = False
    try:
        date_object = parseDate(date)
        date_object = date_object.date()
    except:
        raise Exception("Error in making date_object for "+URL)
    if date_object >= DATE_FROM and date_object <= DATE_END:
        infoHash = backend.run(URL)
        save = storeHTML(URL,infoHash['date'],infoHash['title'],category)
        if save:
            formatter.formatInputsToCSV(infoHash,CSV_NAME,category)
    elif date_object > DATE_END:
        pass
    elif date_object < DATE_FROM:
        BREAK = True
    else:
        print('Possible Error for downloadOrSkip for URL '+ URL)
        
    return BREAK,date_object

def parseDate(date):
    return datetime.datetime.strptime(date, '%I:%M %p, %B %d, %Y')
    
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

#Unneeded because of quick search, can replace safely with getnexturl
def getNextPageURL_Accelerate(link,current_date):
    global DATE_FROM,DATE_END
    if 'page' not in link:
        return link + '?page=1'
        
    current_page = getPageNumberFromURL(link)
    if current_date > DATE_END:
        dayDifference = (current_date - DATE_END).days
        if PRINT_PAGE_NUM:
            print('Skipping ahead to find correct date..')
        current_page = naiveForward(dayDifference,current_page)
        link = link[:link.find('=') + 1]
        return link + str(current_page)
    
    return getNextURL_normal(link)
    
def getPageNumberFromURL(link):
    if 'page' not in link:
        return
    currPageIdx = link.find('=')
    currPageNum = link[currPageIdx+1:]
    return int(currPageNum)
            
def getNextURL_normal(link):
     if 'page' in link:
        currPageIdx = link.find('=')
        currPageNum = link[currPageIdx+1:]
        nextPageNum = str( int(currPageNum) + 1 )
        return link[:currPageIdx + 1] + nextPageNum
     return link + '?page=1'

#==============================================================================
#        Quick find starting point to speed things up - NEED REFACTOR
#==============================================================================
def quickSearchStarting(category_URL):
    global DATE_END,PRINT_PAGE_NUM
    if PRINT_PAGE_NUM:
        print('Beginning quick search for starting page')
    MARGIN_OF_ERROR = 5 #days - risky cause might crash if dont have
    first_article_on_page_date = getFirstArticleDateOnPage(category_URL)
    REPEAT_500,REPEAT_100,REPEAT_50,REPEAT_10 = False,False,False,False
    dayDifference = (first_article_on_page_date - DATE_END).days
    while dayDifference >= MARGIN_OF_ERROR:
        if dayDifference > 500 and REPEAT_500 == False:
             REPEAT_500 = True
             category_URL,first_article_on_page_date = difference(category_URL,first_article_on_page_date,1000)
             continue
        if dayDifference > 100 and REPEAT_100 == False:
             REPEAT_100 = True
             category_URL,first_article_on_page_date = difference(category_URL,first_article_on_page_date,500)
             continue
        if dayDifference > 50 and REPEAT_50 == False:
             REPEAT_50 = True
             category_URL,first_article_on_page_date = difference(category_URL,first_article_on_page_date,50)
             continue
        if dayDifference > 10 and REPEAT_10 == False:
             REPEAT_10 = True
             category_URL,first_article_on_page_date = difference(category_URL,first_article_on_page_date,20)
             continue
        dayDifference2 = (first_article_on_page_date - DATE_END).days
        if dayDifference2 < dayDifference:
            dayDifference = dayDifference2
        else:
            break
        category_URL,first_article_on_page_date = difference(category_URL,first_article_on_page_date,1)
        
    category_URL = backTrackUntilHit(category_URL)
    return category_URL

def difference(category_URL,first_article_on_page_date,skipAmount):
    currentURL = category_URL
    dayDifference = (first_article_on_page_date - DATE_END).days
    while dayDifference > 0:
        pageNum = getPageNumberFromURL(currentURL)
        if pageNum:
            newPageCounter = int(pageNum) + skipAmount
            newURL = currentURL[:currentURL.find('=') + 1] + str(newPageCounter)
        else:
            newPageCounter = skipAmount
            newURL = currentURL+'?page=1'
        try:
            first_article_on_page_date2 = getFirstArticleDateOnPage(newURL)
        except:
            break
        dayDifference = (first_article_on_page_date2 - DATE_END).days
        if dayDifference < 0:
            break
        currentURL = newURL
        first_article_on_page_date = first_article_on_page_date2
    return currentURL,first_article_on_page_date

#dont miss out any articles
def backTrackUntilHit(category_URL):
    global PRINT_PAGE_NUM,DATE_END
    if PRINT_PAGE_NUM:
        print('Backtracking..')
    currentURL = category_URL
    first_article_on_page_date = getFirstArticleDateOnPage(currentURL)
    if first_article_on_page_date > DATE_END:
        return category_URL
    
    prevPage = currentURL
    while first_article_on_page_date <= DATE_END:
        prevPage = getPreviousPage(prevPage)
        first_article_on_page_date = getFirstArticleDateOnPage(prevPage)
    return prevPage
###############################################################################
    
def getPreviousPage(link):
    pageNum = getPageNumberFromURL(link)
    pageNum = str( int(pageNum) - 1 )
    newURL = link[:link.find('=') + 1] + pageNum
    return newURL
    
    
def getFirstArticleDateOnPage(category_URL):
    articles = getArticleDivsOnPage(category_URL)
    first_article = stripURLSFromAllArticles(BASE_LINK,articles)[0]
    first_article_date = parseDate(backend.run(first_article)['date']).date()
    return first_article_date

#dont need this anymore
def naiveForward(dayDifference,current_page):
    if dayDifference > 100:
        current_page += 50
    elif dayDifference > 50:
        current_page += 10
    elif dayDifference > 20:
        current_page += 2
    else:
        current_page += 1
    return current_page

def shouldAccelerate(current_date):
    global DATE_END
    if (current_date - DATE_END).days > 20:
        return True
    return False
    
#not in use
def randomDelay():
    time.sleep(1)
    return
    
# used for resume. delete last category and start from there.
def deleteLastCategory(category_name):
    global HTML_SAVE_FOLDER,CSV_NAME
    try:
        shutil.rmtree(HTML_SAVE_FOLDER+'/'+category_name)
    except:
        print('Could not delete last category for resume - is the name correct?')
    
    try:
        df = pd.read_csv(CSV_NAME)
        df2 = df[df['category'] == category_name]
        df2.to_csv(CSV_NAME,index=False)
    except:
        print('Could not remove incomplete entries from category. Is the name correct and does the file exist?')
    return

def initializeOrResume(RESUME_FROM_PREVIOUS):
    if not RESUME_FROM_PREVIOUS:    
        initialize() #prepare directory
    else:
        deleteLastCategory(RESUME_CATEGORY)
    return

def downloadAllArticlesOnPage(articles,article_URLS,category,BREAK):
    for url in article_URLS:
                #print(url)
        if not BREAK:
            if len(articles) == 0: #no articles found
                BREAK = True
                continue
            BREAK,current_date = downloadOrSkip(url,category)
            if shouldAccelerate(current_date): #hacky, fix later.
                break
        else:
            break
    
    return
    
def downloadAllArticles(articles,article_URLS,category,BREAK):
    for url in article_URLS: 
        if not BREAK:
            if len(articles) == 0: #no articles found
                BREAK = True
                continue
            BREAK,current_date = downloadOrSkip(url,category)
            if shouldAccelerate(current_date): #hacky, fix later.
                break
        else:
            break
    return BREAK
    
def run():
    global DATE_FROM,DATE_END,BASE_LINK,CATEGORIES_TO_SCRAPE,PRINT_PAGE_NUM,RESUME_FROM_PREVIOUS,RESUME_CATEGORY
    initializeOrResume(RESUME_FROM_PREVIOUS)
    OVERRIDE = False
    for category in CATEGORIES_TO_SCRAPE:
        print('Scraping category: ' + category)
        BREAK = False
        if OVERRIDE:
            nextPage_URL = 'http://www.todayonline.com/world?page=6013'
            OVERRIDE = False
        else:
            category_URL = CATEGORIES_TO_SCRAPE[category]
            nextPage_URL = quickSearchStarting(category_URL)
            
        pageNum = getPageNumberFromURL(nextPage_URL)
        while (BREAK == False and nextPage_URL):
            if PRINT_PAGE_NUM:
                print('Investigating and Scraping page '+ str(pageNum) + ' of category '+category + '...')
                
            articles = getArticleDivsOnPage(nextPage_URL)
            article_URLS = stripURLSFromAllArticles(BASE_LINK,articles)
            
            for url in article_URLS: 
                #print(url)
                if not BREAK:
                    if len(articles) == 0: #no articles found
                        BREAK = True
                        continue
                    BREAK,current_date = downloadOrSkip(url,category)
                    if shouldAccelerate(current_date): #hacky, fix later.
                        break
                else:
                    break
            
            nextPage_URL = getNextPageURL_Accelerate(nextPage_URL,current_date)
            pageNum = getPageNumberFromURL(nextPage_URL)
    print('Scraping complete!')
    return
    
    
if __name__ == '__main__':
    run()
    
    
    
    
    