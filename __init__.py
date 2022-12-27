from pathlib import Path

from binaryninjaui import Sidebar
from binaryninjaui import SidebarWidgetType
from PySide6.QtGui import QImage

from .sidebar import WinDocSidebar

root = Path(__file__).parent


class MSFTDocWidget(SidebarWidgetType):
    def __init__(self):
        # Icon is windows by kareemovic1000 from the Noun Project
        # https://thenounproject.com/icon/windows-1787061/
        icon = QImage(str(root.joinpath("icon.png")))
        SidebarWidgetType.__init__(self, icon, "Docs")

    def createWidget(self, frame, data):
        # This callback is called when a widget needs to be created for a given context. Different
        # widgets are created for each unique BinaryView. They are created on demand when the sidebar
        # widget is visible and the BinaryView becomes active.
        return WinDocSidebar("Function doc", frame, data)


Sidebar.addSidebarWidgetType(MSFTDocWidget())
