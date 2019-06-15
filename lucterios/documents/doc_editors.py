# -*- coding: utf-8 -*-
'''
lucterios.documents package

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
from hashlib import md5
from urllib.request import urlopen
from urllib.error import URLError
from etherpad_lite import EtherpadLiteClient, EtherpadException

from django.conf import settings


class DocEditor(object):

    def __init__(self, root_url, doccontainer):
        self.root_url = root_url
        self.doccontainer = doccontainer

    @classmethod
    def get_all_editor(cls):
        def all_subclasses(cls):
            return set(cls.__subclasses__()).union([subclass_item for class_item in cls.__subclasses__() for subclass_item in all_subclasses(class_item)])
        return all_subclasses(cls)

    @classmethod
    def get_all_extension_supported(cls):
        res = ()
        for cls in cls.get_all_editor():
            res += cls.extension_supported()
        return set(res)

    @classmethod
    def extension_supported(cls):
        return ()

    def is_manage(self):
        for ext_item in self.extension_supported():
            if self.doccontainer.name.endswith('.' + ext_item):
                return True

    def get_iframe(self):
        return "{[iframe]}{[/iframe]}"

    def send_content(self):
        pass

    def save_content(self):
        pass

    def close(self):
        pass


class EtherPadEditor(DocEditor):

    def __init__(self, root_url, doccontainer):
        DocEditor.__init__(self, root_url, doccontainer)
        self._client = None
        self._groupid = None
        if hasattr(settings, 'ETHERPAD'):
            self.params = settings.ETHERPAD
        else:
            self.params = None

    @property
    def padid(self):
        md5res = md5()
        md5res.update(self.root_url.encode())
        return '%s-%s' % (md5res.hexdigest(), self.doccontainer.name)

    @classmethod
    def extension_supported(cls):
        if hasattr(settings, 'ETHERPAD') and ('url' in settings.ETHERPAD) and ('apikey' in settings.ETHERPAD):
            try:
                cls('', None).client.checkToken()
                return ('txt', 'html')
            except (URLError, EtherpadException):
                pass
        return ()

    @property
    def client(self):
        if self._client is None:
            self._client = EtherpadLiteClient(base_url='%s/api' % self.params['url'], api_version='1.2.13',
                                              base_params={'apikey': self.params['apikey']})
        return self._client

    def get_iframe(self):
        return '{[iframe name="embed_readwrite" src="%s/p/%s" width="100%%" height="450"]}{[/iframe]}' % (self.params['url'], self.padid)

    def close(self):
        if self.padid in self.client.listAllPads()['padIDs']:
            self.client.deletePad(padID=self.padid)

    def send_content(self):
        pad_ids = self.client.listAllPads()['padIDs']
        if not (self.padid in pad_ids):
            self.client.createPad(padID=self.padid, padName=self.doccontainer.name)
        file_ext = self.doccontainer.name.split('.')[-1]

        content = self.doccontainer.content.read()
        if content != b'':
            if file_ext == 'html':
                self.client.setHTML(padID=self.padid, html=content.decode())
            else:
                self.client.setText(padID=self.padid, text=content.decode())

    def load_export(self, export_type):
        url = "%s/p/%s/export/%s" % (self.params['url'], self.padid, export_type)
        return urlopen(url, timeout=self.client.timeout).read()

    def save_content(self):
        file_ext = self.doccontainer.name.split('.')[-1]
        if file_ext == 'etherpad':
            self.doccontainer.content = self.load_export('etherpad')
        elif file_ext == 'html':
            self.doccontainer.content = self.client.getHTML(padID=self.padid)['html']
        else:  # text
            self.doccontainer.content = self.client.getText(padID=self.padid)['text']
