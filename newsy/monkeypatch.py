from django.conf import settings

from cms.models.placeholdermodel import Placeholder
from cms.models import CMSPlugin



def _get_attached_fields(obj):
    """
    Returns an ITERATOR of all non-cmsplugin reverse foreign key related fields.
    """
    for rel in obj._meta.get_all_related_objects() + \
            obj._meta.get_all_related_many_to_many_objects():
        if issubclass(rel.model, CMSPlugin):
            continue
        field = getattr(obj, rel.get_accessor_name())
        if field.count():
            yield rel.field

__INSTALLED = False

def install():
    if not __INSTALLED and getattr(settings, 'NEWSY_MONKEYPATCH_ATTACHED_FIELDS',
            True):
        Placeholder._get_attached_fields = _get_attached_fields

