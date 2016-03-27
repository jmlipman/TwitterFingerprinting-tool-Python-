# TwitterFingerprint mini-library
# Author: Juan Miguel Valverde (lipman)
# Date: 25 March 2016
# Version 0.1
# License: do whatever you want with this, but if you do something nice (research, project, ...)
# 	   I would be happy to know about it.
# Contact: @jmlipman, www.delanover.com

import urllib2, re, ssl
from time import gmtime
import time
import os

class PathDoesNotExistException(Exception):
	pass

class TwitterFingerprint(object):
	
	screenname = ""
	tweets = []
	length = 0
	lastDate = int(time.time())

	def __init__(self,screenname):
		self.screenname = screenname

	# This function will return whether a tweet is valid
	def __isValid(self,rawTweet):
		return len(rawTweet)>5000
	
	# This function reduces the content of each tweet
	def __getContent(self,rawTweet):
		regex = re.compile(' data-aria-label-part=(.*?)u003e(.*?)\\\u003c\\\/p')
		regex = re.compile('data-aria-label-part=..[0-9]..\\\u003e(.*?)\\\u003c..p')
		text = regex.findall(rawTweet)[0]
		res = text.replace("\u003e",">").replace("\u003c","<").replace("\\\"","\"").replace("\\/","/")
		return res

	# From getContent, it gets the hashtags
	def __getHashtags(self,content):
		regex = re.compile('<s>#</s><b>(.*?)</b>')
		return regex.findall(content)

	# From getContent, it gets other mentioned twitter accounts
	def __getMentions(self,content):
		regex = re.compile('<s>@</s><b>(.*?)</b>')
		return regex.findall(content)

	# From getContent, it cleans understandable tweet (it may require more replacements depending on the language)
	def __getCleanParsedTweet(self,content):
		content = re.sub(r"<(.*?)>", "", content)
		replaces = [("&lt;","<"),("&gt;",">"),("&quot;","\""),("&nbsp;"," ")]
		for rep in replaces:
			content = content.replace(rep[0],rep[1])
		return content

	# From getContent, it gets embedded urls in the tweet
	def __getDataTweet(self,content):
		regex = re.compile('data-expanded-url="(.*?)"')
		return regex.findall(content)

	# Get the language of the tweet
	def __getLang(self,tweet):
		regex = re.compile(' lang=..([a-z]+)?..')
		return regex.findall(tweet)[0]

	# Tweet id
	def __getId(self,tweet):
		regex = re.compile('ndata-item-id=..([0-9]*)')
		return regex.findall(tweet)[0]

	# Date, unix time
	def __getDate(self,tweet):
		regex = re.compile('data-time=..([0-9]+)')
		return regex.findall(tweet)[0]

	# Get the number of retweets and likes
	def __getRTsandLikes(self,tweet):
		regex = re.compile('stat-count=..([0-9]+)?')
		return regex.findall(tweet)

	# Empty (no RT) or screename+name+id
	def __getIsRT(self,tweet):
		regex = re.compile('div(.*?)div')
		text = regex.findall(tweet)[0]
		regex = re.compile('data-retweet-id=.*?data-screen-name=\\\\"(.*?)\\\\" data-name=\\\\"(.*?)\\\\" data-user-id=\\\\"([0-9]*)\\\\"')
		res = regex.findall(text)
		if len(res)>0:
			return res[0]
		return ""

	# Get geo location
	def __getGeo(self,tweet):
		regex = re.compile('Tweet-geo.*?title=\\\\"(.*?)\\\\"')
		return regex.findall(tweet)

	# Get the links of the uploaded images
	def __getImagesLinks(self,tweet):
		regex = re.compile('data-image-url=\\\\"(.*?)\\\\"')
		pre_res = regex.findall(tweet)
		res = []
		if len(pre_res)>0:
			for pic in pre_res:
				res.append(pic.replace('\\/','/'))
		return res

	# Get the extension of the images
	def __getExtension(self,picName):
		return picName.split('.')[-1]


	# This function will collect all tweets according to the limitations established in the parameters
	# After the tweets are collected, one can access to them by simply calling the dictionary "tweets".
	# @fromTweetId: it will download tweets starting after that tweet ID.
	# @limit: max number of tweets retrieved.
	# @limitDate: unix date. Before that date, tweets will not be retrieved.
	# @verbose: whether to display debug during downloading process.
	def obtainLastTweets(self,fromTweetId="",limit=0,limitDate=0,verbose=True):
		
		while (limit<=0 or limit>self.length) and (limitDate<=1142899200 or limitDate<self.lastDate):

			if fromTweetId!="" and type(fromTweetId)==str and fromTweetId.isdigit():
				url = "http://twitter.com/i/profiles/show/{0}/timeline/with_replies?max_position={1}".format(self.screenname,fromTweetId)
			else:
				url = "http://twitter.com/i/profiles/show/{0}/timeline/with_replies".format(self.screenname)


			req = urllib2.Request(url, headers={ 'X-Mashape-Key': 'U3sk6nAZzBmshyiHEUZHigodYxLGp1ZTnkd8LWULJmRRp' })
			gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
			download = urllib2.urlopen(req, context=gcontext).read()	

			# This will find individual tweets
			regex = re.compile("\\u003cli class=..js(.*?)\\u003c\\\/li")
			rawTweets = regex.findall(download);
			i=0

			while i<len(rawTweets) and self.__isValid(rawTweets[i]):
				self.length+=1

				# Extract elements of the tweet
				self.content = self.__getContent(rawTweets[i])

				tweet = {"hashtags": self.__getHashtags(self.content), "mentions": self.__getMentions(self.content), "date": int(self.__getDate(rawTweets[i])), "id": self.__getId(rawTweets[i]), "lang": self.__getLang(rawTweets[i]), "text": self.__getCleanParsedTweet(self.content), "data": self.__getDataTweet(self.content), "rtsandlikes": self.__getRTsandLikes(rawTweets[i]), "isrt": self.__getIsRT(rawTweets[i]), "geo": self.__getGeo(rawTweets[i]), "images": self.__getImagesLinks(rawTweets[i])}
				self.tweets.append(tweet)
				i+=1

			fromTweetId=self.tweets[-1]["id"]
			self.lastDate=self.tweets[-1]["date"]

			if verbose:
				print("Downloading: {0}. Last date: {1}. Tweets: {2}".format(url,self.lastDate,self.length))

			# No more tweets to parse
			if len(rawTweets)==0:
				break

		# To agree with the limits
		if limit!=0:
			self.tweets = self.tweets[0:limit]
			self.length = limit


		if limitDate!=0:
			tmpDate = self.tweets[-1]["date"]
			while tmpDate<limitDate:
				self.tweets.pop()
				tmpDate = self.tweets[-1]["date"]
				


	# This function generates three different histograms: months, weekdays, hours.
	# This can be used to see at what time a user regularly tweets.
	# For instance, you can use it to predict regular schedules of people.
	def getHistograms(self):

		histMonths = [0 for __ in range(12)]
		histWeekdays = [0 for __ in range(7)]
		histHours = [[0 for __ in range(24)] for __ in range(7)]

		for tweet in self.tweets:
			histMonths[gmtime(float(tweet["date"])).tm_mon-1]+=1
			histWeekdays[gmtime(float(tweet["date"])).tm_wday]+=1
			histHours[gmtime(float(tweet["date"])).tm_wday][gmtime(float(tweet["date"])).tm_hour]+=1

		return [histMonths,histWeekdays,histHours]


	# @amount: Amount of tweets containing pictures. Each tweet may contain more than one picture.
	# @includeRTs: Whether to take pictures from Retweets.
	# @savePath: Path where pictures will be stored.
	# @namePictures: inverse -> The most recent picture will be named with the higher number.
	#		 preserve -> Pictures will not be renamed.
	#		 otherwise -> The most recent picture will be 1, and so on.
	# @verbose: Whether to print out comments while downloading pictures.
	def getPicturesLinks(self,amount=0,includeRTs=1,savePath="",namePictures='',verbose=1):
		# Links
		pic = []
		# Names
		names = []

		if amount<=0 or amount>self.length:
			amount=self.length
		
		c_total = 0
		c_images = 0
		while c_total<self.length and c_images<=amount:

			if len(self.tweets[c_total]['images'])>0 and (includeRTs or len(self.tweets[c_total]['isrt'])==0):
				pic.extend(self.tweets[c_total]['images'])
				c_images+=1
				for im in self.tweets[c_total]['images']:
					names.append(im.split('/')[-1])
			c_total+=1

		if savePath!="":
			if not os.path.isdir(savePath):
				raise PathDoesNotExistException("\"{0}\" is not an existing directory.".format(savePath))
			# save pictures in that path

			for i in range(len(names)):

				extension = self.__getExtension(names[i])

				if extension=="jpeg" or \
				   extension=="jpg" or \
				   extension=="gif" or \
				   extension=="png" or \
				   extension=="bmp":

					req = urllib2.Request(pic[i], headers={ 'X-Mashape-Key': 'U3sk6nAZzBmshyiHEUZHigodYxLGp1ZTnkd8LWULJmRRp' })
					gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
					imgDate = urllib2.urlopen(req, context=gcontext).read()
					if namePictures=="preserve":
						tmpName = names[i]
					elif namePictures=="inverse":
						tmpName = "{0}.{1}".format(len(names)-i,extension)
					else:
						tmpName = "{0}.{1}".format(i+1,extension)

					if verbose:
						print("Downloading picture: {0} ({1}/{2})".format(tmpName,i+1,len(names)))

					f=open("{0}/{1}".format(savePath,tmpName),"wb")
					f.write(imgDate)
					f.close()

		return pic
			
