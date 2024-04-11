import json
import os
from pathlib import Path
from typing import List
from typing import Optional

from binaryninja import BackgroundTaskThread
from binaryninja import BinaryView
from binaryninja import execute_on_main_thread
from binaryninjaui import getMonospaceFont
from binaryninjaui import SidebarWidget
from binaryninjaui import UIActionHandler
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout

from .msft_scrapper import MSFTLearnScrapper


def make_hline():
    out = QFrame()
    out.setFrameShape(QFrame.HLine)
    out.setFrameShadow(QFrame.Sunken)
    return out


class ScrapperThread(BackgroundTaskThread):
    def __init__(
        self, function, syntax_callback, description_callback, retval_callback
    ):
        super().__init__(
            f"Getting data for {function} ...",
            can_cancel=True,
        )
        self.function = function
        self.syntax_callback = syntax_callback
        self.description_callback = description_callback
        self.retval_callback = retval_callback
        self.descriptions = []
        self.cache = {}
        self.root = Path(__file__).parent
        self.cache_file = f"{self.root}/cache.json"
        self.syntax = None
        self.description = []
        self.return_value = ""

    def run(self):
        if self.function == "":
            return
        # load or create cache
        if self.load_cache() is False:
            self.create_cache()
            self.load_cache()

        # if function is found in cache set the values
        if self.function in self.cache:
            self.syntax = self.cache[self.function].get("syntax", "")
            self.description = self.cache[self.function].get("description", None)
            self.return_value = self.cache[self.function].get("return_value", None)
        else:
            # setup the scrapper and grab data
            scrapper = MSFTLearnScrapper(self.function)
            self.syntax = [scrapper.get_syntax()]
            self.description = [scrapper.get_description(True)]
            self.return_value = scrapper.get_return_value()

            # make sure to write data to cache only if the description is not empty
            # unknown functions must not be written to cache
            if self.description != [""]:
                self.write_cache()

    def load_cache(self) -> bool:
        if not os.path.exists(self.cache_file):
            return False

        with open(self.cache_file) as json_file:
            self.cache = json.load(json_file)
        return True

    def create_cache(self):
        json_object = json.dumps({})
        with open(self.cache_file, "w") as json_file:
            json_file.write(json_object)

    def write_cache(self):
        cache = {
            "syntax": self.syntax,
            "description": self.description,
            "return_value": self.return_value,
        }
        self.cache[self.function] = cache
        json_object = json.dumps(self.cache)
        with open(self.cache_file, "w") as json_file:
            json_file.write(json_object)

    def cancel(self):
        self.syntax_callback = lambda *_: None
        super().cancel()

    def finish(self):
        super().finish()
        self.syntax_callback(self.syntax)
        self.description_callback(self.description)
        self.retval_callback(self.return_value)


class WinDocSidebar(SidebarWidget):
    """Displays a brief explanation of what an instruction does"""

    timer = 4000

    def __init__(self, name, _frame, bv: Optional[BinaryView] = None):
        SidebarWidget.__init__(self, name)
        self.actionHandler = UIActionHandler()
        self.actionHandler.setupActionHandler(self)

        self._bv = None
        self.bv = bv

        self.last_function = None

        self._scrapper_thread = None
        self._the_timer: QTimer = QTimer(self)
        self._the_timer.setSingleShot(True)
        self._the_timer.timeout.connect(self._timer_expired)

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignTop)

        self._label_font: QFont = QFont()
        self._label_font_small: QFont = QFont()
        self._mono_font: QFont = getMonospaceFont(self)
        self._mono_font_large: QFont = getMonospaceFont(self)

        self._label_font_small.setPointSize(self._label_font.pointSize() - 2)
        self._mono_font_large.setPointSize(self._mono_font.pointSize() + 4)

        def make_label(text):
            label = QLabel(text)
            return label

        self._function = QLabel()
        self._function.setTextFormat(Qt.RichText)
        self._function.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self._function.setOpenExternalLinks(True)
        self._function.setWordWrap(True)
        self._layout.addWidget(self._function)

        self._layout.addWidget(make_hline())

        self._syntax_label = make_label("Syntax:")
        self._layout.addWidget(self._syntax_label)
        self._syntax = QLabel()
        self._syntax.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._syntax.setWordWrap(True)
        self._layout.addWidget(self._syntax)

        self._layout.addWidget(make_hline())

        self._description_label = make_label("Description:")
        self._layout.addWidget(self._description_label)
        self._description = QLabel()
        self._description.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._description.setWordWrap(True)
        self._layout.addWidget(self._description)

        self._layout.addWidget(make_hline())

        self._retval_label = make_label("Return value:")
        self._layout.addWidget(self._retval_label)
        self._retval = QLabel()
        self._retval.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._retval.setWordWrap(True)
        self._layout.addWidget(self._retval)

        self.notifyFontChanged()

    @property
    def function(self):
        return self._function.text()

    @property
    def syntax(self):
        return self._syntax.text()

    @property
    def description(self):
        return self._description.text()

    @property
    def retval(self):
        return self._retval.text()

    @function.setter
    def function(self, instr: Optional[str]):
        self._function.setText(str(instr))

    @syntax.setter
    def syntax(self, syntax_list: List[str]):
        try:
            self._syntax.setText("\n".join(syntax_list))
        except TypeError:
            pass

    @description.setter
    def description(self, description_list: List[str]):
        try:
            self._description.setText("<br>".join(description_list))
        except TypeError:
            pass

    @retval.setter
    def retval(self, retval_list: List[str]):
        try:
            self._retval.setText("\n".join(retval_list))
        except TypeError:
            pass

    @property
    def bv(self):
        return self._bv

    @bv.setter
    def bv(self, new_bv: Optional[BinaryView]):
        self._bv = new_bv

    @staticmethod
    def escape(in_str):
        return in_str

    def _syntax_generated(self, new):
        execute_on_main_thread(self._the_timer.stop)
        self.syntax = new

    def _description_generated(self, new):
        execute_on_main_thread(self._the_timer.stop)
        self.description = new

    def _retval_generated(self, new):
        execute_on_main_thread(self._the_timer.stop)
        self.retval = new

    def _timer_expired(self):
        if self._scrapper_thread is not None:
            self._scrapper_thread.cancel()
        self._syntax.setText("Scrapping timed out")

    def reset(self):
        self.function = ""
        self.syntax = []
        self.description = []
        self.retval = []

    def notifyOffsetChanged(self, offset):
        assembly = self.bv.get_disassembly(offset)
        if len(assembly.split()) != 0 and assembly.split()[0] == "call":
            self.show_function_info(offset)

    def notifyViewChanged(self, view_frame):
        if view_frame is None:
            self.bv = None
        else:
            view = view_frame.getCurrentViewInterface()
            self.bv = view.getData()

    def contextMenuEvent(self, event):
        self.m_contextMenuManager.show(self.m_menu, self.actionHandler)

    def notifyFontChanged(self, *args, **kwargs):
        # I don't know how to get a non-monospaced font from the Binja UI API
        # neither do I ~matteyeux
        self._label_font: QFont = QFont()
        self._label_font_small: QFont = QFont()
        self._mono_font: QFont = getMonospaceFont(self)
        self._mono_font_large: QFont = getMonospaceFont(self)

        self._label_font_small.setPointSize(self._label_font.pointSize() - 2)
        self._mono_font_large.setPointSize(self._mono_font.pointSize() + 4)

        self._syntax_label.setFont(self._label_font)
        self._syntax.setFont(self._mono_font)

    def show_function_info(self, addr):
        """Callback for the menu item that passes the information to the GUI"""
        if self._scrapper_thread is not None:
            self._scrapper_thread.cancel()
        self._the_timer.stop()

        self.last_function = addr
        function_name = None
        try:
            function_name = self.bv.get_function_at(self.bv.get_callees(addr)[0]).name
        except IndexError:
            functions = self.bv.get_functions_containing(addr)
            if len(functions) != 0:
                f = functions[0]
                llil_inst = f.get_low_level_il_at(addr)
                function_name = llil_inst.mlil.operands[1].tokens[0]

        self.function = function_name
        # For some reaseon, binja crashes if I don't set values in these vars
        # QObject: Cannot create children for a parent that is in a different thread.
        # (Parent is QLabel(0x55cd36281b70), parent's thread is QThread(0x55cd31e9bf10), current thread is QThread(0x7fdf74096410)
        # QObject: Cannot create children for a parent that is in a different thread.
        # (Parent is QLabel(0x55cd35185850), parent's thread is QThread(0x55cd31e9bf10), current thread is QThread(0x7fdf74096410)
        # QObject: Cannot create children for a parent that is in a different thread.
        # (Parent is QLabel(0x55cd36066910), parent's thread is QThread(0x55cd31e9bf10), current thread is QThread(0x7fdf74096410)
        # QObject: Cannot create children for a parent that is in a different thread.
        # (Parent is QTextDocument(0x7fdf7401f0d0), parent's thread is QThread(0x7fdf74096410), current thread is QThread(0x55cd31e9bf10)
        # [1]    4732 segmentation fault (core dumped)  ~/Documents/binaryninja/binaryninja -de
        self._syntax.setText(" ")
        self.description = [" "]
        self.retval = [" "]

        # If function starts with `sub_` we should not request doc for this function
        if not self.function.startswith("sub_"):
            self._scrapper_thread = ScrapperThread(
                self.function,
                self._syntax_generated,
                self._description_generated,
                self._retval_generated,
            )
            self._scrapper_thread.start()
            self._the_timer.start(self.timer)
