from amazon.api import AmazonAPI
from pinterest import Pinterest
import time 
import random
#Credentials for Amazon
AMAZON_ACCESS_KEY = 'AKIAJJIMWZWCG6A43X7A'
AMAZON_SECRET_KEY = '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'
AMAZON_ASSOC_TAG = 'bryan787-20'
#Credentials for Pinterest
pinterest = Pinterest(username_or_email='bryanmorganoverbey@gmail.com', password='/b/ryan787')
logged_in = pinterest.login()
amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)
#Define a list of keywords for a search
infile = open('keywords.txt', 'r')

#For item in keyword list:
for line in infile:

	#Do a search
	products = amazon.search(Keywords=line, SearchIndex='All')
	#For item in search return list
	for product in products:

		#Make Add
		pin = pinterest.pin(
			board_id='460282093105681293',
			image_url = product.large_image_url,
			description = product.title,
			link = product.detail_page_url)
		time.sleep(random.randint(60,120))