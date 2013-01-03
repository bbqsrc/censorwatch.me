import pymongo
import tornado.web
import tornado.options
from pymongo import Connection
from tornado.web import HTTPError, RequestHandler, StaticFileHandler
from mako.template import Template
from mako.lookup import TemplateLookup

from restful import JSONMixin

records = Connection().ncd.records
templates = TemplateLookup(directories=['templates'])


class HomePageHandler(RequestHandler):
    def get(self):
        self.write(templates.get_template("home.html").render())


class SearchHandler(RequestHandler):
    def get(self):
        self.write(templates.get_template("search.html").render())


class ClassificationsHandler(JSONMixin, RequestHandler):
    def _parse_query(self, query):
        return query

    def get_json(self):
        self.write({})

    def get_html(self):
        self.write(templates.get_template("classifications.html").render())


class ClassificationHandler(JSONMixin, RequestHandler):
    def get_json(self, id):
        record = records.find_one({"CertificateNo": id})
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
