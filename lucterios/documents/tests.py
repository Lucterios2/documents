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
from lucterios.framework.test import LucteriosTest
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from unittest.suite import TestSuite
from unittest.loader import TestLoader
from lucterios.documents.views import FolderList, FolderAddModify, FolderDel
from lucterios.CORE.models import LucteriosGroup
from lucterios.documents.models import Folder

class FolderTest(LucteriosTest):
    # pylint: disable=too-many-public-methods,too-many-statements

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        group = LucteriosGroup.objects.create(name="my_group")  # pylint: disable=no-member
        group.save()
        group = LucteriosGroup.objects.create(name="other_group")  # pylint: disable=no-member
        group.save()

    def test_list(self):
        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('Core.Custom', 'lucterios.documents', 'folderList')
        self.assert_xml_equal('TITLE', 'Dossiers')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_count_equal('ACTIONS/ACTION', 1)
        self.assert_action_equal('ACTIONS/ACTION', ('Fermer', 'images/close.png'))
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_coordcomp_equal('COMPONENTS/GRID[@name="folder"]', (0, 1, 2, 1))
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/HEADER', 3)
        self.assert_xml_equal('COMPONENTS/GRID[@name="folder"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal('COMPONENTS/GRID[@name="folder"]/HEADER[@name="description"]', "description")
        self.assert_xml_equal('COMPONENTS/GRID[@name="folder"]/HEADER[@name="parent"]', "parent")
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 0)

    def test_add(self):
        self.factory.xfer = FolderAddModify()
        self.call('/lucterios.documents/folderAddModify', {}, False)
        self.assert_observer('Core.Custom', 'lucterios.documents', 'folderAddModify')
        self.assert_xml_equal('TITLE', 'Ajouter un dossier')
        self.assert_count_equal('COMPONENTS/*', 27)
        self.assert_comp_equal('COMPONENTS/EDIT[@name="name"]', None, (1, 0, 1, 1, 1))
        self.assert_comp_equal('COMPONENTS/MEMO[@name="description"]', None, (1, 1, 1, 1, 1))
        self.assert_comp_equal('COMPONENTS/SELECT[@name="parent"]', '0', (1, 2, 1, 1, 1))
        self.assert_count_equal('COMPONENTS/SELECT[@name="parent"]/CASE', 1)
        self.assert_coordcomp_equal('COMPONENTS/CHECKLIST[@name="viewer_available"]', (1, 1, 1, 5, 2))
        self.assert_coordcomp_equal('COMPONENTS/CHECKLIST[@name="viewer_chosen"]', (3, 1, 1, 5, 2))
        self.assert_coordcomp_equal('COMPONENTS/CHECKLIST[@name="modifier_available"]', (1, 6, 1, 5, 2))
        self.assert_coordcomp_equal('COMPONENTS/CHECKLIST[@name="modifier_chosen"]', (3, 6, 1, 5, 2))

    def test_addsave(self):

        folder = Folder.objects.all()  # pylint: disable=no-member
        self.assertEqual(len(folder), 0)

        self.factory.xfer = FolderAddModify()
        self.call('/lucterios.documents/folderAddModify', {'SAVE':'YES', 'name':'newcat', 'description':'new folder', \
                                       'parent':'0', 'viewer':'1;2', 'modifier':'2'}, False)
        self.assert_observer('Core.Acknowledge', 'lucterios.documents', 'folderAddModify')
        self.assert_count_equal('CONTEXT/PARAM', 6)

        folder = Folder.objects.all()  # pylint: disable=no-member
        self.assertEqual(len(folder), 1)
        self.assertEqual(folder[0].name, "newcat")
        self.assertEqual(folder[0].description, "new folder")
        self.assertEqual(folder[0].parent, None)
        grp = folder[0].viewer.all().order_by('id')  # pylint: disable=no-member
        self.assertEqual(len(grp), 2)
        self.assertEqual(grp[0].id, 1)
        self.assertEqual(grp[1].id, 2)
        grp = folder[0].modifier.all().order_by('id')  # pylint: disable=no-member
        self.assertEqual(len(grp), 1)
        self.assertEqual(grp[0].id, 2)

        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('Core.Custom', 'lucterios.documents', 'folderList')
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 1)

    def test_delete(self):
        folder = Folder.objects.create(name='truc', description='blabla')  # pylint: disable=no-member
        folder.viewer = LucteriosGroup.objects.filter(id__in=[1, 2])  # pylint: disable=no-member
        folder.modifier = LucteriosGroup.objects.filter(id__in=[2])  # pylint: disable=no-member
        folder.save()

        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('Core.Custom', 'lucterios.documents', 'folderList')
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 1)

        self.factory.xfer = FolderDel()
        self.call('/lucterios.documents/folderDel', {'folder':'1', "CONFIRME":'YES'}, False)
        self.assert_observer('Core.Acknowledge', 'lucterios.documents', 'folderDel')

        self.factory.xfer = FolderList()
        self.call('/lucterios.documents/folderList', {}, False)
        self.assert_observer('Core.Custom', 'lucterios.documents', 'folderList')
        self.assert_count_equal('COMPONENTS/GRID[@name="folder"]/RECORD', 0)

class DocumentTest(LucteriosTest):
    # pylint: disable=too-many-public-methods,too-many-statements

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        group = LucteriosGroup.objects.create(name="my_group")  # pylint: disable=no-member
        group.save()
        group = LucteriosGroup.objects.create(name="other_group")  # pylint: disable=no-member
        group.save()
        folder = Folder.objects.create(name='truc1', description='blabla')  # pylint: disable=no-member
        folder.viewer = LucteriosGroup.objects.filter(id__in=[1, 2])  # pylint: disable=no-member
        folder.modifier = LucteriosGroup.objects.filter(id__in=[2])  # pylint: disable=no-member
        folder.save()
        folder = Folder.objects.create(name='truc2', description='blabla')  # pylint: disable=no-member
        folder.viewer = LucteriosGroup.objects.filter(id__in=[2])  # pylint: disable=no-member
        folder.modifier = LucteriosGroup.objects.filter(id__in=[2])  # pylint: disable=no-member
        folder.save()

def suite():
    # pylint: disable=redefined-outer-name
    suite = TestSuite()
    loader = TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(FolderTest))
    suite.addTest(loader.loadTestsFromTestCase(DocumentTest))
    return suite
