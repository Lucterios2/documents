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
from django.utils.translation import ugettext_lazy as _
from django.db import models
from lucterios.framework.models import LucteriosModel
from lucterios.CORE.models import LucteriosGroup, LucteriosUser
from django.core.exceptions import ObjectDoesNotExist

class Category(LucteriosModel):
    name = models.CharField(_('name'), max_length=25, blank=False)
    description = models.TextField(_('description'), blank=False)
    parent = models.ForeignKey('Category', verbose_name=_('parent'), null=True, on_delete=models.CASCADE)
    viewer = models.ManyToManyField(LucteriosGroup, related_name="category_viewer", verbose_name=_('viewer'), blank=True)
    modifier = models.ManyToManyField(LucteriosGroup, related_name="category_modifier", verbose_name=_('modifier'), blank=True)

    viewer__titles = [_("Available group viewers"), _("Chosen group viewers")]
    modifier__titles = [_("Available group modifiers"), _("Chosen group modifiers")]

    category__showfields = {_('001@Info'):["name", "description", "parent"], _('001@Permission'):["viewer", "modifier"]}
    category__editfields = {_('001@Info'):["name", "description", "parent"], _('001@Permission'):["viewer", "modifier"]}
    category__searchfields = ["name", "description", "parent.name"]
    default_fields = ["name", "description", "parent"]

    def __str__(self):
        return self.name

    class Meta(object):
        # pylint: disable=no-init
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['parent__name', 'name']

class Document(LucteriosModel):
    category = models.ForeignKey('Category', verbose_name=_('category'), null=False, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=25, blank=False)
    description = models.TextField(_('description'), blank=False)
    modifier = models.ForeignKey(LucteriosUser, related_name="document_modifier", verbose_name=_('modifier'), null=True, on_delete=models.CASCADE)
    date_modification = models.DateTimeField(verbose_name=_('date modification'), null=False, auto_now_add=True)
    creator = models.ForeignKey(LucteriosUser, related_name="document_creator", verbose_name=_('creator'), null=True, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(verbose_name=_('date creation'), null=False, auto_now_add=True)
    
    document__showfields = ["category", "name", "description", ("modifier", "date_modification"), ("creator", "date_creation")]
    document__editfields = ["category", "name", "description"]
    document__searchfields = ["name", "description", "category.name", "date_modification", "date_creation"]
    default_fields = ["category", "name", "description", "date_modification", "modifier"]

    def before_save(self, xfer):
        if (self.creator is None) and xfer.request.user.is_authenticated():
            self.creator = LucteriosUser.objects.get(pk=xfer.request.user.id)
        if (self.modifier is None) and xfer.request.user.is_authenticated():
            self.modifier = LucteriosUser.objects.get(pk=xfer.request.user.id)
        return

    def __str__(self):
        return '[%s] %s' % (self.category, self.name)

    class Meta(object):
        # pylint: disable=no-init
        verbose_name = _('document')
        verbose_name_plural = _('document')
        ordering = ['category__name', 'name']
