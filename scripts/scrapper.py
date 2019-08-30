import random
import re
from pprint import pprint

import pandas

import praw

r = None
with open("../../data/credentials.txt", 'r') as login_credentials:
    credentials = login_credentials.readline().split(',')
    r = praw.Reddit(client_id=credentials[0], client_secret=credentials[1], user_agent=credentials[2] + ":%s".format(random.random()), username=credentials[3], password=credentials[4])

trans_keywords = "|".join(["[Gg]ender[ -][Ii]dentity",
                    "^[Cc][Ii][Ss]",
                     "[Tt]rans[ -]?(phobi[ac]|gender|[Gg]irl|[Ww]om[ae]n|[Mm][ae]n|[Bb]oy|[Ss]?exual)",
                     "[Nn]on[ -]?binary", "enb(y|ies)",
                     "[Mm][Tt][Ff]", "[Ff][Tt][Mm],"
                     "identif(ies|y|ying) as"])
slur_keywords = "|".join(["trann(y|ies)", "attack helicopter", "only ([0-9]+|two) genders", "i identify as", "faggot", "TRA","T[Ii][Mm]", "T[Ii][Ff]", "AGP"])

r_gc = r.subreddit("gendercritical")
r_gc_top_posts = list(r_gc.top(time_filter = 'year', limit = 500)) #997

extract_features = lambda p: {"post": p, "title": p.title, "selftext": p.selftext,
                              "ups": p.ups, "num_comments": p.num_comments,
                              "trans_match":re.search(trans_keywords + slur_keywords, p.title + "\n" + p.selftext)}
gc = pandas.DataFrame(list(map(extract_features, r_gc_top_posts)))

# Extract keyword matches
gc["trans_key"] = gc["trans_match"].apply(lambda m: m.group(0).strip() if m else None)

def summary_stats(gc):
    print("Percentage of posts addressing trans people:  ", len(gc[gc["trans_match"].notnull()])/len(gc))
    print("Percentage of comments on posts addressing trans people:  ", sum(gc[gc["trans_match"].notnull()]["num_comments"])/sum(gc["num_comments"]))
    print("Percentage of upvotes on posts addressing trans people:  ", sum(gc[gc["trans_match"].notnull()]["ups"])/sum(gc["ups"]))

print("Keywords detected:")
pprint(sorted(list(set(gc[gc["trans_key"].notnull()]["trans_key"].apply(lambda s: re.sub("men","man",re.sub("[ -]", "",s)).lower())))))
summary_stats(gc)

# # will take a while to extract comments
# gc["comments"] = gc["posts"].apply(lambda p:p.comments)
# gc["comments"].apply(lambda C: C.replace_more(limit=0))