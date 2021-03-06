#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, unicode_literals
import os
import json
from .util import u, slugify
import codecs


def get_tags_count(journal):
    """Returns a set of tuples (count, tag) for all tags present in the journal."""
    # Astute reader: should the following line leave you as puzzled as me the first time
    # I came across this construction, worry not and embrace the ensuing moment of enlightment.
    tags = [tag
            for entry in journal.entries
            for tag in set(entry.tags)]
    # To be read: [for entry in journal.entries: for tag in set(entry.tags): tag]
    tag_counts = set([(tags.count(tag), tag) for tag in tags])
    return tag_counts


def to_tag_list(journal):
    """Prints a list of all tags and the number of occurrences."""
    tag_counts = get_tags_count(journal)
    result = ""
    if not tag_counts:
        return '[No tags found in journal.]'
    elif min(tag_counts)[0] == 0:
        tag_counts = filter(lambda x: x[0] > 1, tag_counts)
        result += '[Removed tags that appear only once.]\n'
    result += "\n".join("{0:20} : {1}".format(tag, n) for n, tag in sorted(tag_counts, reverse=True))
    return result


def get_todos(journal):
    """
    Returns all todos in a list.
    :rtype: list[Todo]
    """
    todos = [todo
             for entry in journal.entries
             for todo in entry.todos]
    return todos


def to_todo_list(journal):
    """Prints a list of all todos."""
    todos = get_todos(journal)
    if not todos:
        return '[No todos found in journal.]'

    pending_todos = []
    completed_todos = []
    for todo in todos:
        if todo.is_complete:
            completed_todos.append(todo)
        else:
            pending_todos.append(todo)

    def appendable_header(_text):
        separator = '=' * len(_text)
        return "{sep}\n{text}\n{sep}\n".format(sep=separator, text=_text)

    def appendable_todo_list(_todo_list):
        return "\n".join([todo.to_item_format() for todo in _todo_list])

    result = ""
    result += appendable_header("Pending")
    result += appendable_todo_list(pending_todos)
    result += '\n\n' + appendable_header("Completed")
    result += appendable_todo_list(completed_todos)
    return result


def to_json(journal):
    """Returns a JSON representation of the Journal."""
    tags = get_tags_count(journal)
    todos = get_todos(journal)
    entry_dicts = []
    entry_id = 1
    for entry in journal.entries:
        entry_dict = entry.to_dict()
        entry_dict['id'] = entry_id
        entry_dicts.append(entry_dict)
        entry_id += 1
    result = {
        "tags": dict((tag, count) for count, tag in tags),
        "todos": [todo.to_dict() for todo in todos],
        "entries": entry_dicts,
    }
    return json.dumps(result, indent=2)


def to_md(journal):
    """Returns a markdown representation of the Journal"""
    out = []
    year, month = -1, -1
    for e in journal.entries:
        if not e.date.year == year:
            year = e.date.year
            out.append(str(year))
            out.append("=" * len(str(year)) + "\n")
        if not e.date.month == month:
            month = e.date.month
            out.append(e.date.strftime("%B"))
            out.append('-' * len(e.date.strftime("%B")) + "\n")
        out.append(e.to_md())
    result = "\n".join(out)
    return result


def to_txt(journal):
    """Returns the complete text of the Journal."""
    return journal.pprint()


def export(journal, format, output=None):
    """Exports the journal to various formats.
    format should be one of json, txt, text, md, markdown.
    If output is None, returns a unicode representation of the output.
    If output is a directory, exports entries into individual files.
    Otherwise, exports to the given output file.
    """
    maps = {
        "json": to_json,
        "txt": to_txt,
        "text": to_txt,
        "md": to_md,
        "markdown": to_md
    }
    if format not in maps:
        return "[ERROR: can't export to '{0}'. Valid options are 'md', 'txt', and 'json']".format(format)
    if output and os.path.isdir(output):  # multiple files
        return write_files(journal, output, format)
    else:
        content = maps[format](journal)
        if output:
            try:
                with codecs.open(output, "w", "utf-8") as f:
                    f.write(content)
                return "[Journal exported to {0}]".format(output)
            except IOError as e:
                return "[ERROR: {0} {1}]".format(e.filename, e.strerror)
        else:
            return content


def write_files(journal, path, format):
    """Turns your journal into separate files for each entry.
    Format should be either json, md or txt."""
    make_filename = lambda entry: e.date.strftime("%Y-%m-%d_{0}.{1}".format(slugify(u(e.title)), format))
    for e in journal.entries:
        full_path = os.path.join(path, make_filename(e))
        if format == 'json':
            content = json.dumps(e.to_dict(), indent=2) + "\n"
        elif format in ('md', 'markdown'):
            content = e.to_md()
        elif format in ('txt', 'text'):
            content = e.__unicode__()
        with codecs.open(full_path, "w", "utf-8") as f:
            f.write(content)
    return "[Journal exported individual files in {0}]".format(path)
