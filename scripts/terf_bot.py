import traceback
import time

import praw
import pandas

import RedditBot

import random
import re
from pprint import pprint

trans_keywords = "|".join(["gender[ -]identity",
                     "([\b]?cis[\b]?|trans)[ -]?(phobi[ac]|gender|girl|wom[aey]n|m[ae]n|boy|[s]?exual)",
                     "non[ -]?binary", "enb(y|ies)",
                     "mtf", "ftm",
                     #"identif(ies|y|ying) as",
                     "contrapoints"])
slur_keywords = "|".join(["trann(y|ies)", "attack helicopter", "only ([0-9]+|two) genders", "faggot", "agp[s]?", "autogynephilia"])

class TERFBot(RedditBot.RedditBot):

    def __init__(self, name = "terf-bot", subreddit = "gendercritical", keywords = trans_keywords + "|" + slur_keywords):

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

        self.keywords = keywords
        self.regex = re.compile(self.keywords)

        self.comments = pandas.DataFrame({})
        self.posts = pandas.DataFrame({})

    def extract_matches(self, string):
        return list(map(lambda m: m.group(0) if m else "", self.regex.finditer(string.lower())))

    def extract_post_features(self, post):
        print("Scrapping post " + str(post) + "...")
        print("Extracting basic features...")
        post_features = {
            "post": post,
            "id": str(post),
            "title": post.title,
            "selftext": post.selftext,
            "score": post.score,
            "comments": [],
            "matches": self.extract_matches((post.title + "\n" + post.selftext)),
            "subreddit": str(post.subreddit),
            "link": "https://reddit.com" + post.permalink}

        print("Extracting comments...")
        # Extract comments and get keyword matches
        post.comments.replace_more(limit = 0)
        for c in post.comments:
            post_features["comments"].append(c.body)
            post_features["matches"] += self.extract_matches(c.body)

        # Label a post as "trans" if either the post body or comments match keywords
        post_features["trans"] = bool(post_features["matches"])

        print("======================")
        return post_features

    def extract_comment_features(self, comment):
        comment_features = {
                    "comment": comment,
                    "id": str(comment),
                    "post_id": str(comment.submission),
                    "body": comment.body,
                    "score": comment.score,
                    "search": self.extract_matches(comment.body),
                    "parent": str(comment.parent()),
                    "subreddit": str(comment.subreddit),
                    "link": "https://reddit.com" + comment.permalink}

        return comment_features


    def extract_features(self, comment):
        features = self.extract_comment_features(comment)
        self.comments = self.comments.append(features, ignore_index = True)

    # clean up the nested ifs yuck
    def should_extract(self, comment):
        return re.search(self.keywords, comment.body.lower()) and (str(comment) not in self.comments["id"])

    def scrape_subreddit(self, post_limit = 100):
        print("Scrapping posts...")
        top_posts = self.subreddit.top(time_filter='year', limit=post_limit)

        print("Extracting features...")
        print("======================")
        self.posts = pandas.DataFrame(list(map(self.extract_post_features, top_posts)))

        print("Scrapping successful...")
        return self.posts

    def scan(self, stream=None):
        for comment in self.subreddit.stream.comments():
            try:
                if self.should_extract(comment):
                    self.extract_features(comment)

                    # extract parent comment features for context, whether they match keywords or not
                    parent = comment.parent()
                    while str(parent) not in self.comments["id"] and len(str(parent)) == 7:
                        self.extract_features(parent)
                        parent = parent.parent()

                    # extract post details
                    if str(comment.submission) not in self.posts["id"]:
                        self.posts = self.posts.append(self.extract_post_features(comment.submission))
            except Exception as e:
                print("##### ERROR #####")
                print(e.__traceback__)

if __name__ == "__main__":
    terf = TERFBot()
    terf.scan()