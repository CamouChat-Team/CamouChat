"""
Contract to Layer the Web UI Selector File
"""

from abc import ABC
from logging import Logger, LoggerAdapter
from typing import Optional, Union

from playwright.async_api import Page

from camouchat.camouchat_logger import camouchatLogger


class WebUISelectorCapable(ABC):
    """
    A Capable class to cover the Selector Config Type.
    It will add all the functions needed for PLatform specific
    with the custom web ui and Act as a Reference to TypeCheck
    """

    def __init__(self, page: Page, log: Optional[Union[Logger, LoggerAdapter]], **kwargs):
        self.page = page
        self.log = log or camouchatLogger
