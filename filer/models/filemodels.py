#-*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import os

from django.core import urlresolvers
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import ugettext_lazy as _

from polymorphic import PolymorphicModel, PolymorphicManager

from filer import settings as filer_settings
from filer.fields.multistorage_file import MultiStorageFileField
from filer.models.abstract import BasseFile
from filer.models import mixins
from filer.models.foldermodels import Folder
from filer.utils.compatibility import python_2_unicode_compatible, DJANGO_1_7


class FileManager(PolymorphicManager):
    def find_all_duplicates(self):
        r = {}
        for file_obj in self.all():
            if file_obj.sha1:
                q = self.filter(sha1=file_obj.sha1)
                if len(q) > 1:
                    r[file_obj.sha1] = q
        return r

    def find_duplicates(self, file_obj):
        return [i for i in self.exclude(pk=file_obj.pk).filter(sha1=file_obj.sha1)]


class FileDetailsMixin(models.Model):
    description = models.TextField(null=True, blank=True,
        verbose_name=_('description'))

    class Meta:
        abstract = True

from filer.utils.loader import load_object


if not filer_settings.FILER_FILE_MODEL:
    class File(BaseImage):
        date_taken = models.DateTimeField(_('date taken'), null=True, blank=True,
                                          editable=False)

        author = models.CharField(_('author'), max_length=255, null=True, blank=True)

        must_always_publish_author_credit = models.BooleanField(_('must always publish author credit'), default=False)
        must_always_publish_copyright = models.BooleanField(_('must always publish copyright'), default=False)

        def save(self, *args, **kwargs):
            if self.date_taken is None:
                try:
                    exif_date = self.exif.get('DateTimeOriginal', None)
                    if exif_date is not None:
                        d, t = exif_date.split(" ")
                        year, month, day = d.split(':')
                        hour, minute, second = t.split(':')
                        if getattr(settings, "USE_TZ", False):
                            tz = get_current_timezone()
                            self.date_taken = make_aware(datetime(
                                int(year), int(month), int(day),
                                int(hour), int(minute), int(second)), tz)
                        else:
                            self.date_taken = datetime(
                                int(year), int(month), int(day),
                                int(hour), int(minute), int(second))
                except Exception:
                    pass
            if self.date_taken is None:
                self.date_taken = now()
            super(Image, self).save(*args, **kwargs)
else:
    # This is just an alias for the real model defined elsewhere
    # to let imports works transparently
    Image = load_object(filer_settings.FILER_IMAGE_MODEL)

