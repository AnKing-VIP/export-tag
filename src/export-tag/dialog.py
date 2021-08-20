import os
from concurrent.futures import Future

from anki import hooks
from aqt import mw
from aqt.utils import (checkInvalidFilename, openLink, showInfo, showWarning,
                       tooltip, tr)
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import *

from .anki_util import all_tags
from .export_tag import export_tag
from .gui.forms.anki21.tag_export_dialog import Ui_Dialog
from .gui.resources.anki21 import icons_rc  # type: ignore


class TagExportDialog(QDialog):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self.parent = parent
        self.setupDialog()
        self.setupLinks()

        self.completer = Completer(self.dialog.lineedit_tag, all_tags())
        self.dialog.lineedit_tag.setCompleter(self.completer)

        self.dialog.button_export.clicked.connect(self._on_export_button_click)

        self.exec_()

    def setupDialog(self):
        self.dialog = Ui_Dialog()
        self.dialog.setupUi(self)

    def _on_export_button_click(self):
        # adapted from aqt.exporting.ExportDialog.accept

        if self._warn_if_invalid_tag():
            return

        while True:
            file = self._show_save_file_dialog('.apkg')
            if not file:
                return
            if checkInvalidFilename(os.path.basename(file), dirsep=False):
                continue
            if os.path.commonprefix([self.mw.pm.base, file]) == self.mw.pm.base:
                showWarning("Please choose a different export location.")
                continue
            break

        if file:
            # check we can write to file
            try:
                f = open(file, "wb")
                f.close()
            except OSError as e:
                showWarning(tr.exporting_couldnt_save_file(val=str(e)))
            else:
                os.unlink(file)

            # progress handler
            def exported_media(cnt: int) -> None:
                self.mw.taskman.run_on_main(
                    lambda: self.mw.progress.update(
                        label=tr.exporting_exported_media_file(count=cnt)
                    )
                )

            def do_export() -> None:
                self._export_tag(file)

            def on_done(future: Future) -> None:
                self.mw.progress.finish()
                hooks.media_files_did_export.remove(exported_media)
                # raises if exporter failed
                future.result()
                self.on_export_finished()

            self.mw.progress.start()
            hooks.media_files_did_export.append(exported_media)

            self.mw.taskman.run_in_background(do_export, on_done)

    def on_export_finished(self) -> None:
        tooltip("Tag exported", period=3000)
        QDialog.reject(self)

    def _warn_if_invalid_tag(self):
        if self.dialog.lineedit_tag.text() not in all_tags():
            showInfo('Please enter a valid tag')
            return True
        return False

    def _show_save_file_dialog(self, file_extension):
        last_part_of_tag = self.dialog.lineedit_tag.text().split(
            '::')[-1]
        suggested_filename = last_part_of_tag + file_extension
        result, _ = QFileDialog.getSaveFileName(
            self, "", suggested_filename, '*' + file_extension)
        return result

    def _export_tag(self, file):
        export_tag(
            file,
            self.dialog.lineedit_tag.text(),
            self.dialog.checkBox_include_schedul_info.isChecked(),
            self.dialog.checkBox_include_media.isChecked(),
        )

    def setupLinks(self):
        f = self.dialog
        f.toolButton_website.clicked.connect(lambda _: self.openWeb("anking"))
        f.toolButton_youtube.clicked.connect(lambda _: self.openWeb("youtube"))
        f.toolButton_patreon.clicked.connect(lambda _: self.openWeb("patreon"))
        f.toolButton_palace.clicked.connect(lambda _: self.openWeb("palace"))
        f.toolButton_instagram.clicked.connect(
            lambda _: self.openWeb("instagram"))
        f.toolButton_facebook.clicked.connect(
            lambda _: self.openWeb("facebook"))

    def openWeb(self, site):
        if site == "anking":
            openLink('https://www.ankingmed.com')
        elif site == "youtube":
            openLink('https://www.youtube.com/theanking')
        elif site == "patreon":
            openLink('https://www.patreon.com/ankingmed')
        elif site == "instagram":
            openLink('https://instagram.com/ankingmed')
        elif site == "facebook":
            openLink('https://facebook.com/ankingmed')
        elif site == "video":
            openLink('https://youtu.be/5XAq0KpU3Jc')
        elif site == "palace":
            openLink(
                'https://courses.ankipalace.com/?utm_source=anking_tag_export_add-on&utm_medium=anki_add-on&utm_campaign=mastery_course')


class Completer(QCompleter):

    def __init__(self, lineedit, options):
        super().__init__(options)

        self.lineedit = lineedit

        self.setFilterMode(Qt.MatchContains)
        self.setCaseSensitivity(Qt.CaseInsensitive)

        sorted_options = sorted(options, key=lambda x: str(x.count('::')) + x)
        self.model().setStringList(sorted_options)

    # show options when lineedit is clicked even if it is empty
    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress:
            self.setCompletionPrefix(self.lineedit.text())
            self.complete()

        return super().eventFilter(source, event)


def create_get_help_submenu(parent: QMenu) -> QMenu:
    submenu_name = "Get Anki Help"
    menu_options = [
        (
            "Online Mastery Course",
            'https://courses.ankipalace.com/?utm_source=anking_tag_export_add-on&utm_medium=anki_add-on&utm_campaign=mastery_course'
        ),
        ("Daily Q and A Support", "https://www.ankipalace.com/memberships"),
        ("1-on-1 Tutoring", "https://www.ankipalace.com/tutoring"),
    ]
    submenu = QMenu(submenu_name, parent)
    for name, url in menu_options:
        act = QAction(name, mw)
        act.triggered.connect(lambda _, u=url: openLink(u))
        submenu.addAction(act)
    return submenu


def maybe_add_get_help_submenu(menu: QMenu) -> None:
    """Adds 'Get Anki Help' submenu in 'Anking' menu if needed.

    The submenu is added if:
     - The submenu does not exist in menu
     - The submenu is an outdated version - existing is deleted

    With versioning and anking_get_help property,
    future version can rename, hide, or change contents in the submenu
    """
    submenu_property = "anking_get_help"
    submenu_ver = 2
    for act in menu.actions():
        if act.property(submenu_property) or act.text() == "Get Anki Help":
            ver = act.property("version")
            if ver and ver >= submenu_ver:
                return
            submenu = create_get_help_submenu(menu)
            menu.insertMenu(act, submenu)
            menu.removeAction(act)
            act.deleteLater()
            new_act = submenu.menuAction()
            new_act.setProperty(submenu_property, True)
            new_act.setProperty("version", submenu_ver)
            return
    else:
        submenu = create_get_help_submenu(menu)
        menu.addMenu(submenu)
        new_act = submenu.menuAction()
        new_act.setProperty(submenu_property, True)
        new_act.setProperty("version", submenu_ver)


def get_anking_menu() -> QMenu:
    """Return AnKing menu. If it doesn't exist, create one. Make sure its submenus are up to date."""
    menu_name = "&AnKing"
    menubar = mw.form.menubar
    for a in menubar.actions():
        if menu_name == a.text():
            menu = a.menu()
            break
    else:
        menu = menubar.addMenu(menu_name)
    maybe_add_get_help_submenu(menu)
    return menu


def DialogExecute():
    TagExportDialog(mw)


def init_dialog():
    menu = get_anking_menu()
    a = QAction("Export Tag", mw)
    a.triggered.connect(DialogExecute)
    menu.addAction(a)
