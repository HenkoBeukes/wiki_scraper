# wiki_scraper
A scraper using Python and BeautiffulSoup to scrape wikipedia to find the other actors a given actor has worked with. 
The scraper implements a rate limiter via a decorator function on the function which would hit the web-site the most often. 
The results are written to a csv file.
