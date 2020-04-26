# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 15:32:47 2020

@author: jvan1
"""

import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import json
from flask import Flask
import spacy
nlp = spacy.load("en_core_web_lg")
app = Flask(__name__)

def extractTweet(tweet):
    tweet = tweet.split('replies')[0].split('reply')[0]
    find_last_n = tweet[::-1].find('\n')
    tweet = tweet[::-1][find_last_n:][::-1]
    tweet=tweet.strip('\n')
    if 'pic.twitter.com' in tweet:
        tweet = tweet.split('pic.twitter.com')[0]
    elif 'twitter.com' in tweet:
        tweet = tweet.split('twitter.com')[0]
    if 'http' in tweet:
        tweet = tweet.split('http')[0]
    return tweet
def similarity(tweets):
    blob = TextBlob(''.join(tweets).strip('\''))
    words = blob.noun_phrases
    count = [blob.np_counts.values()]
    print(count)
    if len(count)>0:
        max_word = words[list(blob.np_counts.values()).index(max(blob.np_counts.values()))].lower()
        
        nlp_list = []
        max_similarity = 0
        max_sim_tweet1 = ''
        max_sim_tweet2 = ''
        for tweet in words:
                tweet2 = max_word
                if tweet.lower() == tweet2:
                    continue
                token1 = nlp(tweet.lower())
                token2 = nlp(tweet2)
                similarity = token1.similarity(token2)
                nlp_list.append((tweet,tweet2,similarity))
                if similarity > max_similarity:
                    max_similarity = similarity
                    max_sim_tweet1 = tweet.lower()
                    max_sim_tweet2 = tweet2
        return (max_sim_tweet1,max_sim_tweet2,str(max_similarity))
def loadTweets(username):
    url = "http://www.twitter.com/" + username
    response = requests.get(url)
    soup = BeautifulSoup(response.text,'lxml')
    tweets = soup.get_text().split('Thanks. Twitter will use this to make your timeline better.')[0:]
    tweets = [extractTweet(x.split('Embed Tweet')[-1]) for x in tweets if 'Retweeted' not in x.split('replies')[0].split('reply')[0]][:-1]
    tweets = [x for x in tweets if len(x)!=0]
    return tuple(tweets)
def printTweets(tweets):
    return tweets
@app.route('/<name>_<function>', methods=['POST','GET'])
def getTwitterUsername(name,function):
    attempted_username = name
    function_to_call = int(function)
    function_list = [printTweets,similarity]
    tweets = loadTweets(attempted_username)
    past_results = ''
    try:
        result = function_list[function_to_call](tweets)
        result = '<br>'.join(result)
        past_results = result
        return result
    except:
        return past_results
    
def main(username):
    loadTweets(username)
    
if __name__ == '__main__':
    app.run(host='127.0.0.1',port=8080)