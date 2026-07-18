"""Governed output channels for Mnemos.

An adapter is a channel Mnemos can deliver to. Every delivery runs through the same
risk/authority gate as a specialist, plus two rules for channels that reach other people:

  * a third-party channel MUST carry an AI-disclosure line, prepended to the payload --
    Mnemos never contacts anyone while pretending to be a person;
  * a third-party channel is never autonomous -- it needs approval (and a professional
    sign-off at risk 5), like any high-risk action.

Shipped adapters only ever write to the LOCAL filesystem (an outbox draft, a note). There
is deliberately NO telephony, SMS, or social adapter: automated calling/texting of third
parties is regulated (TCPA / GDPR / PECR) and is out of scope for a sovereign local tool.
"""

from .base import Adapter, DeliveryResult, get, names, register, send
from .integrations import register_integrations
from .outbox import register_default

register_default()
register_integrations()

__all__ = ["Adapter", "DeliveryResult", "get", "names", "register", "send"]
