# -*- coding: utf-8 -*-
'''
from_v1 module for documents

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
from django.apps import apps

from lucterios.install.lucterios_migration import MigrateAbstract
from lucterios.framework.filetools import get_user_path
from os.path import join, isfile
from os import mknod
from shutil import copyfile
from django.utils import six


class DocumentsMigrate(MigrateAbstract):

    def __init__(self, old_db):
        MigrateAbstract.__init__(self, old_db)
        self.group_list = self.old_db.objectlinks['groups']
        self.user_list = self.old_db.objectlinks['users']
        self.folder_list = {}
        self.doc_list = {}

    def _folders(self):
        group_mdl = apps.get_model("CORE", "LucteriosGroup")
        folder_mdl = apps.get_model("documents", "Folder")
        folder_mdl.objects.all().delete()
        self.folder_list = {}
        cur = self.old_db.open()
        cur.execute(
            "SELECT id, nom, description FROM org_lucterios_documents_categorie ORDER BY parent,id")
        for folderid, folder_name, folder_description in cur.fetchall():
            self.print_debug(
                "=> Folder [%s]%s '%s'", (folderid, folder_name, folder_description))
            if (folder_description is None) or (folder_description == ""):
                folder_description = folder_name
            self.folder_list[folderid] = folder_mdl.objects.create(
                name=folder_name, description=folder_description)
            modif_group = []
            cur_mod = self.old_db.open()
            cur_mod.execute(
                "SELECT groupe FROM org_lucterios_documents_modification WHERE categorie=%d" % folderid)
            for group_id in cur_mod.fetchall():
                modif_group.append(self.group_list[group_id[0]].id)
            visu_group = []
            cur_visu = self.old_db.open()
            cur_visu.execute(
                "SELECT groupe FROM org_lucterios_documents_visualisation WHERE categorie=%d" % folderid)
            for group_id in cur_visu.fetchall():
                visu_group.append(self.group_list[group_id[0]].id)
            self.folder_list[folderid].modifier = group_mdl.objects.filter(
                id__in=modif_group)
            self.folder_list[folderid].viewer = group_mdl.objects.filter(
                id__in=visu_group)
            self.folder_list[folderid].save()

        cur2 = self.old_db.open()
        cur2.execute(
            "SELECT id, parent FROM org_lucterios_documents_categorie WHERE (NOT parent IS NULL) ORDER BY parent,id")
        for folderid, folder_parent in cur2.fetchall():
            self.print_debug(
                "=> Folder %s  of %s", (folderid, folder_parent))
            if folder_parent is not None:
                self.folder_list[folderid].parent = self.folder_list[
                    folder_parent]
                self.folder_list[folderid].save()

    def _docs(self):
        doc_mdl = apps.get_model("documents", "Document")
        doc_mdl.objects.all().delete()
        self.doc_list = {}
        cur = self.old_db.open()
        cur.execute(
            "SELECT id, nom, description, categorie, modificateur, createur, dateModification, dateCreation FROM org_lucterios_documents_document")
        for docid, doc_name, doc_description, doc_folder, doc_modifier, doc_creator, doc_datemod, doc_datecreat in cur.fetchall():
            self.print_debug("=> Document %s", (doc_name,))
            self.doc_list[docid] = doc_mdl.objects.create(
                name=doc_name, description=doc_description, date_modification=doc_datemod, date_creation=doc_datecreat)
            if doc_folder is not None:
                self.doc_list[docid].folder = self.folder_list[doc_folder]
            self.doc_list[docid].modifier = self.user_list[doc_modifier]
            self.doc_list[docid].creator = self.user_list[doc_creator]
            self.doc_list[docid].save()
            new_filename = get_user_path(
                "documents", "document_%s" % six.text_type(self.doc_list[docid].id))
            old_filename = join(
                self.old_db.tmp_path, "usr", "org_lucterios_documents", "document%d" % docid)
            if isfile(old_filename):
                copyfile(old_filename, new_filename)
            else:
                self.print_info("*** Document '%s' not found ***", doc_name)
                mknod(new_filename)

    def run(self):
        self._folders()
        self._docs()
        self.print_info("Nb folders:%d", len(self.folder_list))
        self.print_info("Nb documents:%d", len(self.doc_list))
