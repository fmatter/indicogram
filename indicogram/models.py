from clld.db.meta import Base, PolymorphicBaseMixin
from clld.db.models import IdNameDescriptionMixin
from clld_morphology_plugin.models import Wordform
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from zope.interface import implementer

from indicogram.interfaces import IPhoneme

# -----------------------------------------------------------------------------
# specialized common mapper classes
# -----------------------------------------------------------------------------


@implementer(IPhoneme)
class Phoneme(Base, IdNameDescriptionMixin):
    pass


class FormPhoneme(Base, PolymorphicBaseMixin):
    phoneme_pk = Column(Integer, ForeignKey("phoneme.pk"), nullable=False)
    form_pk = Column(Integer, ForeignKey("wordform.pk"), nullable=False)
    phoneme = relationship(Phoneme, innerjoin=True, backref="forms")
    form = relationship(Wordform, innerjoin=True, backref="segments")
