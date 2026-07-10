from enum import Enum


class ControlType(str, Enum):
    """
    Generic GUI control types understood by the Vision Engine.
    """

    APPLICATION = "application"

    WINDOW = "window"

    DIALOG = "dialog"

    TOOLBAR = "toolbar"

    MENU_BAR = "menu_bar"

    STATUS_BAR = "status_bar"

    PANEL = "panel"

    SECTION = "section"

    GROUP = "group"

    TAB = "tab"

    BUTTON = "button"

    TEXT_FIELD = "text_field"

    LABEL = "label"

    CHECKBOX = "checkbox"

    RADIO_BUTTON = "radio_button"

    COMBO_BOX = "combo_box"

    LIST = "list"

    TABLE = "table"

    TREE = "tree"

    IMAGE = "image"

    ICON = "icon"

    CANVAS = "canvas"

    UNKNOWN = "unknown"