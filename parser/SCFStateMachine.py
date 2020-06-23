# -*- coding: utf-8 -*-
'''Classes to handle parsing TCL like languages
Pass in a file handle or string to the parser
It will iterate through the file char-at-a-time.
State is held internally to the instance.
'''

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from f5parser.AbstractStateMachine import StateMachineInputError, StateMachineTransitionError
from f5parser.SCFObject import SCFProperties, BracedSSVList, SSVList, BracedNLSVList, NLSVList, \
    PlainString, EmptyValue, Flag
from f5parser.SCFObject import SCFObject
from f5parser.AbstractStateMachine import AbstractStateMachine

__author__ = 'jimd'

# Constants for the SCFStateMachine

SPACE = '\t\v\f\r '
EOL = '\n'
COMMENT = '#'
ESCAPE = '\\'
QUOTE = '"'
OPEN_PAREN = '('
CLOSE_PAREN = ')'
OPEN_BRACK = '['
CLOSE_BRACK = ']'
OPEN_BRACE = '{'
CLOSE_BRACE = '}'
NAME_START = '/'
COLON = ':'
DIGIT = '0123456789'
HEX_DIGIT = '0123456789ABCDEFabcdef'
BLOBTYPES = [('ltm', ['rule']), ('gtm', ['rule']), ('sys', ['application', 'apl-script']),
             ('sys', ['application', 'template']), ('sys', ['icall', 'script']),
             ('cli', ['script'])]
NLSVTYPES = [('gtm', ['region'], 'region-members'), ('ltm', ['virtual'], 'security-log-profiles')]
SSVTYPES = [('gtm', ['server'], 'monitor'),
            ('gtm', ['pool'], 'monitor'),
            ('gtm', ['monitor', 'external'], 'user-defined'),
            ('ltm', ['monitor', 'external'], 'user-defined'),
            ('ltm', ['pool'], 'monitor'),
            ('ltm', ['node'], 'monitor'),
            ('ltm', ['default-node-monitor'], 'rule'),
            ('ltm', ['monitor', 'external'], 'user-defined'),
            ('gtm', ['link'], 'monitor'),]
UNQUOTESTR = [('sys', ['crypto', 'cert'], 'common-name'),
              ('sys', ['crypto', 'cert'], 'expiration'),
              ('sys', ['crypto', 'cert'], 'organization'),
              ('sys', ['crypto', 'cert'], 'ou'),
              ('sys', ['crypto', 'cert'], 'city'),
              ('sys', ['crypto', 'cert'], 'country'),
              ('sys', ['crypto', 'cert'], 'state'),
              ('sys', ['crypto', 'cert'], 'subject-alternative-name'),
              ]
QUOTEDNAME = [('wam', ['policy']),
              ('gtm', ['topology']),
              ('analytics', ['predefined-report']),
              ('security',['log', 'profile']),
              ('security',['dos', 'bot-signature']),
              ('security',['dos', 'bot-signature-category']),
              ]
NONAME = [('cli', ['admin-partitions']),
          ('auth', ['password-policy']),
          ('auth', ['remote-role']),
          ('auth', ['remote-user']),
          ('auth', ['source']),
          ('cli', ['global-settings']),
          ('cli', ['preference']),
          ('net', ['cos global-settings']),
          ('net', ['lldp-globals']),
          ('net', ['packet-filter-trusted']),
          ('ltm', ['default-node-monitor']),
          ('ltm', ['dns', 'analytics', 'global-settings']),
          ('ltm', ['dns', 'cache', 'global-settings']),
          ('net', ['stp-globals']),
          ('sys', ['datastor']),
          ('sys', ['dns']),
          ('sys', ['global-settings']),
          ('sys', ['httpd']),
          ('sys', ['log-rotate']),
          ('sys', ['ntp']),
          ('sys', ['outbound-smtp']),
          ('sys', ['scriptd']),
          ('sys', ['snmp']),
          ('sys', ['sshd']),
          ('sys', ['state-mirroring']),
          ('sys', ['software', 'update']),
          ('wom', ['endpoint-discovery']),]


class SCFStateMachine(AbstractStateMachine):
    """State machine for a char-by-char parser of SCF files

    Attributes:
        debug -- The debug state of the object

        escape -- True if the previous character was an escape

        quoted -- True if the machine is inside a quoted string

        comment -- True if the machine is inside a comment
            Note: comments in Tcl 8.4 process escape characters
            so a comment can have a continuation at the end of a line

        output -- The list of SCFObject() produced from the machine

        dest -- The current stack of destinations
            To aid nesting always operate on dest
            dest will be set on state_newobj_enter to the new SCFObject()
            As properties are worked on they will be appended to the dest
            If a property nests the nest is pushed onto the stack

        nestdepths -- a list for tracking the nest depth inside a
            state. needs to be a stack so it can deal with nesting types.
    """

    __version__ = '0.2.2'

    def __init__(self, source=None, debug=False):
        super().__init__(source=source, start_state='newobj', debug=debug)
        self.escape = False
        self.quoted = False
        self.comment = False
        self.braced = False
        self.nestdepths = []

    def state_start(self):
        """Initalise the output list and current destination stack """
        # self.output = [SCFObject()]
        self.dest = [self.output]

    def state_finish(self):
        # TODO: fix why this ever happens
        if self.output[-1].objmodule == '':
            # get rid of the excess empty object
            self.output.pop()

    def state_newobj_enter(self, old_state, new_state):
        if self.debug:
            try:
                print('%s parsed' % self.dest[-1].objname)
            except IndexError:
                print('No object in destination list')
            except AttributeError:
                print('Last object has no objname attribute')
        if self.depth > 0:
            raise StateMachineInputError('Depth is non-zero %d %r' % (self.depth, self.dest),
                                         self.pos)
        self.output.append(SCFObject())
        self.dest.append(self.output[-1])
        if self.debug:
            print('=' * 80)

    def state_newobj(self, c, pos):
        if self.escape:
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                self.escape = True
            if c in QUOTE:
                self.quoted = False
            self.accumulate(c)
        elif c in EOL:
            if not self.escape:
                self.comment = False
            self.accumulate(c)
        elif self.comment:
            if c in ESCAPE:
                self.escape = True
            self.accumulate(c)
        elif c in ESCAPE:
            self.escape = True
            self.accumulate(c)
        elif c in QUOTE:
            self.quoted = True
            self.accumulate(c)
        elif c in COMMENT:
            # # TMSH-VERSION: 11.6.0
            # ^
            self.comment = True
        elif c in SPACE:
            pass
        else:
            self.accum = c
            self.transition('objmodule', clear_accum=False)
            return

    def state_objmodule(self, c, pos):
        if c in SPACE:
            self.dest[-1].objmodule = self.accum
            self.transition('objtype')
        else:
            self.accumulate(c)

    def state_objtype_leave(self, old_state, new_state):
        if new_state not in ['objname']:
            if (self.output[-1].objmodule, self.output[-1].objtype) not in NONAME and \
                            len(self.output[-1].objtype) > 1:
                self.output[-1].objname = self.output[-1].objtype.pop()
            self.dest.append(self.dest[-1].props)

    def state_objtype(self, c, pos):
        if self.quoted:
            if (self.dest[-1].objmodule, self.dest[-1].objtype) in QUOTEDNAME:
                self.accumulate(c)
                self.transition('objname', clear_accum=False)
            else:
                raise StateMachineInputError("quoted type ('%s',%s)" % (self.dest[-1].objmodule, self.dest[-1].objtype), pos)
        elif c in NAME_START:
            if self.accum == '':
                self.accumulate(c)
                self.transition('objname', clear_accum=False)
            else:
                self.accumulate(c)
        elif c in SPACE:
            if self.accum != '':
                if COLON in self.accum:
                    # TODO: find a neater way to prepend the space when we need
                    self.accum = ' %s' % self.accum
                self.dest[-1].objtype.append(self.accum)
                self.accum = ''
        elif c in QUOTE:
            self.accumulate(c)
            self.quoted = True
        elif c in OPEN_BRACE:
            if (self.dest[-1].objmodule, self.dest[-1].objtype[:-1]) in BLOBTYPES:
                self.transition('nestedblob')
            else:
                self.transition('propsstart')
        elif c in EOL:
            self.dest[-1].objtype.append(self.accum)
            self.transition('newobj')
        else:
            self.accumulate(c)

    def state_objname_leave(self, old_state, new_state):
        self.dest.append(self.dest[-1].props)

    def state_objname(self, c, pos):
        if self.escape:
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                self.escape = True
            if c in QUOTE:
                # gtm topology "/Common/Eagan E" {
                # -----------------------------^
                self.quoted = False
            self.accumulate(c)
        elif c in ESCAPE:
            self.escape = True
            self.accumulate(c)
        elif c in QUOTE:
            # gtm topology "/Common/Eagan E" {
            # -------------^
            self.quoted = True
            self.accumulate(c)
        elif c in SPACE:
            if self.accum != '':
                self.dest[-1].objname = self.accum
                self.accum = ''
        elif c in OPEN_BRACE:
            if (self.dest[-1].objmodule, self.dest[-1].objtype) in BLOBTYPES:
                self.transition('nestedblob')
            else:
                self.transition('propsstart')
        else:
            # gtm topology  ldns: subnet 163.231.255.0/26  server: datacenter "/Common/Eagan E" {
            self.accumulate(c)

            #    def state_propsstart_enter(self, old_state, new_state):
            #        self.dest[-1] = SCFProperties()

    def state_propsstart(self, c, pos):
        if self.escape:
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                self.escape = True
            if c in QUOTE:
                self.quoted = False
            self.accumulate(c)
        elif c in ESCAPE:
            self.escape = True
            self.accumulate(c)
        elif c in SPACE and self.accum != '':
            # single character property name on entry
            self.dest.append(self.accum)
            self.transition('valtypeguess')
        elif c in SPACE + EOL:
            # eat whitespace
            pass
        elif c in CLOSE_BRACE:
            # mod type /Common/name { }
            # ------------------------^
            # this property set is done
            self.transition('propsfinish')
        elif self.quoted and c in QUOTE:
            raise StateMachineInputError('Property name was just an empty double quote', pos)
        elif self.accum == '' and c in QUOTE:
            self.quoted = True
            self.accumulate(c)
        elif not self.quoted and c in QUOTE:
            raise StateMachineInputError('Property name has a quote in the middle', pos)
        else:
            # first property
            self.accumulate(c)
            self.transition('propname', clear_accum=False)

    def state_propnext_enter(self, old_state, new_state):
        if old_state not in ['propname']:
            # flags won't have appended to the destination list
            self.dest.pop()

    def state_propnext(self, c, pos):
        if c in SPACE + EOL:
            # eat whitespace
            pass
        elif c in CLOSE_BRACE:
            # mod type /Common/name {
            #     item1 val1
            # }
            # ^
            # or
            # mod type /Common/name {
            #     braced {
            #         nest1 val1
            #     }
            # ----^
            self.transition('propsfinish')
        else:
            self.accumulate(c)
            self.transition('propname', clear_accum=False)

    def state_propsfinish(self, c, pos):
        if c in EOL:
            self.dest.pop()
            if isinstance(self.dest[-1], SCFObject):
                self.dest.pop()
                self.transition('newobj')
            elif isinstance(self.dest[-1], BracedNLSVList):
                self.transition('valbracednlsvnext')
            else:
                self.dest.pop()
                self.transition('propsstart')
        else:
            raise StateMachineInputError('invalid char \'%s\' at propsfinish' % c, pos)

    def state_propname_enter(self, old_state, new_state):
        if self.accum.startswith(QUOTE):
            self.quoted = True

    def state_propname(self, c, pos):
        if self.escape:
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                self.escape = True
            if c in QUOTE:
                self.quoted = False
            self.accumulate(c)
        elif c in ESCAPE:
            self.escape = True
            self.accumulate(c)
        elif c in EOL:
            # mod type /Common/Name {
            #     flag1
            # ---------^
            if self.accum != '':
                self.dest[-1][self.accum] = Flag()
                self.transition('propnext')
        elif c in QUOTE:
            self.quoted = True
            self.accumulate(c)
        elif c in CLOSE_BRACE:
            raise StateMachineInputError('Close brace in propname', pos)
        elif not self.quoted and c in SPACE:
            self.dest.append(self.accum)
            self.transition('valtypeguess')
        else:
            self.accumulate(c)

    def state_valtypeguess(self, c, pos):
        """Guess the type for this object"""
        if (self.output[-1].objmodule, self.output[-1].objtype, self.dest[-1]) in SSVTYPES:
            self.dest[-2][self.dest[-1]] = SSVList()
            self.dest.append(self.dest[-2][self.dest[-1]])
            self.accumulate(c)
            self.transition('valssv', clear_accum=False)
        elif c in OPEN_BRACE:
            # we have an SSV, NLSV or Empty Object
            self.transition('typelist')
        elif c in EOL:
            raise StateMachineInputError('EOL when attempting to guess type', pos)
        elif c in QUOTE:
            self.quoted = True
            self.accumulate(c)
            self.transition('valplain', clear_accum=False)
        else:
            self.accumulate(c)
            self.transition('valplain', clear_accum=False)

    def state_typelist(self, c, pos):
        if (self.output[-1].objmodule, self.output[-1].objtype, self.dest[-1]) in NLSVTYPES:
            self.dest[-2][self.dest[-1]] = NLSVList()
            self.dest.append(self.dest[-2][self.dest[-1]])
            self.transition('valnlsv')
        elif c in SPACE:
            # mod type /Common/Name {
            #     ssvitem { item1 item2 }
            # -------------^
            self.transition('typessv_or_empty')
        elif c in EOL:
            # tables {
            # --------^
            #     data_opt__http_bypass_apn { }
            #     data_opt__http_servers {
            # ----------------------------^
            #         column-names { name ip port }
            #         rows {
            # --------------^
            #             {
            #                 row { DO1 192.168.114.4 0 }
            #             }
            self.transition('typebracednlsv_or_props')
        else:
            raise StateMachineInputError('Unexpected char \'%s\' when guessing list type' % c, pos)

    def state_typebracednlsv_or_props(self, c, pos):
        """Guess the type for this object"""
        if c in SPACE:
            # just eat spaces until we hit a useful char
            pass
        elif c in OPEN_BRACE:
            # we're in an NLSV
            #     {
            # ----^
            #         row { DO1 192.168.114.4 0 }
            #     }
            #     {
            # ----^
            #         row { DO2 192.168.114.5 0 }
            #     }
            self.dest[-2][self.dest[-1]] = BracedNLSVList()
            self.dest.append(self.dest[-2][self.dest[-1]])
            self.transition('valbracednlsv')
        elif c in CLOSE_BRACE:
            # empty property
            #
            self.dest[-2][self.dest[-1]] = SCFProperties()
            self.transition('propnext', clear_accum=False)
        else:
            # apm policy access-policy /Common/APM-1_access_profile {
            #     default-ending /Common/APM-1_access_profile_end_deny
            #     items {
            #         /Common/APM-1_access_profile_act_localdb_auth { }
            # --------^
            #         /Common/APM-1_access_profile_act_logon_page { }
            #     }
            if c in QUOTE:
                self.quoted = True
            elif c in ESCAPE:
                self.escape = True
            self.dest[-2][self.dest[-1]] = SCFProperties()
            self.dest.append(self.dest[-2][self.dest[-1]])
            self.accumulate(c)
            self.transition('propsstart', clear_accum=False)

    def state_typessv_or_empty(self, c, pos):
        if c in CLOSE_BRACE:
            self.dest[-2][self.dest[-1]] = EmptyValue()
            if isinstance(self.dest[-2], SCFObject):
                # mod type /Common/Name { }
                # ------------------------^
                self.transition('newobj')
            else:
                # mod type /Common/Name {
                #     prop { }
                # -----------^
                self.transition('propnext')
        else:
            if c in QUOTE:
                self.quoted = True
            elif c in ESCAPE:
                self.escape = True
            # mod type /Common/Name {
            #     prop { thing "other thing" }
            # -----------^
            self.dest[-2][self.dest[-1]] = BracedSSVList()
            self.dest.append(self.dest[-2][self.dest[-1]])
            self.accumulate(c)
            self.transition('valbracedssv', clear_accum=False)

    def state_valplain_enter(self, old_state, new_state):
        if self.accum in QUOTE:
            # expression "expr {[mcget {session.localdb.last.result}] == 1}"
            # -----------^
            self.quoted = True
        if self.accum in ESCAPE:
            # expression \nescape
            # -----------^
            self.escape = True

    def state_valplain_leave(self, old_state, new_state):
        if self.escape:
            raise StateMachineInputError('Left valplain still escaping', self.pos)
        if self.quoted:
            raise StateMachineInputError('Left valplain inside quotes', self.pos)
        try:
            self.dest[-2][self.dest[-1]] = PlainString(self.accum)
        except IndexError as e:
            if self.debug:
                print('Unable to update destination %s' % e)
            pass

    def state_valplain(self, c, pos):
        if self.escape:
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                self.escape = True
            if c in QUOTE:
                self.quoted = False
            self.accumulate(c)
        elif c in SPACE:
            if not (self.output[-1].objmodule, self.output[-1].objtype,
                    self.dest[-1]) in UNQUOTESTR:
                raise StateMachineInputError('Space in plain value (\'%s\', %s, \'%s\'),' %
                                             (self.output[-1].objmodule, self.output[-1].objtype,
                                              self.dest[-1]), pos)
            else:
                self.accumulate(c)
        elif c in EOL:
            if self.accum == '':
                # ltm thing /C/Blah {
                #     flag
                # --------^
                # }
                self.accum = Flag()
            self.transition('propnext')
        elif c in ESCAPE:
            # ltm thing /C/Blah {
            #     eprop escape\n
            # ----------------^
            # }
            self.escape = True
            self.accumulate(c)
        elif c in QUOTE:
            self.quoted = True
            self.accumulate(c)
        else:
            self.accumulate(c)

    def state_valssv_enter(self, old_state, new_state):
        if self.accum in QUOTE:
            # expression "expr {[mcget {session.localdb.last.result}] == 1}"
            # -----------^
            self.quoted = True
        if self.accum in ESCAPE:
            # expression \nescape
            # -----------^
            self.escape = True

    def state_valssv_leave(self, old_state, new_state):
        if self.escape:
            raise StateMachineInputError('Left valssv still escaping', self.pos)
        if self.quoted:
            raise StateMachineInputError('Left valssv inside quotes', self.pos)
        if self.accum != '':
            self.dest[-1].append(self.accum)
            self.accum = ''
        self.dest.pop()

    def state_valssv(self, c, pos):
        if self.escape:
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                self.escape = True
            if c in QUOTE:
                self.quoted = False
            self.accumulate(c)
        elif c in SPACE:
            # ltm thing /C/Blah {
            #     monitor /Common/tcp and /Common/http
            # -----------------------^
            # }
            if self.accum != '':
                self.dest[-1].append(self.accum)
                self.accum = ''
        elif c in EOL:
            # ltm thing /C/Blah {
            #     monitor /Common/tcp and /Common/http
            # ----------------------------------------^
            # }
            self.transition('propnext')
        elif c in ESCAPE:
            # ltm thing /C/Blah {
            #     eprop escape\n
            # ----------------^
            # }
            self.escape = True
            self.accumulate(c)
        elif c in QUOTE:
            self.quoted = True
            self.accumulate(c)
        else:
            self.accumulate(c)

    def state_valbracedssv_leave(self, old_state, new_state):
        self.dest.pop()

    def state_valbracedssv(self, c, pos):
        if self.escape:
            # { thing escape\n other }
            # ---------------^
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                # { thing "quoted \" quote" other }
                # ----------------^
                self.escape = True
            if c in QUOTE:
                # { thing "quoted thing" other }
                # ---------------------^
                self.quoted = False
            self.accumulate(c)
        elif c in SPACE:
            # { thing escape\n other }
            # -------^
            self.dest[-1].append(self.accum)
            self.accum = ''
        elif c in CLOSE_BRACE:
            # { thing escape\n other }
            # -----------------------^
            self.transition('propnext')
        elif c in ESCAPE:
            # { thing escape\n other }
            # --------------^
            self.escape = True
            self.accumulate(c)
        elif c in QUOTE:
            # { thing "quoted thing" other }
            # --------^
            self.quoted = True
            self.accumulate(c)
        elif c in EOL:
            raise StateMachineInputError('EOL inside SSV', pos)
        else:
            self.accumulate(c)

    def state_valnlsv_enter(self, old_state, new_state):
        self.dest[-1].append([])

    def state_valnlsv_leave(self, old_state, new_state):
        # pop the extra empty list off the tail
        self.dest[-1].pop()
        self.dest.pop()

    def state_valnlsv(self, c, pos):
        if self.escape:
            # sub\tnet 192.165.214.96/28 { thing\}other }
            # ----^
            self.accumulate(c)
            self.escape = False
        elif self.quoted:
            if c in ESCAPE:
                # "subnet \" quoted" 192.165.214.96/28 { thing\}other }
                # --------^
                self.escape = True
            if c in QUOTE:
                # "subnet \" quoted" 192.165.214.96/28 { thing\}other }
                # -----------------^
                self.quoted = False
            self.accumulate(c)
        elif self.braced:
            #         subnet 192.165.214.96/28 { }
            # ----------------------------------^
            if c in ESCAPE:
                #         subnet 192.165.214.96/28 { thing\}other }
                # ----------------------------------------^
                self.escape = True
            if c in CLOSE_BRACE:
                #         subnet 192.165.214.96/28 { thing\}other }
                # ------------------------------------------------^
                self.braced = False
            self.accumulate(c)
        elif c in SPACE:
            # gtm region /Common/APAC_IP_OVERRIDE {
            #     region-members {
            #         subnet 192.165.214.96/28 { }
            # --------------^
            #         subnet 192.165.215.96/28 { }
            # --------------------------------^
            #     }
            # }
            if self.accum != '':
                self.dest[-1][-1].append(self.accum)
                self.accum = ''
        elif c in EOL:
            # gtm region /Common/APAC_IP_OVERRIDE {
            #     region-members {
            #         subnet 192.165.214.96/28 { }
            # ------------------------------------^
            #         subnet 192.165.215.96/28 { }
            #     }
            # }
            self.dest[-1][-1].append(self.accum)
            self.dest[-1].append([])
            self.accum = ''
        elif c in OPEN_BRACE:
            # gtm region /Common/APAC_IP_OVERRIDE {
            #     region-members {
            #         subnet 192.165.214.96/28 { }
            # ---------------------------------^
            #         subnet 192.165.215.96/28 { }
            #     }
            # }
            self.braced = True
            self.accumulate(c)
        elif c in CLOSE_BRACE:
            # gtm region /Common/APAC_IP_OVERRIDE {
            #     region-members {
            #         subnet 192.165.214.96/28 { }
            # ---------------------------------^
            #         subnet 192.165.215.96/28 { }
            #     }
            # ----^
            # }
            self.transition('propnext')
        elif c in ESCAPE:
            # sub\tnet 192.165.214.96/28 { thing\}other }
            # ---^
            self.escape = True
            self.accumulate(c)
        elif c in QUOTE:
            # "subnet \" quoted" 192.165.214.96/28 { thing\}other }
            # ^
            self.quoted = True
            self.accumulate(c)
        else:
            self.accumulate(c)

    def state_valbracednlsv(self, c, pos):
        if c in SPACE:
            # eat whitespace
            pass
        elif c in EOL:
            #     {
            # -----^
            #         row { DO1 192.168.114.4 0 }
            #     }
            #     {
            # -----^
            #         row { DO2 192.168.114.5 0 }
            #     }
            self.dest[-1].append(SCFProperties())
            self.dest.append(self.dest[-1][-1])
            self.transition('propsstart')
        elif c in CLOSE_BRACE:
            #     {
            #         row { DO1 192.168.114.4 0 }
            #     }
            # ----^
            self.transition('valbracednlsvnext')
        else:
            raise StateMachineInputError('Unexpected char \'%s\' in nlsvstart' % c, pos)

    def state_valbracednlsvnext(self, c, pos):
        if c in SPACE + EOL:
            # eat whitespace
            pass
        elif c in CLOSE_BRACE:
            #     {
            #         row { DO1 192.168.114.4 0 }
            #     }
            # }
            # ^
            self.dest.pop()
            self.transition('propnext')
        elif c in OPEN_BRACE:
            #     {
            # ----^
            #         row { DO1 192.168.114.4 0 }
            #     }
            self.dest[-1].append(SCFProperties())
            self.dest.append(self.dest[-1][-1])
            self.transition('propsstart')
        else:
            raise StateMachineInputError('Unexpected char \'%s\' in nlsvnext' % c, pos)

    def state_nestedblob_enter(self, old_state, new_state):
        self.nestdepths.append(0)

    def state_nestedblob_leave(self, old_state, new_state):
        # strip off the initial \n
        try:
            self.dest[-1]['_blob'] = self.accum[1:]
        except Exception as e:
            raise e
        self.dest.pop()
        self.dest.pop()
        self.nestdepths.pop()
        if self.escape:
            raise StateMachineInputError('Left nestedblob still escaping', self.pos)
        if self.quoted:
            raise StateMachineInputError('Left nestedblob inside quotes', self.pos)
        if self.comment:
            raise StateMachineInputError('Left nestedblob still escaping', self.pos)

    def state_nestedblob(self, c, pos):
        if self.debug:
            print('pos %d nestdepth %d escape %s comment %s quote %s line '
                  '\'%s\'' % (self.pos, self.nestdepths[-1], self.escape, self.comment, self.quoted,
                              self.lines[-1]))
        if self.escape:
            if self.debug:
                print('escape')
            self.accumulate(c)
            self.escape = False
        # elif self.quoted:
        #     if c in ESCAPE:
        #         if self.debug:
        #             print('escape')
        #         self.escape = True
        #     if c in QUOTE:
        #         if self.debug:
        #             print('endquote')
        #         self.quoted = False
        #     self.accumulate(c)
        elif c in EOL:
            if self.debug:
                print('eol')
            if not self.escape:
                self.comment = False
            self.accumulate(c)
        elif self.comment:
            if self.debug:
                print('comment')
            if c in ESCAPE:
                self.escape = True
                if self.debug:
                    print('escape')
            self.accumulate(c)
        elif c in ESCAPE:
            if self.debug:
                print('escape')
            self.escape = True
            self.accumulate(c)
        elif c in OPEN_BRACE:
            if self.debug:
                print('openbrace %d' % self.nestdepths[-1])
            self.nestdepths[-1] += 1
            self.accumulate(c)
        elif c in CLOSE_BRACE:
            if self.debug:
                print('closebrace %d' % self.nestdepths[-1])
            if self.nestdepths[-1] == 0:
                if self.debug:
                    print('closebrace done %d' % self.nestdepths[-1])
                self.transition('newobj')
                return
            self.nestdepths[-1] -= 1
            self.accumulate(c)
        # elif c in QUOTE:
        #     if self.debug:
        #         print('start quote')
        #     self.quoted = True
        #     self.accumulate(c)
        elif c in COMMENT and (self.accum.isspace() or self.accum.strip(' \t').endswith(';')):
            if self.debug:
                print('start comment')
            # self.comment = True
            self.accumulate(c)
        else:
            self.accumulate(c)

    def state_transition(self, old_state, new_state):
        if not self.debug:
            return
        print('----\ntransition %s -> %s' % (old_state, new_state))
        print('pos %6d dep %4d sym \'%s\' accum \'%s\'' %
              (self.pos, self.depth, self.symbol, self.accum))
        for (i, d) in enumerate(self.dest):
            print('%d %s+---%s (%s)' % (i, ' ' * (i * 4), type(d), str(d)))
        print('----')
