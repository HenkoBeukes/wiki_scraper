# A crawl through wikipedia to find the movies an actor has been in or the actors in a
# show.
# This is a scraper dealing with variable formats in Wikipedia.
# Using:
# BeautifulSoup
# lxml


from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import time
import csv

# @TODO put on github

# A rate limiting function to use as a decorator on the functions you need to limit
def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.time() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.time()
            return ret
        return rateLimitedFunction
    return decorate


def get_movie_links(actor_url):
    html = urlopen('http://en.wikipedia.org'+actor_url)
    soup = BeautifulSoup(html, "lxml")
    # find Filmography heading
    if soup.find(id="Filmography_and_awards"):
        filmography = soup.find(id="Filmography_and_awards").string
    elif soup.find(id="Filmography"):
        filmography = soup.find(id="Filmography").string
    elif soup.find(id="Credits"):
        filmography = soup.find(id="Credits").string
    elif soup.find(id="Career"):
        filmography = soup.find(id="Career").string
    elif soup.find(id="Acting"):
        filmography = soup.find(id="Acting").string

    # check for off-page filmography link
    if filmography.parent.parent.find_next_sibling(role='note'):
        # print(filmography.parent.parent.find_next_sibling())
        link_to_filmography = filmography.parent.parent.find_next_sibling().a.get('href')
        # print(link_to_filmography)
        html = urlopen('http://en.wikipedia.org' + link_to_filmography)
        soup = BeautifulSoup(html, "lxml")
        filmography = soup.find(class_="mw-headline").string
        print(filmography)

    next_sib_len = len(filmography.parent.parent.find_next_siblings())
    shows = []
    for i in range(next_sib_len):
        film_table = filmography.parent.parent.find_next_siblings()[i]
        if film_table.find('tbody'):
            # print(film_table)
            # print('NEXT \n')
            links = film_table.find_all('i')
            for link in links:
               try:
                   show = link.find('a').get('href')
                   show = link.find(href=href_show).get('href')
                   shows.append(show)
               except:
                   pass

        if film_table.find(id='References'):
            break
        elif film_table.find(id='Video_games'):
            break
        elif film_table.find(id='Awards_and_nominations'):
            break
    return shows


@RateLimited(0.1)   # delimited to x times per second
def get_actor_links(movie_url):
    html = urlopen('http://en.wikipedia.org' + movie_url)
    soup = BeautifulSoup(html, "lxml")

    actor_links = []
    # find cast section
    if soup.find(id='Cast'):
        cast_sections = soup.find(id='Cast').parent.find_next_siblings()
    if soup.find(id='Cast_and_characters'):
        cast_sections = soup.find(id='Cast_and_characters').parent.find_next_siblings()
    for section in cast_sections:
        # print(section.name)
        if section.name == 'ul' or section.name == 'div':
            actor_tags = section.find_all('li')
            # print('actor tags:', actor_tags)
            for actor_tag in actor_tags:
                try:
                    actor_link = actor_tag.find(href=href_name).get('href')
                except:
                    actor_link = ''
                actor_links.append(actor_link)

        if section.name == 'p':
            # print(section)
            # print('NEXT AGAIN \n')
            # actor_links_2 = section.find_all('a', class_='')
            # print(actor_links_2)
            actor_links_2 = section.find_all(href=href_name)
            for link in actor_links_2:
                actor_link = link.get('href')
                actor_links.append(actor_link)

        if section.name == 'h2':
            break

    return set(actor_links)


def href_name(href):  # try to capture only valid hrefs
    return href and re.compile("/wiki/").search(href) and not re.compile("[(:.\-)]").search(href)


def href_show(href):  # try to capture only valid hrefs
    return href and re.compile("/wiki/").search(href)

# for testing:
# links = get_movie_links("/wiki/Henry_Cavill")  # multiple filmograpy tables on main
# page
# links = get_movie_links("/wiki/Kevin_Bacon")  # seperate filmography page
# links = get_movie_links("/wiki/Freya_Allan")   # single filmography table
# links = get_movie_links("/wiki/Charlize_Theron")
# links = get_movie_links("/wiki/Dennis_Hopper")
# links = get_movie_links("/wiki/Harrison_Ford")
# links = get_actor_links("/wiki/Avengers:_Endgame")
# links = get_actor_links("/wiki/The_Witcher_(TV_series)")
# links = get_actor_links("/wiki/Blade_Runner_2049")
# links = get_actor_links("/wiki/The_Magicians_(American_TV_series)")
# links = get_actor_links("/wiki/Star_Wars_(film)")
# links = get_actor_links("/wiki/Dude_Bro_Party_Massacre_III")
# print(links)

if __name__ == '__main__':
    actor_name = input('Please enter the actor name in the format Name_Surname \n')
    print('You asked about this actor:',actor_name)
    filename = actor_name + '.csv'
    print(f'Results will be saved under results/{filename}')
    start_time = time.time()
    try:
        shows_acted_in = set(get_movie_links("/wiki/"+actor_name))
    except:
        shows_acted_in = ''
        print("Not Found. Try checking the spelling?")

    print('Number of shows:', len(shows_acted_in))
    print('SHOWS:',shows_acted_in)

    actors_list = []
    for show in shows_acted_in:
        try:
            actors_links = get_actor_links(show)
        except:
            actors_links = ''
        actors_list.extend(actors_links)

    actors_list = set(actors_list)
    print('Number of people:',len(actors_list))

    clean_list = []
    for actor in actors_list:   # return the actor's name without the link info
        cleaned_actor = actor.split('/')[-1]
        clean_list.append(cleaned_actor)

    # Remove base actor's name from saved list
    clean_list.remove(actor_name)

    with open('results/'+filename, 'w') as myfile:
        wr = csv.writer(myfile, delimiter=',')
        wr.writerow(clean_list)

    print('People Worked with:', actors_list)
    if '/wiki/Kevin_Bacon' in actors_list:
        print('Linked to Kevin Bacon with a Bacon number of 1')
    else:
        print('Actor has not worked with KeViN BaCoN! ')

    end_time = time.time()
    lapsed_time = (end_time - start_time)  # in seconds
    time_taken_m = lapsed_time//60   # full minutes
    time_taken_s = lapsed_time% 60   # seconds
    print(f"Time taken: {time_taken_m} minutes and {time_taken_s} seconds. ")
