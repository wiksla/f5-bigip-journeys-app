# -*- coding: utf-8 -*-

import pytest
from unittest import TestCase
from collections import UserList
import f5parser.SCFStateMachine as SCFStateMachine
from f5parser.SCFObject import SCFObject, SCFProperties, BracedSSVList, \
    BracedNLSVList, NLSVList, SSVList, DblQuotedString, EmptyValue, Flag

__author__ = 'jimd'


class TestVirtualServer(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm virtual /Common/EXPLICIT-PROXY-HTTPS-BYPASS {
    destination /Common/0.0.0.0:443
    ip-protocol tcp
    mask any
    profiles {
        /Common/tcp { }
    }
    source 0.0.0.0/0
    translate-address disabled
    translate-port enabled
    vlans {
        /Common/tcp-forward-tunnel
    }
    vlans-enabled
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['virtual']
        cls.comp[-1].objname = '/Common/EXPLICIT-PROXY-HTTPS-BYPASS'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['destination'] = '/Common/0.0.0.0:443'
        cls.comp[-1].props['ip-protocol'] = 'tcp'
        cls.comp[-1].props['mask'] = 'any'
        cls.comp[-1].props['profiles'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/tcp'] = EmptyValue()
        cls.comp[-1].props['source'] = '0.0.0.0/0'
        cls.comp[-1].props['translate-address'] = 'disabled'
        cls.comp[-1].props['translate-port'] = 'enabled'
        cls.comp[-1].props['vlans'] = SCFProperties()
        cls.comp[-1].props['vlans']['/Common/tcp-forward-tunnel'] = Flag()
        cls.comp[-1].props['vlans-enabled'] = Flag()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleSimpleObjectSingleProp(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    base-mac 00:01:d7:00:00:00
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['base-mac'] = '00:01:d7:00:00:00'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleSimpleObjectSingleQuotedProp(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    quoted "my string"
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['quoted'] = '"my string"'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleSimpleObjectNoProps(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev { }'''
        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjSingleEmptyProp(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    base-mac { }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['base-mac'] = EmptyValue()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestTwoObjsThreeEmptyProps(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev1.dev {
    base-mac1 { }
    base-mac2 { }
    base-mac3 { }
}
cm device /Common/dev2.dev {
    base-macA { }
    base-macB { }
    base-macC { }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev1.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['base-mac1'] = EmptyValue()
        cls.comp[-1].props['base-mac2'] = EmptyValue()
        cls.comp[-1].props['base-mac3'] = EmptyValue()
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev2.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['base-macA'] = EmptyValue()
        cls.comp[-1].props['base-macB'] = EmptyValue()
        cls.comp[-1].props['base-macC'] = EmptyValue()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjThreeProps(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm cert /Common/dtca-bundle.crt {
    cache-path /config/filestore/files_d/Common_d/trust_certificate_d/:Common:dtca-bundle.crt_32426_13
    checksum SHA1:1298:6b02644bf16c711fec92a63c53258d80b8d85b85
    revision 13
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['cert']
        cls.comp[-1].objname = '/Common/dtca-bundle.crt'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props[
            'cache-path'] = '/config/filestore/files_d/Common_d/trust_certificate_d/:Common:dtca-bundle.crt_32426_13'
        cls.comp[-1].props['checksum'] = 'SHA1:1298:6b02644bf16c711fec92a63c53258d80b8d85b85'
        cls.comp[-1].props['revision'] = '13'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjSingleFlag(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    flag
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['flag'] = Flag()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjThreeFlags(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    flag1
    flag2
    flag3
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['flag1'] = Flag()
        cls.comp[-1].props['flag2'] = Flag()
        cls.comp[-1].props['flag3'] = Flag()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjFlagsAndProps(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    flag1
    prop1 val1
    flag2
    prop2 val2
    prop3 val3
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['flag1'] = Flag()
        cls.comp[-1].props['prop1'] = 'val1'
        cls.comp[-1].props['flag2'] = Flag()
        cls.comp[-1].props['prop2'] = 'val2'
        cls.comp[-1].props['prop3'] = 'val3'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjSSVList(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    ssvitem { val1 "quoted2 with space" }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['ssvitem'] = BracedSSVList()
        cls.comp[-1].props['ssvitem'].append('val1')
        cls.comp[-1].props['ssvitem'].append('"quoted2 with space"')

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestTwoSimpleObjs(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/dev.dev {
    base-mac 00:01:d7:00:00:00
}
ltm virtual /Common/APM-1-test_VS {
    destination /Common/172.16.1.15:9443
    ip-protocol tcp
    mask 255.255.255.255
    pool /Common/test_pool
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/dev.dev'
        cls.comp[-1].props = SCFProperties()
        cls.comp[-1].props['base-mac'] = '00:01:d7:00:00:00'
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['virtual']
        cls.comp[-1].objname = '/Common/APM-1-test_VS'
        cls.comp[-1].props['destination'] = '/Common/172.16.1.15:9443'
        cls.comp[-1].props['ip-protocol'] = 'tcp'
        cls.comp[-1].props['mask'] = '255.255.255.255'
        cls.comp[-1].props['pool'] = '/Common/test_pool'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjSingleNest(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm virtual /Common/APM-1-test_VS {
    vlans {
        /Common/vnmet1
        /Common/vnmet2
    }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['virtual']
        cls.comp[-1].objname = '/Common/APM-1-test_VS'
        cls.comp[-1].props['vlans'] = SCFProperties()
        cls.comp[-1].props['vlans']['/Common/vnmet1'] = Flag()
        cls.comp[-1].props['vlans']['/Common/vnmet2'] = Flag()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('o: %s' % o)
            print('c: %s' % c)
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjThreeNests(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm virtual /Common/APM-1-test_VS {
    profiles {
        /Common/APM_connectivity_profile {
            context clientside
        }
        /Common/scconnect-clientssl {
            context clientside
        }
        /Common/serverssl-insecure-compatible {
            context serverside
        }
    }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['virtual']
        cls.comp[-1].objname = '/Common/APM-1-test_VS'
        cls.comp[-1].props['profiles'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/APM_connectivity_profile'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/APM_connectivity_profile']['context'] = 'clientside'
        cls.comp[-1].props['profiles']['/Common/scconnect-clientssl'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/scconnect-clientssl']['context'] = 'clientside'
        cls.comp[-1].props['profiles']['/Common/serverssl-insecure-compatible'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/serverssl-insecure-compatible'][
            'context'] = 'serverside'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestSingleObjDoubleNest(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm virtual /Common/APM-1-test_VS {
    profiles {
        /Common/APM_connectivity_profile {
            context clientside
        }
    }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['virtual']
        cls.comp[-1].objname = '/Common/APM-1-test_VS'
        cls.comp[-1].props['profiles'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/APM_connectivity_profile'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/APM_connectivity_profile']['context'] = 'clientside'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestComplexObj(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm virtual /Common/APM-2-test_VS {
    destination /Common/172.16.1.15:10443
    ip-protocol tcp
    mask 255.255.255.255
    profiles {
        /Common/APM-2_access_profile { }
        /Common/APM_connectivity_profile {
            context clientside
        }
        /Common/APM_rewrite_profile { }
        /Common/http { }
        /Common/ppp { }
        /Common/rba { }
        /Common/scconnect-clientssl {
            context clientside
        }
        /Common/serverssl-insecure-compatible {
            context serverside
        }
        /Common/tcp { }
        /Common/websso { }
    }
    rules {
        /Common/APM_iRule
    }
    source 0.0.0.0/0
    source-address-translation {
        type automap
    }
    translate-address enabled
    translate-port enabled
    vlans {
        /Common/vnmet1
    }
    vlans-enabled
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['virtual']
        cls.comp[-1].objname = '/Common/APM-2-test_VS'
        cls.comp[-1].props['destination'] = '/Common/172.16.1.15:10443'
        cls.comp[-1].props['ip-protocol'] = 'tcp'
        cls.comp[-1].props['mask'] = '255.255.255.255'
        cls.comp[-1].props['profiles'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/APM-2_access_profile'] = EmptyValue()
        cls.comp[-1].props['profiles']['/Common/APM_connectivity_profile'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/APM_connectivity_profile']['context'] = 'clientside'
        cls.comp[-1].props['profiles']['/Common/APM_rewrite_profile'] = EmptyValue()
        cls.comp[-1].props['profiles']['/Common/http'] = EmptyValue()
        cls.comp[-1].props['profiles']['/Common/ppp'] = EmptyValue()
        cls.comp[-1].props['profiles']['/Common/rba'] = EmptyValue()
        cls.comp[-1].props['profiles']['/Common/scconnect-clientssl'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/scconnect-clientssl']['context'] = 'clientside'
        cls.comp[-1].props['profiles']['/Common/serverssl-insecure-compatible'] = SCFProperties()
        cls.comp[-1].props['profiles']['/Common/serverssl-insecure-compatible'][
            'context'] = 'serverside'
        cls.comp[-1].props['profiles']['/Common/tcp'] = EmptyValue()
        cls.comp[-1].props['profiles']['/Common/websso'] = EmptyValue()
        cls.comp[-1].props['rules'] = SCFProperties()
        cls.comp[-1].props['rules']['/Common/APM_iRule'] = Flag()
        cls.comp[-1].props['source'] = '0.0.0.0/0'
        cls.comp[-1].props['source-address-translation'] = SCFProperties()
        cls.comp[-1].props['source-address-translation']['type'] = 'automap'
        cls.comp[-1].props['translate-address'] = 'enabled'
        cls.comp[-1].props['translate-port'] = 'enabled'
        cls.comp[-1].props['vlans'] = SCFProperties()
        cls.comp[-1].props['vlans']['/Common/vnmet1'] = Flag()
        cls.comp[-1].props['vlans-enabled'] = Flag()

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestiAppSingleTableRow(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''sys application service /Common/cgn.app/cgn {
    tables {
        data_opt__http_servers {
            column-names { name ip port }
            rows {
                {
                    row { DO1 192.168.114.4 0 }
                }
                {
                    row { DO2 192.168.114.5 0 }
                }
            }
        }
    }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'sys'
        cls.comp[-1].objtype = ['application', 'service']
        cls.comp[-1].objname = '/Common/cgn.app/cgn'
        cls.comp[-1].props['tables'] = SCFProperties()
        cls.comp[-1].props['tables']['data_opt__http_servers'] = SCFProperties()
        cls.comp[-1].props['tables']['data_opt__http_servers']['column-names'] = BracedSSVList(
            ['name', 'ip', 'port'])
        rows = BracedNLSVList([SCFProperties(), SCFProperties()])
        rows[0]['row'] = BracedSSVList(['DO1', '192.168.114.4', '0'])
        rows[1]['row'] = BracedSSVList(['DO2', '192.168.114.5', '0'])
        cls.comp[-1].props['tables']['data_opt__http_servers']['rows'] = rows

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestAPMPolicyItem(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''apm policy policy-item /Common/APM-1_access_profile_act_localdb_auth {
    agents {
        /Common/APM-1_access_profile_act_localdb_auth_ag {
            type aaa-localdb
        }
    }
    caption "LocalDB Auth"
    color 1
    item-type action
    rules {
        {
            caption Successful
            expression "expr {[mcget {session.localdb.last.result}] == 1}"
            next-item /Common/APM-1_access_profile_act_pool_assign
        }
        {
            caption "Locked User Out"
            expression "expr {[mcget {session.localdb.last.result}] == 2}"
            next-item /Common/APM-1_access_profile_end_deny
        }
        {
            caption fallback
            next-item /Common/APM-1_access_profile_end_deny
        }
    }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'apm'
        cls.comp[-1].objtype = ['policy', 'policy-item']
        cls.comp[-1].objname = '/Common/APM-1_access_profile_act_localdb_auth'
        cls.comp[-1].props['agents'] = SCFProperties()
        cls.comp[-1].props['agents'][
            '/Common/APM-1_access_profile_act_localdb_auth_ag'] = SCFProperties()
        cls.comp[-1].props['agents']['/Common/APM-1_access_profile_act_localdb_auth_ag'][
            'type'] = 'aaa-localdb'
        cls.comp[-1].props['caption'] = '"LocalDB Auth"'
        cls.comp[-1].props['color'] = '1'
        cls.comp[-1].props['item-type'] = 'action'
        cls.comp[-1].props['rules'] = BracedNLSVList()
        cls.comp[-1].props['rules'].append(SCFProperties())
        cls.comp[-1].props['rules'][-1]['caption'] = 'Successful'
        cls.comp[-1].props['rules'][-1][
            'expression'] = '"expr {[mcget {session.localdb.last.result}] == 1}"'
        cls.comp[-1].props['rules'][-1][
            'next-item'] = '/Common/APM-1_access_profile_act_pool_assign'
        cls.comp[-1].props['rules'].append(SCFProperties())
        cls.comp[-1].props['rules'][-1]['caption'] = '"Locked User Out"'
        cls.comp[-1].props['rules'][-1][
            'expression'] = '"expr {[mcget {session.localdb.last.result}] == 2}"'
        cls.comp[-1].props['rules'][-1]['next-item'] = '/Common/APM-1_access_profile_end_deny'
        cls.comp[-1].props['rules'].append(SCFProperties())
        cls.comp[-1].props['rules'][-1]['caption'] = 'fallback'
        cls.comp[-1].props['rules'][-1]['next-item'] = '/Common/APM-1_access_profile_end_deny'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestGTMNastyTopologyName(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = r'''gtm topology  ldns: subnet 163.231.255.0/26  server: datacenter "/Common/Eagan E" {
    order 1
    score 200
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'gtm'
        cls.comp[-1].objtype = ['topology', ' ldns:', 'subnet', '163.231.255.0/26', ' server:',
                                'datacenter']
        cls.comp[-1].objname = '"/Common/Eagan E"'
        cls.comp[-1].props['order'] = '1'
        cls.comp[-1].props['score'] = '200'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestiAppNestedBlobNastyEscape(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = r'''cli script /Common/f5.iapp.1.1.1.cli {
proc iapp_make_safe_password { password } {
    return [string map { \' \\\\\\\' \# \\\\\\\# \\ \\\\\\\\ } $password]
}
proc iapp_get_items { args } {

    # Set default values.
    set error_msg  "iapp_get_items $args:"
    set do_binary  0
    set nocomplain 0
    set items      ""
    set join_char  "\n"
    set recursive  "recursive"
    set com_dir    "/Common"
    set loc_dir    "[tmsh::pwd]"

    # Set up flag-related work.
    array set flags  {
        -exists      { [set do_binary 1] }
        -nocomplain  { [set nocomplain 1] }
        -list        { [set join_char " "] }
        -norecursive { [set recursive ""] }
        -local       { [set com_dir   ""] }
        -dir         { [set loc_dir      [iapp_pull $ptr args]] }
        -filter      { [set filter_field [iapp_pull $ptr args]] \
                       [set filter_op    [iapp_pull $ptr args]] \
                       [set filter_value [iapp_pull $ptr args]] }
    }
    iapp_process_flags flags args
}
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cli'
        cls.comp[-1].objtype = ['script']
        cls.comp[-1].objname = '/Common/f5.iapp.1.1.1.cli'
        cls.comp[-1].props['_blob'] = r'''proc iapp_make_safe_password { password } {
    return [string map { \' \\\\\\\' \# \\\\\\\# \\ \\\\\\\\ } $password]
}
proc iapp_get_items { args } {

    # Set default values.
    set error_msg  "iapp_get_items $args:"
    set do_binary  0
    set nocomplain 0
    set items      ""
    set join_char  "\n"
    set recursive  "recursive"
    set com_dir    "/Common"
    set loc_dir    "[tmsh::pwd]"

    # Set up flag-related work.
    array set flags  {
        -exists      { [set do_binary 1] }
        -nocomplain  { [set nocomplain 1] }
        -list        { [set join_char " "] }
        -norecursive { [set recursive ""] }
        -local       { [set com_dir   ""] }
        -dir         { [set loc_dir      [iapp_pull $ptr args]] }
        -filter      { [set filter_field [iapp_pull $ptr args]] \
                       [set filter_op    [iapp_pull $ptr args]] \
                       [set filter_value [iapp_pull $ptr args]] }
    }
    iapp_process_flags flags args
}
'''

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestGTMRegionNastiness(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = r'''gtm region /Common/APAC_DC_Region {
    region-members {
        datacenter "/Common/Hong Kong" { }
        datacenter /Common/Bangalore { }
        datacenter /Common/Hyderabad { }
        datacenter /Common/Singapore { }
        pool /Common/lms-bng { }
        pool /Common/smtp-apac { }
        pool /Common/syslog-apac { }
        pool /Common/syslog-idx-sng { }
        pool /Common/vcs-apac { }
        pool /Common/vpn-apac { }
        pool /Common/webmail-apac { }
    }
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = True
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'gtm'
        cls.comp[-1].objtype = ['region']
        cls.comp[-1].objname = '/Common/APAC_DC_Region'
        cls.comp[-1].props['region-members'] = NLSVList([
            ['datacenter', '"/Common/Hong Kong"', '{ }'],
            ['datacenter', '/Common/Bangalore', '{ }'],
            ['datacenter', '/Common/Hyderabad', '{ }'],
            ['datacenter', '/Common/Singapore', '{ }'],
            ['pool', '/Common/lms-bng', '{ }'],
            ['pool', '/Common/smtp-apac', '{ }'],
            ['pool', '/Common/syslog-apac', '{ }'],
            ['pool', '/Common/syslog-idx-sng', '{ }'],
            ['pool', '/Common/vcs-apac', '{ }'],
            ['pool', '/Common/vpn-apac', '{ }'],
            ['pool', '/Common/webmail-apac', '{ }'],
        ])

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestGTMServer(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = ('gtm server /Common/BIAP-ERFPPS01 {\n'
                    '    addresses {\n'
                    '        10.43.126.55 {\n'
                    '            device-name BIAP-ERFPPS01\n'
                    '        }\n'
                    '    }\n'
                    '    datacenter /Common/Bangalore\n'
                    '    monitor /Common/tcp \n'
                    '    product generic-host\n'
                    '    virtual-servers {\n'
                    '        10_30_116_143_1234 {\n'
                    '            destination 10.30.116.143:1234\n'
                    '        }\n'
                    '        10_43_126_55_1234 {\n'
                    '            destination 10.43.126.55:1234\n'
                    '        }\n'
                    '    }\n'
                    '}')
        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'gtm'
        cls.comp[-1].objtype = ['server']
        cls.comp[-1].objname = '/Common/BIAP-ERFPPS01'
        cls.comp[-1].props['addresses'] = SCFProperties()
        cls.comp[-1].props['addresses']['10.43.126.55'] = SCFProperties()
        cls.comp[-1].props['addresses']['10.43.126.55']['device-name'] = 'BIAP-ERFPPS01'
        cls.comp[-1].props['datacenter'] = '/Common/Bangalore'
        cls.comp[-1].props['monitor'] = SSVList(['/Common/tcp'])
        cls.comp[-1].props['product'] = 'generic-host'
        cls.comp[-1].props['virtual-servers'] = SCFProperties()
        cls.comp[-1].props['virtual-servers']['10_30_116_143_1234'] = SCFProperties()
        cls.comp[-1].props['virtual-servers']['10_30_116_143_1234'][
            'destination'] = '10.30.116.143:1234'
        cls.comp[-1].props['virtual-servers']['10_43_126_55_1234'] = SCFProperties()
        cls.comp[-1].props['virtual-servers']['10_43_126_55_1234'][
            'destination'] = '10.43.126.55:1234'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestGTMServerMonitorTrailingSpace(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = ('gtm server /Common/C608YZADAS01B {\n'
                    '    addresses {\n'
                    '        10.51.2.89 {\n'
                    '            device-name C608YZADAS01B\n'
                    '        }\n'
                    '    }\n'
                    '    datacenter /Common/HZL\n'
                    '    monitor /Common/tcp \n'
                    '    product generic-host\n'
                    '    virtual-servers {\n'
                    '        10_51_2_89_8140 {\n'
                    '            destination 10.51.2.89:8140\n'
                    '        }\n'
                    '    }\n'
                    '}')
        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'gtm'
        cls.comp[-1].objtype = ['server']
        cls.comp[-1].objname = '/Common/C608YZADAS01B'
        cls.comp[-1].props['addresses'] = SCFProperties()
        cls.comp[-1].props['addresses']['10.51.2.89'] = SCFProperties()
        cls.comp[-1].props['addresses']['10.51.2.89']['device-name'] = 'C608YZADAS01B'
        cls.comp[-1].props['datacenter'] = '/Common/HZL'
        cls.comp[-1].props['monitor'] = SSVList(['/Common/tcp'])
        cls.comp[-1].props['product'] = 'generic-host'
        cls.comp[-1].props['virtual-servers'] = SCFProperties()
        cls.comp[-1].props['virtual-servers']['10_51_2_89_8140'] = SCFProperties()
        cls.comp[-1].props['virtual-servers']['10_51_2_89_8140']['destination'] = '10.51.2.89:8140'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestCMDevice(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cm device /Common/fwlnnp151.ipnw.vodafone.com.au {
    active-modules { "BIG-IP, LAB(LTM,AFM,APM,ASM,AM, DNS, PSM,GTM),VE|ZMTWBDI-UVKQZVM|IPV6 Gateway|Rate Shaping|Ram Cache|50 MBPS COMPRESSION|Client Authentication|External Interface and Network HSM, VE|SDN Services, VE|Routing Bundle, VE|SSL, Forward Proxy, VE|WOM, VE|ASM, VE|PSM, VE|PEM, Quota Management, VE|AFM, VE (LAB ONLY - NO ROUTING)|PEM, VE|DNS Services (LAB)|WBA, VE|SSL, VE|Acceleration Manager, VE|Advanced Protocols, VE|DNSSEC|Anti-Virus Checks|Base Endpoint Security Checks|Firewall Checks|Network Access|Secure Virtual Keyboard|APM, Web Application|Machine Certificate Checks|Protected Workspace|Max Compression, VE|Remote Desktop|App Tunnel|AAM, Upgrade from WAM, (v11.4 & later)|DNS Rate Fallback, Unlimited|DNS Licensed Objects, Unlimited|DNS Rate Limit, Unlimited QPS" "CGN, VE (LAB)|PXDKSXG-SNKNMWS|SSL, VE" "DNSSEC|HZIKNRK-YUWIGOD" "GTM, VE (LAB)|TDDVAIE-BTMVRDT|IPV6 Gateway|Ram Cache|STP|DNS Express|DNSSEC|GTM Licensed Objects, Unlimited|DNS Rate Fallback, Unlimited|DNS Licensed Objects, Unlimited|GTM Rate Fallback, (UNLIMITED)|DNS Rate Limit, Unlimited QPS|GTM Rate, Unlimited" }
    base-mac 00:0c:29:c5:81:5f
    build 1.0.169
    cert /Common/dtdi1.crt
    chassis-id 564dfbca-8224-ac44-946e36c5815f
    configsync-ip 192.168.255.5
    edition "Hotfix HF1"
    hostname fwlnnp151.ipnw.vodafone.com.au
    key /Common/dtdi1.key
    management-ip 172.18.40.187
    marketing-name "BIG-IP Virtual Edition"
    mirror-ip 192.168.255.5
    multicast-interface eth0
    multicast-ip 224.0.0.245
    multicast-port 62960
    optional-modules { "App Mode (TMSH Only, No Root/Bash)" "IPI Subscription, 3Yr, VE" "PEM URL Filtering, Subscription, 3Yr, 200Mbps" "Routing Bundle" "SWG Subscription, 3Yr, VE" "URL Filtering Subscription, 3Yr, VE" }
    platform-id Z100
    product BIG-IP
    self-device true
    time-limited-modules { "IPI Subscription, 1Yr, VE|SELUURY-VEFYEXS|20150317|20150617|SUBSCRIPTION" "SWG Subscription, 1Yr, VE|MIUEJHE-VJMJCHN|20150317|20150502|SUBSCRIPTION" "URL Filtering Subscription, 1Yr, VE|EGQQMDP-IYELXPG|20150317|20150502|SUBSCRIPTION" }
    time-zone EST
    unicast-address {
        {
            effective-ip 192.168.255.5
            effective-port 1026
            ip 192.168.255.5
        }
    }
    version 11.5.2
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cm'
        cls.comp[-1].objtype = ['device']
        cls.comp[-1].objname = '/Common/fwlnnp151.ipnw.vodafone.com.au'
        cls.comp[-1].props['active-modules'] = BracedSSVList([
            '"BIG-IP, LAB(LTM,AFM,APM,ASM,AM, DNS, PSM,GTM),VE|ZMTWBDI-UVKQZVM|IPV6 Gateway|Rate '
            'Shaping|Ram Cache|50 MBPS COMPRESSION|Client Authentication|External Interface and '
            'Network HSM, VE|SDN Services, VE|Routing Bundle, VE|SSL, Forward Proxy, VE|WOM, '
            'VE|ASM, VE|PSM, VE|PEM, Quota Management, VE|AFM, VE (LAB ONLY - NO ROUTING)|PEM, '
            'VE|DNS Services (LAB)|WBA, VE|SSL, VE|Acceleration Manager, VE|Advanced Protocols, '
            'VE|DNSSEC|Anti-Virus Checks|Base Endpoint Security Checks|Firewall Checks|Network '
            'Access|Secure Virtual Keyboard|APM, Web Application|Machine Certificate '
            'Checks|Protected Workspace|Max Compression, VE|Remote Desktop|App Tunnel|AAM, '
            'Upgrade from WAM, (v11.4 & later)|DNS Rate Fallback, Unlimited|DNS Licensed '
            'Objects, Unlimited|DNS Rate Limit, Unlimited QPS"',
            '"CGN, VE (LAB)|PXDKSXG-SNKNMWS|SSL, VE"', '"DNSSEC|HZIKNRK-YUWIGOD"',
            '"GTM, VE (LAB)|TDDVAIE-BTMVRDT|IPV6 Gateway|Ram Cache|STP|DNS Express|DNSSEC|GTM '
            'Licensed Objects, Unlimited|DNS Rate Fallback, Unlimited|DNS Licensed Objects, '
            'Unlimited|GTM Rate Fallback, (UNLIMITED)|DNS Rate Limit, Unlimited QPS|GTM Rate, '
            'Unlimited"'
        ])
        cls.comp[-1].props['base-mac'] = '00:0c:29:c5:81:5f'
        cls.comp[-1].props['build'] = '1.0.169'
        cls.comp[-1].props['cert'] = '/Common/dtdi1.crt'
        cls.comp[-1].props['chassis-id'] = '564dfbca-8224-ac44-946e36c5815f'
        cls.comp[-1].props['configsync-ip'] = '192.168.255.5'
        cls.comp[-1].props['edition'] = '"Hotfix HF1"'
        cls.comp[-1].props['hostname'] = 'fwlnnp151.ipnw.vodafone.com.au'
        cls.comp[-1].props['key'] = '/Common/dtdi1.key'
        cls.comp[-1].props['management-ip'] = '172.18.40.187'
        cls.comp[-1].props['marketing-name'] = '"BIG-IP Virtual Edition"'
        cls.comp[-1].props['mirror-ip'] = '192.168.255.5'
        cls.comp[-1].props['multicast-interface'] = 'eth0'
        cls.comp[-1].props['multicast-ip'] = '224.0.0.245'
        cls.comp[-1].props['multicast-port'] = '62960'
        cls.comp[-1].props['optional-modules'] = BracedSSVList([
            '"App Mode (TMSH Only, No Root/Bash)"', '"IPI Subscription, 3Yr, VE"',
            '"PEM URL Filtering, Subscription, 3Yr, 200Mbps"', '"Routing Bundle"',
            '"SWG Subscription, 3Yr, VE"', '"URL Filtering Subscription, 3Yr, VE"'
        ])
        cls.comp[-1].props['platform-id'] = 'Z100'
        cls.comp[-1].props['product'] = 'BIG-IP'
        cls.comp[-1].props['self-device'] = 'true'
        cls.comp[-1].props['time-limited-modules'] = BracedSSVList([
            '"IPI Subscription, 1Yr, VE|SELUURY-VEFYEXS|20150317|20150617|SUBSCRIPTION"',
            '"SWG Subscription, 1Yr, VE|MIUEJHE-VJMJCHN|20150317|20150502|SUBSCRIPTION"',
            '"URL Filtering Subscription, 1Yr, VE|EGQQMDP-IYELXPG|20150317|20150502|SUBSCRIPTION"'
        ])
        cls.comp[-1].props['time-zone'] = 'EST'
        cls.comp[-1].props['unicast-address'] = BracedNLSVList([SCFProperties(),])
        cls.comp[-1].props['unicast-address'][0]['effective-ip'] = '192.168.255.5'
        cls.comp[-1].props['unicast-address'][0]['effective-port'] = '1026'
        cls.comp[-1].props['unicast-address'][0]['ip'] = '192.168.255.5'
        cls.comp[-1].props['version'] = '11.5.2'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        # the trailing space at 177 will be dropped
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        # the trailing space at 177 will be dropped
        assert (c == str(self.text))


class TestLTMPolicy(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm policy /Common/PAC-Policy {
    requires { http }
    rules {
        PAC-Redirect {
            actions {
                0 {
                    http-host
                    replace
                    value 10.32.0.10
                }
            }
            ordinal 1
        }
    }
    strategy /Common/first-match
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['policy']
        cls.comp[-1].objname = '/Common/PAC-Policy'
        cls.comp[-1].props['requires'] = BracedSSVList(['http'])
        cls.comp[-1].props['rules'] = SCFProperties()
        cls.comp[-1].props['rules']['PAC-Redirect'] = SCFProperties()
        cls.comp[-1].props['rules']['PAC-Redirect']['actions'] = SCFProperties()
        cls.comp[-1].props['rules']['PAC-Redirect']['actions']['0'] = SCFProperties()
        cls.comp[-1].props['rules']['PAC-Redirect']['actions']['0']['http-host'] = Flag()
        cls.comp[-1].props['rules']['PAC-Redirect']['actions']['0']['replace'] = Flag()
        cls.comp[-1].props['rules']['PAC-Redirect']['actions']['0']['value'] = '10.32.0.10'
        cls.comp[-1].props['rules']['PAC-Redirect']['ordinal'] = '1'
        cls.comp[-1].props['strategy'] = '/Common/first-match'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        # the trailing space at 177 will be dropped
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        # the trailing space at 177 will be dropped
        assert (c == str(self.text))


class TestLTMPoolMultiMonitor(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = ('ltm pool /Common/MYVODA-8080-PRD-Pool {\n'
                    '    description "MyVodafone WebCache Prod Pool"\n'
                    '    load-balancing-mode least-connections-member\n'
                    '    members {\n'
                    '        /Common/VAAS015002:8080 {\n'
                    '            address 172.16.33.27\n'
                    '        }\n'
                    '        /Common/VAAS016002:8080 {\n'
                    '            address 172.16.34.27\n'
                    '        }\n'
                    '        /Common/VANS015002:8080 {\n'
                    '            address 172.16.209.25\n'
                    '        }\n'
                    '        /Common/VANS016002:8080 {\n'
                    '            address 172.16.212.25\n'
                    '        }\n'
                    '    }\n'
                    '    monitor /Common/tcp and /Common/http \n'
                    '}')
        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['pool']
        cls.comp[-1].objname = '/Common/MYVODA-8080-PRD-Pool'
        cls.comp[-1].props['description'] = '"MyVodafone WebCache Prod Pool"'
        cls.comp[-1].props['load-balancing-mode'] = 'least-connections-member'
        cls.comp[-1].props['members'] = SCFProperties()
        cls.comp[-1].props['members']['/Common/VAAS015002:8080'] = SCFProperties()
        cls.comp[-1].props['members']['/Common/VAAS015002:8080']['address'] = '172.16.33.27'
        cls.comp[-1].props['members']['/Common/VAAS016002:8080'] = SCFProperties()
        cls.comp[-1].props['members']['/Common/VAAS016002:8080']['address'] = '172.16.34.27'
        cls.comp[-1].props['members']['/Common/VANS015002:8080'] = SCFProperties()
        cls.comp[-1].props['members']['/Common/VANS015002:8080']['address'] = '172.16.209.25'
        cls.comp[-1].props['members']['/Common/VANS016002:8080'] = SCFProperties()
        cls.comp[-1].props['members']['/Common/VANS016002:8080']['address'] = '172.16.212.25'
        cls.comp[-1].props['monitor'] = SSVList(['/Common/tcp', 'and', '/Common/http'])

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        # the trailing space at 177 will be dropped
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        # the trailing space at 177 will be dropped
        assert (c == str(self.text))


class TestUnnamedObjects(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''sys sflow global-settings http { }
sys sflow global-settings vlan { }
sys software update {
    auto-check enabled
    frequency weekly
}
wom deduplication {
    disabled
}
wom endpoint-discovery { }'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = True
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'sys'
        cls.comp[-1].objtype = ['sflow', 'global-settings', 'http']
        cls.comp[-1].objname = None
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'sys'
        cls.comp[-1].objtype = ['sflow', 'global-settings', 'vlan']
        cls.comp[-1].objname = None
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'sys'
        cls.comp[-1].objtype = ['software', 'update']
        cls.comp[-1].objname = None
        cls.comp[-1].props['auto-check'] = 'enabled'
        cls.comp[-1].props['frequency'] = 'weekly'
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'wom'
        cls.comp[-1].objtype = ['deduplication']
        cls.comp[-1].objname = None
        cls.comp[-1].props['disabled'] = Flag()
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'wom'
        cls.comp[-1].objtype = ['endpoint-discovery']
        cls.comp[-1].objname = None

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: %s' % self.text)
            print('o: %s' % str(o))
            print('c: %s' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestNestedBlobNotComment(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cli script /Common/f5.iapp.1.1.3.cli {
#  Initialization proc for all templates.
#  Parameters "start" and "stop" or "end".
proc iapp_upgrade_template { upgrade_var upgrade_trans } {
    upvar $upgrade_var   upgrade_var_arr
    upvar $upgrade_trans upgrade_trans_arr

    # create the new variables from the old
    foreach { var } [array names upgrade_var_arr] {

        # substitute old variable name for abbreviation "##"
        regsub -all {##} $upgrade_var_arr($var) \$$var map_cmd

        # run the mapping command from inside the array
        if { [catch { subst $map_cmd } err] } {
            if { [string first "no such variable" $err] == -1 } {
                puts "ERROR $err"
            }
        }
    }
}
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cli'
        cls.comp[-1].objtype = ['script']
        cls.comp[-1].objname = '/Common/f5.iapp.1.1.3.cli'
        cls.comp[-1].props['_blob'] = '''#  Initialization proc for all templates.
#  Parameters "start" and "stop" or "end".
proc iapp_upgrade_template { upgrade_var upgrade_trans } {
    upvar $upgrade_var   upgrade_var_arr
    upvar $upgrade_trans upgrade_trans_arr

    # create the new variables from the old
    foreach { var } [array names upgrade_var_arr] {

        # substitute old variable name for abbreviation "##"
        regsub -all {##} $upgrade_var_arr($var) \$$var map_cmd

        # run the mapping command from inside the array
        if { [catch { subst $map_cmd } err] } {
            if { [string first "no such variable" $err] == -1 } {
                puts "ERROR $err"
            }
        }
    }
}
'''

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: \'%s\'' % self.text)
            print('o: \'%s\'' % str(o))
            print('c: \'%s\'' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestNestedBlobNastyEscapes(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''cli script /Common/f5.iapp.1.1.3.cli {
proc iapp_make_safe_password { password } {
    return [string map { \' \\\' \" \\\" \{ \\\{ \} \\\} \; \\\; \| \\\| \# \\\# \  \\\  \\ \\\\ } $password]
}
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'cli'
        cls.comp[-1].objtype = ['script']
        cls.comp[-1].objname = '/Common/f5.iapp.1.1.3.cli'
        # cls.comp[-1].props['_blob'] = '\n'.join(cls.text.splitlines()[1:-1])
        cls.comp[-1].props['_blob'] = '''proc iapp_make_safe_password { password } {
    return [string map { \' \\\' \" \\\" \{ \\\{ \} \\\} \; \\\; \| \\\| \# \\\# \  \\\  \\ \\\\ } $password]
}
'''

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: \'%s\'' % self.text)
            print('o: \'%s\'' % str(o))
            print('c: \'%s\'' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestLTMDatagroupInternal(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm data-group internal /Staging/background_class {
    records {
        "/9j/4AAQSkZJRgABAQEAYABgAAD/4QCgRXhpZgAATU0AKgAAAAgACAEaAAUAAAABAAAAbgEbAAUA
        AAABAAAAdgEoAAMAAAABAAIAAAExAAIAAAASAAAAfgMBAAUAAAABAAAAkFEQAAEAAAABAQAAAFER
        AAQAAAABAAAOw1ESAAQAAAABAAAOwwAAAAAAAXbyAAAD6AABdvIAAAPoUGFpbnQuTkVUIHYzLjUu
        MTEAAAGGoAAAsY//2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4R
        DgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQU
        FBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAHMAmwDASIAAhEBAxEB/8QA
        HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQR
        BRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdI
        SUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2
        t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEB
        AQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMi
        MoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpj
        ZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbH
        yMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD8zWlfefmPWpPNbP3j
        UMi/MR71a0+xe/nSNR9TXFJpK7OlK7sjV8P6Y2pXILlhEvJPrXpVrIljaqv3FWsCwhj0y3RF4AHP
        vVPU9eO0qrcV8/W5sVOy2PQjy0o6bmnrGtHBCOa5ua+Z85eqF1fFs4aqYui7AAV20sOoKxzynqai
        yPJJwScVq2duWwSxqhptsXwe1dbp2nfKMdKmrUUVYcYk2nWL/LySa6zTdNZmXB/OotKsPu5FdjpO
        nrlQVzznNeVOrqdMYj9G0s+YuB+dd/ouj5TIGT+tU9D0sFl7DP516Fo+khWUYx71lGo1sOSKmn6K
        0jBiOBXQWujlQSOK3NL0fcRtXaDXRR6KPLztwfaumM9TGSPOtQsTGpAyK5DVYdpJr1nWtN+U/Lj3
        rz3W7P5mwMjFfT4SWiPOqKzOCmyHwePSqVxJ90bseta99b7ZcnkCsu6QE8DBr2oNGBk3shwRk/Wu
        v2heT9319zTjuB//2Q==" { }
    }
    type string
}'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = False
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['data-group', 'internal']
        cls.comp[-1].objname = '/Staging/background_class'
        cls.comp[-1].props['records'] = SCFProperties()
        cls.comp[-1].props['records'][
            '"/9j/4AAQSkZJRgABAQEAYABgAAD/4QCgRXhpZgAATU0AKgAAAAgACAEaAAUAAAABAAAAbgEbAAUA\n' \
            '        AAABAAAAdgEoAAMAAAABAAIAAAExAAIAAAASAAAAfgMBAAUAAAABAAAAkFEQAAEAAAABAQAAAFER\n' \
            '        AAQAAAABAAAOw1ESAAQAAAABAAAOwwAAAAAAAXbyAAAD6AABdvIAAAPoUGFpbnQuTkVUIHYzLjUu\n' \
            '        MTEAAAGGoAAAsY//2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4R\n' \
            '        DgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQU\n' \
            '        FBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAHMAmwDASIAAhEBAxEB/8QA\n' \
            '        HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQR\n' \
            '        BRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdI\n' \
            '        SUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2\n' \
            '        t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEB\n' \
            '        AQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMi\n' \
            '        MoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpj\n' \
            '        ZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbH\n' \
            '        yMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD8zWlfefmPWpPNbP3j\n' \
            '        UMi/MR71a0+xe/nSNR9TXFJpK7OlK7sjV8P6Y2pXILlhEvJPrXpVrIljaqv3FWsCwhj0y3RF4AHP\n' \
            '        vVPU9eO0qrcV8/W5sVOy2PQjy0o6bmnrGtHBCOa5ua+Z85eqF1fFs4aqYui7AAV20sOoKxzynqai\n' \
            '        yPJJwScVq2duWwSxqhptsXwe1dbp2nfKMdKmrUUVYcYk2nWL/LySa6zTdNZmXB/OotKsPu5FdjpO\n' \
            '        nrlQVzznNeVOrqdMYj9G0s+YuB+dd/ouj5TIGT+tU9D0sFl7DP516Fo+khWUYx71lGo1sOSKmn6K\n' \
            '        0jBiOBXQWujlQSOK3NL0fcRtXaDXRR6KPLztwfaumM9TGSPOtQsTGpAyK5DVYdpJr1nWtN+U/Lj3\n' \
            '        rz3W7P5mwMjFfT4SWiPOqKzOCmyHwePSqVxJ90bseta99b7ZcnkCsu6QE8DBr2oNGBk3shwRk/Wu\n' \
            '        v2heT9319zTjuB//2Q=="'] = EmptyValue()
        cls.comp[-1].props['type'] = 'string'

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: \'%s\'' % self.text)
            print('o: \'%s\'' % str(o))
            print('c: \'%s\'' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestLTMRuleCommentedWhen(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm rule /Common/DEECD_BLOCKSYMANTEC {
                                            #when HTTP_REQUEST {
#if { [[string tolower [HTTP::host]] contains "ent-shasta-rrs.symantec.com"] }
#{
#HTTP::close
#}
#}

when HTTP_REQUEST {
    if { [HTTP::host] contains "ent-shasta-rrs.symantec.com"} {
        #log local0. "Closing Symantec connection [IP::client_addr]:[TCP::client_port] -> [
        IP::local_addr]:[TCP::local_port]"
        HTTP::close
    }
}
}
'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = True
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['rule',]
        cls.comp[-1].objname = '/Common/DEECD_BLOCKSYMANTEC'
        cls.comp[-1].props['_blob'] = '''                                            #when
        HTTP_REQUEST {
#if { [[string tolower [HTTP::host]] contains "ent-shasta-rrs.symantec.com"] }
#{
#HTTP::close
#}
#}

when HTTP_REQUEST {
    if { [HTTP::host] contains "ent-shasta-rrs.symantec.com"} {
        #log local0. "Closing Symantec connection [IP::client_addr]:[TCP::client_port] -> [
        IP::local_addr]:[TCP::local_port]"
        HTTP::close
    }
}
'''

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: \'%s\'' % self.text)
            print('o: \'%s\'' % str(o))
            print('c: \'%s\'' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))


class TestLTMRuleCommentedWhen2(TestCase):

    @classmethod
    def setup_class(cls):
        cls.text = '''ltm rule /Common/iRule_campbells_AWS_80_v2.0 {
    when CLIENT_ACCEPTED {
	set IP::addr [getfield [IP::client_addr] "%" 1]
        set retries 0
}

when HTTP_REQUEST {
    if {not[class match [IP::client_addr] equals NETSTART_Allowed_IP]} {
           reject
    }
   	if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> "}

	switch -glob [HTTP::uri] {
		"/convenience/login*" -
		"/convenience/register*" {
    		  if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]>
    		  Redirect to HTTPS " }
  		# pool Pool_AWSUS_hybris_b2b-prd-app_80
              HTTP::redirect https://[getfield [HTTP::host] ":" 1][HTTP::uri]
               # HTTP::respond 302 Location "https://[HTTP::host][HTTP::uri]"

		}
   		"/images/*" -
  		"/_ui/*" -
    		"/favicon.ico*" -
   		"/convenience*" -
   		"/medias/*"  {
                        pool Pool_AWSUS_hybris_b2b-prd-app_80
   			if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -
   			Allowed client <$IP::addr> is now connecting to pool
   			<Pool_AWSUS_hybris_b2b-prd-app_80>" }
   		}
		"/ccc/*"  {
			#HTTP::redirect https://[HTTP::host][HTTP::uri]
                       pool Pool_ccc_landingpage_metwebdev09
			if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -
			Allowed client <$IP::addr> is now connecting to pool <Pool_ccc_landingpage>" }
		}
                "/iga/*" {
		         HTTP::respond 302 Location "https://[HTTP::host][HTTP::uri]"
                }
		default {


                          pool Pool_campbells_125

           		if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -
           		Allowed client <$IP::addr> is now connecting to pool
           		<Pool_AWSUS_hybris_b2b-prd-app_80>" }
   		}

    }
}

#when HTTP_RESPONSE {
# HTTP::header replace X-Frame-Options "SAMEORIGIN"
}
'''

        cls.scf = SCFStateMachine()
        cls.scf.input = cls.text
        cls.scf.debug = True
        cls.scf.run()
        cls.comp = []
        cls.comp.append(SCFObject())
        cls.comp[-1].objmodule = 'ltm'
        cls.comp[-1].objtype = ['rule',]
        cls.comp[-1].objname = '/Common/iRule_campbells_AWS_80_v2.0'
        cls.comp[-1].props['_blob'] = '''    when CLIENT_ACCEPTED {
	set IP::addr [getfield [IP::client_addr] "%" 1]
        set retries 0
}

when HTTP_REQUEST {
    if {not[class match [IP::client_addr] equals NETSTART_Allowed_IP]} {
           reject
    }
   	if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> "}

	switch -glob [HTTP::uri] {
		"/convenience/login*" -
		"/convenience/register*" {
    		  if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]>
    		  Redirect to HTTPS " }
  		# pool Pool_AWSUS_hybris_b2b-prd-app_80
              HTTP::redirect https://[getfield [HTTP::host] ":" 1][HTTP::uri]
               # HTTP::respond 302 Location "https://[HTTP::host][HTTP::uri]"

		}
   		"/images/*" -
  		"/_ui/*" -
    		"/favicon.ico*" -
   		"/convenience*" -
   		"/medias/*"  {
                        pool Pool_AWSUS_hybris_b2b-prd-app_80
   			if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -
   			Allowed client <$IP::addr> is now connecting to pool
   			<Pool_AWSUS_hybris_b2b-prd-app_80>" }
   		}
		"/ccc/*"  {
			#HTTP::redirect https://[HTTP::host][HTTP::uri]
                       pool Pool_ccc_landingpage_metwebdev09
			if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -
			Allowed client <$IP::addr> is now connecting to pool <Pool_ccc_landingpage>" }
		}
                "/iga/*" {
		         HTTP::respond 302 Location "https://[HTTP::host][HTTP::uri]"
                }
		default {


                          pool Pool_campbells_125

           		if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -
           		Allowed client <$IP::addr> is now connecting to pool
           		<Pool_AWSUS_hybris_b2b-prd-app_80>" }
   		}

    }
}

#when HTTP_RESPONSE {
# HTTP::header replace X-Frame-Options "SAMEORIGIN"
'''

    def test_parse_eq_comp(self):
        for (o, c) in zip(self.scf.output, self.comp):
            print('t: \'%s\'' % self.text)
            print('o: \'%s\'' % str(o))
            print('c: \'%s\'' % str(c))
            assert (str(o) == str(c))

    def test_parse_eq_text(self):
        o = '\n'.join([str(_) for _ in self.scf.output])
        assert (o == str(self.text))

    def test_comp_eq_text(self):
        c = '\n'.join([str(_) for _ in self.comp])
        assert (c == str(self.text))
