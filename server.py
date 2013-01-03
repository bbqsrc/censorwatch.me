import logging
import re

import pymongo
import tornado.web
import tornado.options
from pymongo import Connection
from tornado.web import HTTPError, RequestHandler, StaticFileHandler
from mako.template import Template
from mako.lookup import TemplateLookup

from restful import JSONMixin

collection = Connection().ncd.records
templates = TemplateLookup(directories=['templates'])


class HomePageHandler(RequestHandler):
    def get(self):
        self.write(templates.get_template("home.html").render())


class SearchHandler(RequestHandler):
    def get(self):
        self.write(templates.get_template("search.html").render())


class ClassificationsHandler(JSONMixin, RequestHandler):
    queriables = [
        "title", "category", "medium", "author", "producer",
        "production-company", "country", "ratings_G", "ratings_PG", "ratings_M",
        "ratings_MA", "ratings_R", "ratings_X", "ratings_CAT1", "ratings_CAT2",
        "ratings_RC", "ratings_Misc", "ratings_Unrestricted", "from-date",
        "to-date", "file-number", "classification-number", "order-by",
        "direction", "count", "page"
    ]

    ratings = {
        "G": ["G"],
        "PG": ["PG"],
        "M": ["M"],
        "MA": ["MA"],
        "R": ["R"],
        "X": ["X"],
        "CAT1": ["CAT1"],
        "CAT2": ["CAT2"],
        "RC": ["RC"],
        "Misc": ["Misc"],
        "Unrestricted": ["Unrestricted"]
    }

    query_map = {
        "title": lambda x: {"Title": x.upper()},
        "category": lambda x: {"ApplicationGroupName": re.compile(x, re.I)},
        "medium": lambda x: {"MediaType": re.compile(x, re.I)},
        "author": lambda x: {"Creator": x.upper()},
        "producer": lambda x: {"Producer": x.upper()},
        "production-company": lambda x: {"ProductionCompany": x.upper()},
        "country": lambda x: {"ProductionCountry": x.upper()},
        "file-number": lambda x: {"FileNumber": x},
        "classification-number": lambda x: {"CertificateNo": x},
    }

    #order-by and direction are special cases!

    def _int(self, q, default, min_=None, max_=None):
        try:
            x = int(self.get_argument(q, default))
        except:
            x = default
        if min_ is not None:
            x = max(min_, x)
        if max_ is not None:
            x = min(max_, x)
        return x

    def _parse_query(self):
        query = {"$query": {}}

        for q in self.queriables:
            arg = self.get_argument(q, None)
            if arg is None:
                continue

            # order-by and direction are special case
            if q == "direction":
                continue

            if q == "order-by":
                direction = self.get_argument("direction", 1)
                try:
                    direction = int(direction)
                except:
                    direction = 1
                query.update({"$orderby": {arg: direction}})
                continue

            # rating is multi-param
            if q.startswith("ratings"):
                arg = self.ratings[q.split("_")[-1]]
                if query['$query'].get('Rating') is None:
                    query['$query']['Rating'] = {'$in': []}
                query['$query']['Rating']['$in'] += arg
                continue

            # dates too are special.
            if q.endswith("date"):
                if query['$query'].get("CertificateDate") is None:
                    query['$query']['CertificateDate'] = {}

                if q == "from-date":
                    query['$query']['CertificateDate']['$gte'] = arg
                elif q == "to-date":
                    query['$query']['CertificateDate']['$lte'] = arg
                continue

            # for everything else...
            res = self.query_map.get(q, lambda x: {})(arg)
            query['$query'].update(res)

        return query

    def _get_cursor(self):
        query = self._parse_query()

        # set page and count
        count = self._int("count", 20, 0, 100)
        skip = self._int("page", 0) * count

        return collection.find(query).limit(count).skip(skip), count, skip

    def _parse_results(self):
        records, count, skip = self._get_cursor()

        # TODO: work out why this always returns 0 :<
        total = records.count()

        records = list(records)
        for r in records:
            del r['_id']

        return {
            "results": records,
            "page": skip // count,
            "count": count,
            "total": total
        }

    def get_json(self):
        records = self._parse_results()
        self.write(records)

    def get_html(self):
        logging.debug(self._parse_query())
        logging.debug(self._parse_results())
        self.write(templates.get_template("classifications.html").render())


class ClassificationHandler(JSONMixin, RequestHandler):
    def get_json(self, id):
        record = collection.find_one({"CertificateNo": id})
        if record is None:
            raise HTTPError(404)

        del record['_id']
        self.write(record)

    def get_html(self, id):
        self.write(templates.get_template("classification.html").render())


if __name__ == "__main__":
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/static/(.*)", StaticFileHandler, {"path": "static"}),
        (r"/", HomePageHandler),
        (r"/search", SearchHandler),
        (r"/classifications", ClassificationsHandler),
        (r"/classifications/(.+)", ClassificationHandler)
    ])
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
