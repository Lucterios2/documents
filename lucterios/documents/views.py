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
    
from lucterios.documents.models import Category, Document
from lucterios.framework.xferadvance import XferListEditor, XferDelete, XferAddEditor, XferShowEditor
from lucterios.framework.xfersearch import XferSearchEditor
from lucterios.framework.tools import MenuManage, FORMTYPE_NOMODAL, ActionsManage

MenuManage.add_sub("documents.conf", "core.extensions", "", _("Document"), "", 10)

@MenuManage.describ('documents.change_category', FORMTYPE_NOMODAL, 'documents.conf', _("Management of document's categories"))
class CategoryList(XferListEditor):
    caption = _("Categories")
    icon = "documentConf.png"
    model = Category
    field_id = 'category'

@ActionsManage.affect('Category', 'add', 'edit')
@MenuManage.describ('documents.add_category')
class CategoryAddModify(XferAddEditor):
    icon = "documentConf.png"
    model = Category
    field_id = 'category'
    caption_add = _("Add category")
    caption_modify = _("Modify category")

@ActionsManage.affect('Category', 'del')
@MenuManage.describ('documents.delete_category')
class CategoryDel(XferDelete):
    caption = _("Delete category")
    icon = "documentConf.png"
    model = Category
    field_id = 'category'

MenuManage.add_sub("office", None, "lucterios.documents/images/office.png", _("Office"), _("Office tools"), 70)

MenuManage.add_sub("documents.actions", "office", "lucterios.documents/images/document.png", _("Documents"), _("Documents storage tools"), 80)

@MenuManage.describ('documents.change_document', FORMTYPE_NOMODAL, 'documents.actions', _("Management of documents"))
class DocumentList(XferListEditor):
    caption = _("Documents")
    icon = "document.png"
    model = Document
    field_id = 'document'

@MenuManage.describ('documents.change_document', FORMTYPE_NOMODAL, 'documents.actions', _('To find a document following a set of criteria.'))
class LegalEntitySearch(XferSearchEditor):
    caption = _("Document search")
    icon = "documentFind.png"
    model = Document
    field_id = 'document'

@ActionsManage.affect('Document', 'add', 'modify')
@MenuManage.describ('documents.add_document')
class DocumentAddModify(XferAddEditor):
    icon = "document.png"
    model = Document
    field_id = 'document'
    caption_add = _("Add document")
    caption_modify = _("Modify document")

@ActionsManage.affect('Document', 'show')
@MenuManage.describ('documents.change_document')
class LegalEntityShow(XferShowEditor):
    caption = _("Show document")
    icon = "document.png"
    model = Document
    field_id = 'document'

@ActionsManage.affect('Document', 'del')
@MenuManage.describ('documents.delete_document')
class DocumentDel(XferDelete):
    caption = _("Delete document")
    icon = "document.png"
    model = Document
    field_id = 'document'
