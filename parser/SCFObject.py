# -*- coding: utf-8 -*-

from collections import OrderedDict, UserString, UserList
from functools import total_ordering

__author__ = 'jimd'
__version__ = '0.5.0'

from fnmatch import fnmatch


class SCFValue:
    def __init__(self, *args, **kwargs):
        self._tabstop = 4
        self.data = None
        super().__init__(*args, **kwargs)

    def _tostr(self, tab=0, order=None):
        return '%s%s' % (' ' * tab, str(self))

    def __eq__(self, other):
        '''Override the default Equals behavior'''
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        '''Define a non-equality test'''
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        '''Override the default hash behavior (that returns the id or the object)'''
        return hash(tuple(sorted(self.__dict__.items())))

    def _as_base_type(self):
        return str(self)

    def as_tmsh(self, mode='replace-all-with', order=None):
        return self._tostr(tab=0)


class EmptyValue(SCFValue):
    def __init__(self, value=None):
        super().__init__()

    def _tostr(self, tab=0, order=None):
        return '%s%s' % (' ' * tab, str(self))

    def __str__(self):
        return '{ }'

    def as_tmsh(self, mode='replace-all-with', order=None):
        return self._tostr(tab=0)


class Flag(SCFValue):
    def __init__(self, value=True):
        super().__init__()
        self.data = value

    def _tostr(self, tab=0, order=None):
        if self.data:
            return '%s%s' % (' ' * tab, str(self))

    def __str__(self):
        return ''

    def _as_base_type(self):
        return self.data

    def as_tmsh(self, mode='replace-all-with', order=None):
        return self._tostr(tab=0)


class PlainString(SCFValue, UserString):
    '''Used for type hinting in output, the string will be stored without
        quotes. This object is mutable.
    '''

    def __init__(self, value, *args, **kwargs):
        super().__init__(str(value), *args, **kwargs)

    def _tostr(self, tab=0, order=None):
        return '%s%s' % (' ' * tab, str(self))

    def __str__(self):
        return self.data

    def __rmod__(self, format):
        '''Work around bug 25652 in Python 3.5
        '''
        return self.__class__(format % self.__str__)

    def _as_base_type(self):
        return self.data

    def as_tmsh(self, mode='replace-all-with', order=None):
        return self._tostr(tab=0)


class DblQuotedString(SCFValue, UserString):
    '''Used for type hinting in output, the string will be stored without
        quotes. This object is mutable.
    '''

    def __init__(self, value='', strip_quotes=True):
        if strip_quotes:
            super().__init__(str(value).strip('"'))
        else:
            super().__init__(str(value))

    def _tostr(self, tab=0, order=None):
        return '%s%s' % (' ' * tab, str(self))

    def __str__(self):
        '''Represent the contained string wrapped in double quotes'''
        return '"%s"' % self.data

    def __rmod__(self, format):
        '''Work around bug 25652 in Python 3.5
        '''
        return self.__class__(format % self.__str__)

    def _as_base_type(self):
        return str(self.data)

    def as_tmsh(self, mode='replace-all-with', order=None):
        return self._tostr(tab=0)


class BracedSSVList(SCFValue, UserList):
    '''Used for type hinting in output, the list will be stored without
        braces and be space separated.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _tostr(self, tab=0, order=None):
        r = '{ '
        for m in self.data if not order else order(self.data):
            if isinstance(m, SCFValue):
                r += '%s ' % m._tostr(0)
            elif isinstance(m, SCFObject):
                r += '%s ' % m.objname
            else:
                r += '%s ' % m
        r += '}'
        return r

    def __str__(self):
        '''Represent the list as a set of space separated values in braces.'''
        return self._tostr(0)

    def _as_base_type(self):
        return [v._as_base_type() if isinstance(v, SCFValue) else v for v in self.data]

    def as_tmsh(self, mode='replace-all-with', order=None):
        return self._tostr(tab=0)


class SSVList(SCFValue, UserList):
    '''Used for type hinting in output, the list will be stored without
        braces and be space separated.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _tostr(self, tab=0, order=None):
        r = ''
        if not order:
            k = self.data
        else:
            k = order(self.data)
        for m in k:
            if isinstance(m, SCFProperties):
                r += '%s ' % m._tostr(0)[1:]
            elif isinstance(m, SCFValue):
                r += '%s ' % m._tostr(0)
            elif isinstance(m, SCFObject):
                r += '%s ' % m.objname
            else:
                r += '%s ' % m
        return r

    def __str__(self):
        '''Represent the list as a set of space separated values in braces.'''
        return self._tostr(0)

    def _as_base_type(self):
        return [v._as_base_type() if isinstance(v, SCFValue) else v for v in self.data]

    def as_tmsh(self, mode='replace-all-with', order=None):
        return self._tostr(tab=0)


class BracedNLSVList(SCFValue, UserList):
    '''Used for type hinting in output, the list will be stored without
        braces and be space separated.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _tostr(self, tab=0, order=None):
        r = ''
        for m in self.data if not order else order(self.data):
            r += '%s{\n' % (' ' * tab)
            if isinstance(m, SCFProperties):
                r += '%s' % m._tostr(order=order, tab=tab + self._tabstop)[1:]
            elif isinstance(m, SCFValue):
                r += '%s\n' % m._tostr(order=order, tab=tab + self._tabstop)
            elif isinstance(m, SCFObject):
                r += '%s%s\n' % (' ' * (tab + self._tabstop), m.objname)
            else:
                r += '%s%s\n' % (' ' * (tab + self._tabstop), str(m))
            r += '%s}\n' % (' ' * tab)
        # remember to trim off the final \n for consistency
        return r[:-1]

    def __str__(self):
        '''Represent the list as a set of space separated values in braces.'''
        return self._tostr(0)

    def _as_base_type(self):
        return [v._as_base_type() if isinstance(v, SCFValue) else v for v in self.data]

    def as_tmsh(self, mode='replace-all-with', order=None):
        r = ''
        for m in self.data if not order else order(self.data):
            r += '{ '
            if isinstance(m, SCFProperties):
                r += '%s ' % m._tostr(order=order)[1:]
            elif isinstance(m, SCFValue):
                r += '%s ' % m._tostr(order=order)
            elif isinstance(m, SCFObject):
                r += '%s ' % (m.objname)
            else:
                r += '%s ' % (str(m))
            r += '} '
        # remember to trim off the final \n for consistency
        return r[:-1]


class NLSVList(SCFValue, UserList):
    '''Used for type hinting in output, the list will be stored without
        braces and be space separated.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _tostr(self, tab=0, order=None):
        r = ''
        for m in self.data if not order else order(self.data):
            if isinstance(m, SCFProperties):
                r += '%s\n' % (m._tostr(order=order, tab=tab)[1:-1])
            elif isinstance(m, list):
                r += '%s%s\n' % ((' ' * tab, ' '.join(m)))
            elif isinstance(m, SCFValue):
                r += '%s' % m._tostr(order=order, tab=tab)
            elif isinstance(m, SCFObject):
                r += '%s%s\n' % (' ' * tab, m.objname)
            else:
                r += '%s%s\n' % (' ' * tab, str(m))
        # remember to trim off the final \n for consistency
        return r[0:-1]

    def __str__(self):
        '''Represent the list as a set of space separated values in braces.'''
        return self._tostr(0)

    def _as_base_type(self):
        return [v._as_base_type() if isinstance(v, SCFValue) else v for v in self.data]

    def as_tmsh(self, mode='replace-all-with', order=None):
        r = ''
        for m in self.data if not order else order(self.data):
            if isinstance(m, SCFProperties):
                r += '%s ' % (m._tostr(order=order, tab=tab)[1:-1])
            elif isinstance(m, list):
                r += '%s%s ' % ((' ' * tab, ' '.join(m)))
            elif isinstance(m, SCFValue):
                r += '%s' % m._tostr(order=order, tab=tab)
            elif isinstance(m, SCFObject):
                r += '%s%s ' % (' ' * tab, m.objname)
            else:
                r += '%s%s ' % (' ' * tab, str(m))
        # remember to trim off the final \n for consistency
        return r[0:-1]


@total_ordering
class SCFProperties(SCFValue, OrderedDict):
    '''A wrapper for SCF Properties stored in an OrderedDict'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _tostr(self, tab=0, order=None):
        if len(self) == 0:
            return ' '
        r = '\n'
        # tab in one depth
        for k in self.keys() if not order else order(self.keys()):
            if str(k).startswith('_!'):
                # internal object properties are prefixed with '_!'
                continue
            elif isinstance(self[k], SCFProperties):
                r += '%s%s {%s%s}\n' % (' ' * tab, k, self[k]._tostr(order=order,
                                                                     tab=tab + self._tabstop),
                                        ' ' * tab)
            elif isinstance(self[k], BracedNLSVList):
                r += '%s%s {\n%s\n%s}\n' % (' ' * tab, k, self[k]._tostr(order=order,
                                                                         tab=tab + self._tabstop),
                                            ' ' * tab)
            elif isinstance(self[k], NLSVList):
                r += '%s%s {\n%s\n%s}\n' % (' ' * tab, k, self[k]._tostr(order=order,
                                                                         tab=tab + self._tabstop),
                                            ' ' * tab)
            elif isinstance(self[k], Flag):
                if self[k].data:
                    r += '%s%s\n' % (' ' * tab, k)
            elif k == '_blob':
                r += '%s' % self[k]
            elif isinstance(self[k], SCFObject):
                r += '%s%s %s\n' % (' ' * tab, k, self[k].objname)
            elif isinstance(self[k], SCFValue):
                r += '%s%s %s\n' % (' ' * tab, k, self[k]._tostr(order=order, tab=0))
            else:
                r += '%s%s %s\n' % (' ' * tab, k, str(self[k]))
        return r

    def __str__(self):
        return self._tostr(0)

    def __lt__(self, other):
        # for sorting, treat the dictionary length as the key
        if not isinstance(other, SCFProperties):
            return False
        return (len(self) < len(other))

    def __eq__(self, other):
        if not isinstance(other, dict):
            return False
        if self.keys() != other.keys(): return False
        for key in self.keys():
            if self[key] != other[key]: return False
        return True

    def _as_base_type(self):
        return {k: self[k]._as_base_type() if isinstance(v, SCFValue) else v
                for k, v in self.items()}

    def as_tmsh(self, mode='replace-all-with', order=None):
        r = '%s { ' % mode
        for k in self.keys() if not order else order(self.keys()):
            if str(k).startswith('_!'):
                # internal object properties are prefixed with '_!'
                continue
            elif isinstance(self[k], SCFProperties):
                r += '%s {%s} ' % (k, self[k].as_tmsh(mode=mode, order=order))
            elif isinstance(self[k], BracedNLSVList):
                r += '%s {%s} ' % (k, self[k].as_tmsh(mode=mode, order=order))
            elif isinstance(self[k], NLSVList):
                r += '%s {%s} ' % (k, self[k].as_tmsh(mode=mode, order=order))
            elif isinstance(self[k], Flag):
                if self[k].data:
                    r += '%s ' % (k)
            elif k == '_blob':
                r += '%s ' % self[k]
            elif isinstance(self[k], SCFObject):
                r += '%s %s ' % (k, self[k].objname)
            elif isinstance(self[k], SCFValue):
                r += '%s %s ' % (k, self[k].as_tmsh(mode=mode, order=order))
            else:
                r += '%s %s ' % (k, str(self[k]))
        return '%s}' % r


@total_ordering
class SCFObject:
    '''
        Attributes:
        objmodule -- The module for this object
            eg
                'ltm'
                'cm'
                'sys'
                'auth'

        objtype -- The array of the object's type
            eg
                for objmodule 'ltm':
                    ['virtual']
                for objmodule 'apm':
                    ['resource','remote-desktop','citrix-client-bundle']

        objname -- The name of the object, detected by seeing a '/'

        props -- The OrderedDict of properties for this object
            OrderedDict is used in case the order is needed in the future
            For blob objects like irules and iapp templates, the property
            name is _blob
            The type of the property can be stored (TODO)
                eg
                'bracedlist'
                    name { listitem1 listitem2 }
                'quotedstring'
                    name "this is a quoted string"
            If a property has no name '_nonameX' is used (TODO)
                X to autoincrement (TODO)
    '''

    __version__ = __version__

    def __init__(self, *args, **kwargs):
        '''Initialise the SCFObject() with empty values'''

        self._tabstop = 4
        self._order = None
        self.objmodule = kwargs.get('objmodule', '')
        self.objtype = kwargs.get('objtype', [])
        self.objname = kwargs.get('objname')
        self.props = SCFProperties(kwargs.get('props', {}))

    def __str__(self):
        '''Format the object as an SCF text (TODO)'''
        r = '%s %s ' % (self.objmodule, ' '.join(self.objtype))
        if self.objname:
            r += '%s ' % (self.objname)
        r += '{'
        # if self.props == SCFProperties():
        #     r += ' '
        # else:
        r += '%s' % self.props._tostr(tab=self._tabstop, order=self._order)
        r += '}'
        return r

    def __eq__(self, other):
        if not isinstance(other, SCFObject): return False
        if self.fulldef != other.fulldef: return False
        if self.props != other.props: return False
        return True

    def __lt__(self, other):
        if not isinstance(other, SCFObject):
            raise TypeError('Cannot compare %s and %s for sorting' %
                            (self.__class__, other.__class__))
        if str(self.fulldef).lower() < str(other.fulldef).lower(): return True
        return False

    @property
    def objdef(self):
        r = [self.objmodule]
        for _ in self.objtype:
            r.append(_)
        return tuple(r)
        # return tuple([self.objmodule, *self.objtype])

    @property
    def objnamespace(self):
        return tuple([self.objmodule, self.objtype[0]])

    @property
    def strdef(self):
        return ' '.join(self.objdef)

    @property
    def fulldef(self):
        r = []
        for _ in self.objdef:
            r.append(_)
        r.append(self.objname if self.objname else '')
        return ' '.join(r).rstrip(' ')
        # return ' '.join([*self.objdef, self.objname if self.objname else '']).rstrip(' ')

    @property
    def folder(self):
        return self.objname.split('/')[1:-1] if self.objname and self.objname.startswith('/') else None

    def glob(self, comp):
        return fnmatch(self.fulldef, comp)

    def as_tmsh(self, mode='create', props_mode='replace-all-with'):
        return 'tmsh %s %s %s' % (mode, self.fulldef, self.props.as_tmsh(mode=props_mode)[len(props_mode) + 1:])
