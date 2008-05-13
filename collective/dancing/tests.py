import unittest
from zope.testing import doctest
from Testing import ZopeTestCase as ztc
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup

from email.Parser import Parser
from email.Header import Header, decode_header
from email.Charset import Charset, QP, SHORTEST
from copy import deepcopy

import collective.dancing

def setup_error_log(site):
    site.error_log._ignored_exceptions = ()
    def print_error(index=0):
        logs = site.error_log.getLogEntries()
        if logs:
            print logs[index]['tb_text']
    return print_error

def replace_with_fieldindex(name, site):
    site.portal_catalog.delIndex(name)
    site.portal_catalog.addIndex(name, 'FieldIndex')
    site.portal_catalog.manage_reindexIndex((name,))

@onsetup
def setUp():
    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml', collective.dancing)
    fiveconfigure.debug_mode = False
    ztc.installPackage('collective.dancing')

setUp()
ptc.setupPloneSite(products=['collective.dancing'])

def decodeMessageAsString( msg):
    """ This helper method takes Message object or string and returns 
        string which does not contain base64 encoded parts
        Returns message without any encoding in parts
    """
    if isinstance(msg, str):
        msg = Parser().parsestr(msg)
    
    new = deepcopy(msg)
    # From is utf8 encoded: '=?utf-8?q?Site_Administrator_=3C=3E?='
    new.replace_header('From', decode_header(new['From'])[0][0])
    new.replace_header('Subject', decode_header(new['Subject'])[0][0])
    charset = Charset('utf-8')
    charset.header_encoding = SHORTEST
    charset.body_encoding   = QP
    charset.output_charset  = 'utf-8'

    for part in new.walk():
        if part.get_content_maintype()=="multipart":
            continue
        decoded = part.get_payload(decode=1)
        del part['Content-Transfer-Encoding']
        part.set_payload(decoded, charset)

    return new.as_string()        

def test_suite():
    return unittest.TestSuite([

        doctest.DocTestSuite('collective.dancing.channel'),
        doctest.DocTestSuite('collective.dancing.composer'),
        doctest.DocTestSuite('collective.dancing.utils'),

        ztc.ZopeDocFileSuite(
            'channel.txt',
            test_class=ptc.PloneTestCase,
            ),

        ztc.ZopeDocFileSuite(
            'collector.txt',
            test_class=ptc.PloneTestCase,
            ),

        ztc.ZopeDocFileSuite(
            'composer.txt',
            test_class=ptc.PloneTestCase,
            ),

        ztc.ZopeDocFileSuite(
            'browser.txt',
            test_class=ptc.FunctionalTestCase,
            ),
        ztc.ZopeDocFileSuite(
            'portlets.txt',
            test_class=ptc.FunctionalTestCase,
            ),
        ])
