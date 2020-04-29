# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 15:32:47 2020

@author: jvan1
"""
import warnings
import requests
import re 
from bs4 import BeautifulSoup
from textblob import TextBlob
import json
from flask import Flask, request
import spacy
import nltk
from flask import render_template
from collections import Counter
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from nltk.sentiment.vader import SentimentIntensityAnalyzer

warnings.filterwarnings('ignore')
nlp = spacy.load("en_core_web_lg")
app = Flask(__name__)
name_dict = dict()

def word_cloud(tweets):
    stopwords = set(STOPWORDS)
    all_words = ' '.join([text for text in tweets])
    wordcloud = WordCloud(
        background_color='white',
        stopwords=stopwords,
        width=1600,
        height=800,
        random_state=21,
        colormap='jet',
        max_words=50,
        max_font_size=200).generate(all_words)
    plt.figure(figsize = (8, 8), facecolor = None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad = 0)
    return plt
def sentiment(tweets):
    sid = SentimentIntensityAnalyzer()
    results = ''
    sent_list = []
    for tweet in tweets:
        scores = sid.polarity_scores(tweet)
    
        for key in sorted(scores):
            sent_list.append('{0}: {1} '.format(key, scores[key]))
    
        if scores["compound"] >= 0.05:
            sent_list.append('Positive')
    
        elif scores["compound"] <= -0.05:
            sent_list.append('Negative')
        else:
            sent_list.append('Neutral')
    results = '<br/>'.join(sent_list)
    return results
            
            
            
def poscount(tweets):
    results = ''
    count_list = []
    for tweet in tweets:
        lower_case = tweet.lower()
        count_list.append(lower_case)
        tokens = nltk.word_tokenize(lower_case)
        tags = nltk.pos_tag(tokens)
        counts = dict(Counter( tag for word,  tag in tags))
        for key in list(counts.keys()):
            count_list.append(str(key)+': '+str(counts[key]))
    results = '<br/>'.join(count_list)
    return results
def extractTweet(tweet):
    tweet = tweet.split('replies')[0].split('reply')[0]
    find_last_n = tweet[::-1].find('\n')
    tweet = tweet[::-1][find_last_n:][::-1]
    tweet=tweet.replace('\n',' ')
    if 'pic.twitter.com' in tweet:
        tweet = tweet.split('pic.twitter.com')[0]
    elif 'twitter.com' in tweet:
        tweet = tweet.split('twitter.com')[0]
    if 'http' in tweet:
        tweet = tweet.split('http')[0]
    return tweet
def similarity(tweets):
    
    blob = TextBlob(' '.join(tweets).strip('\''))
    words = blob.noun_phrases
    words = [x for word in words for x in word.lower().split(' ') ]
    count = [blob.words.count(x) for x in words]
    if len(count)>0:
        
        nlp_list = []
        for i in range(len(list(set(words)))):
            tweet = list(set(words))[i]
            for j in range(i,len(list(set(words)))):
                tweet2 = list(set(words))[j]
                if tweet.lower() == tweet2:
                    continue
                token1 = nlp(tweet.lower())
                token2 = nlp(tweet2)
                similarity = token1.similarity(token2)
                nlp_list.append((tweet,tweet2,str(similarity)))
        nlp_list.sort(key = lambda x: x[2])
        return tuple([' '.join(x) for x in nlp_list[0:5]])
def loadTweets(username):
    url = "http://www.twitter.com/" + username
    response = requests.get(url)
    soup = BeautifulSoup(response.text,'lxml')
    tweets = soup.get_text().split('Thanks. Twitter will use this to make your timeline better.')[0:]
    tweets = [extractTweet(x.split('Embed Tweet')[-1]) for x in tweets if 'Retweeted' not in x.split('replies')[0].split('reply')[0]][:-1]
    tweets = [x for x in tweets if len(x)!=0]
    tweets = [re.sub(r'[^a-zA-Z0-9 ]','',x.replace('-',' ')) for x in tweets]
    return tuple(tweets)
def printTweets(tweets):
    return tweets
@app.route('/<name>_<function>', methods=['GET'])
def getTwitterUsername(name,function):
    attempted_username = name
    past_results = ''
    function_list = [printTweets,similarity,word_cloud,sentiment,poscount]
    try:
        function_to_call_list = [int(x) for x in function.split('+')]
    except:
        function_to_call_list = []
        past_results = 'HTTP 400 Bad Request - Bad Function Syntax'
    if len([x for x in function_to_call_list if x < len(function_list)])==0:
        past_results = 'HTTP 400 Bad Request - Function not found'
        function_to_call_list = []
    tweets = loadTweets(attempted_username)
    if len(past_results)==0:
        past_results = analyzeTweets(name,tweets,function_to_call_list)
    name_dict[name] = past_results
    return past_results
            #return past_results
@app.route('/Analyze',methods=['POST'])
def getPostRequest():
    past_results = ''
    try:
        name = request.values['name']
    except:
        past_results = 'HTTP 400 Bad Request - Name not found'
    try:
        tweet = request.values['tweets']
        tweet = tweet.split('+')
        print(tweet)
    except:
        past_results = 'HTTP 400 Bad Request - Tweets not found'
    try:
        functions = request.values['functions']
        try:
            functions = [int(x) for x in functions.split('+')]
        except:
            functions = []
            past_results = 'HTTP 400 Bad Request - Bad Function Syntax'
    except:
        past_results = 'HTTP 400 Bad Request - Functions not found'
    if len(past_results)==0:
        past_results = analyzeTweets(name,tweet,functions)
        name_dict[name] = past_results
    return past_results
def analyzeTweets(name,tweets,function_to_call_list):
    function_list = [printTweets,similarity,word_cloud,sentiment,poscount]
    function_header = ['Tweets from this account:','Similarity between words:','Word Cloud:','Sentiment:','Parts of Speech Tagging:']
    past_results = ''
    if len(tweets)==0:            
        past_results = 'HTTP 400 - User has no available tweets'
        function_to_call_list = []
    for function_to_call in function_to_call_list:
        if function_to_call != 2:
            result = function_list[function_to_call](tweets)
            if type(result) == type(()):
                result = '<br/>'.join(result)
            past_results = '<br/>'.join((past_results,function_header[function_to_call],result))
    if 2 in function_to_call_list:
        plt = function_list[2](tweets)
        plt.savefig('static/images/'+name+'.png')
        past_results = '<br/>'.join((past_results,function_header[2]))
        return render_template('tweetsWordCloud.html', header = past_results, url ='/static/images/'+name+'.png')
    return render_template('tweetsNoWordCloud.html', header = past_results, url ='/static/images/'+name+'.png')        
@app.route('/get_<name>', methods=['GET'])
def getName(name):
    try:
        past_results = name_dict[name]
        return past_results
    except:
        return notFound(name)
def notFound(name):
    return 'HTTP 404 Not Found'
if __name__ == '__main__':

    app.run(host='127.0.0.1',port=8080)