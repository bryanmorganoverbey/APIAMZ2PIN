from amazon.api import AmazonAPI
from pinterest import Pinterest
import time 
import random
#Credentials for Amazon
#Note these aren't real keys. These are examples.
AMAZON_ACCESS_KEY = 'AKIAJJIMWZWCG6A43X7'
AMAZON_SECRET_KEY = 'oGQmOaSZNwcIkJgWZyxe7KgDDUSaQgAi88orVRb'
AMAZON_ASSOC_TAG = 'bryan787-20'
#Credentials for Pinterest
pinterest = Pinterest(username_or_email='bryanmorganoverbey@gmail.com', password='')
logged_in = pinterest.login()
amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)
#Define a list of keywords for a search
infile = open('keywords.txt', 'r')

#For item in keyword list:
for line in infile:

		#Do a search
	try:
		products = amazon.search(Keywords=line, SearchIndex='All')
	except:
		print("got here 1")
		pass
		#For item in search return list
	try:
		for product in products:
			print(product)
			try:
				#Make Add
				pin = pinterest.pin(
					board_id='460282093105681293',
					image_url = product.large_image_url,
					description = product.title,
					link = product.detail_page_url)
				print(product.detail_page_url)
				time.sleep(random.randint(60,120))
			except:
				print("got here 2")
				pass
	except:
		print("got here 3: " + line)
		pass
