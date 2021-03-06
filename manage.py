#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from flask.ext.script import Manager, Command, Option

from eventviz import settings
from eventviz.app import app
from eventviz.db import insert_item, connection, get_database_names
from eventviz.lib.parsers import get_parser_by_name, get_parser_names


class LoadData(Command):
    """
    Parses a file and load its data in the database.
    """
    option_list = (
        Option('-f', '--filename', dest='filename', required=True),
        Option('-p', '--parser', dest='parser_name', required=True),
        Option('-P', '--project', dest='project_name', required=True)
    )

    def run(self, filename=None, parser_name=None, project_name=None):
        parser_cls = get_parser_by_name(parser_name)
        if parser_cls is None:
            print "Unknown parser: %s" % parser_name
            return
        if not os.path.exists(filename):
            print "File not found: %s" % filename
            return
        parser = parser_cls(filename)
        count = 0
        for item in parser.run():
            if settings.DEBUG_PARSERS:
                count += 1
            else:
                if insert_item(project_name, parser, item):
                    count += 1
            if count % 100 == 0:
                msg = "Inserted %d events..." % count
                sys.stdout.write(msg)
                sys.stdout.flush()
                sys.stdout.write('\b' * len(msg))
        sys.stdout.write("Inserted %d events...\n" % count)


class ListParsers(Command):
    """
    Lists currently available parser types.
    """
    def run(self):
        print "Available parsers:"
        for parser_name in get_parser_names():
            print '*', parser_name


class DropProject(Command):
    """
    Drops database for given project.
    """
    option_list = (
        Option('-P', '--project', dest='project', required=True),
    )

    def run(self, project=None):
        if project not in get_database_names():
            print "No such project: %s" % project
            return
        connection.drop_database(project)
        print "Dropped '%s' project" % project


class DropCollection(Command):
    """
    Drops a project's data for given parser.
    """
    option_list = (
        Option('-P', '--project', dest='project', required=True),
        Option('-p', '--parser', dest='parser', required=True)
    )

    def run(self, project=None, parser=None):
        if project not in get_database_names():
            print "No such project: %s" % project
            return
        db = connection[project]
        if parser not in db.collection_names():
            print "No data for parser: %s" % parser
            return
        db.drop_collection(parser)
        print "Dropped data for '%s' in project '%s'" % (parser, project)


class ListProjects(Command):
    """
    Lists available projects.
    """
    def run(self):
        print "Available projects:"
        for db_name in get_database_names():
            print '*', db_name


class TestParser(Command):
    """
    Tests a parser (for debugging purpose only).
    """
    option_list = (
        Option('-p', '--parser', dest='parser', required=True),
        Option('-i', '--inputfile', dest='inputfile', required=True)
    )

    def run(self, parser=None, inputfile=None):
        settings.DEBUG = True
        parser_cls = get_parser_by_name(parser)
        if parser_cls is None:
            print "Unknown parser: %s" % parser
            return
        if not os.path.exists(inputfile):
            print "File not found: %s" % inputfile
            return
        parser = parser_cls(inputfile)
        for _ in parser.run():
            pass

manager = Manager(app)
manager.add_command('load_data', LoadData())
manager.add_command('list_parsers', ListParsers())
manager.add_command('drop_project', DropProject())
manager.add_command('drop_collection', DropCollection())
manager.add_command('list_projects', ListProjects())
manager.add_command('test_parser', TestParser())
manager.run()
