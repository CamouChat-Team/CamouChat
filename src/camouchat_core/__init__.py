"""src — Anti-detection WhatsApp automation SDK."""

__version__ = "0.7.0"

from .global_metadata import Platform , StorageType
from .contracts import ChatProtocol , MessageProtocol , UiConfigProtocol, MessageProcessorProtocol , ChatProcessorProtocol
from .contracts import  StorageProtocol, LoginProtocol, InteractionControllerProtocol ,  MediaCapableProtocol
from .Encryption import MessageEncryptor, MessageDecryptor, KeyManager
from .Exceptions import CamouChatError
from .camouchat_logger import camouchatLogger, browser_logger
from .directory import DirectoryManager

__all__ = [
    "Platform" , 
    "StorageType",
    "ChatProtocol" , 
    "MessageProtocol" , 
    "StorageProtocol",
    "LoginProtocol",
    "MessageEncryptor" , 
    "MessageDecryptor",
    "KeyManager",
    "CamouChatError",
    "camouchatLogger",
    "browser_logger",
    "DirectoryManager",
    "InteractionControllerProtocol",
    "MediaCapableProtocol",
    "UiConfigProtocol",
    "MessageProcessorProtocol",
    "ChatProcessorProtocol"
]