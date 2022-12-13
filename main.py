# IMPORTING LIBRARIES
import configparser as cp
import pandas as pd
import streamlit as st
import tweepy as tp
import streamlit.components.v1 as components
from textblob import TextBlob
import matplotlib.pyplot as plt
import plotly.express as px
import requests
import fun

# READ CONFIGS FILE
config = cp.ConfigParser()
config.read('config.ini')

# SECRET KEYS FROM TWITTER API
api_key = config['twitter']['api_key']
api_key_secret = config['twitter']['api_key_secret']
access_token = config['twitter']['access_token']
access_token_secret = config['twitter']['access_token_secret']
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAIf8gwEAAAAAPyF47sM6UGJKQGtVBcVL6t%2FVHwY%3DNciSlNBZEBq9heuovwgXXEKiX5la23y30inP1yNV6bMwIUT6oL'

# AUTHENTICATION
auth = tp.OAuth1UserHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)

# INSTANCE OF API
api = tp.API(auth, wait_on_rate_limit=True)


###################################################################
# STREAMLIT APP STARTS HERE......

# TITLE
st.title("Twitter User Profiling")

# GRABS INFO FROM INPUT FIELD
with st.form("my_form"):
    check_username = st.text_input("Username", key="name")

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
####################################################################

# TWEEPY
name = check_username

# Slider for number of tweets
no_of_tweets = st.slider('Select no. of tweets want to retrieve', 2, 25)

# # Getting User
if name == "":
    pass
else:
    user = api.get_user(screen_name=name)
    data = user._json
    fun.basic_info(data)
    
    timeline = api.user_timeline(
        screen_name=name, count=200, include_rts=False, tweet_mode='extended')

    # Variables for storing information
    df = []
    display_df = []
    analysis = []
    analysis_emoji = []
    tweet_time = []
    days = []
    top_5_tweets = []
    likes = []
    links = []

    # Get information from user timeline
    for info in timeline:
        df.append(info.full_text)
        analysis.append( TextBlob(info.full_text).sentiment.polarity )
        x = info.created_at
        tweet_time.append(x.strftime("%H"))
        days.append(x.strftime("%A"))
        likes.append(info.favorite_count)
        links.append(f"https://twitter.com/twitter/statuses/{info.id}")

    for info in timeline[:no_of_tweets]:
        display_df.append(info.full_text)
        x = info.created_at
    
    df_table = pd.DataFrame(data= df, columns= ['Tweets'])
    tweet_time_df = pd.DataFrame(data=tweet_time, columns=['Time'])
    tweet_time_df['Days'] = days
    df_table['Polarity'] = analysis
    st.table(display_df)

    # Emoji's based on the polarity values
    for val in analysis:
        if val >= -1 and val <= -0.6:
            analysis_emoji.append('😟')
        elif val >= -0.5 and val <= -0.1:
            analysis_emoji.append('😶')
        elif val == 0:
            analysis_emoji.append('😐')
        elif val >= 0.0 and val <= 0.4:
            analysis_emoji.append('🙂')
        elif val >= 0.4 and val <= 1:
            analysis_emoji.append('😀')


    # DataFrames for Likes, Emoji's
    df_table['Likes'] = likes
    df_table['Emoji'] = pd.DataFrame(analysis_emoji)
    st.table(df_table)

    ### Getting most liked tweet
    most_liked_tweet = pd.DataFrame(data= links)
    most_liked_tweet['Likes'] = likes
    most_liked_tweet_df = most_liked_tweet.sort_values(by='Likes', ascending=False)
    st.table(most_liked_tweet_df)

    # Top 5 tweets
    top_5_tweets_df = pd.DataFrame(data= top_5_tweets, columns=['Tweets', 'Likes'])
    top_5_tweets_df['Tweets'] = df_table['Tweets']
    top_5_tweets_df['Likes'] = likes
    st.table(top_5_tweets_df.sort_values(by='Likes', ascending=False))
    top_tweets_5 = top_5_tweets_df.sort_values(by='Likes', ascending=False)

    for t in top_tweets_5['Tweets'][:5]:
        print(t)

    ## Displaying top tweet
    st.title("Most liked tweet")
    class Tweet(object):
        def __init__(self, s, embed_str=False):
            if not embed_str:
                # Use Twitter's oEmbed API
                # https://dev.twitter.com/web/embedded-tweets
                api = "https://publish.twitter.com/oembed?url={}".format(s)
                response = requests.get(api)
                self.text = response.json()["html"]
            else:
                self.text = s

        def _repr_html_(self):
            return self.text

        def component(self):
            return components.html(self.text, height=600)

    t = Tweet(most_liked_tweet_df.iat[0, 0]).component()

    ### Download section
    tweet_time_df.to_csv(index=False)
    @st.experimental_memo
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')


    csv = convert_df(tweet_time_df)

    st.download_button(
    "Press to Download",
    csv,
    "file.csv",
    "text/csv",
    key='download-csv'
    )

    ### Chart display
    st.title("Activetly tweeted time")
    fig = tweet_time_df.set_index('Days')
    st._arrow_bar_chart(fig)