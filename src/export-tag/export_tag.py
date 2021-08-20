import re

from anki.exporting import AnkiPackageExporter
from aqt import mw


class TagExporter(AnkiPackageExporter):

    def __init__(self, col, tag) -> None:
        AnkiPackageExporter.__init__(self, col)
        self.tag = tag

    def postExport(self):
        # remove all tags except the ones that start with self.tag from notes
        for nid in self.dst.find_notes(''):
            note = self.dst.get_note(nid)

            tag_string = note.string_tags()
            m = re.search(f'(?:^| ){self.tag}([(::)\w]+)(?:$| )', tag_string)
            tag_suffix = m.group(1) if m else ""
            note.set_tags_from_str(self.tag + tag_suffix)

            note.flush()


def export_tag(file, tag, include_schedul_info, include_media):
    exporter = TagExporter(mw.col, tag)
    exporter.includeSched = include_schedul_info
    exporter.includeMedia = include_media

    cids = mw.col.find_cards(f'"tag:{tag}"')
    exporter.cids = cids
    exporter.exportInto(file)
