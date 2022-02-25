import re

from anki.exporting import AnkiPackageExporter
from aqt import mw


class TagExporter(AnkiPackageExporter):
    def __init__(self, col, tag) -> None:
        AnkiPackageExporter.__init__(self, col)
        self.tag = tag

    def postExport(self):
        for nid in self.dst.find_notes(""):
            # remove all tags except the ones that start with self.tag from notes
            note = self.dst.get_note(nid)
            filtered_tags = [
                m.group(1)
                for tag in note.string_tags().split(" ")
                if (m := re.search(f"^({self.tag}(::\S+)*)$", tag))
            ]
            note.set_tags_from_str(" ".join(filtered_tags))

            note.flush()


def export_tag(file, tag, include_schedul_info, include_media):
    exporter = TagExporter(mw.col, tag)
    exporter.includeSched = include_schedul_info
    exporter.includeMedia = include_media

    cids = set(mw.col.find_cards(f'"tag:{tag}"'))
    cids.update(
        set(mw.col.find_cards(f'"tag:{tag}::*"'))
    )  # not needed in newer Anki versions

    exporter.cids = list(cids)
    exporter.exportInto(file)
