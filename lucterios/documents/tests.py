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
from os.path import join, dirname, exists
from shutil import rmtree, copyfile

from django.utils import formats, timezone
from django.contrib.auth.models import Permission

from lucterios.framework.test import LucteriosTest, add_empty_user
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.filetools import get_user_path, get_user_dir

from lucterios.CORE.models import LucteriosGroup, LucteriosUser

from lucterios.documents.models import Folder, Document
from lucterios.documents.views import FolderList, FolderAddModify, FolderDel, \
    DocumentList, DocumentAddModify, DocumentShow, DocumentDel, DocumentSearch


class FolderTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        group = LucteriosGroup.objects.create(
            name="my_group")
        group.save()
        group = LucteriosGroup.objects.create(
            name="other_group")
        group.save()

    def test_list(self):
        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'folderList')
        self.assert_xml_equal('TITLE', 'Dossiers')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_count_equal('ACTIONS/ACTION', 1)
        self.assert_action_equal('ACTIONS/ACTION', ('Fermer', 'images/close.png'))
        self.assert_count_equal('COMPONENTS/*', 3)
        self.assert_coordcomp_equal('COMPONENTS/GRID[@name="folder"]', (0, 1, 2, 1))
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/HEADER', 3)
        self.assert_xml_equal('COMPONENTS/GRID[@name="folder"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal('COMPONENTS/GRID[@name="folder"]/HEADER[@name="description"]', "description")
        self.assert_xml_equal('COMPONENTS/GRID[@name="folder"]/HEADER[@name="parent"]', "parent")
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 0)

    def test_add(self):
        self.factory.xfer = FolderAddModify()
        self.call('/lucterios.documents/folderAddModify', {}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'folderAddModify')
        self.assert_xml_equal('TITLE', 'Ajouter un dossier')
        self.assert_count_equal('COMPONENTS/*', 8)
        self.assert_comp_equal('COMPONENTS/EDIT[@name="name"]', None, (0, 0, 1, 1, 1))
        self.assert_comp_equal('COMPONENTS/MEMO[@name="description"]', None, (0, 1, 1, 1, 1))
        self.assert_comp_equal('COMPONENTS/SELECT[@name="parent"]', '0', (0, 2, 1, 1, 1))
        self.assert_count_equal('COMPONENTS/SELECT[@name="parent"]/CASE', 1)
        self.assert_coordcomp_equal('COMPONENTS/CHECKLIST[@name="viewer"]', (0, 0, 3, 1, 2))
        self.assert_coordcomp_equal('COMPONENTS/CHECKLIST[@name="modifier"]', (0, 1, 3, 1, 2))

    def test_addsave(self):

        folder = Folder.objects.all()
        self.assertEqual(len(folder), 0)

        self.factory.xfer = FolderAddModify()
        self.call('/lucterios.documents/folderAddModify', {'SAVE': 'YES', 'name': 'newcat', 'description': 'new folder',
                                                           'parent': '0', 'viewer': '1;2', 'modifier': '2'}, False)
        self.assert_observer('core.acknowledge', 'lucterios.documents', 'folderAddModify')
        self.assert_count_equal('CONTEXT/PARAM', 5)

        folder = Folder.objects.all()
        self.assertEqual(len(folder), 1)
        self.assertEqual(folder[0].name, "newcat")
        self.assertEqual(folder[0].description, "new folder")
        self.assertEqual(folder[0].parent, None)
        grp = folder[0].viewer.all().order_by('id')
        self.assertEqual(len(grp), 2)
        self.assertEqual(grp[0].id, 1)
        self.assertEqual(grp[1].id, 2)
        grp = folder[0].modifier.all().order_by('id')
        self.assertEqual(len(grp), 1)
        self.assertEqual(grp[0].id, 2)

        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'folderList')
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 1)

    def test_delete(self):
        folder = Folder.objects.create(
            name='truc', description='blabla')
        folder.viewer = LucteriosGroup.objects.filter(id__in=[1, 2])
        folder.modifier = LucteriosGroup.objects.filter(id__in=[2])
        folder.save()

        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'folderList')
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 1)

        self.factory.xfer = FolderDel()
        self.call('/lucterios.documents/folderDel', {'folder': '1', "CONFIRME": 'YES'}, False)
        self.assert_observer('core.acknowledge', 'lucterios.documents', 'folderDel')

        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'folderList')
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 0)


class DocumentTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)

        rmtree(get_user_dir(), True)
        current_user = add_empty_user()
        current_user.is_superuser = False
        current_user.save()
        group = LucteriosGroup.objects.create(name="my_group")
        group.save()
        group = LucteriosGroup.objects.create(name="other_group")
        group.save()
        self.factory.user = LucteriosUser.objects.get(username='empty')
        self.factory.user.groups = LucteriosGroup.objects.filter(id__in=[2])
        self.factory.user.user_permissions = Permission.objects.all()
        self.factory.user.save()

        folder1 = Folder.objects.create(name='truc1', description='blabla')
        folder1.viewer = LucteriosGroup.objects.filter(id__in=[1, 2])
        folder1.modifier = LucteriosGroup.objects.filter(id__in=[1])
        folder1.save()
        folder2 = Folder.objects.create(name='truc2', description='bouuuuu!')
        folder2.viewer = LucteriosGroup.objects.filter(id__in=[2])
        folder2.modifier = LucteriosGroup.objects.filter(id__in=[2])
        folder2.save()
        folder3 = Folder.objects.create(name='truc3', description='----')
        folder3.parent = folder2
        folder3.viewer = LucteriosGroup.objects.filter(id__in=[2])
        folder3.save()
        folder4 = Folder.objects.create(name='truc4', description='no')
        folder4.parent = folder2
        folder4.save()

    def create_doc(self):
        file_path = join(dirname(__file__), 'static',
                         'lucterios.documents', 'images', 'documentFind.png')
        copyfile(file_path, get_user_path('documents', 'document_1'))
        copyfile(file_path, get_user_path('documents', 'document_2'))
        copyfile(file_path, get_user_path('documents', 'document_3'))
        current_date = timezone.now()
        new_doc1 = Document.objects.create(name='doc1.png', description="doc 1", creator=self.factory.user,
                                           date_creation=current_date, date_modification=current_date)
        new_doc1.folder = Folder.objects.get(id=2)
        new_doc1.save()
        new_doc2 = Document.objects.create(name='doc2.png', description="doc 2", creator=self.factory.user,
                                           date_creation=current_date, date_modification=current_date)
        new_doc2.folder = Folder.objects.get(id=1)
        new_doc2.save()
        new_doc3 = Document.objects.create(name='doc3.png', description="doc 3", creator=self.factory.user,
                                           date_creation=current_date, date_modification=current_date)
        new_doc3.folder = Folder.objects.get(id=4)
        new_doc3.save()
        return current_date

    def test_list(self):
        folder = Folder.objects.all()
        self.assertEqual(len(folder), 4)

        self.factory.xfer = DocumentList()
        self.call('/lucterios.documents/documentList', {}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentList')
        self.assert_xml_equal('TITLE', 'Documents')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_count_equal('ACTIONS/ACTION', 1)
        self.assert_action_equal('ACTIONS/ACTION', ('Fermer', 'images/close.png'))
        self.assert_count_equal('COMPONENTS/*', 8)
        self.assert_coordcomp_equal('COMPONENTS/GRID[@name="document"]', (2, 2, 2, 2))
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/HEADER', 4)
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/HEADER[@name="description"]', "description")
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/HEADER[@name="date_modification"]', "date de modification")
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/HEADER[@name="modifier"]', "modificateur")
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/ACTIONS/ACTION', 3)

        self.assert_coordcomp_equal('COMPONENTS/CHECKLIST[@name="current_folder"]', (0, 2, 2, 1))
        self.assert_count_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE', 2)
        self.assert_xml_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE[@id="1"]', "truc1")
        self.assert_xml_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE[@id="2"]', "truc2")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbltitlecat"]', ">")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbldesc"]', '{[center]}{[i]}{[/i]}{[/center]}')

        self.factory.xfer = DocumentList()
        self.call('/lucterios.documents/documentList', {"current_folder": "1"}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/ACTIONS/ACTION', 1)
        self.assert_count_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE', 1)
        self.assert_xml_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE[@id="0"]', "..")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbltitlecat"]', ">truc1")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbldesc"]', "{[center]}{[i]}blabla{[/i]}{[/center]}")

        self.factory.xfer = DocumentList()
        self.call('/lucterios.documents/documentList', {"current_folder": "2"}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/ACTIONS/ACTION', 3)
        self.assert_count_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE', 2)
        self.assert_xml_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE[@id="0"]', "..")
        self.assert_xml_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE[@id="3"]', "truc3")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbltitlecat"]', ">truc2")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbldesc"]', "{[center]}{[i]}bouuuuu!{[/i]}{[/center]}")

        self.factory.xfer = DocumentList()
        self.call('/lucterios.documents/documentList', {"current_folder": "3"}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/ACTIONS/ACTION', 1)
        self.assert_count_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE', 1)
        self.assert_xml_equal('COMPONENTS/CHECKLIST[@name="current_folder"]/CASE[@id="2"]', "..")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbltitlecat"]', ">truc2>truc3")
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="lbldesc"]', "{[center]}{[i]}----{[/i]}{[/center]}")

    def test_add(self):
        self.factory.xfer = DocumentAddModify()
        self.call('/lucterios.documents/documentAddModify', {"current_folder": "2"}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentAddModify')
        self.assert_xml_equal('TITLE', 'Ajouter un document')
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="folder"]', ">truc2", (1, 0, 1, 1))
        self.assert_comp_equal('COMPONENTS/UPLOAD[@name="filename"]', None, (1, 1, 1, 1))
        self.assert_comp_equal('COMPONENTS/MEMO[@name="description"]', None, (1, 2, 1, 1))

    def test_addsave(self):
        self.factory.user = LucteriosUser.objects.get(username='empty')

        self.assertFalse(exists(get_user_path('documents', 'document_1')))
        file_path = join(dirname(__file__), 'static', 'lucterios.documents', 'images', 'documentFind.png')

        docs = Document.objects.all()
        self.assertEqual(len(docs), 0)

        self.factory.xfer = DocumentAddModify()
        with open(file_path, 'rb') as file_to_load:
            self.call('/lucterios.documents/documentAddModify', {"current_folder": "2", 'SAVE': 'YES', 'description': 'new doc',
                                                                 'filename_FILENAME': 'doc.png', 'filename': file_to_load}, False)
        self.assert_observer('core.acknowledge', 'lucterios.documents', 'documentAddModify')
        self.assert_count_equal('CONTEXT/PARAM', 3)

        docs = Document.objects.all()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].folder.id, 2)
        self.assertEqual(docs[0].name, 'doc.png')
        self.assertEqual(docs[0].description, "new doc")
        self.assertEqual(docs[0].creator.username, "empty")
        self.assertEqual(docs[0].modifier.username, "empty")
        self.assertEqual(docs[0].date_creation, docs[0].date_modification)
        self.assertTrue(exists(get_user_path('documents', 'document_1')))

    def test_saveagain(self):
        current_date = self.create_doc()

        self.factory.xfer = DocumentShow()
        self.call('/lucterios.documents/documentShow', {"document": "1"}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentShow')
        self.assert_xml_equal('TITLE', "Afficher le document")
        self.assert_count_equal('COMPONENTS/*', 9)
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="folder"]', ">truc2", (1, 0, 2, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="name"]', "doc1.png", (1, 1, 2, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="description"]', "doc 1", (1, 2, 2, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="modifier"]', '---', (1, 3, 1, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="date_modification"]', formats.date_format(current_date, "DATETIME_FORMAT"), (2, 3, 1, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="creator"]', "empty", (1, 4, 1, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="date_creation"]', formats.date_format(current_date, "DATETIME_FORMAT"), (2, 4, 1, 1))
        self.assert_count_equal('ACTIONS/ACTION', 2)

        self.factory.xfer = DocumentAddModify()
        self.call('/lucterios.documents/documentAddModify', {'SAVE': 'YES', "document": "1", 'description': 'old doc'}, False)
        docs = Document.objects.all().order_by('id')
        self.assertEqual(len(docs), 3)
        self.assertEqual(docs[0].folder.id, 2)
        self.assertEqual(docs[0].name, 'doc1.png')
        self.assertEqual(docs[0].description, "old doc")
        self.assertEqual(docs[0].creator.username, "empty")
        self.assertEqual(docs[0].modifier.username, "empty")
        self.assertNotEqual(docs[0].date_creation, docs[0].date_modification)

    def test_delete(self):
        current_date = self.create_doc()

        self.factory.xfer = DocumentList()
        self.call('/lucterios.documents/documentList', {"current_folder": "2"}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/RECORD', 1)
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/RECORD[@id="1"]/VALUE[@name="name"]', "doc1.png")
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/RECORD[@id="1"]/VALUE[@name="description"]', "doc 1")
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/RECORD[@id="1"]/VALUE[@name="date_modification"]', formats.date_format(current_date, "DATETIME_FORMAT"))
        self.assert_xml_equal('COMPONENTS/GRID[@name="document"]/RECORD[@id="1"]/VALUE[@name="modifier"]', "---")
        self.assertTrue(exists(get_user_path('documents', 'document_1')))

        self.factory.xfer = DocumentDel()
        self.call('/lucterios.documents/documentDel',
                  {"document": "1", "CONFIRME": 'YES'}, False)
        self.assert_observer('core.acknowledge', 'lucterios.documents', 'documentDel')

        self.factory.xfer = DocumentList()
        self.call(
            '/lucterios.documents/documentList', {"current_folder": "2"}, False)
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/RECORD', 0)
        self.assertFalse(exists(get_user_path('documents', 'document_1')))

    def test_readonly(self):
        current_date = self.create_doc()

        self.factory.xfer = DocumentShow()
        self.call('/lucterios.documents/documentShow', {"document": "2"}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentShow')
        self.assert_xml_equal('TITLE', "Afficher le document")
        self.assert_count_equal('COMPONENTS/*', 9)
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="folder"]', ">truc1", (1, 0, 2, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="name"]', "doc2.png", (1, 1, 2, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="description"]', "doc 2", (1, 2, 2, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="modifier"]', '---', (1, 3, 1, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="date_modification"]', formats.date_format(current_date, "DATETIME_FORMAT"), (2, 3, 1, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="creator"]', "empty", (1, 4, 1, 1))
        self.assert_comp_equal('COMPONENTS/LABELFORM[@name="date_creation"]', formats.date_format(current_date, "DATETIME_FORMAT"), (2, 4, 1, 1))
        self.assert_count_equal('ACTIONS/ACTION', 1)

        self.factory.xfer = DocumentAddModify()
        self.call('/lucterios.documents/documentAddModify', {"document": "2"}, False)
        self.assert_observer('core.exception', 'lucterios.documents', 'documentAddModify')
        self.assert_xml_equal('EXCEPTION/MESSAGE', "Écriture non autorisée !")

        self.factory.xfer = DocumentDel()
        self.call('/lucterios.documents/documentDel', {"document": "2"}, False)
        self.assert_observer('core.exception', 'lucterios.documents', 'documentDel')
        self.assert_xml_equal('EXCEPTION/MESSAGE', "Écriture non autorisée !")

    def test_cannot_view(self):
        self.create_doc()

        self.factory.xfer = DocumentShow()
        self.call('/lucterios.documents/documentShow', {"document": "3"}, False)
        self.assert_observer('core.exception', 'lucterios.documents', 'documentShow')
        self.assert_xml_equal('EXCEPTION/MESSAGE', "Visualisation non autorisée !")

        self.factory.xfer = DocumentAddModify()
        self.call('/lucterios.documents/documentAddModify', {"document": "3"}, False)
        self.assert_observer('core.exception', 'lucterios.documents', 'documentAddModify')
        self.assert_xml_equal('EXCEPTION/MESSAGE', "Visualisation non autorisée !")

        self.factory.xfer = DocumentDel()
        self.call('/lucterios.documents/documentDel', {"document": "3"}, False)
        self.assert_observer('core.exception', 'lucterios.documents', 'documentDel')
        self.assert_xml_equal('EXCEPTION/MESSAGE', "Visualisation non autorisée !")

    def test_search(self):
        self.create_doc()

        docs = Document.objects.filter(name__endswith='.png')
        self.assertEqual(len(docs), 3)

        self.factory.xfer = DocumentSearch()
        self.call('/lucterios.documents/documentSearch', {'CRITERIA': 'name||7||.png'}, False)
        self.assert_observer('core.custom', 'lucterios.documents', 'documentSearch')
        self.assert_count_equal('COMPONENTS/GRID[@name="document"]/RECORD', 2)
