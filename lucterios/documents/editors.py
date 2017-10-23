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
from os.path import isfile, join

from django.utils.translation import ugettext_lazy as _
from django.utils import six, timezone

from lucterios.framework.filetools import get_user_path, get_user_dir
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.tools import ActionsManage, CLOSE_NO, FORMTYPE_MODAL
from lucterios.framework.xfercomponents import XferCompUpLoad, XferCompDownLoad
from lucterios.framework.editors import LucteriosEditor

from lucterios.CORE.models import LucteriosUser
from lucterios.documents.models import Folder


class DocumentEditor(LucteriosEditor):

    def before_save(self, xfer):
        current_folder = xfer.getparam('current_folder')
        if current_folder is not None:
            if current_folder != 0:
                self.item.folder = Folder.objects.get(
                    id=current_folder)
            else:
                self.item.folder = None
        if xfer.getparam('filename_FILENAME') is not None:
            self.item.name = xfer.getparam('filename_FILENAME')
        if (self.item.creator is None) and xfer.request.user.is_authenticated():
            self.item.creator = LucteriosUser.objects.get(
                pk=xfer.request.user.id)
        if xfer.request.user.is_authenticated():
            self.item.modifier = LucteriosUser.objects.get(
                pk=xfer.request.user.id)
        else:
            self.item.modifier = None
        self.item.date_modification = timezone.now()
        if self.item.id is None:
            self.item.date_creation = self.item.date_modification
        return

    def saving(self, xfer):
        if 'filename' in xfer.request.FILES.keys():
            tmp_file = xfer.request.FILES['filename']
            file_path = get_user_path("documents", "document_%s" % six.text_type(
                self.item.id))
            with open(file_path, "wb") as file_tmp:
                file_tmp.write(tmp_file.read())  # write the tmp file

    def edit(self, xfer):
        xfer.change_to_readonly("folder")
        obj_cmt = xfer.get_components('name')
        xfer.remove_component('name')
        file_name = XferCompUpLoad('filename')
        file_name.http_file = True
        file_name.maxsize = 16 * 1024 * 1024  # 16Mo
        file_name.compress = True
        file_name.set_value('')
        file_name.set_location(obj_cmt.col, obj_cmt.row, obj_cmt.colspan, obj_cmt.rowspan)
        xfer.add_component(file_name)

    def show(self, xfer):
        destination_file = join("documents", "document_%s" % six.text_type(
            self.item.id))
        if not isfile(join(get_user_dir(), destination_file)):
            raise LucteriosException(IMPORTANT, _("File not found!"))
        obj_cmt = xfer.get_components('creator')
        down = XferCompDownLoad('filename')
        down.compress = True
        down.http_file = True
        down.maxsize = 0
        down.set_value(self.item.name)
        down.set_download(destination_file)
        down.set_action(xfer.request, ActionsManage.get_action_url('documents.Document', 'AddModify', xfer),
                        modal=FORMTYPE_MODAL, close=CLOSE_NO)
        down.set_location(obj_cmt.col, obj_cmt.row + 1, 4)
        xfer.add_component(down)
