# -*- coding: utf-8 -*-
'''
lucterios.contacts package

@author: Laurent GAY
@organization: sd-libre.fr
@contact: info@sd-libre.fr
@copyright: 2015 sd-libre.fr
@license: This file is part of Lucterios.

Lucterios is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Lucterios is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Lucterios.  If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import unicode_literals
from os import unlink
from os.path import isfile

from django.db import models
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from lucterios.framework.models import LucteriosModel
from lucterios.framework.filetools import get_user_path
from lucterios.CORE.models import LucteriosGroup, LucteriosUser


class Folder(LucteriosModel):
    name = models.CharField(_('name'), max_length=25, blank=False)
    description = models.TextField(_('description'), blank=False)
    parent = models.ForeignKey(
        'Folder', verbose_name=_('parent'), null=True, on_delete=models.CASCADE)
    viewer = models.ManyToManyField(
        LucteriosGroup, related_name="folder_viewer", verbose_name=_('viewer'), blank=True)
    modifier = models.ManyToManyField(
        LucteriosGroup, related_name="folder_modifier", verbose_name=_('modifier'), blank=True)

    viewer__titles = [_("Available group viewers"), _("Chosen group viewers")]
    modifier__titles = [
        _("Available group modifiers"), _("Chosen group modifiers")]

    @classmethod
    def get_show_fields(cls):
        return {_('001@Info'): ["name", "description", "parent"], _('001@Permission'): ["viewer", "modifier"]}

    @classmethod
    def get_edit_fields(cls):
        return {_('001@Info'): ["name", "description", "parent"], _('001@Permission'): ["viewer", "modifier"]}

    @classmethod
    def get_search_fields(cls):
        return ["name", "description", "parent.name"]

    @classmethod
    def get_default_fields(cls):
        return ["name", "description", "parent"]

    def get_title(self):
        title = ">" + self.name
        if self.parent is not None:
            title = self.parent.get_title() + \
                title
        return title

    def __str__(self):
        return self.get_title()

    def is_readonly(self, user):
        readonly = True
        for modifier_item in self.modifier.all():
            if modifier_item in user.groups.all():
                readonly = False
        return readonly

    def cannot_view(self, user):
        cannotview = True
        for viewer_item in self.viewer.all():
            if viewer_item in user.groups.all():
                cannotview = False
        return cannotview

    def delete(self):
        file_paths = []
        docs = self.document_set.all()
        for doc in docs:
            file_paths.append(
                get_user_path("documents", "document_%s" % six.text_type(doc.id)))
        LucteriosModel.delete(self)
        for file_path in file_paths:
            if isfile(file_path):
                unlink(file_path)

    class Meta(object):

        verbose_name = _('folder')
        verbose_name_plural = _('folders')
        ordering = ['parent__name', 'name']


class Document(LucteriosModel):
    folder = models.ForeignKey(
        'Folder', verbose_name=_('folder'), null=True, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=25, blank=False)
    description = models.TextField(_('description'), blank=False)
    modifier = models.ForeignKey(LucteriosUser, related_name="document_modifier", verbose_name=_(
        'modifier'), null=True, on_delete=models.CASCADE)
    date_modification = models.DateTimeField(
        verbose_name=_('date modification'), null=False)
    creator = models.ForeignKey(LucteriosUser, related_name="document_creator", verbose_name=_(
        'creator'), null=True, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(
        verbose_name=_('date creation'), null=False)

    @classmethod
    def get_show_fields(cls):
        return ["folder", "name", "description", ("modifier", "date_modification"), ("creator", "date_creation")]

    @classmethod
    def get_edit_fields(cls):
        return ["folder", "name", "description"]

    @classmethod
    def get_search_fields(cls):
        return ["name", "description", "folder.name", "date_modification", "date_creation"]

    @classmethod
    def get_default_fields(cls):
        return ["name", "description", "date_modification", "modifier"]

    def __str__(self):
        return '[%s] %s' % (self.folder, self.name)

    def delete(self):
        file_path = get_user_path("documents", "document_%s" % six.text_type(
            self.id))
        LucteriosModel.delete(self)
        if isfile(file_path):
            unlink(file_path)

    class Meta(object):

        verbose_name = _('document')
        verbose_name_plural = _('documents')
        ordering = ['folder__name', 'name']
