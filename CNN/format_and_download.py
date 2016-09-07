# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 08:28:53 2016

@author: waffleboy
"""
import csv,os
from collections import deque


def formatInputsToCSV(infoHash,CSV_NAME,category):
    initializeCSV(CSV_NAME)
    lastRow = get_last_row(CSV_NAME)
    if lastRow[0] == 'ArticleID':
        articleID = 1
    else:
        articleID = int(lastRow[0]) + 1
    addToCSV(infoHash,CSV_NAME,articleID,category)
    return 
    
def initializeCSV(CSV_NAME):
    if not os.path.exists(CSV_NAME):
        with open(CSV_NAME,'w',newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ArticleID','ParagraphID','PublishedTime','Author1','Author2',
                             'Headline','Text','Category'])
            f.close()
    return
    
def get_last_row(csv_filename):
    with open(csv_filename, 'r') as f:
        try:
            lastrow = deque(csv.reader(f), 1)[0]
        except IndexError:  # empty file
            lastrow = None
        return lastrow
        
def addToCSV(infoHash,CSV_NAME,articleID,category):
    with open(CSV_NAME,'a',newline='') as f:
        writer = csv.writer(f)
        rows = []
        
        author1 = infoHash['author1']
        author2 = infoHash['author2']
        date    = infoHash['date']
        title   = infoHash['title']
        content = infoHash['content']
        paragraphNumber = 1
        
        for p_tag in content:
            paragraph = str(p_tag) # with the <p> tag, else use .text instead
            rows.append([articleID,paragraphNumber,date,author1,author2,title,paragraph,
                         category])
            paragraphNumber += 1
        writer.writerows(rows)
    return