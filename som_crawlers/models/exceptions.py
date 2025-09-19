# -*- coding: utf-8 -*-


class CrawlingProcessException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.msg


class NoResultsException(CrawlingProcessException):
    def __init__(self, msg, download_was_clicked=False, add_msg_tag=True):
        tag = ""
        if add_msg_tag:
            tag = "SENSE RESULTATS: "
        super(NoResultsException, self).__init__(tag + msg)


class CrawlingLoginException(CrawlingProcessException):
    pass
