#! /usr/bin/env python
#coding=utf-8
#=============================================================================
#
#          FILE:  pygdiff.py
#
#         USAGE:  pygdiff.py project/module tag/sha1 tag/sha1
#
#   DESCRIPTION:  get the detail diffrents in two BL, tag or SHA1
#
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR:  Volans Wang (VOLW), volansw@gmail.com
#       COMPANY:
#       VERSION:  1.0
#=============================================================================
import os
import sys
import random
import subprocess
import commands


debug = False


class Git_Diff():
    '''dff for git working directory.
    '''

    def __debug(self, msg):
        global debug
        if debug:
            print msg
        else:
            pass

    def __init__(self, path, tag1, tag2):
        '''path: git working directory
        tag1: one tag or SHA1
        tag2: another tag or SHA1
        '''
        self.prj_path = path
        self.working_temp = "/tmp/gitdiff_" + str(random.getrandbits(50))
        self.tag1 = tag1
        self.tag2 = tag2

    def __is_Git_Directory(self):
        if os.path.exists(".git"):
            return True
        else:
            return False

    def __is_Project(self):
        if self.__is_Git_Directory():
            if os.path.exists(".gitmodules"):
                return True
            else:
                return False
        else:
            return False

    def __get_diffrents_list(self, tag1, tag2, path='.'):
        '''get the diffrents files list.
        For project, we get diffrent files and modules.
        For modules, we get diffrent files list.
        '''
        os.chdir(path)
        cmd = "/usr/bin/env git diff %s %s --name-only" % (tag1, tag2)
        output = commands.getoutput(cmd).split()
        os.chdir(self.prj_path)
        return output

    def __get_module_sha1s(self, module):
        '''git diff only show submodule name in project level.
        This function get the detail SHA1 update in submodule.
        '''
        os.chdir(self.prj_path)
        cmd = "/usr/bin/env git diff %s %s -- %s" \
            % (self.tag1, self.tag2, module)
        diff_msg = commands.getoutput(cmd).split('\n')
        sha1_1 = [i.split()[-1] for i in diff_msg if "-Subproject" in i]
        if sha1_1:
            sha1_1 = sha1_1[0]
        else:
            sha1_1 = False

        sha1_2 = [i.split()[-1] for i in diff_msg if "+Subproject" in i]
        if sha1_2:
            sha1_2 = sha1_2[0]
        else:
            sha1_2 = False
        return (sha1_1, sha1_2)

    def __get_module_list(self):
        '''it return the .gitmodules items.
        Including all modules in A and B, only in A and only in B.
        '''
        os.chdir(self.prj_path)
        cmd = "/usr/bin/env git show %s:.gitmodules" % (self.tag1)
        gitmodules = commands.getoutput(cmd).split('\n')
        l1 = [i.split()[2] for i in gitmodules if "path" in i]

        cmd = "/usr/bin/env git show %s:.gitmodules" % (self.tag2)
        gitmodules = commands.getoutput(cmd).split('\n')
        l2 = [i.split()[2] for i in gitmodules if "path" in i]

        self.module_list = list(set(l1) | set(l2))
        self.new_module_list = list(set(l2) - set(l1))
        self.del_module_list = list(set(l1) - set(l2))

    def __copy_list(self, files, tag, dest):
        '''copy files of special version to dest directory.
        create directory tree automatically.
        '''
        for i in files:
            if os.path.isdir(i):
                continue
            cmd = "/usr/bin/env git show %s:%s" % (tag, i)
            self.__debug("git show cmd: %s" % (cmd))
            (exitcode, output) = commands.getstatusoutput(cmd)
            if exitcode == 0:
                dest_dir = dest + '/' + os.path.dirname(i)
                self.__debug("dest_dir=%s" % (dest_dir))
                if not os.path.exists(dest_dir):
                    os.makedirs(dest + '/' + os.path.dirname(i))
                    self.__debug("dir maked: %s" \
                        % (dest + '/' + os.path.dirname(i)))
                f = open(dest+'/'+i, 'w').write(output)
                self.__debug("writed file: %s" % (dest+'/'+i))

    def __diff_mode(self):
        '''diff module
        '''
        files = self.__get_diffrents_list(tag1=self.tag1, tag2=self.tag2)
        self.__debug("modified files:%s" % (files))
        dest1 = self.working_temp + '/' + self.tag1
        self.__copy_list(files, self.tag1, dest1)

        dest2 = self.working_temp + '/' + self.tag2
        self.__copy_list(files, self.tag2, dest2)

        command = "/usr/bin/env meld %s %s" % (dest1, dest2)
        subprocess.Popen(command, shell=True, \
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def __diff_project(self):
        '''diff project
        '''
        self.__get_module_list()
        diff_list = self.__get_diffrents_list(tag1=self.tag1, tag2=self.tag2)
        self.__debug(diff_list)
        self.__debug(self.module_list)
        dest1 = self.working_temp + '/' + self.tag1
        dest2 = self.working_temp + '/' + self.tag2
        for name in diff_list:
            if name in self.module_list:
                if name in self.new_module_list:
                    os.makedirs(self.working_temp+'/'+self.tag2+'/'+name)
                    open(self.working_temp+'/'+self.tag2+'/'+name+'/'\
                        +'new_module', 'w').write('')
                    self.__debug("%s it is a new module" % (name))
                elif name in self.del_module_list:
                    os.makedirs(self.working_temp+'/'+self.tag1+'/'+name)
                    open(self.working_temp+'/'+self.tag1+'/'+name+'/'\
                        +'deleted_module', 'w').write('')
                    self.__debug("%s it is a deleted module" % (name))
                else:
                    sha1_1, sha1_2 = self.__get_module_sha1s(name)
                    self.__debug("\n\n=====%s's Sha1 update from %s to %s" \
                        % (name, sha1_1, sha1_2))
                    files = self.__get_diffrents_list(sha1_1, sha1_2, name)
                    self.__debug("modified files:%s" % (files))
                    os.chdir(name)
                    self.__copy_list(files, sha1_1, \
                        self.working_temp+'/'+self.tag1+'/'+name)
                    self.__copy_list(files, sha1_2, \
                        self.working_temp+'/'+self.tag2+'/'+name)
                    os.chdir(self.prj_path)
            else:
                self.__debug("--------%s----------" % (name))
                self.__copy_list([name], self.tag1, dest1)
                self.__copy_list([name], self.tag2, dest2)

        command = "/usr/bin/env meld %s %s" % (dest1, dest2)
        subprocess.Popen(command, shell=True, \
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def diff(self):
        '''start diff.
        It is the root diff operation.
        '''
        os.chdir(self.prj_path)
        if self.__is_Project():
            print("===========pygdif working on a GIT project=============")
            self.__diff_project()
        elif self.__is_Git_Directory():
            print("===========pygdif working on a GIT module=============")
            self.__diff_mode()
        else:
            print("=========Sorry, Please give me a GIT working dir =====")


def help():
    print("=======================================================")
    print("  pygdiff.py [module/project path] tag/SHA1 tag/SHA1   ")
    print("  Note: all parameters are needed                      ")
    print("=======================================================")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        help()
        sys.exit()

    git_dir = sys.argv[1]
    tag1 = sys.argv[2]
    tag2 = sys.argv[3]
    test = Git_Diff(git_dir, tag1, tag2)
    test.diff()
