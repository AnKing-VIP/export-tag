from aqt import gui_hooks

from .dialog import init_dialog


def init_comatibility_aliases():
    from anki import Collection
    from anki.notes import Note

    if "get_note" not in list(Collection.__dict__.keys()):
        Collection.get_note = Collection.getNote

    if "string_tags" not in list(Note.__dict__.keys()):
        Note.string_tags = Note.stringTags

    if "set_tags_from_str" not in list(Note.__dict__.keys()):
        Note.set_tags_from_str = Note.setTagsFromStr


gui_hooks.profile_did_open.append(init_comatibility_aliases)


init_dialog()

