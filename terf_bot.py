import traceback

import praw

import RedditBot

import random
import re
import nltk

trans_keywords = "|".join(["[Gg]ender[ -][Ii]dentity",
                     "[Tt]rans[ -]?(gender|[Ww]om[ae]n|[Mm][ae]n|[Ss]?exual)",
                     "[Nn]on[ -]?binary",
                     "[Mm][Tt][Ff]", "[Ff][Tt][Mm]"])
slur_keywords = "|".join(["trann(y|ies)", "attack helicopter", "i identify as", "faggot"])

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


    # clean up the nested ifs yuck
    def should_respond(self, comment):
        return re.search(self.keywords, comment.body.lower())

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
            self.logger.debug("Reading comment %s", comment)

            try:
                # check if we should respond
                if self.should_respond(comment):
                    print("##### COMMENT FOUND #####")
                    print("Match:  ", re.search(self.keywords, comment.body).group(0))
                    print("Link:  ", comment.subreddit.permalink)
                    print("Subreddit:  ", comment.subreddit)
                    print("Post:  ", comment.submission.title)
                    print("Text:  ", comment.body)
            except Exception:
                continue

if __name__ == "main":
    terf = TERFBot()
    terf.scan()