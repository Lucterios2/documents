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
from os.path import join, exists
from os import makedirs, walk
from shutil import rmtree
from zipfile import ZipFile

from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.utils import six

from lucterios.framework.xferadvance import XferListEditor, XferDelete, XferAddEditor, XferShowEditor,\
    TITLE_ADD, TITLE_MODIFY, TITLE_DELETE, TITLE_EDIT, TITLE_CANCEL, TITLE_OK,\
    TEXT_TOTAL_NUMBER
from lucterios.framework.xfersearch import XferSearchEditor
from lucterios.framework.tools import MenuManage, FORMTYPE_NOMODAL, ActionsManage, \
    FORMTYPE_MODAL, CLOSE_NO, FORMTYPE_REFRESH, SELECT_SINGLE, SELECT_NONE, \
    WrapAction, CLOSE_YES, SELECT_MULTI
from lucterios.framework.xfercomponents import XferCompButton, XferCompLabelForm, \
    XferCompCheckList, XferCompImage, XferCompUpLoad, \
    XferCompDownLoad
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework import signal_and_lock
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.filetools import get_tmp_dir, get_user_dir
from lucterios.CORE.parameters import notfree_mode_connect
from lucterios.CORE.models import LucteriosGroup

from lucterios.documents.models import Folder, Document

MenuManage.add_sub(
    "documents.conf", "core.extensions", "", _("Document"), "", 10)


@MenuManage.describ('documents.change_folder', FORMTYPE_NOMODAL, 'documents.conf', _("Management of document's folders"))
class FolderList(XferListEditor):
    caption = _("Folders")
    icon = "documentConf.png"
    model = Folder
    field_id = 'folder'


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('documents.add_folder')
class FolderAddModify(XferAddEditor):
    icon = "documentConf.png"
    model = Folder
    field_id = 'folder'
    caption_add = _("Add folder")
    caption_modify = _("Modify folder")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('documents.delete_folder')
class FolderDel(XferDelete):
    caption = _("Delete folder")
    icon = "documentConf.png"
    model = Folder
    field_id = 'folder'


class FolderImportExport(XferContainerAcknowledge):
    icon = "documentConf.png"
    model = Folder
    field_id = 'folder'

    def add_components(self, dlg):
        pass

    def run_archive(self):
        pass

    def fillresponse(self):
        if self.getparam('SAVE') is None:
            dlg = self.create_custom()
            dlg.item = self.item
            img = XferCompImage('img')
            img.set_value(self.icon_path())
            img.set_location(0, 0, 1, 3)
            dlg.add_component(img)
            lbl = XferCompLabelForm('title')
            lbl.set_value_as_title(self.caption)
            lbl.set_location(1, 0, 6)
            dlg.add_component(lbl)

            dlg.fill_from_model(1, 1, False, desc_fields=['parent'])
            parent = dlg.get_components('parent')
            parent.colspan = 3

            self.add_components(dlg)
            dlg.add_action(self.get_action(TITLE_OK, "images/ok.png"), close=CLOSE_YES, params={'SAVE': 'YES'})
            dlg.add_action(WrapAction(TITLE_CANCEL, 'images/cancel.png'))
        else:
            if self.getparam("parent", 0) != 0:
                self.item = Folder.objects.get(id=self.getparam("parent", 0))
            else:
                self.item = Folder()
            self.run_archive()


@ActionsManage.affect_grid(_("Import"), "zip.png", unique=SELECT_NONE)
@MenuManage.describ('documents.add_folder')
class FolderImport(FolderImportExport):
    caption = _("Import")

    def add_components(self, dlg):
        dlg.fill_from_model(1, 2, False, desc_fields=['viewer', 'modifier'])
        zipfile = XferCompUpLoad('zipfile')
        zipfile.http_file = True
        zipfile.description = _('zip file')
        zipfile.maxsize = 1024 * 1024 * 1024  # 1Go
        zipfile.add_filter('.zip')
        zipfile.set_location(1, 15)
        dlg.add_component(zipfile)

    def run_archive(self):
        viewerids = self.getparam("viewer", ())
        modifierids = self.getparam("modifier", ())
        if 'zipfile' in self.request.FILES.keys():
            upload_file = self.request.FILES['zipfile']
            tmp_dir = join(get_tmp_dir(), 'zipfile')
            if exists(tmp_dir):
                rmtree(tmp_dir)
            makedirs(tmp_dir)
            try:
                with ZipFile(upload_file, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                viewers = LucteriosGroup.objects.filter(id__in=viewerids)
                modifiers = LucteriosGroup.objects.filter(id__in=modifierids)
                self.item.import_files(
                    tmp_dir, viewers, modifiers, self.request.user)
            finally:
                if exists(tmp_dir):
                    rmtree(tmp_dir)


@ActionsManage.affect_grid(_("Extract"), "zip.png", unique=SELECT_NONE)
@MenuManage.describ('documents.add_folder')
class FolderExtract(FolderImportExport):
    caption = _("Extract")

    def open_zipfile(self, filename):
        dlg = self.create_custom()
        dlg.item = self.item
        img = XferCompImage('img')
        img.set_value(self.icon_path())
        img.set_location(0, 0, 1, 3)
        dlg.add_component(img)
        lbl = XferCompLabelForm('title')
        lbl.set_value_as_title(self.caption)
        lbl.set_location(1, 0, 6)
        dlg.add_component(lbl)
        zipdown = XferCompDownLoad('filename')
        zipdown.compress = False
        zipdown.http_file = True
        zipdown.maxsize = 0
        zipdown.set_value(filename)
        zipdown.set_download(filename)
        zipdown.set_location(1, 15, 2)
        dlg.add_component(zipdown)

    def run_archive(self):
        tmp_dir = join(get_tmp_dir(), 'zipfile')
        download_file = join(get_user_dir(), 'extract.zip')
        if exists(tmp_dir):
            rmtree(tmp_dir)
        makedirs(tmp_dir)
        try:
            self.item.extract_files(tmp_dir)
            with ZipFile(download_file, 'w') as zip_ref:
                for (dirpath, _dirs, filenames) in walk(tmp_dir):
                    for filename in filenames:
                        zip_ref.write(
                            join(dirpath, filename), join(dirpath[len(tmp_dir):], filename))
        finally:
            if exists(tmp_dir):
                rmtree(tmp_dir)
        self.open_zipfile('extract.zip')


MenuManage.add_sub("office", None, "lucterios.documents/images/office.png", _("Office"), _("Office tools"), 70)

MenuManage.add_sub("documents.actions", "office", "lucterios.documents/images/document.png",
                   _("Documents"), _("Documents storage tools"), 80)


@MenuManage.describ('documents.change_document', FORMTYPE_NOMODAL, 'documents.actions', _("Management of documents"))
class DocumentList(XferListEditor):
    caption = _("Documents")
    icon = "document.png"
    model = Document
    field_id = 'document'

    def fillresponse_header(self):
        self.current_folder = self.getparam('current_folder', 0)
        if self.current_folder > 0:
            self.filter = Q(folder=self.current_folder)
        else:
            self.filter = Q(folder=None)

    def fill_current_folder(self, new_col, new_row):
        lbl = XferCompLabelForm('lblcat')
        lbl.set_value_as_name(_("current folder:"))
        lbl.set_location(new_col, new_row)
        self.add_component(lbl)
        lbl = XferCompLabelForm('lbltitlecat')
        if self.current_folder > 0:
            folder_obj = Folder.objects.get(id=self.current_folder)
            lbl.set_value(folder_obj.get_title())
            folder_description = folder_obj.description
        else:
            folder_obj = None
            lbl.set_value('>')
            folder_description = ""
        lbl.set_location(new_col + 1, new_row)
        self.add_component(lbl)
        lbl = XferCompLabelForm('lbldesc')
        lbl.set_value_as_header(folder_description)
        lbl.set_location(new_col + 2, new_row, 2)
        self.add_component(lbl)
        return folder_obj

    def add_folder_buttons(self, new_col, new_row):
        btn = XferCompButton('btnFolder')
        btn.set_location(new_col, new_row + 2)
        btn.set_action(self.request, FolderAddModify.get_action(_('add'), "images/add.png"),
                       modal=FORMTYPE_MODAL, close=CLOSE_NO)
        self.add_component(btn)
        if self.current_folder > 0:
            btn = XferCompButton('btnEditFolder')
            btn.set_location(new_col + 1, new_row + 2, 1)
            btn.set_action(self.request, FolderAddModify.get_action(_('edit'), "images/edit.png"),
                           modal=FORMTYPE_MODAL, close=CLOSE_NO, params={'folder': six.text_type(self.current_folder)})
            self.add_component(btn)

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        obj_doc = self.get_components('document')
        self.remove_component('document')
        self.tab = obj_doc.tab
        new_col = obj_doc.col
        new_row = obj_doc.row
        obj_doc.set_location(new_col + 2, new_row + 1, 2, 2)
        self.add_component(obj_doc)

        folder_obj = self.fill_current_folder(new_col, new_row)
        list_folders = []
        if self.current_folder > 0:
            folder_filter = Q(parent__id=self.current_folder)
        else:
            folder_filter = Q(parent=None)
        if notfree_mode_connect() and not self.request.user.is_superuser:
            folder_filter &= Q(viewer__in=self.request.user.groups.all())
        folder_list = Folder.objects.filter(folder_filter).order_by("name").distinct()
        for folder_item in folder_list:
            list_folders.append((folder_item.id, folder_item.name))
        if folder_obj is not None:
            if folder_obj.parent is None:
                parent_id = 0
            else:
                parent_id = folder_obj.parent.id
            list_folders.insert(0, (parent_id, '..'))
        select = XferCompCheckList('current_folder')
        select.simple = True
        select.set_select(list_folders)
        select.set_location(new_col, new_row + 1, 2)
        select.set_action(self.request, self.get_action(), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(select)

        self.add_folder_buttons(new_col, new_row)


def docgrid_modify_condition(xfer, gridname=''):
    current_folder = xfer.getparam('current_folder', 0)
    if current_folder > 0:
        folder_obj = Folder.objects.get(id=current_folder)
    else:
        folder_obj = None
    if folder_obj is not None and notfree_mode_connect() and not xfer.request.user.is_superuser:
        if folder_obj.cannot_view(xfer.request.user):
            raise LucteriosException(IMPORTANT, _("No allow to view!"))
        if folder_obj.is_readonly(xfer.request.user):
            return False
    return True


def docshow_modify_condition(xfer):
    if xfer.item.folder is not None and notfree_mode_connect() and not xfer.request.user.is_superuser:
        if xfer.item.folder.cannot_view(xfer.request.user):
            raise LucteriosException(IMPORTANT, _("No allow to view!"))
        if xfer.item.folder.is_readonly(xfer.request.user):
            return False
    return True


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png", condition=docgrid_modify_condition)
@ActionsManage.affect_show(TITLE_MODIFY, "images/edit.png", close=CLOSE_YES, condition=docshow_modify_condition)
@MenuManage.describ('documents.add_document')
class DocumentAddModify(XferAddEditor):
    icon = "document.png"
    model = Document
    field_id = 'document'
    caption_add = _("Add document")
    caption_modify = _("Modify document")

    def fill_simple_fields(self):
        XferAddEditor.fill_simple_fields(self)
        if self.item.id is None:
            current_folder = self.getparam('current_folder')
            if current_folder is not None:
                self.item.folder = Folder.objects.get(id=current_folder)
                self.has_changed = True
        return self.has_changed

    def fillresponse(self):
        if self.item.folder is not None and notfree_mode_connect() and not self.request.user.is_superuser:
            if self.item.folder.cannot_view(self.request.user):
                raise LucteriosException(IMPORTANT, _("No allow to view!"))
            if self.item.folder.is_readonly(self.request.user):
                raise LucteriosException(IMPORTANT, _("No allow to write!"))
        XferAddEditor.fillresponse(self)


@ActionsManage.affect_grid(TITLE_EDIT, "images/show.png", unique=SELECT_SINGLE)
@MenuManage.describ('documents.change_document')
class DocumentShow(XferShowEditor):
    caption = _("Show document")
    icon = "document.png"
    model = Document
    field_id = 'document'


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI, condition=docgrid_modify_condition)
@MenuManage.describ('documents.delete_document')
class DocumentDel(XferDelete):
    caption = _("Delete document")
    icon = "document.png"
    model = Document
    field_id = 'document'

    def fillresponse(self):
        folder = None
        if len(self.items) > 0:
            folder = self.items[0].folder
        if folder is not None and notfree_mode_connect() and not self.request.user.is_superuser:
            if folder.cannot_view(self.request.user):
                raise LucteriosException(IMPORTANT, _("No allow to view!"))
            if folder.is_readonly(self.request.user):
                raise LucteriosException(IMPORTANT, _("No allow to write!"))
        XferDelete.fillresponse(self)


@MenuManage.describ('documents.change_document', FORMTYPE_NOMODAL, 'documents.actions', _('To find a document following a set of criteria.'))
class DocumentSearch(XferSearchEditor):
    caption = _("Document search")
    icon = "documentFind.png"
    model = Document
    field_id = 'document'

    def get_text_search(self):
        criteria_desc = XferSearchEditor.get_text_search(self)
        if notfree_mode_connect():
            if self.filter is None:
                self.filter = Q()
            self.filter = self.filter & (Q(folder=None) | Q(folder__viewer__in=self.request.user.groups.all()))
        return criteria_desc


@signal_and_lock.Signal.decorate('summary')
def summary_documents(xfer):
    if WrapAction.is_permission(xfer.request, 'documents.change_document'):
        row = xfer.get_max_row() + 1
        lab = XferCompLabelForm('documenttitle')
        lab.set_value_as_infocenter(_('Document management'))
        lab.set_location(0, row, 4)
        xfer.add_component(lab)
        filter_result = Q()
        if notfree_mode_connect():
            filter_result = filter_result & (
                Q(folder=None) | Q(folder__viewer__in=xfer.request.user.groups.all()))
        nb_doc = len(Document.objects.filter(
            *[filter_result]))
        lbl_doc = XferCompLabelForm('lbl_nbdocument')
        lbl_doc.set_location(0, row + 1, 4)
        if nb_doc == 0:
            lbl_doc.set_value_center(_("no file currently available"))
        elif nb_doc == 1:
            lbl_doc.set_value_center(_("one file currently available"))
        else:
            lbl_doc.set_value_center(_("%d files currently available") % nb_doc)
        xfer.add_component(lbl_doc)
        lab = XferCompLabelForm('documentend')
        lab.set_value_center('{[hr/]}')
        lab.set_location(0, row + 2, 4)
        xfer.add_component(lab)
        return True
    else:
        return False


@signal_and_lock.Signal.decorate('conf_wizard')
def conf_wizard_document(wizard_ident, xfer):
    if isinstance(wizard_ident, list) and (xfer is None):
        wizard_ident.append(("document_params", 55))
    elif (xfer is not None) and (wizard_ident == "document_params"):
        xfer.add_title(_("Lucterios documents"), _("Parameters"))
        lbl = XferCompLabelForm("nb_folder")
        lbl.set_location(1, xfer.get_max_row() + 1)
        lbl.set_value(TEXT_TOTAL_NUMBER % {'name': Folder._meta.verbose_name_plural, 'count': len(Folder.objects.all())})
        xfer.add_component(lbl)
        lbl = XferCompLabelForm("nb_doc")
        lbl.set_location(1, xfer.get_max_row() + 1)
        lbl.set_value(TEXT_TOTAL_NUMBER % {'name': Document._meta.verbose_name_plural, 'count': len(Document.objects.all())})
        xfer.add_component(lbl)
        btn = XferCompButton("btnconf")
        btn.set_location(4, xfer.get_max_row() - 1, 1, 2)
        btn.set_action(xfer.request, FolderList.get_action(TITLE_MODIFY, "images/edit.png"), close=CLOSE_NO)
        xfer.add_component(btn)
