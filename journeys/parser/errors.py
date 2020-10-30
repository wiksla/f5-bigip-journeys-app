# -*- coding: utf-8 -*-

"""
Copyright 2020 F5 Networks Inc.

Copyright 2018 NGINX, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This file has been modified by F5 Networks Inc. for the purpose of adding support for processing bigip config files.
"""


class ParserBaseException(Exception):
    def __init__(self, strerror, filename, lineno):
        self.args = (strerror, filename, lineno)
        self.filename = filename
        self.lineno = lineno
        self.strerror = strerror

    def __str__(self):
        if self.lineno is not None:
            return "%s in %s:%s" % self.args
        else:
            return "%s in %s" % self.args


class ParserSyntaxError(ParserBaseException):
    pass
