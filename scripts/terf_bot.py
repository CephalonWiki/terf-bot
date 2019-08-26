import traceback

import praw
import pandas

import RedditBot

import random
import re
from pprint import pprint

trans_keywords = "|".join(["[Gg]ender[ -][Ii]dentity",
                     "[Tt]rans[ -]?(phobi[ac]|gender|[Gg]irl|[Ww]om[ae]n|[Mm][ae]n|[Bb]oy|[Ss]?exual)",
                     "[Nn]on[ -]?binary", "enby",
                     "[Mm][Tt][Ff]", "[Ff][Tt][Mm],"
                     "identif(ies|y|ying) as"])
slur_keywords = "|".join(["trann(y|ies)", "attack helicopter", "only ([0-9]+|two) genders", "i identify as", "faggot", "T[Ii][Mm]", "T[Ii][Ff]"])

class TERFBot(RedditBot.RedditBot):

    def __init__(self, name="terf-bot", subreddit="all"):

        # create Reddit instance
        with open("../../data/credentials.txt", 'r') as login_credentials:
            credentials = login_credentials.readline().split(',')
            reddit_instance = praw.Reddit(client_id=credentials[0], client_secret=credentials[1],
                                          user_agent=credentials[2] + ":%s".format(random.random()),
                                          username=credentials[3], password=credentials[4])
            super().__init__(reddit_instance)

        super().set_name(name)

        super().set_subreddit(subreddit)
        super().set_mechanic("1st_transit_of_venus")

        self.keywords = trans_keywords + slur_keywords
        self.comments = pandas.read_csv("../data/comments.csv")
        self.posts = pandas.read_csv("../data/posts.csv")

    def extract_features(self, c):
        if len(str(c))==7:
            if str(c) not in self.comments["id"]:
                features = {"id": str(c),
                            "body": c.body,
                            "trans_match": "",
                            "subreddit": str(c.subreddit),
                            "post": c.submission.title,
                            "link": "https://reddit.com" + c.permalink}
                if re.search(self.keywords, c.body.lower()):
                    features["trans_match"] = re.search(self.keywords, c.body.lower()).group(0)
                self.comments = self.comments.append(features, ignore_index = True)
                pprint(features)

                #recurses until the parent submission is reached
                if str(c.parent()) not in self.comments["id"]:
                    self.extract_features(c.parent())

                return features
        elif len(str(c))==6:
            if str(c) not in self.posts["id"]:
                features = {"id": str(c),
                            "title": c.title,
                            "selftext": c.selftext,
                            "trans_match": "",
                            "subreddit": str(c.subreddit),
                            "link": "https://reddit.com" + c.permalink}
                if re.search(self.keywords, (c.title + "\n" + c.selftext).lower()):
                    features["trans_match"] = re.search(self.keywords, (c.title + "\n" + c.selftext).lower()).group(0)
                self.posts = self.posts.append(features, ignore_index = True)
                pprint(features)
        else:
            return None

    # clean up the nested ifs yuck
    def should_respond(self, comment):
        return re.search(self.keywords, comment.body.lower())

    def load(self):
        self.comments = pandas.read_csv("../data/comments.csv")
        self.posts = pandas.read_csv("../data/posts.csv")

    def save(self):
        self.comments.to_csv("../data/comments.csv", index=False)
        self.posts.to_csv("../data/posts.csv", index=False)

    def scan(self, stream=None):
        # Stream set-up
        # Subreddit comment stream must be re-initialized after exception
        # Otherwise, make a copy of the stream because...I forgot?  lolz
        scan_stream = None
        if not stream:
            scan_stream = self.subreddit.stream.comments()
        else:
            scan_stream = stream.copy()

        for comment in scan_stream:
            try:
                # check if we should respond
                if self.should_respond(comment):
                    features = self.extract_features(comment)
                    if features:
                        self.save()
            except Exception as e:
                print("##### ERROR #####")
                print(e)

if __name__ == "main":
    terf = TERFBot()
    terf.scan()