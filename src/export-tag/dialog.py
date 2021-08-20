from aqt import mw
from aqt.utils import openLink, showInfo
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import *

from .anki_util import all_tags
from .gui.forms.anki21.tag_export_dialog import Ui_Dialog
from .gui.resources.anki21 import icons_rc  # type: ignore


class TagExportDialog(QDialog):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self.parent = parent
        self.setupDialog()

        self.completer = Completer(self.dialog.lineedit_tag, all_tags())
        self.dialog.lineedit_tag.setCompleter(self.completer)

        self.dialog.button_export.clicked.connect(self._on_export_button_click)

        self.exec_()

    def setupDialog(self):
        self.dialog = Ui_Dialog()
        self.dialog.setupUi(self)

    def _on_export_button_click(self):
        if self._warn_if_invalid_tag():
            return

        file_name = self._show_save_file_dialog('.apkg')
        self._export_tag(file_name)

    # helper functions
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

    def _export_tag(self, file_name):
        print(file_name)
        print(self.dialog.lineedit_tag.text())


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
            'https://courses.ankipalace.com/?utm_source=anking_autocomplete_add-on&utm_medium=anki_add-on&utm_campaign=mastery_course'
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
