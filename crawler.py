from bs4 import BeautifulSoup as bs # Used to parse html into a neat tree-like data structure
import requests # Used to retrieve web pages
from urlparse import urlsplit # Used to parse urls
from requests.exceptions import ConnectionError, InvalidURL, MissingSchema # Common exceptions that might be thrown during the recursing process
import hashlib # Used to compute hexdigests of files so as not to download duplicates
import os # Used to remove duplicate files

#The domain we care about
domain = 'ece.udel.edu'
#The url of the first website
first_site = 'http://{}'.format(domain)

#A set that includes all of the urls we have visited
visited_sites = set()
#A set that includes urls we don't wan't to visit again because of weird errors
blacklist = set()
#The extensions we can't parse
blacklisted_extensions = ('.jpg', '.pdf', '.pptx', '.doc', '.png')
#A dictionary containing all of the sites downloaded and the amount of times its been duplicated
saved_site_dict = {}

#Predicate for what we don't want to include
def filter_unwanted_sites(site):
	return domain in site

#Resolves the url given the href values
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

#Save only unique sites to this directory
def save_page(soup):
	#The next index is the length of the saved sites dictionary
	index = len(saved_site_dict)
	#This file name
	this_file_name = "site_{}.html".format(index)
	#Save the file as the contents of the soup
	with open(this_file_name, "w") as file:
		file.write(str(soup))
	#Calculate the md5sum
	hasher = hashlib.md5()
	with open(this_file_name, "rb") as file:
		buf = file.read()
		hasher.update(buf)
	#The key of the saved site dict is the md5sum of the file
	#If the md5sum already exists, remove the file AND dont add it to the saved sites dictionary
	digest = hasher.hexdigest()
	if digest in saved_site_dict:
		os.remove(this_file_name)
		#Increment the duplicate count if this site is a duplicate
		saved_site_dict[digest] = (saved_site_dict[digest][0], saved_site_dict[digest][1] + 1)
	else:
		saved_site_dict[digest] = (this_file_name, 0)

#The start of the recursive function
def recurse(url):
	#Base cases
	if url in blacklist:
		return
	elif url in visited_sites:
		return

	#Make get request, handle oopsies
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
	#This is the only reasonably recoverable error assuming that the protocol
	except MissingSchema as e:
		print("Missing schema: {}".format(url))
		recurse("http://{}".format(url))
		return
	#The actual logic assuming the previous try didn't fail
	#Parse the page
	page = bs(page.content, 'html.parser')
	#Add this site to the list
	visited_sites.add(url)
	#The amount of urls visited including the current one
	sites_visited = len(visited_sites)
	print("Current url: {}, Sites visited: {}".format(url, sites_visited))
	#Try to save the page
	save_page(page)

	#Get all of the anchor tags
	links = page.find_all('a', href=True)
	#Get all the hrefs only that aren't one of the blacklisted file endings
	links = [anchor['href'] for anchor in links if not anchor['href'].endswith(blacklisted_extensions)]
	#Ignore mailto anchors
	links = [link for link in links if not link.startswith("mailto")]
	#Make a set
	links = set(links)
	#Resolve the links
	links = {fix_url(link, url) for link in links}
	#Filter the unwanted links
	links = {site for site in links if filter_unwanted_sites(site)}
	#If the links set isn't empty go down the rabbit hole
	if len(links) > 0:
		for site in links:
			recurse(site)
	else:
		return

if __name__ == "__main__":
	#Call the method... thats what this script should do
	recurse(first_site)
	#Print top 10 duplicated sites
	decompose_dups_to_list = []
	for key, val in saved_site_dict.iteritems():
		#Values club only
		decompose_dups_to_list.append(val)
	#Reverse sort it so I can see the most duplicated first
	decompose_dups_to_list.sort(reverse=True, key=lambda tup: tup[1])

print("Top 10 duplicated sites")
print(decompose_dups_to_list[:10])