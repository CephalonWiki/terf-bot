import traceback

import praw
import pandas

import RedditBot

import random
import re
from pprint import pprint

trans_keywords = "|".join(["gender[ -]identity",
                    "^cis",
                     "trans[ -]?(phobi[ac]|gender|girl|wom[aey]n|m[ae]n|boy|[s]?exual)",
                     "non[ -]?binary", "enb(y|ies)",
                     "mtf", "ftm",
                     "identif(ies|y|ying) as",
                     "contrapoints"])
slur_keywords = "|".join(["trann(y|ies)", "attack helicopter", "only ([0-9]+|two) genders", "i identify as", "faggot", "^tim[s]?$", "^tif[s]?$", "agp[s]?"])

class TERFBot(RedditBot.RedditBot):

    def __init__(self, name = "terf-bot", subreddit = "all", keywords = trans_keywords + slur_keywords):

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

        if subreddit == "all":
            self.load()
        else:
            self.comments = None
            self.posts = None

    def extract_features(self, comment):
        if len(str(comment))==7:
            if str(comment) not in self.comments["id"]:
                features = {"id": str(comment),
                            "body": comment.body,
                            "trans_match": re.search(self.keywords, comment.body.lower()),
                            "parent": str(comment.parent()),
                            "subreddit": str(comment.subreddit),
                            "post": comment.submission.title,
                            "link": "https://reddit.com" + comment.permalink}
                if features["trans_match"]:
                    features["trans_match"] = features["trans_match"].apply(lambda m: m.group(0).strip() if m else "")
                self.comments = self.comments.append(features, ignore_index = True)
                pprint(features)

                #recurses until the parent submission is reached
                if features["parent"] not in self.comments["id"]:
                    self.extract_features(comment.parent())

                return features
        elif len(str(comment))==6:
            # In this case, the "parent comment" is the post itself and can be treated as such.
            if str(comment) not in self.posts["id"]:
                features = {"id": str(comment),
                            "title": comment.title,
                            "selftext": comment.selftext,
                            "trans_match": re.search(self.keywords, (comment.title + "\n" + comment.selftext).lower()),
                            "subreddit": str(comment.subreddit),
                            "link": "https://reddit.com" + comment.permalink}
                features["trans_match"] = features["trans_match"].apply(lambda m: m.group(0).strip() if m else "")
                self.posts = self.posts.append(features, ignore_index = True)
                pprint(features)
        else:
            return None

    # clean up the nested ifs yuck
    def should_respond(self, comment):
        return re.search(self.keywords, comment.body.lower())

    def load(self):
        self.comments = pandas.read_csv("../data/" + str(self.subreddit) + "_comments.csv")
        self.posts = pandas.read_csv("../data/" + str(self.subreddit) + "_posts.csv")

    def save(self):
        if self.comments:
            self.comments.to_csv("../data/" + str(self.subreddit) + "_comments.csv", index=False)

        if self.posts:
            self.posts.to_csv("../data/" + str(self.subreddit) + "_posts.csv", index=False)

    def scrape_subreddit(self, subreddit_name, post_limit = 100):
        subreddit = self.reddit.subreddit(subreddit_name)
        top_posts = list(subreddit.top(time_filter='year', limit=post_limit))

        extract_features = lambda p: {
                    "post": p,
                    "id": str(p),
                    "title": p.title,
                    "ups": p.ups,
                    "selftext": p.selftext,
                    "trans_match": re.search(self.keywords, (p.title + "\n" + p.selftext).lower()),
                    "subreddit": str(p.subreddit),
                    "link": "https://reddit.com" + p.permalink}

        sub_df = pandas.DataFrame(list(map(extract_features, top_posts)))


        sub_df["post"].apply(lambda p: p.comments.replace_more(limit = 0))
        sub_df["comments"] = sub_df["post"].apply(lambda p: list(p.comments))

        # Extract keyword matches at the post- and comment-level
        sub_df["trans_match"] = sub_df["trans_match"].apply(lambda m: m.group(0).strip() if m else "")
        sub_df["comment_matches"] = sub_df["comments"].apply(lambda c_list: list(
            map(lambda m: m.group(0), filter(None.__ne__, map(lambda c: re.search(self.keywords, c.lower()), c_list)))))
        sub_df["matches"] = sub_df.apply(lambda r: list(filter(lambda s: s != "", r["comment_matches"] + [r["trans_match"]])), axis=1)
        sub_df["trans"] = sub_df["matches"].apply(lambda l: l != [])


        # print("Percentage of posts addressing trans people:  ", len(sub_df[sub_df["trans_match"].notna()]) / len(sub_df))
        # print("Percentage of comments on posts addressing trans people:  ",
        #       sum(sub_df[sub_df["trans_match"].notna()]["num_comments"]) / sum(sub_df["num_comments"]))
        # print("Percentage of upvotes on posts addressing trans people:  ",
        #       sum(sub_df[sub_df["trans_match"].notna()]["ups"]) / sum(sub_df["ups"]))

        return sub_df



    def scan(self, stream=None):
        for comment in self.subreddit.stream.comments():
            try:
                # check if we should respond
                if self.should_respond(comment):
                    features = self.extract_features(comment)
                    if features:
                        self.save()
            except Exception as e:
                print("##### ERROR #####")
                print(e)

if __name__ == "__main__":
    terf = TERFBot()
    terf.scan()