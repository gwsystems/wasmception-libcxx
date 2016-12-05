#===----------------------------------------------------------------------===##
#
#                     The LLVM Compiler Infrastructure
#
# This file is dual licensed under the MIT and the University of Illinois Open
# Source Licenses. See LICENSE.TXT for details.
#
#===----------------------------------------------------------------------===##

import platform
import os
import lit.util
import libcxx.util


class CXXCompiler(object):
    CM_Default = 0
    CM_PreProcess = 1
    CM_Compile = 2
    CM_Link = 3

    def __init__(self, path, flags=None, compile_flags=None, link_flags=None,
                 warning_flags=None, modules_flags=None, use_modules=False,
                 use_ccache=False, use_warnings=False, compile_env=None,
                 cxx_type=None, cxx_version=None):
        self.path = path
        self.flags = list(flags or [])
        self.compile_flags = list(compile_flags or [])
        self.warning_flags = list(warning_flags or [])
        self.link_flags = list(link_flags or [])
        self.modules_flags = list(modules_flags or [])
        self.use_modules = use_modules
        assert not use_modules or modules_flags is not None
        self.use_ccache = use_ccache
        self.use_warnings = use_warnings
        if compile_env is not None:
            self.compile_env = dict(compile_env)
        else:
            self.compile_env = None
        self.type = cxx_type
        self.version = cxx_version
        if self.type is None or self.version is None:
            self._initTypeAndVersion()

    def copy(self):
        new_cxx = CXXCompiler(
            self.path, flags=self.flags, compile_flags=self.compile_flags,
            link_flags=self.link_flags, warning_flags=self.warning_flags,
            modules_flags=self.modules_flags, use_modules=self.use_modules,
            use_ccache=self.use_ccache, use_warnings=self.use_warnings,
            compile_env=self.compile_env, cxx_type=self.type,
            cxx_version=self.version)
        return new_cxx

    def useModules(self, value=True):
        self.use_modules = value
        assert not self.use_modules or self.modules_flags is not None

    def useCCache(self, value=True):
        self.use_ccache = value

    def useWarnings(self, value=True):
        self.use_warnings = value

    def _initTypeAndVersion(self):
        # Get compiler type and version
        macros = self.dumpMacros()
        if macros is None:
            return
        compiler_type = None
        major_ver = minor_ver = patchlevel = None
        if '__clang__' in macros.keys():
            compiler_type = 'clang'
            # Treat apple's llvm fork differently.
            if '__apple_build_version__' in macros.keys():
                compiler_type = 'apple-clang'
            major_ver = macros['__clang_major__']
            minor_ver = macros['__clang_minor__']
            patchlevel = macros['__clang_patchlevel__']
        elif '__GNUC__' in macros.keys():
            compiler_type = 'gcc'
            major_ver = macros['__GNUC__']
            minor_ver = macros['__GNUC_MINOR__']
            patchlevel = macros['__GNUC_PATCHLEVEL__']
        self.type = compiler_type
        self.version = (major_ver, minor_ver, patchlevel)

    def _basicCmd(self, source_files, out, mode=CM_Default, flags=[],
                  input_is_cxx=False):
        cmd = []
        if self.use_ccache \
                and not mode == self.CM_Link \
                and not mode == self.CM_PreProcess:
            cmd += ['ccache']
        cmd += [self.path]
        if out is not None:
            cmd += ['-o', out]
        if input_is_cxx:
            cmd += ['-x', 'c++']
        if isinstance(source_files, list):
            cmd += source_files
        elif isinstance(source_files, str):
            cmd += [source_files]
        else:
            raise TypeError('source_files must be a string or list')
        if mode == self.CM_PreProcess:
            cmd += ['-E']
        elif mode == self.CM_Compile:
            cmd += ['-c']
        cmd += self.flags
        if self.use_modules:
            cmd += self.modules_flags
        if mode != self.CM_Link:
            cmd += self.compile_flags
            if self.use_warnings:
                cmd += self.warning_flags
        if mode != self.CM_PreProcess and mode != self.CM_Compile:
            cmd += self.link_flags
        cmd += flags
        return cmd

    def _getWarningFlags(self):
        return self.warning_flags if self.use_warnings else []

    def preprocessCmd(self, source_files, out=None, flags=[]):
        return self._basicCmd(source_files, out, flags=flags,
                             mode=self.CM_PreProcess,
                             input_is_cxx=True)

    def compileCmd(self, source_files, out=None, flags=[]):
        return self._basicCmd(source_files, out, flags=flags,
                             mode=self.CM_Compile,
                             input_is_cxx=True) + ['-c']

    def linkCmd(self, source_files, out=None, flags=[]):
        return self._basicCmd(source_files, out, flags=flags,
                              mode=self.CM_Link)

    def compileLinkCmd(self, source_files, out=None, flags=[]):
        return self._basicCmd(source_files, out, flags=flags)

    def preprocess(self, source_files, out=None, flags=[], cwd=None):
        cmd = self.preprocessCmd(source_files, out, flags)
        out, err, rc = lit.util.executeCommand(cmd, env=self.compile_env,
                                               cwd=cwd)
        return cmd, out, err, rc

    def compile(self, source_files, out=None, flags=[], cwd=None):
        cmd = self.compileCmd(source_files, out, flags)
        out, err, rc = lit.util.executeCommand(cmd, env=self.compile_env,
                                               cwd=cwd)
        return cmd, out, err, rc

    def link(self, source_files, out=None, flags=[], cwd=None):
        cmd = self.linkCmd(source_files, out, flags)
        out, err, rc = lit.util.executeCommand(cmd, env=self.compile_env,
                                               cwd=cwd)
        return cmd, out, err, rc

    def compileLink(self, source_files, out=None, flags=[],
                    cwd=None):
        cmd = self.compileLinkCmd(source_files, out, flags)
        out, err, rc = lit.util.executeCommand(cmd, env=self.compile_env,
                                               cwd=cwd)
        return cmd, out, err, rc

    def compileLinkTwoSteps(self, source_file, out=None, object_file=None,
                            flags=[], cwd=None):
        if not isinstance(source_file, str):
            raise TypeError('This function only accepts a single input file')
        if object_file is None:
            # Create, use and delete a temporary object file if none is given.
            with_fn = lambda: libcxx.util.guardedTempFilename(suffix='.o')
        else:
            # Otherwise wrap the filename in a context manager function.
            with_fn = lambda: libcxx.util.nullContext(object_file)
        with with_fn() as object_file:
            cc_cmd, cc_stdout, cc_stderr, rc = self.compile(
                source_file, object_file, flags=flags, cwd=cwd)
            if rc != 0:
                return cc_cmd, cc_stdout, cc_stderr, rc

            link_cmd, link_stdout, link_stderr, rc = self.link(
                object_file, out=out, flags=flags, cwd=cwd)
            return (cc_cmd + ['&&'] + link_cmd, cc_stdout + link_stdout,
                    cc_stderr + link_stderr, rc)

    def dumpMacros(self, source_files=None, flags=[], cwd=None):
        if source_files is None:
            source_files = os.devnull
        flags = ['-dM'] + flags
        cmd, out, err, rc = self.preprocess(source_files, flags=flags, cwd=cwd)
        if rc != 0:
            return None
        parsed_macros = {}
        lines = [l.strip() for l in out.split('\n') if l.strip()]
        for l in lines:
            assert l.startswith('#define ')
            l = l[len('#define '):]
            macro, _, value = l.partition(' ')
            parsed_macros[macro] = value
        return parsed_macros

    def getTriple(self):
        cmd = [self.path] + self.flags + ['-dumpmachine']
        return lit.util.capture(cmd).strip()

    def hasCompileFlag(self, flag):
        if isinstance(flag, list):
            flags = list(flag)
        else:
            flags = [flag]
        # Add -Werror to ensure that an unrecognized flag causes a non-zero
        # exit code. -Werror is supported on all known compiler types.
        if self.type is not None:
            flags += ['-Werror', '-fsyntax-only']
        cmd, out, err, rc = self.compile(os.devnull, out=os.devnull,
                                         flags=flags)
        return rc == 0

    def addFlagIfSupported(self, flag):
        if isinstance(flag, list):
            flags = list(flag)
        else:
            flags = [flag]
        if self.hasCompileFlag(flags):
            self.flags += flags
            return True
        else:
            return False

    def addCompileFlagIfSupported(self, flag):
        if isinstance(flag, list):
            flags = list(flag)
        else:
            flags = [flag]
        if self.hasCompileFlag(flags):
            self.compile_flags += flags
            return True
        else:
            return False

    def hasWarningFlag(self, flag):
        """
        hasWarningFlag - Test if the compiler supports a given warning flag.
        Unlike addCompileFlagIfSupported, this function detects when
        "-Wno-<warning>" flags are unsupported. If flag is a
        "-Wno-<warning>" GCC will not emit an unknown option diagnostic unless
        another error is triggered during compilation.
        """
        assert isinstance(flag, str)
        if not flag.startswith('-Wno-'):
            if self.hasCompileFlag(flag):
                self.warning_flags += [flag]
                return True
            return False
        flags = ['-Werror', flag]
        old_use_warnings = self.use_warnings
        self.useWarnings(False)
        cmd = self.compileCmd('-', os.devnull, flags)
        self.useWarnings(True)
        # Remove '-v' because it will cause the command line invocation
        # to be printed as part of the error output.
        # TODO(EricWF): Are there other flags we need to worry about?
        if '-v' in cmd:
            cmd.remove('-v')
        out, err, rc = lit.util.executeCommand(cmd, input='#error\n')
        assert rc != 0
        if flag in err:
            return False
        return True

    def addWarningFlagIfSupported(self, flag):
        if self.hasWarningFlag(flag):
            self.warning_flags += [flag]
            return True
        return False
