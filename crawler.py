from bs4 import BeautifulSoup as bs
import requests
from urlparse import urlsplit
from requests.exceptions import ConnectionError, InvalidURL, MissingSchema

domain = 'ece.udel.edu'
first_site = 'http://{}'.format(domain)

visited_sites = set()
blacklist = set()
blacklisted_extensions = ('.jpg', '.pdf', '.pptx', '.doc', '.png')
def filter_unwanted_sites(site):
	return domain in site

def fix_url(link, url):
	base_url = "{0.scheme}://{0.netloc}".format(urlsplit(url))
	if len(link) == 0:
		return base_url
	elif link[0:1] == '//':
		return "http://{0.netloc}".format(urlsplit(link))
	elif link[0] == '/' and not link[1] == '/':
		return urlsplit("{}{}".format(base_url, link)).geturl().split('#')[0]
	else:
		return urlsplit(link).geturl().split('#')[0]

def save_page(index, soup):
	with open("site_{}.html".format(index), "w") as file:
		file.write(str(soup))

def recurse(url):
	#Base cases
	if url in blacklist:
		return
	elif url in visited_sites:
		return

	#Make get request
	try:
		page = requests.get(url)
	except ConnectionError as e:
		print('Tried connecting to {}'.format(url))
		blacklist.add(url)
		visited_sites.add(url)
		return
	except InvalidURL as e:
		print('Doesn\'t exist: {}'.format(url))
		blacklist.add(url)
		visited_sites.add(url)
		return
	except MissingSchema as e:
		print("Missing schema: {}".format(url))
		recurse("http://{}".format(url))
		return
	#Parse the page
	page = bs(page.content, 'html.parser')

	#Add this site to the list
	visited_sites.add(url)
	index = len(visited_sites)

	print("Current url: {}, Sites visited: {}".format(url, index))
	save_page(index, page)

	#Get all of the anchor tags
	links = page.find_all('a', href=True)
	#Get all the hrefs only
	links = [anchor['href'] for anchor in links if not anchor['href'].endswith(blacklisted_extensions)]
	#Ignore mailto
	links = [link for link in links if not link.startswith("mailto")]
	#Make a set
	links = set(links)
	#Resolve all of the links
	links = {fix_url(link, url) for link in links}
	#Filter all of the unwanted links
	links = {site for site in links if filter_unwanted_sites(site)}
	if len(links) > 0:
		for site in links:
			recurse(site)
	else:
		return

recurse(first_site)