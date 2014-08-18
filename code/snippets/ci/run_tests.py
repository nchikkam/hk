import os
import re
import csv
import sys
import time
import glob
import shutil
import getopt
import xml.sax.saxutils
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal
import threading
import time

from config import Config
from string import Template
from xml.dom import minidom
import traceback
from decimal import *
import enum
from enum import Enum

ExitCode = Enum('OK', 'Error', 'Skipped')
exitCode = ExitCode.OK # Exit code
timeOut = 3600 # Default value for timeout

class Test:
    class Status:
        PASSED, FAILED, IGNORED = range(3)

    testName = ""
    testError = []
    status = None
    def __init__(self, testName):
        self.testName = testName

def get_branch_name(basedir):
    branch = os.getenv("BRANCH")
    return branch

def get_config(basedir):
    cfg = None
    branch_cfg = None

    default_file = basedir + '/test_runner/default.ini'
    default_cfg = Config(file(default_file))

    branch = get_branch_name(basedir)
    branch_file = basedir + '/test_runner/' + branch + '.ini'

    if os.path.isfile(branch_file):
        branch_cfg  = Config(file(branch_file))

    if branch_cfg == None:
        logEvent('INFO: Branch Specific Config Doesn\'t Exists: ' + branch_file + ' Using ' + default_file )
        cfg = default_cfg
    else:
        logEvent('INFO: Config Version\'s: %s(%s) - %s(%s)' % (default_file, default_cfg.dev.version, branch_file, branch_cfg.dev.version) )
        if default_cfg.dev.version != branch_cfg.dev.version:
            logEvent('INFO: Versions doesn\'t match, DEFAULT BRANCH HAS LATEST CHANGES THAN ' + branch)
            logEvent('INFO: PLEASE MERGE THE CHANGES FROM DEFAULT BRANCH TO YOUR BRANCH')
            sys.exit(1)
        else:
            cfg = branch_cfg

    return cfg

def replaceSlash(string):
    return os.path.normpath(string)

# We still need this method as gadget gives us details and we need to copy
# only few files from there.
def copyDirectory(root_src_dir, root_dst_dir):
    logEvent("INFO: Copying from " + root_src_dir + ' to ' + root_dst_dir)
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                try:
                    os.remove(dst_file)
                except:
                    os.system('attrib -R %s' % dst_file)
                    os.remove(dst_file)
            shutil.copy2(src_file, dst_dir)

def removeDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

def backupResults(src, dst, dev):
    ts = time.strftime('%Y_%m_%d_%H_%M_%S')
    dst = dst + ts + '_' + dev + '/'
    logEvent("INFO: Backing Up Results " + src + ' --> ' + dst)
    try:
        copyDirectory(src, dst)
    except:
        pass

def getSuiteName(fileName):
    fileName = fileName.replace('/', '\\')
    m = re.search('.*\\\(.*)\.xml$', fileName)
    if not m == None:
        suite = m.group(1)
    else:
        m = re.search('.*\\\(.*)$', fileName)
        suite = m.group(1)
    return suite

class Format:
    """ The class to keep the format string to generate the report
        Reads the template file only once for ever.
    """
    fmt = None
    def __init__(self, templateFile):
        if Format.fmt is None:
            try:
                fh = open(templateFile)
                Format.fmt = ''.join(fh.readlines())
                fh.close()
            except:
                traceback.print_exc()

class Executor:
    def __init__(self, testName, platform):
        self.basedir = replaceSlash(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath( __file__ )), '..')))
        self.cfg = get_config(self.basedir)
        logEvent ("INFO: basedir: " + self.basedir)

        self.testName = testName
        self.platform = self.get_platfrom(platform)
        self.template = self.basedir + self.cfg.details.settings.common.template
        self.xmlreport = None

        self.consoldationreport = self.basedir + self.cfg.details.settings[self.platform].consolidationreport
        self.posttestsrcdir = self.basedir + self.cfg.details.settings.common.posttestsrcdir
        self.posttestdstdir = self.basedir + self.cfg.details.settings.common.posttestdstdir
        logEvent("INFO: Actual Platform: [" + platform + '] Short Form: [' + self.platform + ']')

        # Set branch dir name
        dir = self.basedir
        dir = dir.replace("\\", "/")
        #logEvent ("DEBUG: dir: " + dir)
        pattern = re.compile (".*\/(.*)")
        m = pattern.search(dir)
        self.branchDirName = m.group(1)

    def get_platfrom(self, platform_long_name):
        platforms = self.cfg.details.settings.keys()
        for platform in platforms:
            if platform.lower() in platform_long_name.lower():
                return platform
        return None

    def cleanFolderContent(self, path):
        actual_path = replaceSlash(path)
        if os.path.exists(actual_path):
            flag = None
            for root, dirs, files in os.walk(actual_path, topdown=False):
                try:
                    for f in files:
                        flag = "file"
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        flag = "dir"
                        shutil.rmtree(os.path.join(root, d),ignore_errors=True)

                except:
                    logEvent("INFO: Some file was not deleted. Trying to delete that forcefully")
                    if flag == "file":
                        file_to_delete = os.path.join(root, f)
                        os.system('attrib -R %s' %file_to_delete)
                        os.remove(file_to_delete)

    def createTestDirs(self):
        for dir in self.testDirs:
            path = self.basedir + dir.strip()
            if not os.path.exists(path):
                logEvent("INFO: Creating " + path)
                os.makedirs(replaceSlash(path))

    def parse_UnitTest_log(self, log):
        if os.path.getsize(log) == 0:
            logEvent("INFO: " + log + " is empty")
            return -1,-1,-1
        else:
            file = open(log, "r")
            lines = file.readlines()
            file.close()
            line = lines[-1]
            m = re.search("Run:\s([0-9]+)\s+Failure total:\s([0-9]+)\s+Failures:\s([0-9]+)\s+Errors:\s([0-9]+)$",line)
            if not m == None:
                totalCount = int(m.group(1))
                failCount = int(m.group(2))
                passCount = totalCount - failCount
            else:
                m = re.search("OK\s([0-9]+)\stests\spassed$", line)
                if not m == None:
                    passCount = int(m.groups(1)[0])
                    failCount = 0
                    totalCount = passCount + failCount
                else:
                    logEvent("WARNING: " + log + " does not contain test summary")
                    return -1,-1,-1
            return passCount, failCount, totalCount

    def generateReportFile(  self,
                             reportFile,
                             detailTestName,
                             count_passed=0,
                             count_failed=0,
                             count_skipped=0,
                             count_aborted=0,
                             count_total=0,
                             exe_start_time=" ",
                             exe_end_time=" "):
        reportFile = replaceSlash(reportFile)
        logEvent( "INFO: Writing test results to file: " + reportFile )
        report = open(reportFile, "a")
        template = Format(self.template)
        line_to_write = template.fmt % (escape(detailTestName), count_passed, count_failed, count_skipped, count_aborted, count_total) + '\n'
        report.write(line_to_write)
        report.close()

    def parse_UnitTest(self):
        log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        log = replaceSlash(log)

        if os.path.exists(log):
            passCount, failCount, totalCount = self.parse_UnitTest_log(log)
            if totalCount == -1:
                logEvent ("WARNING: No Unittest results found")
                return
            reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
            self.generateReportFile(reportFile, self.testName, passCount, failCount, 0, 0, totalCount)
        else:
            logEvent("WARNING: " +  log + ' file is not found' )

    def parsegTeamTestResult(self, log_file):
        line_count = 0
        field_count = 0
        pass_count = 0
        fail_count = 0
        skip_count = 0
        abort_count = 0

        if not os.path.exists(log_file):
            logEvent( "WARNING: gTeam test result xml file is not found. File name: " + log_file )
            return -1,-1,-1,-1,-1

        if os.path.getsize(log_file) == 0:
            logEvent( "WARNING: gTeam test result xml file is empty. File name: " + log_file )
        else:
            f = open(log_file, 'rb')
            f.readline()
            required_line = f.readline()
            f.close()

            line_count = 0
            field_count = 0
            pass_count = 0
            fail_count = 0
            skip_count = 0
            abort_count = 0

            if re.match("<testsuite errors=", required_line): # Check for the Errors Count.
                required_line = required_line.split(" ")
                fail_count = int(required_line[2].split("=")[1].strip("\""))
                total_count = int(required_line[3].split("=")[1].strip("\""))
            pass_count = total_count - fail_count
        return pass_count, fail_count, skip_count, abort_count, total_count

    def parse_gTeam(self):
        summary_suite = []
        mdataresultsdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].xmlresultdir
        xmllist = glob.glob(mdataresultsdir + '/*.xml')
        for log_file in xmllist:
            try:
                log_file = replaceSlash(log_file.strip())
                #m = re.search('.*/(.*)\.xml$', log_file)
                #suite_name = m.group(1)
                suite_name = getSuiteName(log_file)
                summary_suite.append(suite_name)
                pass_count, fail_count, skip_count, abort_count, total_count = self.parsegTeamTestResult(log_file)
                if total_count == -1:
                    logEvent ("WARNING: No test result was parsed")
                    return
                detailTestName = self.testName + ' ' + suite_name
                reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
                self.generateReportFile(reportFile, detailTestName, pass_count, fail_count, skip_count, abort_count, total_count)
            except:
                logEvent( "WARNING: Error encountered. Here is the trace back" )
                traceback.print_exc()

        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
        pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total = self.calculateSummaryCounts(reportFile)
        if total_count_total == -1:
            logEvent ("WARNING: No summary was calculated for search")
            return
        detailTestName = self.testName + ' ' + ' '.join(summary_suite)
        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].summaryreport
        self.generateReportFile(reportFile, detailTestName, pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total)

    def parserTeamTestResult(self, log_file):
        logEvent ("INFO: Parsing route test file: " + str(log_file))
        if (os.path.getsize(log_file) == 0):
            logEvent("WARNING: rTeam test result xml file is empty. File name: " + log_file)
            return -1,-1,-1,-1,-1
        else:
            logEvent( "INFO: Parsing rTeam test result file: " + log_file )
            f = open(log_file, 'rb')
            lines = f.readlines()
            f.close()

            line_count  = 0
            field_count = 0
            pass_count  = 0
            fail_count  = 0
            skip_count  = 0
            abort_count = 0
            total_count = 0
            multi_line  = 0

            for required_line in lines:
                #print "\nDEBUG: line: " + required_line
                if (re.match("<testsuite", required_line) and re.search(">$", required_line)): # Check for the Errors Count.
                    required_line = required_line.strip().strip(">").strip("<").split(" ")
                    #print "\nDEBUG: req_line: " + str(required_line)
                    if (len(required_line) < 7):
                        logEvent ("ERROR: testsuite tag does not contain required information, file: " + log_file)
                        break
                    fail_count = int(required_line[7].split("=")[1].strip("\""))
                    abort_count = int(required_line[6].split("=")[1].strip("\""))
                    total_count = int(required_line[5].split("=")[1].strip("\""))
                    break
                elif(re.match(">", required_line) and multi_line):
                    break
                elif((re.match("<testsuite", required_line) and not re.search(">$", required_line)) or multi_line):
                    required_line = required_line.strip().strip(">").strip("<").strip(" ")
                    multi_line = 1
                    if (re.search ("failures=", required_line)):
                        fail_count = int(required_line.split("=")[1].strip("\""))
                    elif (re.search ("errors=", required_line)):
                        abort_count = int(required_line.split("=")[1].strip("\""))
                    elif (re.search ("tests=", required_line)):
                        total_count = int(required_line.split("=")[1].strip("\""))

            pass_count = total_count - fail_count - abort_count
            #logEvent ("DEBUG: pass " + str(pass_count))
            #if multi_line:
                #logEvent ("DEBUG: Performed multi line match")
        return pass_count, fail_count, skip_count, abort_count, total_count

    def parse_rTeam(self):
        summary_suite = []
        mdataresultsdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].csvresultdir
        csvlist = glob.glob(mdataresultsdir + '/*.xml')
        for log_file in csvlist:
            try:
                log_file = replaceSlash(log_file.strip())
                #logEvent ("DEBUG: Checking file: " + log_file)
                if log_file.lower().find('summary') == -1: #parse only suite summaries not binary produced ones.
                    logEvent ("INFO: Processing file: " + log_file)
                    m = re.search('.*\\\(.*)\.xml$', log_file)
                    if m == None:
                        m = re.search('.*/(.*)\.xml$', log_file)
                    if m == None:
                        logEvent ("WARNING: Unable to detect suite_name, results could not be parsed")
                        return
                    suite_name = m.group(1)
                    #logEvent ("DEBUG: suite_name:" + suite_name)
                    summary_suite.append(suite_name)
                    pass_count, fail_count, skip_count, abort_count, total_count = self.parserTeamTestResult(log_file)
                    if total_count == -1:
                        logEvent ("WARNING: No results were parsed for rTeam")
                        return

                    detailTestName = self.testName + ' ' + suite_name
                    reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
                    self.generateReportFile(reportFile, detailTestName, pass_count, fail_count, skip_count, abort_count, total_count)
            except:
                traceback.print_exc()

        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
        reportFile = replaceSlash(reportFile)
        pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total = self.calculateSummaryCounts(reportFile)
        if total_count_total == -1:
            logEvent ("\nWARNING: No summary was calculated for rTeam")
            return
        detailTestName = self.testName + ' ' + ' '.join(summary_suite)
        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].summaryreport
        self.generateReportFile(reportFile, detailTestName, pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total)

    def calculateSummaryCounts(self, reportFile):
        if not os.path.exists(reportFile):
            logEvent ("\nWARNING: Cannot find result file for calculating summary: " + reportFile)
            return -1,-1,-1,-1,-1
        f = open(reportFile, "r")
        detail_log_file_lines = f.readlines()
        f.close()

        pass_count = 0
        fail_count = 0
        skip_count = 0
        abort_count = 0
        total_count = 0

        for line in detail_log_file_lines:
            if re.search("Passed:",line):
                pass_count = pass_count + int(line.split(":")[1].strip())
            elif re.search("Failed:",line):
                fail_count = fail_count + int(line.split(":")[1].strip())
            elif re.search("Skipped:",line):
                skip_count = skip_count + int(line.split(":")[1].strip())
            elif re.search("Aborted:",line):
                abort_count = abort_count + int(line.split(":")[1].strip())

        total_count = pass_count + fail_count + skip_count + abort_count
        return pass_count, fail_count, skip_count, abort_count, total_count

    def generateConsolidationReport(self):

        summarydir = self.summarydir
        reportFile = self.consoldationreport
        summarylogs = glob.glob(summarydir + '/*summary.log')

        #pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total
        sums = [0, 0, 0, 0, 0]
        for summary in summarylogs:
            l = self.calculateSummaryCounts(summary)
            sums = [sum(pair) for pair in zip(sums, l)]
        pass_count, fail_count, skip_count, abort_count, total = sums
        self.generateReportFile(reportFile, 'WHOLE SUMMARY', pass_count, fail_count, skip_count, abort_count, total)

    def convertCsvToXml(self, csvFile, xml):
        if os.path.getsize(csvFile) == 0:
            logEvent( "WARNING: Test result file is empty. File name: " + csvFile )
            return
        else:
            xml_log_file = open(xml, "w")

            f = open(csvFile, 'rb')
            csv_lines = csv.reader(f)

            test_case_count = 0
            fail_count = 0
            field_count = 0
            lines = []

            for row in csv_lines:
                if test_case_count == 0:

                    header = row
                    for field in header:
                        if re.search("suite",field):
                            classname_field_index = field_count
                        elif re.search("case",field):
                            name_field_index = field_count
                        elif re.search("passed",field):
                            passed_field_index = field_count
                        elif re.search("reason",field):
                            reason_field_index = field_count

                        field_count = field_count + 1
                    test_case_count = test_case_count + 1

                else:
                    test_case_count = test_case_count + 1

                    classname = row[classname_field_index]
                    name = row[name_field_index]
                    failure_message = row[reason_field_index]

                    if row[passed_field_index] == "0":
                        fail_count = fail_count + 1
                        lines.append("<testcase classname=\"" + classname + "\" name=\"" + name + "\" >\n")
                        lines.append("<failure message=\"" + failure_message + "\">FAILED</failure>\n")
                        lines.append("</testcase>\n")
                    else:
                        lines.append("<testcase classname=\"" + classname + "\" name=\"" + name + "\" />\n")

            if test_case_count < 1:
                logEvent( "WARNING: No results found in the csv file: " + csv )
                return

            xml_log_file.write("<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n")
            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(fail_count)+"\" tests=\"" + str(test_case_count-1) +"\" name=\"rTeam\">\n")
            for x in lines:
                xml_log_file.write(x)

            xml_log_file.write("</testsuite>")
            xml_log_file.close()
            f.close()

    def convertToXML(self):
        if self.xmlreport == None:
            return
        logEvent("INFO: " + self.testName.upper() + ' Generating XML files')
        summary_suite = []
        mdataresultsdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].csvresultdir
        xmlresultdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].xmlresultdir
        csvlist = glob.glob(mdataresultsdir + '/*.csv')

        for csv in csvlist:
            csv = replaceSlash(csv.strip())
            if csv.lower().find('summary') == -1: #parse only suite summaries not binary produced ones.
                m = re.search('.*\\\(.*)\.csv$', csv)
                if m == None:
                    m = re.search('.*/(.*)\.csv$', csv)
                suite_name = m.group(1)
                xml = xmlresultdir + '/' + suite_name + '.xml'
                self.convertCsvToXml(csv, xml)

    def convertCppUnitToJUnit(self):
        if self.xmlreport == None:
            return

        xmlOutput = self.basedir + self.cfg.details.settings[self.platform][self.testName].xml_output
        xmlResultDir = self.basedir + self.cfg.details.settings[self.platform][self.testName].xmlresultdir
        xmlFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].xunit_output
        msxslBin = self.basedir + self.cfg.details.settings.common.msxsl
        cppunit2junit_xsl = self.basedir + self.cfg.details.settings.common.cppunit2junit_xsl

        convertCmd = msxslBin + ' ' + xmlOutput + ' ' + cppunit2junit_xsl + ' -o ' + xmlFile

        logEvent("Running: " + convertCmd)
        try:
            retcode = subprocess.call(convertCmd, shell=True)
            if retcode < 0:
                logEvent("[E] Child was terminated by signal " + str(retcode))
                print >>sys.stderr, "[E] Child was terminated by signal ", -retcode
            elif retcode > 0:
                logEvent("[E] XML parsing error " + str(retcode))
            else:
                logEvent("INFO: XML parsed.")
        except OSError, e:
            logEvent("[E] Execution failed: " + str(e))

class gadgetExecutor(Executor):
    def __init__(self, testName):
        Executor.__init__(self, testName, os.getenv("PLATFORM"))

        self.testDirs = self.cfg.details.settings[self.platform][self.testName].testdirs
        self.summarydir = self.basedir + self.cfg.details.settings.common.gadget_summarydir

        self.consoldationreport = self.basedir + self.cfg.details.settings[self.platform].consolidationreport

        self.gadget_posttestsrcdir = self.basedir + self.cfg.details.settings.common.gadget_posttestsrcdir
        self.posttestdstdir = self.basedir + self.cfg.details.settings.common.posttestdstdir
        self.createTestDirs()

    def executeCommands(self, cmd, log, timeoutMultiplier):
        global exitCode
        global timeOut
        cmd = cmd
        timeout = self.cfg.details.settings[self.platform][self.testName].timeout
        try:
            if (os.environ["PROCESS_TIMEOUT"] != None):
                timeout = int(os.environ["PROCESS_TIMEOUT"])
        except:
            timeout = timeout

        if (timeout == None or timeout < 0 or timeout == ''):
            timeout = int(3600) # Default timeout of 1 hr

        try:
            timeout = int(timeout)
        except:
            # Timeout value is not an integer value, set default value
            timeout = int(3600) # Default timeout of 1 hr

        # Use timeoutMultiplier to have enough time for all tests to be executed
        if (not timeoutMultiplier>0):
            timeoutMultiplier = 1
        timeout = timeout * timeoutMultiplier
        timeOut = timeout

        self.timeoutExceeded = None
        # Check if timeout exceeded during execution of previous command
        if (self.timeoutExceeded):
            logEvent ("INFO: Timeout period exceeded while executing: " + cmd + ", skipping any remaining commands")
            exitCode = ExitCode.Error
            return 1

        if (log==None):
            log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        # Remove leading and trailing spaces
        cmd = cmd.lstrip()
        cmd = cmd.rstrip()
        log = log.lstrip()
        log = log.rstrip()

        cmd = cmd.replace("/", "\\")
        log = log.replace("/", "\\")
        errlog = log + '_err'
        logEvent('INFO: Executing: ' + cmd + ', storing output to log: ' + log)
        logEvent('INFO: Expecting the process to complete in ' + str(timeout) + ' seconds')
        try:
            Fh = open(log, "w")
            ErrFh = open(errlog, "w")
            timer = threading.Timer(timeout, self.procHandler)
            timer.start()
            self.proc = subprocess.Popen(cmd, stdout=Fh, stderr=ErrFh)
            self.proc.wait()
            if (timer.isAlive()):
                timer.cancel()
            if (self.proc.returncode < 0):
                # Raise error as test binary has exited with a negative exit code
                exitCode = ExitCode.Error
                logEvent ("ERROR: Child exited with exit code: " + str(self.proc.returncode))
            else:
                logEvent ("INFO: Child exited with exit code: " + str(self.proc.returncode))

            Fh.close()
            ErrFh.close()
        except Exception as e:
            exitCode = ExitCode.Error
            logEvent ("WARNING: Exception caught while executing: " + str(cmd) + ", excep: " + str(e))

    def procHandler(self):
        global exitCode
        global timeOut
        try:
            exitCode = ExitCode.Error
            self.proc.poll()
            logEvent ("WARNING: Process exceeded timeout[" + str(self.platform) + "-" + str(self.testName) + "][" + str(timeOut) + "], terminating child pid: " + str(self.proc.pid))
            self.proc.kill()
            self.timeoutExceeded = 1
        except Exception as e:
            exitCode = ExitCode.Error
            logEvent ("WARNING: Exception caught while terminating child process: " + str(self.proc.pid))

    def shutDowngadgetSimulator(self):
        logEvent("INFO: Shutting down gadgetSimulator")
        time.sleep(10)
        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].shutdown.filename
        cmds = self.cfg.details.settings[self.platform][self.testName].shutdown.cmds
        f = open(file, 'w')
        f.write('\n'.join(cmds))
        f.close()
        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].shutdown.CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        logEvent('INFO: Running Command: ' + cmd)
        os.system(cmd)
        time.sleep(30)
        logEvent("INFO: gadgetSimulator is shutdown")

    def mountSMHardDisk(self):
        logEvent("INFO: Attaching SM to local PC")
        file_for_disk_mount = self.basedir + 'base_dir/mount_disk.txt'
        disk_mount_file = open(file_for_disk_mount, "w")
        x = self.cfg.details.settings[self.platform][self.testName].gadgetSimulator_2nd_harddisk
        disk_mount_file.write("SELECT VDISK FILE=\""+ x + "\"\n")
        disk_mount_file.write("ATTACH VDISK")
        disk_mount_file.close()

        mount_bat_file_path = replaceSlash(self.basedir + 'base_dir/mount_SM.bat')
        logEvent(mount_bat_file_path)
        os.system(mount_bat_file_path)
        time.sleep(20)

    def unmountSMHardDisk(self):
        logEvent("INFO: Detaching SM from local PC")
        file_for_disk_unmount = self.basedir + 'base_dir/umount_disk.txt'
        disk_umount_file = open(file_for_disk_unmount, "w")
        x = self.cfg.details.settings[self.platform][self.testName].gadgetSimulator_2nd_harddisk
        disk_umount_file.write("SELECT VDISK FILE=\""+ x +"\"\n")
        disk_umount_file.write("DETACH VDISK")
        disk_umount_file.close()
        unmount_bat_file_path = replaceSlash(self.basedir + 'base_dir/umount_SM.bat')
        logEvent(unmount_bat_file_path)
        os.system(unmount_bat_file_path)
        time.sleep(20)

    def copy_results(self):
        local_drive_letter = self.cfg.details.settings[self.platform].local_drive_letter
        src = self.cfg.details.settings[self.platform][self.testName].shutdown.srcfolder
        dst = self.basedir + self.cfg.details.settings[self.platform][self.testName].shutdown.dstfolder
        src = src.replace('/', '\\')
        dst = dst.replace('/', '\\')
        logEvent("INFO: Copying Results from SM to Local Disk")
        copyDirectory(src, dst)
        removeDir(src)

    def gatherResults(self):
        logEvent ("\nINFO: Gathering results")
        self.shutDowngadgetSimulator()
        self.mountSMHardDisk()
        self.copy_results()
        self.unmountSMHardDisk()

class gadgetUnit(gadgetExecutor):
    def __init__(self):
        gadgetExecutor.__init__(self, 'unittest')

    def run(self):
        exe = self.cfg.dev[self.testName].gadget_exe
        bin = exe
        m = re.search('.*\/(.+)', exe)
        if not m == None:
            bin = m.group(1)

        exe = exe.replace ('/', '\\')

        currcmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].filename
        f = open(file, 'w')
        precmds = self.cfg.details.settings[self.platform][self.testName].precmds
        precmds = "\n".join(precmds)
        preraw  = Template(precmds)
        precmds = preraw.substitute(branchDir=self.branchDirName, exe=exe, bin=bin)

        f.write(precmds + '\n')

        # Unlike win, the tests are put into a single PS1 file and hence the timeout
        # mentioned might turn out to be too less. To follow an approach similar to win
        # count the number of commands to be run and pass it as an arg which would be
        # used as a multiplier for the timeout
        timeoutMultiplier = 0
        for curcmd in currcmds:
            rawcmd = Template(curcmd)
            cmd = rawcmd.substitute(branchDir=self.branchDirName,bin=bin)
            currcmdslist.append(cmd)
            timeoutMultiplier += 1

        f.write('\n'.join(currcmdslist) + '\n')

        postcmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        postcmds = "\n".join(postcmds)
        postraw  = Template(postcmds)
        postcmds = postraw.substitute(branchDir=self.branchDirName)

        f.write(postcmds + "\n")
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)

        cmd.replace('/', '\\')
        log = self.basedir + self.cfg.details.settings[self.platform][self.testName].binlog
        #logEvent("INFO: Running  " + cmd)
        #os.system(cmd)
        self.executeCommands(cmd, log, timeoutMultiplier)

    def parse(self):
        self.parse_UnitTest()

    def convertToXML(self):
        pass

    def getName(self):
        return "unittest"

class gadgetgTeam(gadgetExecutor):
    def __init__(self):
        gadgetExecutor.__init__(self, 'gTeam')
        self.xmlreport = None

    def get_suites_from_dir(self, suites_dir):
        suites_dir = suites_dir.replace('\\', '/')
        logEvent("INFO: Suites Dir: " + suites_dir)
        suites = {}
        for top, dirs, files in os.walk(suites_dir):
            for nm in files:
                if nm.find('.json') != -1 and nm.find('.svn') == -1:
                    top = top.replace('\\', '/')
                    m = re.search('(.*)/\d{8}$', top)
                    if not m == None:
                        suite = m.group(1)
                        if not suites.has_key(suite):
                            suites[suite] = 1
        return suites.keys()

    def get_suites(self, suite_selector):
        if suite_selector == 'suites_dir':
            raw_suites_dir = Template(self.datadir + self.cfg.dev[self.testName].suites_dir)
            self.suites_dir = raw_suites_dir.substitute(branch=get_branch_name(self.basedir))
            return self.get_suites_from_dir(self.suites_dir)
        elif suite_selector == 'suites':
            return map(lambda suite: self.datadir + self.cfg.dev[self.testName].suites_dir + suite, self.cfg.dev[self.testName].suites)

    def change_drive(self, suite):
        l = list(suite)
        l[0] = self.cfg.details.settings[self.platform].gadgetSimulator_drive
        return ''.join(l)

    def run(self):
        exe = self.cfg.dev[self.testName].gadget_exe
        bin = exe
        m = re.search('.*\/(.+)', exe)
        if not m == None:
            bin = m.group(1)

        exe = exe.replace ('/', '\\')

        currcmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].filename
        f = open(file, 'w')
        precmds = self.cfg.details.settings[self.platform][self.testName].precmds
        precmds = "\n".join(precmds)
        preraw  = Template(precmds)
        precmds = preraw.substitute(branchDir=self.branchDirName, exe=exe, bin=bin)

        f.write(precmds + '\n')

        self.exe = self.cfg.dev[self.testName].gadget_exe
        self.mdata = self.cfg.dev[self.testName].mdata
        self.cache = self.cfg.dev[self.testName].cache
        #self.datadir = self.cfg.details.settings.gadget.datadir
        #self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.datadir = self.cfg.details.settings.gadget.gadgetSimulator_drive + ':\\' + self.cfg.details.settings.common.datadir
        gd = Template(self.cfg.dev[self.testName].gTeamdata)
        self.gTeamdata = gd.substitute(branch=get_branch_name(self.basedir))

        #self.suites = self.cfg.dev[self.testName].suites
        self.suites = self.get_suites(self.cfg.dev[self.testName].suite_selector)
        logEvent("INFO:" + self.testName + ' Suites: ')
        for s in self.suites:
            logEvent(s)

        # Unlike win, the tests are put into a single PS1 file and hence the timeout
        # mentioned might turn out to be too less. To follow an approach similar to win
        # count the number of commands to be run and pass it as an arg which would be
        # used as a multiplier for the timeout
        timeoutMultiplier = 0

        for curcmd in currcmds:
            for s in self.suites:
                xm = self.change_drive(s.strip())
                suiteName = getSuiteName(xm)
                rawcmd = Template(curcmd)
                cmd = rawcmd.substitute(branchDir=self.branchDirName, bin=bin, basedir=self.basedir, datadir=self.datadir,
                                        xml=xm, suite=suiteName, gTeamdata=self.gTeamdata,
                                        mdata=self.mdata, cache=self.cache)

                currcmdslist.append('echo ' + suiteName)
                currcmdslist.append(cmd.replace('/', '\\'))
                timeoutMultiplier += 1

        f.write('\n'.join(currcmdslist)  + '\n')

        postcmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        f.write("\n".join(postcmds) + "\n")
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        #logEvent("INFO: Executing " + cmd)
        #os.system(cmd)
        self.executeCommands(cmd, log, timeoutMultiplier)

    def parse(self):
        self.parse_gTeam()

    def convertToXML(self):
        if not self.xmlreport == None:
            Executor.convertToXML(self)

    def getName(self):
        return "gTeam"

class gadgetrTeam(gadgetExecutor):
    def __init__(self):
        self.testName = 'rTeam'
        gadgetExecutor.__init__(self, self.testName)
        self.xmlreport = int(self.cfg.details.settings[self.platform][self.testName].xmlreport)

    def get_suites_from_dir(self, suites_dir):
        suites_dir = suites_dir.replace('/', '\\')
        logEvent("INFO: rTeam suites Dir: " + suites_dir)
        suites = {}
        for top, dirs, files in os.walk(suites_dir):
            for nm in files:
                if nm.find('.xml') != -1 and nm.find('.svn') == -1:
                    suite = suites_dir + '\\' + nm
                    #print "\nDEBUG: suite: " + suite
                    if not suites.has_key(suite):
                        suites[suite] = 1
        return suites.keys()

    def get_suites(self, suite_selector):
        if suite_selector == 'suites_dir':
            #raw_suites_dir = Template(self.datadir + self.cfg.dev[self.testName].suites_dir)
            raw_suites_dir = Template(os.path.split(os.path.split(self.basedir)[0])[0] + self.cfg.details.settings.common.datadir + self.cfg.dev[self.testName].suites_dir)
            self.suites_dir = raw_suites_dir.substitute(branch=get_branch_name(self.basedir))
            return self.get_suites_from_dir(self.suites_dir)
        elif suite_selector == 'suites':
            suites_dir = self.cfg.dev[self.testName].suites_dir.replace('/', '\\')
        return map(lambda suite: self.datadir + suites_dir + '/' + suite, self.cfg.dev[self.testName].suites)

    def run(self):
        exe = self.cfg.dev[self.testName].gadget_exe
        bin = exe
        m = re.search('.*\/(.+)', exe)
        if not m == None:
            bin = m.group(1)

        exe = exe.replace ('/', '\\')

        currcmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        suites = self.cfg.dev[self.testName].suites
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].filename
        f = open(file, 'w')
        precmds = self.cfg.details.settings[self.platform][self.testName].precmds
        precmds = "\n".join(precmds)
        preraw  = Template(precmds)
        precmds = preraw.substitute(branchDir=self.branchDirName, exe=exe, bin=bin)

        f.write(precmds + '\n')

        self.exe = self.cfg.dev[self.testName].gadget_exe
        self.mdata = self.cfg.dev[self.testName].mdata
        self.cache = self.cfg.dev[self.testName].cache
        self.datadir = self.cfg.details.settings[self.platform].datadir
        #print "\nDEBUG: datadir: " + self.datadir
        self.server = self.cfg.dev[self.testName].server
        self.emptycache = self.cfg.dev[self.testName].emptycache
        self.optional_param = self.cfg.dev[self.testName].optional_param

        self.suites = self.get_suites(self.cfg.dev[self.testName].suite_selector)
        logEvent("INFO: " + self.testName + ' suites: ')
        for s in self.suites:
            logEvent(s)

        # Unlike win, the tests are put into a single PS1 file and hence the timeout
        # mentioned might turn out to be too less. To follow an approach similar to win
        # count the number of commands to be run and pass it as an arg which would be
        # used as a multiplier for the timeout
        timeoutMultiplier = 0
        for curcmd in currcmds:
            for s in self.suites:
                #xm = self.datadir + s.strip()
                xm = s.strip()
                suiteName = getSuiteName(xm)
                rawcmd = Template(curcmd)
                cmd = rawcmd.substitute(branchDir=self.branchDirName,bin=bin, basedir=self.basedir, datadir=self.datadir,
                                        xml=xm, suite=suiteName, mdata=self.mdata, cache=self.cache,
                                        emptycache=self.emptycache, server=self.server, optional_param=self.optional_param)
                currcmdslist.append('echo ' + suiteName)
                currcmdslist.append(cmd)
                timeoutMultiplier += 1

        f.write('\n'.join(currcmdslist)  + '\n')

        postcmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        f.write("\n".join(postcmds) + "\n")
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        #logEvent("INFO: Executing " + cmd)
        #os.system(cmd)
        self.executeCommands(cmd, log, timeoutMultiplier)

    def parse(self):
        self.parse_rTeam()

    def convertToXML(self):
        pass
#        if not self.xmlreport == None:
#            Executor.convertToXML(self)

    def getName(self):
        return "rTeam"

class gadgetrenpTeam(gadgetExecutor):
    def __init__(self):
        self.testName = 'renpTeam'
        gadgetExecutor.__init__(self, self.testName)

    def run(self):
        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].filename
        f = open(file, 'w')
        #offline|online
        tests = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        # Unlike win, the tests are put into a single PS1 file and hence the timeout
        # mentioned might turn out to be too less. To follow an approach similar to win
        # count the number of commands to be run and pass it as an arg which would be
        # used as a multiplier for the timeout
        timeoutMultiplier = 0
        for type in tests:
            currcmds = self.cfg.details.settings[self.platform][self.testName][type].CMDLIST
            currcmdslist = []

            cmds = self.cfg.details.settings[self.platform][self.testName][type].precmds
            f.write('\n'.join(cmds) + '\n')

            self.exe = self.cfg.dev.rendering.gadget_exe
            self.cache = self.cfg.dev[self.testName].cache
            self.datadir = self.cfg.details.settings[self.platform].datadir

            for curcmd in currcmds:
                rawcmd = Template(curcmd)
                cmd = rawcmd.substitute(branchDir=self.branchDirName, exe=self.exe, basedir=self.basedir, datadir=self.datadir)
                currcmdslist.append(cmd)
                timeoutMultiplier += 1

            f.write('\n'.join(currcmdslist)  + '\n')

            cmds = self.cfg.details.settings[self.platform][self.testName][type].postcmds
            rawcmds = Template(cmds)
            cmds = rawcmds.substitute(branchDir=self.branchDirName)
            f.write('\n'.join(cmds) + '\n')

        f.close()
        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        #logEvent("INFO: Running " + cmd)
        #os.system(cmd)
        self.executeCommands(cmd, log, timeoutMultiplier)

    def parse(self):
        pass

    def convertToXML(self):
        pass

class gadgetrenrTeam(gadgetExecutor):
    def __init__(self):
        self.testName = 'renrTeam'
        gadgetExecutor.__init__(self, self.testName)

    def run(self):
        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].filename
        f = open(file, 'w')
        #offline|online
        tests = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        for type in tests:
            currcmds = self.cfg.details.settings[self.platform][self.testName][type].CMDLIST
            currcmdslist = []

            cmds = self.cfg.details.settings[self.platform][self.testName][type].precmds
            f.write('\n'.join(cmds) + '\n')

            self.exe = self.cfg.dev.rendering.gadget_exe
            self.cache = self.cfg.dev[self.testName].cache
            self.datadir = self.cfg.details.settings[self.platform].datadir

            for curcmd in currcmds:
                rawcmd = Template(curcmd)
                cmd = rawcmd.substitute(branchDir=self.branchDirName, exe=self.exe, basedir=self.basedir, datadir=self.datadir)
                currcmdslist.append(cmd)

            f.write('\n'.join(currcmdslist)  + '\n')

            cmds = self.cfg.details.settings[self.platform][self.testName][type].postcmds
            rawcmds = Template(cmds)
            cmds = rawcmds.substitute(branchDir=self.branchDirName)
            f.write('\n'.join(cmds) + '\n')

        f.close()
        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        #logEvent("INFO: Executing " + cmd)
        #os.system(cmd)
        self.executeCommands(cmd, log)

    def parse(self):
        pass

    def convertToXML(self):
        pass

class winExecutor(Executor):
    def __init__(self, testName):
        Executor.__init__(self, testName, os.getenv("PLATFORM"))

        self.testName=testName
        self.cmdList = []
        self.datadir= None
        self.exe= None
        self.suites=[]
        self.suites_dir = None
        self.testDirs = self.cfg.details.settings[self.platform][self.testName].testdirs
        self.proc = None # store the sub process
        #self.report = self.cfg.details.settings.win[self.testName].report
        #The Binaries are creating few summary files which we are not interested in. In order to keep these house keeping
        #files, it is better to launch the binary after changing into this folder. Its clean and safe in our processing.
        self.rawresultsdir = self.basedir + self.cfg.details.settings[self.platform][testName].binresultsdir
        self.summarydir = self.basedir + self.cfg.details.settings.common.summarydir

    def get_suites_from_dir(self, suites_dir):
        logEvent("INFO: Suites Dir: " + suites_dir)
        suites_dir = suites_dir.replace('\\', '\\')
        suites = {}
        for top, dirs, files in os.walk(suites_dir):
            for nm in files:
                if nm.find('.json') != -1 and nm.find('.svn') == -1:
                    top = top.replace('\\', '/')
                    m = re.search('(.*)/\d{8}$', top)
                    if m: # json files can also be outside of testcase directories, ignore them
                        suite = m.group(1)
                        if not suites.has_key(suite):
                            suites[suite] = 1
        return suites.keys()

    def get_suites(self, suite_selector):
        if suite_selector == 'suites_dir':
            raw_suites_dir = Template(self.datadir + self.cfg.dev[self.testName].suites_dir)
            self.suites_dir = raw_suites_dir.substitute(branch=get_branch_name(self.basedir))
            return self.get_suites_from_dir(self.suites_dir)
        elif suite_selector == 'suites':
            return map(lambda suite: self.datadir + self.cfg.dev[self.testName].suites_dir + suite, self.cfg.dev[self.testName].suites)

    def composeCommands(self):
        cmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.exe = self.cfg.dev[self.testName].win_exe
        self.suites = self.cfg.dev[self.testName].suites
        for c in cmds:
            c = c.strip()
            rawcmd = Template(c)
            for s in self.suites:
                xm = self.datadir + s.strip()
                suiteName = getSuiteName(xm)
                cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir, datadir=self.datadir, xml=xm, suite=suiteName)
                self.cmdList.append(cmd)
        return self.cmdList

    def executeCommands(self, cmdLst):
        global exitCode
        global timeOut
        timeout = self.cfg.details.settings[self.platform][self.testName].timeout
        try:
            if (os.environ["PROCESS_TIMEOUT"] != None):
                timeout = int(os.environ["PROCESS_TIMEOUT"])
        except:
            timeout = timeout

        if (timeout == None or timeout < 0 or timeout == ''):
            timeout = int(3600) # Default timeout of 1 hr

        try:
            timeout = int(timeout)
        except:
            # Timeout value is not an integer value, set default value
            timeout = int(3600) # Default timeout of 1 hr

        timeOut = timeout
        self.timeoutExceeded = None
        for cmd in cmdLst:
            # Check if timeout exceeded during execution of previous command
            if (self.timeoutExceeded):
                logEvent ("INFO: Timeout period exceeded while executing: " + cmd + ", skipping any remaining commands")
                exitCode = ExitCode.Error
                return 1
            # Split the command to get the output direction file, since Popen does not support it
            # Replace \ and \\ with / to avoid any issue with regex
            #logEvent('About to invoke: ' + str(cmd))
            cmd = cmd.replace("\\", "/")
            pattern = re.compile(".*\s(.*\>.*)\s")
            log = None
            if (pattern.search(cmd)):
                m = pattern.search(cmd)
                cmdArr = cmd.split(m.group(1))
                # We expect that there is only one '>' in cmd and we get a 2 element array
                cmd = cmdArr[0]
                log = cmdArr[1]
            else:
                # Nothing, no redirection
                cmd = cmd

            # Remove leading and trailing spaces
            cmd = cmd.lstrip()
            cmd = cmd.rstrip()
            log = log.lstrip()
            log = log.rstrip()

            #cmd = cmd.replace("/", "\\")
            #log = log.replace("/", "\\")
            logEvent('INFO: Executing: ' + cmd + ', logging to: ' + log)
            logEvent('INFO: Expecting the process to complete in ' + str(timeout) + ' seconds')
            Fh = None
            try:
                Fh = open(log, "w")
                timer = threading.Timer(timeout, self.procHandler)
                timer.start()
                self.proc = subprocess.Popen(cmd, stdout=Fh, stderr=subprocess.STDOUT)
                self.proc.wait()
                if (timer.isAlive()):
                    timer.cancel()
                if (self.proc.returncode < 0):
                    # Raise error as test binary has exited with a negative exit code
                    exitCode = ExitCode.Error
                    logEvent ("ERROR: Child exited with exit code: " + str(self.proc.returncode))
                else:
                    logEvent ("INFO: Child exited with exit code: " + str(self.proc.returncode))

                Fh.close()
            except Exception as e:
                logEvent ("WARNING: Exception caught while executing: " + str(cmd) + ", excep: " + str(e))
                exitCode = ExitCode.Error
                Fh.close()

    def procHandler(self):
        global exitCode
        global timeOut
        try:
            exitCode = ExitCode.Error
            self.proc.poll()
            logEvent ("ERROR: Process exceeded timeout[" + str(self.platform) + "-" + self.testName + "][" + str(timeOut) + "], terminating child pid: " + str(self.proc.pid))
            self.proc.kill()
            self.timeoutExceeded = 1
        except Exception as e:
            exitCode = ExitCode.Error
            logEvent ("WARNING: Exception caught while terminating child process: " + str(self.proc.pid))

def timeFmt():
    return time.strftime('%d:%m:%Y %H:%M:%S')

def logEvent(text):
    print "\n[%s]\t%s" % (timeFmt(), text)

def escape(text):
    return "\'" + text + "\'"

class winUnit(winExecutor):
    def __init__(self):
        winExecutor.__init__(self, 'unittest')
        self.xmlreport = int(self.cfg.details.settings[self.platform][self.testName].xmlreport)
        self.composeCommands()

    def composeCommands(self):
        rawcmd = Template(self.cfg.details.settings[self.platform][self.testName].CMD)
        self.exe = self.cfg.dev[self.testName].win_exe
        cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir)
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.cmdList.append(cmd)
        return self.cmdList

    def run(self):
        self.createTestDirs()
        t = Template(self.cfg.details.settings[self.platform][self.testName].mdata_src_path)
        mdata_dir = self.cfg.dev[self.testName].mdata_path
        mdata_src_path = t.substitute(datadir=self.datadir, mdata_path=mdata_dir)
        t = Template(self.cfg.details.settings[self.platform][self.testName].mdata_dst_path)
        mdata_dst_path = t.substitute(basedir=self.basedir)
        copyDirectory(mdata_src_path, mdata_dst_path)

        self.executeCommands(self.cmdList)
        """for cmd in self.cmdList:
            cmd = cmd.replace("/","\\")
            try:
                # Binary creates special set of housekeeping files. Change to the directory where we need these files.
                pwd =  os.getcwd()
                os.chdir(self.rawresultsdir)
                logEvent('Running  ' + cmd)
                os.system(cmd)

                os.chdir(pwd)
            except:
                traceback.print_exc()
        """

    def parse(self):
        self.parse_UnitTest()

    def convertToXML(self):
        if not self.xmlreport == None:
            logEvent("INFO: " + self.testName.upper() + ' Generating XML files')
            Executor.convertCppUnitToJUnit(self)

class wingTeam(winExecutor):
    def __init__(self):
        winExecutor.__init__(self, 'gTeam')
        self.composeCommands()
        self.detailTestName = 'gTeam '

    def composeCommands(self):
        cmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.exe = self.cfg.dev[self.testName].win_exe
        self.mdata = self.cfg.dev[self.testName].mdata
        self.cache =self.cfg.dev[self.testName].cache
        gd = Template(self.cfg.dev[self.testName].gTeamdata)
        self.gTeamdata = gd.substitute(branch=get_branch_name(self.basedir))

        self.suites = self.get_suites(self.cfg.dev[self.testName].suite_selector)

        for c in cmds:
            c = c.strip()
            rawcmd = Template(c)
            for s in self.suites:
                xm = s.strip()
                suiteName = getSuiteName(xm)
                cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir, datadir=self.datadir,
                                        xml=xm, suite=suiteName, gTeamdata=self.gTeamdata,
                                        mdata=self.mdata, cache=self.cache)
                self.cmdList.append(cmd)
        return self.cmdList

    def run(self):
        self.createTestDirs()
        logEvent(self.testName + ' Suites: ')
        for s in self.suites:
            logEvent(s)

        self.executeCommands(self.cmdList)
        """
        for cmd in self.cmdList:
            cmd = cmd.replace("/","\\")
            try:
                os.chdir(self.rawresultsdir)
                logEvent('Running  ' + cmd)
                os.system(cmd)
            except:
                traceback.print_exc()
        """

    def parse(self):
        self.parse_gTeam()

    def convertToXML(self):
        if not self.xmlreport == None:
            Executor.convertToXML(self)

class winrTeam(winExecutor):
    def __init__(self):
        winExecutor.__init__(self, 'rTeam')
        self.xmlreport = int(self.cfg.details.settings[self.platform][self.testName].xmlreport)
        self.composeCommands()

    def composeCommands(self):
        cmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.exe = self.cfg.dev[self.testName].win_exe
        self.mdata = self.cfg.dev[self.testName].mdata
        self.cache =self.cfg.dev[self.testName].cache
        self.server =self.cfg.dev[self.testName].server
        self.emptycache =self.cfg.dev[self.testName].emptycache
        self.optional_param = self.cfg.dev[self.testName].optional_param

        self.suites = self.get_suites(self.cfg.dev[self.testName].suite_selector)

        for c in cmds:
            c = c.strip()
            rawcmd = Template(c)
            for s in self.suites:
                xm = s.strip()
                suiteName = getSuiteName(xm)
                cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir, datadir=self.datadir,
                                        xml=xm, suite=suiteName, mdata=self.mdata, cache=self.cache,
                                        server=self.server, emptycache=self.emptycache, optional_param=self.optional_param)
                self.cmdList.append(cmd)
        return self.cmdList

    def run(self):
        self.createTestDirs()
        self.executeCommands(self.cmdList)
        """
        for cmd in self.cmdList:
            cmd = cmd.replace("/","\\")
            try:
                os.chdir(self.rawresultsdir)
                logEvent('Running  ' + cmd)
                os.system(cmd)
            except:
                traceback.print_exc()
        """

    def parse(self):
        self.parse_rTeam()

    def convertToXML(self):
        pass

class winrenrTeam(winExecutor):
    def __init__(self):
        winExecutor.__init__(self, 'renrTeam')
        self.xmlreport = int(self.cfg.details.settings[self.platform][self.testName].xmlreport)
        self.composeCommands()

    def composeCommands(self):
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.exe = self.cfg.dev.rendering.win_exe
        cmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        for k,c in cmds.iteritems():
            c = c.strip()
            rawcmd = Template(c)
            cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir, datadir=self.datadir, config_type=k)
            self.cmdList.append((k, cmd))
        return self.cmdList

    def run(self):
        self.createTestDirs()
        diskcache_src = self.datadir + self.cfg.dev[self.testName].diskcache
        logEvent("cache source for Rendering RT : "  + cache_src)
        cache_dst = self.basedir + self.cfg.details.settings[self.platform][self.testName].cache_dst
        copyDirectory(cache_src, cache_dst)

        cache = cache_dst
        imgOutput = self.basedir + self.cfg.details.settings[self.platform][self.testName].image_output
        tcOutImage = self.basedir + self.cfg.details.settings[self.platform][self.testName].testcase_imageoutput

        self.cleanFolderContent(tcOutImage)
        self.cleanFolderContent(imgOutput)

        for (config_type, cmd) in self.cmdList:
            log_dir = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + config_type
            xml_dir = self.basedir + self.cfg.details.settings[self.platform][self.testName].detailed_results_dir + config_type
            self.cleanFolderContent(log_dir)
            if (not os.path.exists(log_dir)):
                os.mkdir(log_dir)
            if (not os.path.exists(xml_dir)):
                os.mkdir(xml_dir)

            try:
                src_cfg = self.datadir + self.cfg.dev[self.testName][config_type]
                dst_cfg = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_cfg
                logEvent('INFO: Copying ' + str(src_cfg) + ' to ' + str(dst_cfg))
                if (os.path.exists(src_cfg)):
                    shutil.copy2(src_cfg, dst_cfg)
                else:
                    logEvent ('INFO: Unable to copy as file not found')

                src_tc = self.datadir + self.cfg.dev[self.testName].testcases
                dst_tc = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_csv
                logEvent('INFO: Copying ' + str(src_tc) + ' to ' + str(dst_tc))
                if (os.path.exists(src_tc)):
                    shutil.copy2(src_tc, dst_tc)
                else:
                    logEvent ('INFO: Unable to copy as file not found')
            except:
                traceback.print_exc()

            cmdLst = []
            cmdLst.append(cmd)
            self.executeCommands(cmdLst)
            if (self.timeoutExceeded == 1):
                # Timeout exceeded, skip remaining tests
                break

            try:
                dst_cfg = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_cfg
                dst_tc = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_csv
                #Copy Results
                if (os.path.exists(dst_cfg) and os.path.exists(dst_tc) and os.path.exists(log_dir)):
                    shutil.move(dst_cfg, log_dir)
                    shutil.move(dst_tc,  log_dir)
                else:
                    logEvent ('INFO: Unable to copy as file not found')

                img_output = self.basedir + self.cfg.details.settings[self.platform][self.testName].image_output
                logEvent ('INFO: Moving ' + img_output + ' to ' + log_dir)
                if (os.path.exists(img_output) and os.path.exists(log_dir)):
                    shutil.move(img_output, log_dir)
                else:
                    logEvent ('INFO: Unable to complete move operation')

                testcase_imageoutput = self.basedir + self.cfg.details.settings[self.platform][self.testName].testcase_imageoutput
                logEvent ('INFO: Moving ' + str(testcase_imageoutput) + ' to ' + str(log_dir))
                if (os.path.exists(testcase_imageoutput) and os.path.exists(log_dir)):
                    shutil.move(testcase_imageoutput, log_dir)
                else:
                    logEvent ('INFO: Unable to complete move operation')

            except:
                traceback.print_exc()

        """
            cmd = cmd.replace("/","\\")
            try:
                os.chdir(self.rawresultsdir)
                logEvent('Running  ' + cmd)

                src_cfg = self.datadir + self.cfg.dev[self.testName][config_type]
                dst_cfg = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_cfg
                logEvent('Copying ' + src_cfg + ' to ' + dst_cfg)
                shutil.copy2(src_cfg, dst_cfg)

                src_tc = self.datadir + self.cfg.dev[self.testName].testcases
                dst_tc = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_csv
                logEvent('Copying ' + src_tc + ' to ' + dst_tc)
                shutil.copy2(src_tc, dst_tc)

                os.system(cmd)

                #Copy Results
                shutil.move(dst_cfg, log_dir)
                shutil.move(dst_tc,  log_dir)
                img_output = self.basedir + self.cfg.details.settings[self.platform][self.testName].image_output
                shutil.move(img_output, log_dir)
                testcase_imageoutput = self.basedir + self.cfg.details.settings[self.platform][self.testName].testcase_imageoutput
                shutil.move(testcase_imageoutput, log_dir)

            except:
                traceback.print_exc()
        """
        self.cleanFolderContent(cache)
        logEvent ('INFO: Removing dir: ' + str(cache))
        if (os.path.exists(cache)):
            os.rmdir(cache)
        else:
            logEvent ('INFO: ' + str(cache) + ' not found')

    def parse(self):
        pass

    def convertToXML(self):
        if not self.xmlreport == None:
            for (config_type, cmd) in self.cmdList:
                self.cfg.details.settings[self.platform][self.testName].log = self.cfg.details.settings[self.platform][self.testName].log.replace("$config_type",config_type)
                self.cfg.details.settings[self.platform][self.testName].xml_output = self.cfg.details.settings[self.platform][self.testName].xml_output.replace("$config_type",config_type)
                self.cfg.details.settings[self.platform][self.testName].xunit_output = self.cfg.details.settings[self.platform][self.testName].xunit_output.replace("$config_type",config_type)
                self.cfg.details.settings[self.platform][self.testName].xmlresultdir = self.cfg.details.settings[self.platform][self.testName].xmlresultdir.replace("$config_type",config_type)
                logEvent("INFO: " + self.testName.upper() + ' Generating XML files')
                Executor.convertCppUnitToJUnit(self)

class winrenpTeam(winExecutor):
    def __init__(self):
        winExecutor.__init__(self, 'renpTeam')
        self.xmlreport = int(self.cfg.details.settings[self.platform][self.testName].xmlreport)
        self.composeCommands()

    def composeCommands(self):
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.exe = self.cfg.dev.rendering.win_exe
        cmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        for k,c in cmds.iteritems():
            c = c.strip()
            rawcmd = Template(c)
            cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir, datadir=self.datadir, config_type=k)
            self.cmdList.append((k, cmd))
        return self.cmdList

    def run(self):
        self.createTestDirs()
        cache_src = self.datadir + self.cfg.dev[self.testName].cache
        logEvent("cache source for Rendering Perf Test : "  + cache_src)
        cache_dst = self.basedir + self.cfg.details.settings[self.platform][self.testName].cache_dst
        copyDirectory(cache_src, cache_dst)
        cache = cache_dst

        for (config_type, cmd) in self.cmdList:
            log_dir = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + config_type
            xml_dir = self.basedir + self.cfg.details.settings[self.platform][self.testName].detailed_results_dir + config_type
            self.cleanFolderContent(log_dir)
            if (not os.path.exists(log_dir)):
                os.mkdir(log_dir)
            if (not os.path.exists(xml_dir)):
                os.mkdir(xml_dir)

            try:
                src_cfg = self.datadir + self.cfg.dev[self.testName][config_type]
                dst_cfg = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_cfg
                logEvent('INFO: Copying ' + str(src_cfg) + ' to ' + str(dst_cfg))
                if (os.path.exists(src_cfg) and os.path.exists(dst_cfg)):
                    shutil.copy2(src_cfg, dst_cfg)
                else:
                    logEvent ('INFO: Unable to copy')

            except:
                traceback.print_exc()

            cmdLst = []
            cmdLst.append(cmd)
            self.executeCommands(cmdLst)
            if (self.timeoutExceeded == 1):
                # Timeout exceeded, skip remaining tests
                break

            try:
                #Copy Results
                logEvent('INFO: Moving ' + str(dst_cfg) + ' to ' + str(log_dir))
                if (os.path.exists(dst_cfg) and os.path.exists(log_dir)):
                    shutil.move(dst_cfg, log_dir)
                else:
                    logEvent ('INFO: Unable to complete move')

                perftest = self.basedir + self.cfg.details.settings[self.platform][self.testName].perftest
                logEvent('INFO: Moving ' + str(perftest) + ' to ' + str(log_dir))
                if (os.path.exists(perftest) and os.path.exists(log_dir)):
                    shutil.move(perftest, log_dir)
                else:
                    logEvent ('INFO: Unable to complete move')

            except:
                traceback.print_exc()

        """
            cmd = cmd.replace("/","\\")
            try:
                os.chdir(self.rawresultsdir)

                src_cfg = self.datadir + self.cfg.dev[self.testName][config_type]
                dst_cfg = self.basedir + self.cfg.details.settings[self.platform][self.testName].target_cfg
                logEvent('Copying ' + src_cfg + ' to ' + dst_cfg)
                shutil.copy2(src_cfg, dst_cfg)

                logEvent('Running  ' + cmd)
                os.system(cmd)

                #Copy Results
                shutil.move(dst_cfg, log_dir)
                perftest = self.basedir + self.cfg.details.settings[self.platform][self.testName].perftest
                shutil.move(perftest, log_dir)

            except:
                traceback.print_exc()
        """
        self.cleanFolderContent(cache)
        logEvent ('INFO: Removing dir: ' + str(cache))
        if (os.path.exists(cache)):
            os.rmdir(cache)
        else:
            logEvent ('INFO: ' + str(cache) + ' not found')

    def parse(self):
        pass

    def convertToXML(self):
        if not self.xmlreport == None:
            for (config_type, cmd) in self.cmdList:
                self.cfg.details.settings[self.platform][self.testName].log = self.cfg.details.settings[self.platform][self.testName].log.replace("$config_type",config_type)
                self.cfg.details.settings[self.platform][self.testName].xml_output = self.cfg.details.settings[self.platform][self.testName].xml_output.replace("$config_type",config_type)
                self.cfg.details.settings[self.platform][self.testName].xunit_output = self.cfg.details.settings[self.platform][self.testName].xunit_output.replace("$config_type",config_type)
                self.cfg.details.settings[self.platform][self.testName].xmlresultdir = self.cfg.details.settings[self.platform][self.testName].xmlresultdir.replace("$config_type",config_type)
                logEvent("INFO: " + self.testName.upper() + ' Generating XML files')
                Executor.convertCppUnitToJUnit(self)


#0000000
def calculate_tolerance( k, l):
    nom = k
    if nom < l: nom = k
    else: nom = l

    denom = k
    if denom > l: denom = k
    else: denom = l

    return (Decimal(nom)/Decimal(denom))* 100

def get_ref_data( csv_ref_file):
    ref_hash = {}

    try:
        data = csv.reader(open(csv_ref_file))
        version = data.next()
        comment = data.next()
        fields = data.next()
        for row in data:
            r_key = '_'.join(row[0:5])
            if not ref_hash.has_key(r_key):
                ref_hash[r_key] = row
    except IOError:
        logEvent('File Not Found: ' + csv_ref_file)
    return ref_hash

def process_files( out_directory, ref_directory, log):
    logEvent('Processing Files ... ' + out_directory + ' --- ' + ref_directory)

    geocoded_location_list_fail_count = 0
    xPos_fail_count = 0
    yPos_fail_count = 0
    negative_offset_fail_count = 0
    positive_offset_fail_count = 0
    street_directionality_fail_count = 0
    congestion_side_fail_count = 0
    length_meter_fail_count = 0
    average_speed_ms_fail_count = 0
    average_speed_limit_ms_fail_count = 0
    primary_location_gdbid_fail_count = 0
    affected_streets_fail_count = 0
    affected_area_fail_count = 0
    map_matched_polylines_fail_count = 0
    street_categories_fail_count = 0
    gdbids_fail_count = 0
    pass_count = 0
    fail_count = 0
    report = []

    ref_files = glob.glob(ref_directory + '/*.csv')

    for ref_file in ref_files:
        msg = ''
        data = csv.reader(open(ref_file))
        version = data.next()
        comment = data.next()
        fields = data.next()

        out_file = ref_file.split('\\')[-1]
        out_file = out_directory + out_file
        ref_hash = get_ref_data(out_file)

        logEvent( 'Comparing ' + ref_file + ' ------- ' +  out_file )
        for row in data:
            o_key = '_'.join(row[0:5])
            if ref_hash.has_key(o_key):
                passed = True
                msg = ''
                if ref_hash[o_key][6] != row[6]:
                    msg = msg + ' Mismatch in     map_list\n'
                    map_list_fail_count = map_list_fail_count + 1
                    passed = False
                if ref_hash[o_key][7] != row[7]:
                    if (Decimal(ref_hash[o_key][7]) - Decimal(row[7])) > 0.1 or (Decimal(ref_hash[o_key][7]) - Decimal(row[7])) < -0.1:
                        msg = msg + ' Mismatch in xPos reference file xPos =' + ref_hash[o_key][7] + ' and the output file shows ' + row[7] + ' \n'
                        xPos_fail_count  = xPos_fail_count + 1
                        passed = False
                if ref_hash[o_key][8] != row[8]:
                    if (Decimal(ref_hash[o_key][8]) - Decimal(row[8])) > 0.1  or (Decimal(ref_hash[o_key][8]) - Decimal(row[8])) < -0.1:
                        msg = msg + ' Mismatch in yPos reference file yPos =' + ref_hash[o_key][8] + ' and the output file shows ' + row[8] + ' \n'
                        yPos_fail_count = yPos_fail_count + 1
                        passed = False
                if ref_hash[o_key][9] != row[9]:
                    msg = msg + ' Mismatch in negative_offset ref= ' + ref_hash[o_key][9] +  'out =' + row[9] + '\n'
                    negative_offset_fail_count = negative_offset_fail_count + 1
                    passed = False
                if ref_hash[o_key][10] != row[10]:
                    msg = msg + ' Mismatch in positive_offset ref= ' + ref_hash[o_key][10] + 'out =' + row[10] + '\n'
                    positive_offset_fail_count = positive_offset_fail_count + 1
                    passed = False
                if ref_hash[o_key][11] != row[11]:
                    msg = msg + ' Mismatch in street_directionality ref= ' + ref_hash[o_key][11] + 'out =' + row[11] + '\n'
                    street_directionality_fail_count = street_directionality_fail_count + 1
                    passed = False
                if ref_hash[o_key][12] != row[12]:
                    msg = msg + ' Mismatch in congestion_side ref= ' + ref_hash[o_key][12] + 'out =' + row[12] + '\n'
                    congestion_side_fail_count = congestion_side_fail_count + 1
                    passed = False
                if ref_hash[o_key][13] != row[13]:
                    tolerance = calculate_tolerance( ref_hash[o_key][13],  row[13])
                    if tolerance < 90:
                        msg = msg + ' Mismatch in length_meter ref= ' + ref_hash[o_key][13] + 'out =' + row[13] + '\n'
                        length_meter_fail_count = length_meter_fail_count + 1
                        passed = False
                if ref_hash[o_key][14] != row[14]:
                    tolerance = calculate_tolerance(ref_hash[o_key][14], row[14])
                    if tolerance < 90:
                        msg = msg + ' Mismatch in average_speed_ms ref= ' + ref_hash[o_key][14] + 'out =' + row[14] +'\n'
                        average_speed_ms_fail_count = average_speed_ms_fail_count + 1
                        passed = False
                if ref_hash[o_key][15] != row[15]:
                    tolerance = calculate_tolerance( ref_hash[o_key][15],  row[15] )
                    if tolerance < 90:
                        msg = msg + ' Mismatch in average_speed_limit_ms ref= ' + ref_hash[o_key][15] + 'out =' + row[15] + '\n'
                        average_speed_limit_ms_fail_count = average_speed_limit_ms_fail_count + 1
                        passed = False
                if ref_hash[o_key][16] != row[16]:
                    msg = msg + ' Mismatch in primary_location_gdbid ref= ' + ref_hash[o_key][16] + 'out =' + row[16] + '\n'
                    primary_location_gdbid_fail_count = primary_location_gdbid_fail_count + 1
                    passed = False
                if ref_hash[o_key][17] != row[17]:
                    msg = msg + ' Mismatch in affected_streets ref= ' + ref_hash[o_key][16] + 'out =' + row[17] + '\n'
                    affected_streets_fail_count = affected_streets_fail_count + 1
                    passed = False
                if ref_hash[o_key][18] != row[18]:
                    msg = msg + ' Mismatch in affected_area ref= ' + ref_hash[o_key][18] + 'out =' + row[18] + '\n'
                    affected_area_fail_count = affected_area_fail_count + 1
                    passed = False
                if ref_hash[o_key][19] != row[19]:
                    msg = msg + ' Mismatch in map_matched_polylines ref= ' + ref_hash[o_key][19] + 'out =' + row[19] + '\n'
                    map_matched_polylines_fail_count = map_matched_polylines_fail_count + 1
                    passed = False
                if ref_hash[o_key][20] != row[20]:
                    msg = msg + ' Mismatch in Street_categories ref= ' + ref_hash[o_key][20] + 'out =' + row[20] + '\n'
                    street_categories_fail_count = street_categories_fail_count + 1
                    passed = False
                if ref_hash[o_key][21] != row[21]:
                    msg = msg + ' Mismatch in gdbids ref= ' + ref_hash[o_key][21] + 'out =' + row[21] + '\n'
                    gdbids_fail_count = gdbids_fail_count + 1
                    passed = False

                if passed == False:
                    print msg
                    break
            else:
                if len(ref_hash) == 0:
                    msg = 'File Not Found : ' + out_file
                else:
                    msg = 'Key itself is missing in the new output ref=' + o_key + ' out=' + ' '.join(map(str, row))
                break

        if msg == '':
            pass_count = pass_count + 1
            report.append('SUITE SUCCEEDED: ' + ref_file)
        else:
            report.append('SUITE FAILED: ' + ref_file + '|' + msg)
            fail_count = fail_count + 1
            del ref_hash #Clear Hash

    summary = ['gb_list :' + str(map_list_fail_count),
              'xpos : ' + str(xPos_fail_count),
              'ypos : ' + str(yPos_fail_count),
              'neg_offset : ' + str(negative_offset_fail_count),
              'pos_offset:  ' + str(positive_offset_fail_count),
              'directionality :  ' +str( street_directionality_fail_count),
              'congestion_side : ' + str(congestion_side_fail_count),
              'length_meter : ' + str(length_meter_fail_count),
              'average_speed_ms : ' + str(average_speed_ms_fail_count),
              'average_speed_limit_ms : ' + str(average_speed_limit_ms_fail_count),
              'affected_streets : ' + str(affected_streets_fail_count),
              'affected_area : ' + str(affected_area_fail_count),
              'gb_matched_multilines : ' +str( map_matched_polylines_fail_count),
              'Street_categories : ' + str(street_categories_fail_count),
              'primary_location_id : ' + str(primary_location_gdbid_fail_count),
              'idlist : ' + str(gdbids_fail_count),
              'pass: ' + str(pass_count),
              'fail: ' + str(fail_count)
              ]

    report.append('\n'.join(summary) )

    FILE_OUT = open(log, 'w')

    FILE_OUT.write( '\n'.join(report) )
    FILE_OUT.close()

def get_summary_for_decoder_scenario_tests(logfile):
    myvar = open(logfile, 'r')
    lines = myvar.readlines()
    passed = 0
    failed = 0
    pass_suite = []
    fail_suite = {}
    for line in lines:
        if 'pass' in line:
            passed = line.split(' ')[1]
        if 'fail' in line:
            failed = line.split(' ')[1]
        if 'SUITE SUCCEEDED' in line:
            pass_suite.append(line.split(' ')[-1])
        if 'SUITE FAILED' in line:
            msg = line.split('|')
            suite = msg[0].split(' ')[-1]
            error = msg[1]
            fail_suite[suite] = error

    myvar.close()

    ret_data = {
                'passed': passed,
                'failed': failed,
                'pass_suite': pass_suite,
                'fail_suite': fail_suite,
                }
    return ret_data
#congestion -----------------------------------Start -----------------------------
class winCongestion(winExecutor):
    def __init__(self):
        winExecutor.__init__(self, 'Congestion')
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + self.cfg.details.settings.common.datadir

    def get_suites_from_dir(self, location_table):
        location_table = location_table.replace('\\', '/')
        files = os.listdir(location_table)
        return files

    def get_suites(self, suite_selector):
        if suite_selector == 'location_table':
            location_table = self.datadir + self.cfg.dev[self.testName].location_table
            return self.get_suites_from_dir(location_table)
        elif suite_selector == 'tables':
            return self.cfg.dev[self.testName].tables

    def run(self):
        self.createTestDirs()
        self.run_tmc_decoder_scenario_test()
        self.run_Congestion_search_route_test()
        self.run_Congestion_search_position_test()
        self.run_Congestion_thread_safety_test()
        self.run_Congestion_perf_test()
        self.run_Congestion_memory_test()
        self.run_Congestion_np_test()

    def run_Congestion_thread_safety_test(self):

		if hasattr (self.cfg.dev[self.testName], 'temp_bundle'):
			threadsafetytest = self.cfg.details.settings[self.platform][self.testName].Congestion_THREADSAFETY_TEST
			rawcmd = Template(threadsafetytest)
			Congestion_perf_exe =  self.cfg.dev[self.testName].Congestion_perf_exe
			Congestion_perf_server = self.cfg.dev[self.testName].Congestion_perf_server
			temp_bundle = self.basedir + self.cfg.dev[self.testName].temp_bundle
			geoapis = self.basedir + self.cfg.dev[self.testName].geoapis
			tmc = self.basedir + self.cfg.dev[self.testName].tmc
			logEvent("Running thread safety test ... ")
			cmd = rawcmd.substitute(basedir=self.basedir,
									  Congestion_perf_exe=Congestion_perf_exe,
									  tmc=tmc,
									  Congestion_perf_server=Congestion_perf_server,
									  geoapis=geoapis,
									  temp_bundle=temp_bundle,
									  )
			cmd = os.path.normpath(cmd)
			logEvent("Running: " + cmd)
			os.system(cmd)
			exit_code = subprocess.call(cmd)
			if exit_code < 0:
				logEvent("Application exit code is < 0. Application crashed")
			else:
				logEvent("Application not crashed")

    def run_Congestion_memory_test(self):


		if hasattr (self.cfg.dev[self.testName], 'template_xml') & hasattr(self.cfg.dev[self.testName], 'route_data'):
			Congestion_xml_template_file = self.datadir + self.cfg.dev[self.testName].template_xml
			logEvent('Congestion_xml_template:' + Congestion_xml_template_file)
			scenario = self.cfg.dev[self.testName].scenario
			template_string = Format(Congestion_xml_template_file)
			dire = self.datadir
			substituted_string = template_string.fmt % (scenario, dire, dire, dire, dire, dire, dire, dire, dire) + '\n'
			substitution_xml = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + 'substitution_xml.xml'
			r = open(substitution_xml, 'w')
			r.write(substituted_string)
			r.close()

			logEvent("Running Memory Tests ... ")

			Congestion_memory_test_cmd = self.cfg.details.settings[self.platform][self.testName].Congestion_MEMORY_TEST
			rawcmd = Template(Congestion_memory_test_cmd)
			Congestion_perf_exe =  self.cfg.dev[self.testName].Congestion_perf_exe
			mdata = self.datadir + self.cfg.dev[self.testName].mdata
			Congestion_perf_server = self.cfg.dev[self.testName].Congestion_perf_server
			xml_data_1 = self.datadir + self.cfg.dev[self.testName].xml_data_1

			for run_id in range (0, 63):
				cmd = rawcmd.substitute(basedir=self.basedir,
										Congestion_perf_exe=Congestion_perf_exe,
										mdata=mdata,
										Congestion_perf_server=Congestion_perf_server,
										xml_data_1=xml_data_1,
										log_name = "requestCongestion.log",
										run_id=run_id)
				cmd = os.path.normpath(cmd)
				logEvent("Running Request Congestion Scn: " + cmd)
				os.system(cmd)

			self.calculateAggregation("requestCongestion.log")

			xml_data_2 = self.datadir + self.cfg.dev[self.testName].xml_data_2

			for run_id in range (0, 63):
				cmd = rawcmd.substitute(basedir=self.basedir,
										Congestion_perf_exe=Congestion_perf_exe,
										mdata=mdata,
										 Congestion_perf_server=Congestion_perf_server,
										xml_data_1=xml_data_2,
										log_name = "displayCongestion.log",
										run_id=run_id)
				cmd = os.path.normpath(cmd)
				logEvent("Running Display Congestion Scn: " + cmd)
				os.system(cmd)

			self.calculateAggregation("displayCongestion.log")

			xml_data_4 = self.datadir + self.cfg.dev[self.testName].xml_data_4

			for run_id in range (0, 63):
				cmd = rawcmd.substitute(basedir=self.basedir,
									  Congestion_perf_exe=Congestion_perf_exe,
									  mdata=mdata,
									  Congestion_perf_server=Congestion_perf_server,
									  xml_data_1=xml_data_4,
									  log_name ="populateCongestiondb.log",
									  run_id=run_id)
			cmd = os.path.normpath(cmd)
			logEvent("Running Populate Congestion DB Scn: " + cmd)
			os.system(cmd)
			self.calculateAggregation("populateCongestiondb.log")

			xml_data_3 = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + 'substitution_xml.xml'

			for run_id in range (0, 1):
				cmd = rawcmd.substitute(basedir=self.basedir,
										Congestion_perf_exe=Congestion_perf_exe,
										mdata=mdata,
										Congestion_perf_server=Congestion_perf_server,
										xml_data_1=xml_data_3,
										log_name = "movingdisplayCongestion.log",
										run_id=run_id)
			cmd = os.path.normpath(cmd)
			logEvent("Running Moving display Congestion Scn: " + cmd)
			os.system(cmd)

			self.calculateAggregation("movingdisplayCongestion.log")

			scenario='displayCongestiononroute'

			substituted_string = template_string.fmt % (scenario, dire, dire, dire, dire, dire, dire, dire, dire) + '\n'
			substitution_xml = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + 'substitution_xml.xml'
			r = open(substitution_xml, 'w')
			r.write(substituted_string)
			r.close()

			xml_data_5 = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + 'substitution_xml.xml'
			for run_id in range (0, 1):
				cmd = rawcmd.substitute(basedir=self.basedir,
										Congestion_perf_exe=Congestion_perf_exe,
										mdata=mdata,
										Congestion_perf_server=Congestion_perf_server,
										xml_data_1=xml_data_5,
										log_name = "displayCongestiononroute.log",
										run_id=run_id)
				cmd = os.path.normpath(cmd)
			logEvent("Running display Congestion on route: " + cmd)
			os.system(cmd)

			self.calculateAggregation("displayCongestiononroute.log")

			scenario='movingrequestCongestion'
			substituted_string = template_string.fmt % (scenario, dire, dire, dire, dire, dire, dire, dire, dire) + '\n'
			substitution_xml = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + 'substitution_xml.xml'
			r = open(substitution_xml, 'w')
			r.write(substituted_string)
			r.close()


			xml_data_6 = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + 'substitution_xml.xml'

			for run_id in range (0, 1):
				cmd = rawcmd.substitute(basedir=self.basedir,
										Congestion_perf_exe=Congestion_perf_exe,
										mdata=mdata,
										Congestion_perf_server=Congestion_perf_server,
										log_name = "movingrequestCongestion.log",
										xml_data_1=xml_data_6,
										run_id=run_id)
			cmd = os.path.normpath(cmd)
			logEvent("Running moving request Congestion Scn: " + cmd)
			os.system(cmd)
			self.calculateAggregation("movingrequestCongestion.log")

    def calculateAggregation(self, log_name):
        out_path = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + log_name
        f = open(out_path, 'r')
        sum_of_memory_usage_peak = 0
        count = 0
        stored_floats = []
        print 'Calculating ' , log_name
        for line in f:
            if 'Memory usage peak in MB: ' in line:
                peak = float(line.split(' ')[-1])
                stored_floats.append(peak)
                sum_of_memory_usage_peak = sum_of_memory_usage_peak + peak
                count +=1
        if sum_of_memory_usage_peak > 0 :
            print 'Total Memory usage peak: ', sum_of_memory_usage_peak
            print 'Count: ', count
            print 'Average consumption:  ', (sum_of_memory_usage_peak / count)
            print 'Minimum: ', min(stored_floats)
            print 'Maximum: ', max(stored_floats)
            stored_floats.sort()
            print '98th Percentile: ', self.calc_percentile(stored_floats, P=0.98)

    def calc_percentile(self, N, P):
        n = int(round(P * len(N) + 0.5))
        return N[n-1]


    def run_Congestion_perf_test(self):
          logEvent("Running Performance Tests ... ")
          Congestion_perf_test_cmd = self.cfg.details.settings[self.platform][self.testName].Congestion_PERFORMANCE_TEST
          rawcmd = Template(Congestion_perf_test_cmd)
          Congestion_perf_exe =  self.cfg.dev[self.testName].Congestion_perf_exe
          mdata = self.datadir + self.cfg.dev[self.testName].mdata
          Congestion_perf_server = self.cfg.dev[self.testName].Congestion_perf_server
          route_data = self.datadir + self.cfg.dev[self.testName].route_data
          cmd = rawcmd.substitute(basedir=self.basedir,
                                  Congestion_perf_exe=Congestion_perf_exe,
                                  mdata=mdata,
                                  Congestion_perf_server=Congestion_perf_server,
                                  route_data=route_data)
          cmd = os.path.normpath(cmd)
          logEvent("Running: " + cmd)
          os.system(cmd)

    def run_tmc_decoder_scenario_test(self):
        logEvent('Running tmc_decoder_scenario_tests - launching location tests')

        tmc_decoder_test_exe = self.cfg.dev[self.testName].win_tmc_decoder_test_exe
        mdata = self.datadir + self.cfg.dev[self.testName].mdata
        stats_file = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir + '\stats_scenarios.txt'

        stats_handle = open(stats_file, 'a')

        scenarios_folder = self.datadir + self.cfg.dev[self.testName].scenarios_reference_folder
        logEvent(scenarios_folder)
        files = os.listdir(scenarios_folder)
        out_folder = self.basedir + self.cfg.details.settings[self.platform][self.testName].out_folder

        output = self.basedir + self.cfg.details.settings[self.platform][self.testName].output + '/'
        error =  self.basedir + self.cfg.details.settings[self.platform][self.testName].error  + '/'
        stats =  self.basedir + self.cfg.details.settings[self.platform][self.testName].stats  + '/'

        for file in files:
            tmc_decoder_test_cmd = self.cfg.details.settings[self.platform][self.testName].TMC_DECODER_SCENARIO_TEST
            rawcmd = Template(tmc_decoder_test_cmd)

            output_file = output + file
            error_file =  error  + file
            stats_file =  stats  + file

            scenario_file = scenarios_folder + '/' + file

            cmd = rawcmd.substitute(tmc_decoder_test_exe=tmc_decoder_test_exe,
                                    input=input,
                                    basedir=self.basedir,
                                    mdata=mdata,
                                    output=output,
                                    error=error,
                                    stats_file=stats_file,
                                    scenario_file=scenario_file)

            logEvent('Running : ' + cmd)
            os.system(cmd)

        scenarios_log = self.cfg.details.settings[self.platform][self.testName].scenarios_log
        rawlog = Template(scenarios_log)
        log = rawlog.substitute(basedir=self.basedir)

        process_files(out_folder, scenarios_folder, log)
        self.generateXML(log, 'scenarios')

    def run_Congestion_search_route_test(self):
        tss_cmd = self.cfg.details.settings[self.platform][self.testName].Congestion_SEARCH_rTeam_TEST
        Congestion_exe = self.cfg.dev[self.testName].win_Congestion_search_tester_exe
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + self.cfg.details.settings.common.datadir

        mdata = self.datadir + self.cfg.dev[self.testName].mdata
        tss_server = self.cfg.dev[self.testName].tss_server
        suites_dir = self.datadir + self.cfg.dev[self.testName].suites_dir
        resource_db = self.basedir + '/resource.db'
        mwconfig_xml = self.basedir + '/mwconfig.xml'

        suites = xmllist = glob.glob(suites_dir + '/*.xml')
        for suite in suites:
            rawcmd = Template(tss_cmd)
            suite_log_name = getSuiteName(suite) + '.log'
            cmd = rawcmd.substitute(Congestion_search_tester_exe=Congestion_exe,
                                    basedir=self.basedir,
                                    mdata=mdata,
                                    tss_server=tss_server,
                                    suite=suite,
                                    resource_db=resource_db,
                                    mwconfig_xml=mwconfig_xml,
                                    log=suite_log_name)

            logEvent('Running :' + cmd)
            os.system(cmd)

        stats_log_dir = self.basedir + self.cfg.details.settings[self.platform][self.testName].rTeam_logs
        self.generateXML(stats_log_dir, 'rTeam_tests')

    def get_params(self, node):
        childNodes = node.childNodes
        (radius, yPos, xPos, fl_avail, inc_avail) = (
                                         childNodes[1].firstChild.data,
                                         childNodes[3].firstChild.data,
                                         childNodes[5].firstChild.data,
                                         childNodes[7].firstChild.data,
                                         childNodes[9].firstChild.data
                                         )
        return (radius, yPos, xPos, fl_avail, inc_avail)

    def run_Congestion_search_position_test(self):
        tss_cmd = self.cfg.details.settings[self.platform][self.testName].Congestion_SEARCH_POSITION_TEST
        Congestion_exe = self.cfg.dev[self.testName].win_Congestion_search_tester_exe
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + self.cfg.details.settings.common.datadir

        mdata = self.datadir + self.cfg.dev[self.testName].mdata
        tss_server = self.cfg.dev[self.testName].tss_server
        resource_db = self.basedir + '/res.database'
        mwconfig_xml = self.basedir + '/conf.xml'

        coverage_suites = self.datadir + self.cfg.dev[self.testName].coverage_suites
        country_suites = glob.glob(coverage_suites + '*.xml')

        for suites_xml in country_suites:

            rawcmd = Template(tss_cmd)

            fsock = open(suites_xml)
            xmldoc = minidom.parse(fsock)
            grammarNode = xmldoc.firstChild
            l = len(grammarNode.childNodes )
            for i in range(1,l,2):
                refNode = grammarNode.childNodes[i]
                (radius, yPos, xPos, water_available, events_available) = self.get_params(refNode)
                water = '0'
                events = '0'
                if water_available == 'true':
                    water = '1'
                if events_available == 'true':
                    events = '1'
                suite_log_name = getSuiteName(suites_xml) + '_'+ water + '_' + events + '_radius_'+ radius +'.log'
                cmd = rawcmd.substitute(Congestion_search_tester_exe=Congestion_exe,
                                    basedir=self.basedir,
                                    mdata=mdata,
                                    tss_server=tss_server,
                                    resource_db=resource_db,
                                    conf_xml=conf_xml,
                                    radius=radius,
                                    yPos=yPos,
                                    xPos=xPos,
                                    log=suite_log_name)

                logEvent('Running :' + cmd)
                os.system(cmd)

            logs_dir = self.basedir + self.cfg.details.settings[self.platform][self.testName].position_logs

        self.generateXML(logs_dir, 'position_tests')

###################################################################################################

    ###For testing non preloaded maps for Congestion
    ## get the configuration files from svn that contains the params
    ## run it
    def run_Congestion_np_test(self):
        Congestion_tile_tester_cmd = self.cfg.details.settings[self.platform][self.testName].Congestion_np_MAP_TEST
        Congestion_exe = self.cfg.dev[self.testName].win_Congestion_tile_tester_exe
        server = self.cfg.dev[self.testName].server
        resource_db = self.basedir + '/res.database'
        conf_xml = self.basedir + '/conf.xml'
        param_cfg_path = self.datadir + self.cfg.dev[self.testName].np_param_path
        files = os.listdir(param_cfg_path)
        tile_cmd = self.cfg.details.settings[self.platform][self.testName].Congestion_np_MAP_TEST
        for file in files:
            rawcmd = Template(tile_cmd)
            suite_log_name = file.replace('.', '_') + '.log'
            cmd = rawcmd.substitute(Congestion_tile_tester_exe=Congestion_exe,
                                    cfg=param_cfg_path+'/' + file,
                                    basedir=self.basedir,
                                    resource_db=resource_db,
                                    conf_xml=conf_xml,
                                    log_name=suite_log_name )

            logEvent('Running :' + cmd)
            os.system(cmd)

        self.generateXML( suite_log_name, 'np_gb_tests')

###################################################################################################

    def parse_np_log(self):

        log_dir = self.basedir + self.cfg.details.settings[self.platform][self.testName].results_dir
        logEvent( log_dir )
        logs = glob.glob(log_dir + '/np*.log')

        result = {}

        for log in logs:
            file = open(log, 'r')
            lines = file.readlines()
            file.close()
            (dirName, fileName) = os.path.split(log)
            kkey = fileName.replace('_cfg.log', '.cfg')
            if not result.has_key(kkey):
                result[kkey] = {'passed':'0'}
            for line in lines:
                if 'ERROR' in line:
                    result[kkey]['ERROR'] = line
                else:
                    if "*****total original in screen " in line:
                        original_in_screen = line.split(' ')[4]
                        result[kkey]['original_in_screen'] = original_in_screen
                        original_in_screen = int(original_in_screen)
                        if original_in_screen == 0:
                            result[kkey]['passed'] = '1'
                    elif "*****total water " in line:
                        water = line.split(' ')[2]
                        result[kkey]['water'] = water.strip()
                    elif "*****total events " in line:
                        events = line.split(' ')[2]
                        result[kkey]['events'] = events.strip()
                    elif "*****total decoded events " in line:
                        decoded_events = line.split(' ')[3]
                        result[kkey]['decoded_events'] = decoded_events.strip()
                    elif "*****total decoded water " in line:
                        decoded_water = line.split(' ')[3]
                        result[kkey]['decoded_water'] = decoded_water.strip()
                    elif "*****total original " in line:
                        original = line.split(' ')[2]
                        result[kkey]['original'] = original.strip()
                    elif "Time Taken for decoding(ms): " in line:
                        time_taken = line.split(' ')[4]
                        result[kkey]['time_taken'] = time_taken.strip()

        return result

###################################################################################################


    def parse(self):
        pass

    def convertToXML(self):
        pass

    #Function to accumulate all the counts !!!
    def getAllCounts(self, stats_file):
        myvar = open(stats_file, 'r')
        lst = myvar.readlines()
        myvar.close()

        total = 0
        decoded = 0
        original = 0

        for line in lst:
            sub_total, sub_decoded, sub_original = line.split(',')[2:5]
            total = total + int(sub_total)
            decoded = decoded + int(sub_decoded)
            original = original + int(sub_original)

        return (total, decoded, original)


    def get_ref_location_stats_dict(self):
        #this ref file is in svn, keep checking if there were mismatches in the failure cases.
        ref_stats = self.datadir + self.cfg.dev[self.testName].reference_stats
        ref_dict = {}
        f = open(ref_stats, 'r')
        lines = f.readlines()
        for line in lines:
            testcase, dummy, total, converted, unconverted = line.split(',')[0:5]
            if not ref_dict.has_key(testcase):
                ref_dict[testcase] = {'total' : total,
                                      'converted' : converted,
                                      'unconverted' : unconverted
                                      }
        return ref_dict

    def get_test_counts(self, result_file):
        myvar = open(result_file, 'r')
        lst = myvar.readlines()
        ref_dict = self.get_ref_location_stats_dict()
        passed = 0
        failed = 0
        for line in lst:
            testcase, dummy, total, converted, unconverted = line.split(',')[0:5]
            if  ref_dict[testcase]['total'] == total and ref_dict[testcase]['converted'] == converted and ref_dict[testcase]['unconverted'] == unconverted :
                passed = passed + 1
            else:
                failed = failed + 1
        return (passed, failed)

    def generateXML(self, stats_file, report_type, last_line=None):
        xml = self.basedir + self.cfg.details.settings[self.platform][self.testName].xml_report_dir + '/Congestion_' + report_type + '.xml'
        xml_log_file = open(xml, 'w')
        xml_log_file.write("<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n")

        if report_type == 'scenarios':
            summary = get_summary_for_decoder_scenario_tests(stats_file)

            classname = self.datadir + self.cfg.dev[self.testName].scenarios_reference_folder
            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(summary['failed'])+"\" tests=\"" + str(summary['passed']) +"\" name=\"Congestion\">\n")

            for suite_file in summary['pass_suite']:
                name = getSuiteName(suite_file)
                suite = os.path.dirname(suite_file)
                xml_log_file.write("<testcase classname=\"" + suite + "\" name=\"" + name +"\" />\n")

            if len(summary['fail_suite'].keys()) > 0:
                for suite_file in summary['fail_suite'].keys():
                    name = getSuiteName(suite_file)
                    suite = os.path.dirname(suite_file)
                    xml_log_file.write("<testcase classname=\"" + suite + "\" name=\"" + name + "\" >\n")
                    xml_log_file.write("<failure>" + summary['fail_suite'][suite_file] + "</failure>\n")
                    xml_log_file.write("</testcase>\n")

        elif report_type == 'position_tests': #Parse the directory not file in this case
            result = self.get_parsed_resluts(stats_file)
            passed_suites = []
            failed_suites = []
            pass_count = 0
            fail_count = 0

            classname = self.datadir + self.cfg.dev[self.testName].coverage_suites
            for suite in result.keys():
                suite_name = suite + '.xml'
                for radius in result[suite]:
                    water = result[suite][radius]['water']
                    converted_water = result[suite][radius]['converted_water']
                    events = result[suite][radius]['events']
                    converted_events = result[suite][radius]['converted_events']
                    water_supported = int(result[suite][radius]['water_available'])
                    events_supported = int(result[suite][radius]['events_available'])
                    water_match = True
                    events_match = True
                    s = "<testcase classname=\"" + classname + "\" name=\"" + suite_name + "\" radius=\"" + radius + "\" water=\"" + water + "\" converted_water=\"" + str(converted_water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) +"\" >"

                    if water_supported == 1:
                        if water != converted_water or water == '0':
                            water_match = False
                    if events_supported == 1:
                        if events != converted_events or events == '0':
                            events_match = False

                    if water_match == True and events_match == True:
                        passed_suites.append(s)
                        passed_suites.append("</testcase>")
                        pass_count += 1
                    else:
                        failed_suites.append(s)
                        failed_suites.append("<failure>")
                        failed_suites.append("<radius>" + radius + "</radius>")
                        failed_suites.append("<water_available>" + str(water_supported) + "</water_available>")
                        failed_suites.append("<events_available>" + str(events_supported) + "</events_available>")
                        failed_suites.append("</failure>")
                        failed_suites.append("</testcase>")
                        fail_count += 1

            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(fail_count)+"\" tests=\"" + str(pass_count) +"\" name=\"Congestion\">\n")
            xml_log_file.write('\n'.join(passed_suites))
            xml_log_file.write('\n'.join(failed_suites))

        elif report_type == 'rTeam_tests': #Parse the directory not file in this case
            (failed, passed) = self.get_total_counts_for_tss_tests(report_type, stats_file)

            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(failed)+"\" tests=\"" + str(passed) +"\" name=\"Congestion\">\n")

            logs = glob.glob(stats_file + '/*.log')
            classname = self.datadir + self.cfg.dev[self.testName].suites_dir
            for log in logs:
                (suite, water, events, converted_events, converted_water) = self.get_counts_for_tss_tests(log)
                if water > 0 and events > 0 and converted_events > 0 and converted_water > 0:
                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" water=\"" + str(water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) + "\" converted_water=\"" + str(converted_water) +"\" />\n")
                else:
                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" water=\"" + str(water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) + "\" converted_water=\"" + str(converted_water) +"\" >\n")
                    xml_log_file.write("<failure>FAILED</failure>\n")
                    xml_log_file.write("</testcase>\n")

        elif report_type == 'np_gb_tests':
            result = self.parse_np_log()
            pass_count = 0
            fail_count = 0

            for k in result:
                if result[k]['passed'] == '1':
                    pass_count = pass_count + 1
                else:
                    fail_count = fail_count + 1
            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(fail_count)+"\" tests=\"" + str(pass_count) +"\" name=\"Congestion\">\n")
            classname = self.datadir + self.cfg.dev[self.testName].np_param_path

            for suite in result:
                if result[suite]['passed'] == '1':
                    water = result[suite]['water']
                    events = result[suite]['events']
                    converted_events = result[suite]['converted_events']
                    converted_water = result[suite]['converted_water']
                    unconverted = result[suite]['unconverted']
                    time_taken = result[suite]['time_taken']
                    unconverted_in_screen = result[suite]['unconverted_in_screen']

                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" water=\"" + str(water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) + "\" converted_water=\"" + str(converted_water) + "\" unconverted=\"" + str(unconverted) + "\" time_taken=\"" + str(time_taken) + "\" unconverted_in_screen=\"" + str(unconverted_in_screen) + "\" />\n")
                else:
                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" >\n")
                    error = result[suite]['ERROR']
                    xml_log_file.write("<failure>" + error + "</failure>\n")
                    xml_log_file.write("</testcase>\n")

        xml_log_file.write("</testsuite>")
        xml_log_file.close()

    def get_parsed_resluts(self, stats_file):
        logs = glob.glob(stats_file + '*.log')
        result = {}
        for log in logs:
            name = getSuiteName(log)
            name = name.replace('.log', '')
            params = name.split('_')
            country = params[0]
            region = params[1]
            radius = params[-1]
            events_available = params[-3]
            water_available = params[-4]

            if len(params) == 6:
                kkey = '_'.join([country, region])
            else:
                kkey = country

            if not result.has_key(kkey):
                    result[kkey] = {radius: {'water_available': water_available, 'events_available':events_available} }
            else:
                if not result[kkey].has_key(radius):
                    result[kkey][radius] = {'water_available': water_available, 'events_available':events_available}

            f = open(log, 'r')
            for line in f:
                l = line.strip()
                if "*****total water " in line:
                    water = line.split(' ')[2]
                    result[kkey][radius]['water'] = water.strip()
                elif "*****total events " in line:
                    events = line.split(' ')[2]
                    result[kkey][radius]['events'] = events.strip()
                elif "*****total converted events " in line:
                    converted_events = line.split(' ')[3]
                    result[kkey][radius]['converted_events'] = converted_events.strip()
                elif "*****total converted water " in line:
                    converted_water = line.split(' ')[3]
                    result[kkey][radius]['converted_water'] = converted_water.strip()
        return result

    def get_total_counts_for_tss_tests(self, report_type, logs_dir):
        passed = 0
        failed = 0

        if 'position' in report_type:
            (suite, water, events, converted_events, converted_water) = self.get_counts_for_tss_tests(logs_dir)
            if water > 0 and events > 0 and converted_events > 0 and converted_water > 0:
                passed = passed + 1
            else:
                failed = failed + 1
        else: #rTeam
            logs = glob.glob(logs_dir + '/*.log')

            for log in logs:
                (suite, water, events, converted_events, converted_water) = self.get_counts_for_tss_tests(log)
                if water > 0 and events > 0 and converted_events > 0 and converted_water > 0:
                    passed = passed + 1
                else:
                    failed = failed + 1

        return (failed, passed)


    def get_counts_for_tss_tests(self, log_file):
        myvar = open(log_file, 'r')
        lst = myvar.readlines()
        suite = ''
        water = 0
        events = 0
        converted_events = 0
        converted_water = 0

        for line in lst:
            if 'xml' in line:
                suite = getSuiteName(line)
            if '*****total water' in line:
                water = int(line.split(' ')[2])
            if '*****total events' in line:
                events = int(line.split(' ')[2])
            if '*****total converted events' in line:
                converted_events = int(line.split(' ')[3])
            if '*****total converted water' in line:
                converted_water = int(line.split(' ')[3])

        myvar.close()

        return (suite, water, events, converted_events, converted_water)

    def generateConsolidationReport(self):
        pass

class gadgetCongestion(gadgetExecutor):
    def __init__(self, gadgetSimulator_ip_address=None):
        gadgetExecutor.__init__(self, 'Congestion')
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + self.cfg.details.settings.common.datadir
        self.gadgetSimulator_ip_address = gadgetSimulator_ip_address

    def change_drive(self, suite):
        l = list(suite)
        l[0] = self.cfg.details.settings[self.platform].gadgetSimulator_drive
        return ''.join(l)

    def run_tmc_decoder_scenario_test(self):
        logEvent('Running tmc_decoder_scenario_tests - launching scenario tests')
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].scenario_filename
        f = open(file, 'w')
        cmds = self.cfg.details.settings[self.platform][self.testName].precmds
        f.write('open-device ' + self.gadgetSimulator_ip_address + '\n')
        f.write('\n'.join(cmds) + '\n')

        self.exe = self.cfg.dev[self.testName].gadget_tmc_decoder_test_exe
        self.mdata = self.cfg.dev[self.testName].mdata
        scenarios_folder = self.datadir + self.cfg.dev[self.testName].scenarios_reference_folder

        self.suites = os.listdir(scenarios_folder)

        logEvent(self.testName + ' Suites: ')
        for s in self.suites:
            logEvent( scenarios_folder + s)

        curcmd = self.cfg.details.settings[self.platform][self.testName].tmc_decoder_scenario_cmd
        for suite in self.suites:
            rawcmd = Template(curcmd)
            p = self.change_drive(scenarios_folder)
            csvsuite = p + suite

            cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir, mdata=self.mdata, scenario_file=csvsuite, suite=suite)

            currcmdslist.append('echo ' + csvsuite)
            currcmdslist.append('echo ' + cmd)

            currcmdslist.append(cmd.replace('/', '\\'))

        f.write('\n'.join(currcmdslist)  + '\n')

        cmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        f.write('\n'.join(cmds) + '\n')
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].scenario_CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        logEvent('Running  ' + cmd)
        os.system(cmd)

    def get_params(self, node):
        childNodes = node.childNodes
        (radius, yPos, xPos, fl, inc) = (
                                         childNodes[1].firstChild.data,
                                         childNodes[3].firstChild.data,
                                         childNodes[5].firstChild.data,
                                         childNodes[7].firstChild.data,
                                         childNodes[9].firstChild.data
                                         )
        return (radius, yPos, xPos, fl, inc)

    def run_Congestion_search_position_test(self):
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].tss_position_filename
        f = open(file, 'w')
        cmds = self.cfg.details.settings[self.platform][self.testName].precmds
        f.write('open-device ' + self.gadgetSimulator_ip_address + '\n')
        f.write('\n'.join(cmds) + '\n')

        self.exe = self.cfg.dev[self.testName].gadget_Congestion_search_tester_exe
        self.mdata = self.datadir + self.cfg.dev[self.testName].mdata
        tss_server = self.cfg.dev[self.testName].tss_server
        resource_db = self.cfg.details.settings[self.platform][self.testName].resource_db
        conf_xml = self.cfg.details.settings[self.platform][self.testName].conf_xml


        tss_cmd = self.cfg.details.settings[self.platform][self.testName].tss_position_test_cmd
        coverage_suites = self.datadir + self.cfg.dev[self.testName].coverage_suites
        country_suites = glob.glob(coverage_suites + '*.xml')

        for suites_xml in country_suites:
            fsock = open(suites_xml)
            xmldoc = minidom.parse(fsock)
            grammarNode = xmldoc.firstChild
            l = len(grammarNode.childNodes )

            rawcmd = Template(tss_cmd)
            for i in range(1,l,2):
                refNode = grammarNode.childNodes[i]
                (radius, yPos, xPos, fl, inc) = self.get_params(refNode)
                mdata = self.change_drive(self.mdata)
                cmd = rawcmd.substitute(exe=self.exe,
                                    basedir=self.basedir,
                                    mdata=mdata,
                                    tss_server=tss_server,
                                    resource_db=resource_db,
                                    conf_xml=conf_xml,
                                    radius=radius,
                                    yPos=yPos,
                                    xPos=xPos)

                currcmdslist.append('echo SUITE:' + suites_xml)
                currcmdslist.append('echo RADIUS:' + radius)
                currcmdslist.append('echo waterSUPPORTED:' + fl)
                currcmdslist.append('echo eventsSUPPORTED:' + inc)
                currcmdslist.append(cmd)

        f.write('\n'.join(currcmdslist)  + '\n')

        cmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        f.write('\n'.join(cmds) + '\n')
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].tss_position_CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        logEvent('Running  ' + cmd)
        os.system(cmd)

        log_file = self.basedir + self.cfg.details.settings[self.platform][self.testName].tss_position_log
        self.generateXML(log_file, 'position_tests')

    def run_Congestion_search_route_test(self):
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].tss_route_filename
        f = open(file, 'w')
        cmds = self.cfg.details.settings[self.platform][self.testName].precmds
        f.write('open-device ' + self.gadgetSimulator_ip_address + '\n')
        f.write('\n'.join(cmds) + '\n')

        self.exe = self.cfg.dev[self.testName].gadget_Congestion_search_tester_exe
        self.mdata = self.datadir + self.cfg.dev[self.testName].mdata
        tss_server = self.cfg.dev[self.testName].tss_server
        resource_db = self.cfg.details.settings[self.platform][self.testName].resource_db
        conf_xml = self.cfg.details.settings[self.platform][self.testName].conf_xml

        tss_cmd = self.cfg.details.settings[self.platform][self.testName].tss_route_test_cmd
        suites_dir = self.datadir + self.cfg.dev[self.testName].suites_dir

        suites = xmllist = glob.glob(suites_dir + '/*.xml')
        for suite in suites:
            rawcmd = Template(tss_cmd)
            suite_log_name = getSuiteName(suite) + '.log'
            mdata = self.change_drive(self.mdata)
            st = self.change_drive(suite)
            suite_log_name = self.change_drive(suite_log_name)

            cmd = rawcmd.substitute(exe=self.exe,
                                    basedir=self.basedir,
                                    mdata=mdata,
                                    tss_server=tss_server,
                                    suite=st,
                                    resource_db=resource_db,
                                    conf_xml=conf_xml,
                                    log=suite_log_name)

            currcmdslist.append('echo ' + cmd)
            currcmdslist.append(cmd)

        f.write('\n'.join(currcmdslist)  + '\n')

        cmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        f.write('\n'.join(cmds) + '\n')
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].tss_route_CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        logEvent('Running  ' + cmd)
        os.system(cmd)

        log_file = self.basedir + self.cfg.details.settings[self.platform][self.testName].tss_route_log
        self.generateXML(log_file, 'rTeam_tests')

    def run(self):
        self.createTestDirs()
        self.run_tmc_decoder_scenario_test()
        self.run_Congestion_search_position_test()
        self.run_Congestion_search_route_test()
        self.run_Congestion_np_test()
        self.run_Congestion_perf_test()

    def run_Congestion_perf_test(self):
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].Congestion_perf_filename
        f = open(file, 'w')
        cmds = self.cfg.details.settings[self.platform][self.testName].precmds
        f.write('open-device ' + self.gadgetSimulator_ip_address + '\n')
        f.write('\n'.join(cmds) + '\n')

        self.exe = self.cfg.dev[self.testName].gadget_Congestion_perf_exe
        self.mdata = self.datadir + self.cfg.dev[self.testName].mdata

        suites_path = self.datadir + self.cfg.dev[self.testName].route_data
        suites = self.change_drive(suites_path)
        self.mdata = self.change_drive(self.mdata)
        t_server = self.cfg.dev[self.testName].Congestion_perf_server

        Congestion_perf_cmd = self.cfg.details.settings[self.platform][self.testName].Congestion_perf_cmd
        rawcmd = Template(Congestion_perf_cmd)

        cmd = rawcmd.substitute(exe=self.exe,
                                mdata=self.mdata,
                                basedir=self.basedir,
                                server=t_server,
                                route_data=suites)

        currcmdslist.append(cmd)

        f.write('\n'.join(currcmdslist)  + '\n')

        cmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        f.write('\n'.join(cmds) + '\n')
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].Congestion_perf_CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        logEvent('Running  ' + cmd)
        os.system(cmd)

    def run_Congestion_np_test(self):
        currcmdslist = []

        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].np_filename
        f = open(file, 'w')
        cmds = self.cfg.details.settings[self.platform][self.testName].precmds
        f.write('open-device ' + self.gadgetSimulator_ip_address + '\n')
        f.write('\n'.join(cmds) + '\n')

        self.exe = self.cfg.dev[self.testName].gadget_Congestion_tile_tester_exe
        self.mdata = self.datadir + self.cfg.dev[self.testName].mdata

        param_cfg_path = self.datadir + self.cfg.dev[self.testName].np_param_path

        tile_cmd = self.cfg.details.settings[self.platform][self.testName].np_gb_cmd
        files = os.listdir(param_cfg_path)

        for file in files:
            rawcmd = Template(tile_cmd)

            log_dir = self.basedir + self.cfg.details.settings.common.gadget_raw_dir
            log_dir = os.path.normcase(log_dir)

            cfg_path = self.change_drive(param_cfg_path)

            suite_log_name = log_dir + '/' + file.replace('.', '_') + '.log'
            cmd = rawcmd.substitute(exe=self.exe,
                                    cfg=cfg_path +'/' + file,
                                    basedir=self.basedir,
                                    log_name=suite_log_name )

            currcmdslist.append('echo SUITE:' + file)
            currcmdslist.append(cmd)
            currcmdslist.append('echo SUITEEND')

        f.write('\n'.join(currcmdslist)  + '\n')

        cmds = self.cfg.details.settings[self.platform][self.testName].postcmds
        f.write('\n'.join(cmds) + '\n')
        f.close()

        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].np_CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        logEvent('Running  ' + cmd)
        os.system(cmd)

        log_file = self.basedir + self.cfg.details.settings[self.platform][self.testName].np_log
        self.generateXML(log_file, 'np_gb_tests')

    def parse(self):
        pass

    def convertToXML(self):
        scenarios_folder = self.datadir + self.cfg.dev[self.testName].scenarios_reference_folder
        out_folder = self.basedir + self.cfg.details.settings[self.platform][self.testName].out_folder

        scenarios_log = self.cfg.details.settings[self.platform][self.testName].scenarios_log
        rawlog = Template(scenarios_log)
        log = rawlog.substitute(basedir=self.basedir)

        process_files(out_folder, scenarios_folder, log)
        self.generateXML(log, 'scenarios')

    #Function to accumulate all the counts !!!
    def getAllCounts(self, stats_file):
        myvar = open(stats_file, 'r')
        lst = myvar.readlines()
        myvar.close()

        total = 0
        converted = 0
        unconverted = 0

        for line in lst:
            sub_total, sub_converted, sub_unconverted = line.split(',')[2:5]
            total = total + int(sub_total)
            converted = converted + int(sub_converted)
            unconverted = unconverted + int(sub_unconverted)

        return (total, converted, unconverted)

    def generateXML(self, stats_file, report_type, last_line=None):
        xml = self.basedir + self.cfg.details.settings[self.platform][self.testName].xml_report_dir + '/Congestion_' + report_type + '.xml'
        xml_log_file = open(xml, 'w')
        xml_log_file.write("<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n")

        if report_type == 'scenarios':
            summary = get_summary_for_decoder_scenario_tests(stats_file)

            classname = self.datadir + self.cfg.dev[self.testName].scenarios_reference_folder
            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(summary['failed'])+"\" tests=\"" + str(summary['passed']) +"\" name=\"Congestion\">\n")

            for suite_file in summary['pass_suite']:
                name = getSuiteName(suite_file)
                suite = os.path.dirname(suite_file)
                xml_log_file.write("<testcase classname=\"" + suite + "\" name=\"" + name +"\" />\n")

            for suite_file in summary['fail_suite']:
                name = getSuiteName(suite_file)
                suite = os.path.dirname(suite_file)
                xml_log_file.write("<testcase classname=\"" + suite + "\" name=\"" + name + "\" >\n")
                xml_log_file.write("<failure>FAILED</failure>\n")
                xml_log_file.write("</testcase>\n")

        elif report_type == 'position_tests': #Parse the directory not file in this case
            result = self.get_tss_position_results(stats_file)
            passed_suites = []
            failed_suites = []
            pass_count = 0
            fail_count = 0

            classname = self.datadir + self.cfg.dev[self.testName].coverage_suites
            for suite in result.keys():
                suite_name = suite + '.xml'
                for radius in result[suite]:
                    water = result[suite][radius]['water']
                    converted_water = result[suite][radius]['converted_water']
                    events = result[suite][radius]['events']
                    converted_events = result[suite][radius]['converted_events']
                    water_supported = result[suite][radius]['water_available']
                    events_supported = result[suite][radius]['events_available']
                    water_match = True
                    events_match = True
                    s = "<testcase classname=\"" + classname + "\" name=\"" + suite_name + "\" radius=\"" + radius + "\" water=\"" + water + "\" converted_water=\"" + str(converted_water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) +"\" >"

                    if water_supported == 'true':
                        if water != converted_water or water == '0':
                            water_match = False
                    if events_supported == 'true':
                        if events != converted_events or events == '0':
                            events_match = False

                    if water_match == True and events_match == True:
                        passed_suites.append(s)
                        passed_suites.append("</testcase>")
                        pass_count += 1
                    else:
                        failed_suites.append(s)
                        failed_suites.append("<failure>")
                        failed_suites.append("<radius>" + radius + "</radius>")
                        failed_suites.append("<water_available>" + str(water_supported) + "</water_available>")
                        failed_suites.append("<events_available>" + str(events_supported) + "</events_available>")
                        failed_suites.append("</failure>")
                        failed_suites.append("</testcase>")
                        fail_count += 1

            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(fail_count)+"\" tests=\"" + str(pass_count) +"\" name=\"Congestion\">\n")
            xml_log_file.write('\n'.join(passed_suites))
            xml_log_file.write('\n'.join(failed_suites))

        elif report_type == 'rTeam_tests': #Parse the directory not file in this case
            (failed, passed) = self.get_total_counts_for_tss_tests(report_type, stats_file)

            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(failed)+"\" tests=\"" + str(passed) +"\" name=\"Congestion\">\n")

            logs = glob.glob(stats_file + '/*.log')
            classname = self.datadir + self.cfg.dev[self.testName].suites_dir
            for log in logs:
                (suite, water, events, converted_events, converted_water) = self.get_counts_for_tss_tests(log)
                if water > 0 and events > 0 and converted_events > 0 and converted_water > 0:
                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" water=\"" + str(water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) + "\" converted_water=\"" + str(converted_water) +"\" />\n")
                else:
                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" water=\"" + str(water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) + "\" converted_water=\"" + str(converted_water) +"\" >\n")
                    xml_log_file.write("<failure>FAILED</failure>\n")
                    xml_log_file.write("</testcase>\n")

        elif report_type == 'np_gb_tests':
            result = self.parse_np_log(stats_file)
            pass_count = 0
            fail_count = 0

            for k in result:
                if result[k]['passed'] == '1':
                    pass_count = pass_count + 1
                else:
                    fail_count = fail_count + 1
            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(fail_count)+"\" tests=\"" + str(pass_count) +"\" name=\"Congestion\">\n")
            classname = self.datadir + self.cfg.dev[self.testName].np_param_path

            for suite in result:
                if result[suite]['passed'] == '1':
                    water = result[suite]['water']
                    events = result[suite]['events']
                    converted_events = result[suite]['converted_events']
                    converted_water = result[suite]['converted_water']
                    unconverted = result[suite]['unconverted']
                    time_taken = result[suite]['time_taken']
                    unconverted_in_screen = result[kkey]['unconverted_in_screen']

                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" water=\"" + str(water) + "\" events=\"" + str(events) + "\" converted_events=\"" + str(converted_events) + "\" converted_water=\"" + str(converted_water) + "\" unconverted=\"" + str(unconverted) + "\" time_taken=\"" + str(time_taken) + "\" unconverted_in_screen=\"" + str(unconverted_in_screen) + "\" />\n")
                else:
                    xml_log_file.write("<testcase classname=\"" + classname + "\" name=\"" + suite + "\" >\n")
                    error = result[suite]['ERROR']
                    xml_log_file.write("<failure>" + error + "</failure>\n")
                    xml_log_file.write("</testcase>\n")

        xml_log_file.write("</testsuite>")
        xml_log_file.close()

    def parse_np_log(self, log_file):
        result = {}
        f = open(log_file, 'r')
        line = f.readline()

        while line:
            l = line.strip()
            if "SUITE:" in l:
                suite = line.strip()
                suite = suite.split(':')[-1]
                kkey = suite
                if not result.has_key(kkey):
                    result[kkey] = {'passed':'0'} #by default set the test to failed

                line = f.readline()
                while not "SUITEEND" in line and line:
                    line = line.strip()
                    if "*****total water " in line:
                        water = line.split(' ')[2]
                        result[kkey]['water'] = water.strip()
                    elif "*****total nodes " in line:
                        nodes = line.split(' ')[2]
                        result[kkey]['nodes'] = nodes.strip()
                    elif "*****total converted nodes " in line:
                        converted_nodes = line.split(' ')[3]
                        result[kkey]['converted_nodes'] = converted_nodes.strip()
                    elif "*****total converted water " in line:
                        converted_water = line.split(' ')[3]
                        result[kkey]['converted_water'] = converted_water.strip()
                    elif "*****total unconverted " in line:
                        unconverted = line.split(' ')[2]
                        result[kkey]['unconverted'] = unconverted.strip()
                    elif "*****total unconverted in screen " in line:
                        unconverted_in_screen = line.split(' ')[4]
                        result[kkey]['unconverted_in_screen'] = unconverted_in_screen
                        unconverted_in_screen = int(unconverted_in_screen)
                        if unconverted_in_screen == 0:
                            result[kkey]['passed'] = '1'
                    elif "Time Taken for decoding(ms): " in line:
                        time_taken = line.split(' ')[3]
                        result[kkey]['time_taken'] = time_taken.strip()
                    elif "ERROR" in line:
                        result[kkey]['ERROR'] = line
                    line = f.readline()

            line = f.readline()

        return result

    def get_tss_position_results(self, log_file):
        result = {}
        f = open(log_file, 'r')
        line = f.readline()

        while line:
            l = line.strip()
            if "SUITE:" in l:
                suite = line.strip()
                suite = getSuiteName(suite.split(':')[-1])

                line = f.readline()
                radius = line.strip()
                radius = radius.split(':')[-1]

                line = f.readline()
                water_available = line.strip()
                water_available = water_available.split(':')[-1]

                line = f.readline()
                nodes_available = line.strip()
                nodes_available = nodes_available.split(':')[-1]

                params = suite.split('_')
                if len(params) == 2:
                    country = params[0]
                    region = params[1]
                    kkey = '_'.join([country, region])
                else:
                    country = params[0]
                    kkey = country

                if not result.has_key(kkey):
                    result[kkey] = {radius: {'water_available': water_available, 'nodes_available':nodes_available} }
                else:
                    if not result[kkey].has_key(radius):
                        result[kkey][radius] = {'water_available': water_available, 'nodes_available':nodes_available}

                line = f.readline() #skip the [INFO ] log line in the log
                for k in range(0,4):
                    line = f.readline()
                    line = line.strip()
                    if "*****total water " in line:
                        water = line.split(' ')[2]
                        result[kkey][radius]['water'] = water.strip()
                    elif "*****total nodes " in line:
                        nodes = line.split(' ')[2]
                        result[kkey][radius]['nodes'] = nodes.strip()
                    elif "*****total converted nodes " in line:
                        converted_nodes = line.split(' ')[3]
                        result[kkey][radius]['converted_nodes'] = converted_nodes.strip()
                    elif "*****total converted water " in line:
                        converted_water = line.split(' ')[3]
                        result[kkey][radius]['converted_water'] = converted_water.strip()

            line = f.readline()
        return result

    def get_total_counts_for_tss_tests(self, report_type, logs_dir):
        passed = 0
        failed = 0

        if 'position' in report_type:
            (suite, water, nodes, converted_nodes, converted_water) = self.get_counts_for_tss_tests(logs_dir)
            if water > 0 and nodes > 0 and converted_nodes > 0 and converted_water > 0:
                passed = passed + 1
            else:
                failed = failed + 1
        else: #rTeam
            logs = glob.glob(logs_dir + '/*.log')

            for log in logs:
                (suite, water, nodes, converted_nodes, converted_water) = self.get_counts_for_tss_tests(log)
                if water > 0 and nodes > 0 and converted_nodes > 0 and converted_water > 0:
                    passed = passed + 1
                else:
                    failed = failed + 1

        return (failed, passed)


    def get_counts_for_tss_tests(self, log_file):
        myvar = open(log_file, 'r')
        lst = myvar.readlines()
        suite = ''
        water = 0
        nodes = 0
        converted_nodes = 0
        converted_water = 0

        for line in lst:
            if 'xml' in line:
                suite = getSuiteName(line)
            if '*****total water' in line:
                water = int(line.split(' ')[-1])
            if '*****total nodes' in line:
                nodes = int(line.split(' ')[-1])
            if '*****total converted nodes' in line:
                converted_nodes = int(line.split(' ')[-1])
            if '*****total converted water' in line:
                converted_water = int(line.split(' ')[-1])

        myvar.close()

        return (suite, water, nodes, converted_nodes, converted_water)

    def generateConsolidationReport(self):
        pass

    def getName(self):
        return 'Congestion'

#Congestion -------------------------------------end -----------------------------

class gadgetDeviceExecutor(Executor):
    def __init__(self, testName):
        Executor.__init__(self, testName, os.getenv("PLATFORM"))
        self.testDirs = self.cfg.details.settings[self.platform][self.testName].testdirs
        self.gadget_posttestsrcdir = self.basedir + self.cfg.details.settings.common.gadget_posttestsrcdir
        self.posttestdstdir = self.basedir + self.cfg.details.settings.common.posttestdstdir
        self.createTestDirs()

    def executeCommands(self, cmdLst):
        global exitCode
        global timeOut
        timeout = self.cfg.details.settings[self.platform][self.testName].timeout
        try:
            if (os.environ["PROCESS_TIMEOUT"] != None):
                timeout = int(os.environ["PROCESS_TIMEOUT"])
        except:
            timeout = timeout

        if (timeout == None or timeout < 0 or timeout == ''):
            timeout = int(3600) # Default timeout of 1 hr

        try:
            timeout = int(timeout)
        except:
            # Timeout value is not an integer value, set default value
            timeout = int(3600) # Default timeout of 1 hr

        timeOut = timeout
        self.timeoutExceeded = None
        for cmd in cmdLst:
            # Check if timeout exceeded during execution of previous command
            if (self.timeoutExceeded):
                logEvent ("INFO: Timeout period exceeded while executing: " + cmd + ", skipping any remaining commands")
                exitCode = ExitCode.Error
                return 1
            log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
            err_log = self.basedir + self.cfg.details.settings[self.platform][self.testName].err_log
            # Remove leading and trailing spaces
            cmd = cmd.lstrip()
            cmd = cmd.rstrip()
            log = log.lstrip()
            log = log.rstrip()
            err_log = err_log.lstrip()
            err_log = err_log.rstrip()

            logEvent('INFO: Executing: ' + cmd + ', logging to: ' + log)
            logEvent('INFO: Expecting the process to complete in ' + str(timeout) + ' seconds')
            Fh = None
            ErrFh = None
            try:
                Fh = open(log, "a")
                ErrFh = open(err_log, "a")
                timer = threading.Timer(timeout, self.procHandler)
                timer.start()
                self.proc = subprocess.Popen(cmd, stdout=Fh, stderr=ErrFh, shell=True)
                self.proc.wait()
                if (timer.isAlive()):
                    timer.cancel()
                if (self.proc.returncode != 0):
                    # Raise error as test binary has exited with a negative exit code
                    exitCode = ExitCode.Error
                    logEvent ("ERROR: Child exited with exit code: " + str(self.proc.returncode))
                else:
                    logEvent ("INFO: Child exited with exit code: " + str(self.proc.returncode))
                Fh.flush()
                ErrFh.flush()
                Fh.close()
                ErrFh.close()
            except Exception as e:
                logEvent ("WARNING: Exception caught while executing: " + str(cmd) + ", excep: " + str(e))
                exitCode = ExitCode.Error
                Fh.flush()
                ErrFh.flush()
                Fh.close()
                ErrFh.close()

    def procHandler(self):
        global exitCode
        global timeOut
        try:
            exitCode = ExitCode.Error
            self.proc.poll()
            logEvent ("ERROR: Process exceeded timeout[" + str(self.platform) + "-" + self.testName + "][" + str(timeOut) + "], terminating child pid: " + str(self.proc.pid))
            self.proc.kill()
            self.timeoutExceeded = 1
        except Exception as e:
            exitCode = ExitCode.Error
            logEvent ("WARNING: Exception caught while terminating child process: " + str(self.proc.pid))

class gadgetDeviceSMTest(gadgetDeviceExecutor):
    def __init__(self, test_file_name):
        self.file_name = test_file_name
        gadgetDeviceExecutor.__init__(self, 'SMtest')
        self.test_execution = self.basedir+self.cfg.details.settings.common.posttestsrcdir

    def run(self):
        params = dict(basedir=self.basedir,
            file_name = self.file_name,
            packages_root = os.getenv("PACKAGES_ROOT"),
            powershell_exe = os.getenv("POWER_SHELL_PATH")+"\\powershell.exe",
            workspace = os.getenv("WORKSPACE")
        )
        precmds = self.cfg.details.settings[self.platform][self.testName].precmds
        cmds = []
        for cmd in precmds:
          cmds.append(Template(cmd).substitute(params))
        self.executeCommands(cmds)

        cmds = [Template(self.cfg.details.settings[self.platform][self.testName].CMD).substitute(params)]
        self.executeCommands(cmds)

    def parse(self):
        pass

    def convertToXML(self):
        try:
            with open(self.basedir+self.cfg.details.settings.gadget_arm.SMtest.xml_output) as f:
                f.close()
                self.xmlreport = 1
                Executor.convertCppUnitToJUnit(self)
        except IOError as e:
            pass

    def getName(self):
        return 'SMtest'

class gadgetDeviceUnitTest(gadgetDeviceSMTest):
    def __init__(self, test_file_name):
        self.file_name = test_file_name
        gadgetDeviceExecutor.__init__(self, 'SMtest')
        self.test_execution = self.basedir+self.cfg.details.settings.common.posttestsrcdir

    def parse(self):
        global exitCode
        try:
            with open(os.path.join(self.test_execution, "error.txt")) as f:
                exitCode = ExitCode.Error
        except IOError as e:
            pass

    def convertToXML (self):
        numOfTests = 0
        numOfFailure = 0
        testCaseList = []
        failureList = []
        failureCaseIdList = []
        try:
            with open(os.path.join(self.test_execution, "conoutput.txt")) as test:
                for line in test:
                    m = re.search("CPPUNIT_ASSERT|Failed", line[:-1])

                    if m != None:
                        print 'failed'
                        failureList.append(line[:-1])
                        failureCaseIdList.append(numOfTests-1)
                        print line[:-1]
                        #print numOfTests
                        numOfFailure = numOfFailure + 1

                    m = re.search("Test::|Testd::|Testf::", line[:-1])
                    if m != None:
                        print 'passed'
                        testCaseList.append(line[:-1])
                        print line[:-1]
                        numOfTests = numOfTests + 1

            print "Num of Tests: %d" % numOfTests
            print "Num of failure: %d" % numOfFailure
            f = open(self.basedir+self.cfg.details.settings.gadget_arm.SMtest.xml_output, "w")
            f.write("<?xml version=\"1.0\" encoding=\'ISO-8859-1\' standalone=\'yes\' ?>\n")
            f.write("<TestRun>\n")
            if numOfFailure == 0:
                f.write("\t<FailedTests></FailedTests>\n")
            else:
                f.write("\t<FailedTests>\n")
                for index in range(len(failureList)):
                    failureCaseId = failureCaseIdList[index]
                    f.write("\t\t<FailedTest id=\"%d\">\n" % (failureCaseId+1))
                    f.write("\t\t\t<Name>%s</Name>\n" % testCaseList[failureCaseId])
                    m = re.search("ASSERT", failureList[index])
                    if m != None:
                        failureType = "Assertion"
                    else:
                        failureType = "Exception"

                    f.write("\t\t\t<FailureType>%s</FailureType>\n" % failureType)
                    f.write("\t\t\t<Location>\n")

                    errorInfo = failureList[index]
                    fileNameIndex = errorInfo.find("(")
                    lineNumberIndex = errorInfo.find(")")
                    messageIndexEnd = errorInfo.find(";")

                    filename = errorInfo[0:fileNameIndex]
                    lineNumber = errorInfo[(fileNameIndex + 1):lineNumberIndex]
                    errorMsg = errorInfo[(lineNumberIndex + 3):(messageIndexEnd + 1)]
                    if (errorMsg.find("&") > 0):
                        errorMsg = errorMsg.replace("&", " ")
                    f.write("\t\t\t\t<File>%s</File>\n" % filename)
                    f.write("\t\t\t\t<Line>%s</Line>\n" % lineNumber)
                    f.write("\t\t\t</Location>\n")
                    f.write("\t\t\t<Message>%s\n" % errorMsg)
                    f.write("\t\t\t</Message>\n")
                    f.write("\t</FailedTest>\n")
                f.write("\t</FailedTests>\n")

            f.write("\t<SuccessfulTests>\n")
            for index in range(len(testCaseList)):

                if not(index in failureCaseIdList):
                    f.write("\t\t<Test id=\"%d\">\n" % (index+1))
                    f.write("\t\t\t<Name>%s</Name>\n" % testCaseList[index])
                    f.write("\t\t</Test>\n")

            f.write("\t</SuccessfulTests>\n")
            f.write("\t<Statistics>\n")
            f.write("\t\t<Tests>%s</Tests>\n" % numOfTests)
            f.write("\t\t<FailuresTotal>%s</FailuresTotal>\n" % numOfFailure)
            f.write("\t\t<Errors>%s</Errors>\n" % numOfFailure)
            f.write("\t\t<Failures>%s</Failures>\n" % numOfFailure)
            f.write("\t</Statistics>\n")
            f.write("</TestRun>\n")
            f.close()
            self.xmlreport = 1
            Executor.convertCppUnitToJUnit(self)
        except IOError as e:
            exitCode = ExitCode.Error

    def getName(self):
        return 'SMtest'


if __name__ == "__main__":
    logEvent("[exec]" + " ".join(sys.argv))

    # print environment variables
    for e in ["PLATFORM","STEP","TEST_SET"]:
        logEvent("[environment] " + e + "=" + str(os.getenv(e)))

    if sys.platform.lower().startswith('win'):
        os.system("regedit /s disable_crash_popup.reg")

    platform = os.getenv("PLATFORM")
    basedir = replaceSlash(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath( __file__ )), '..')))

    cfg = get_config(basedir)

    tests = cfg.dev.tests
    logEvent("[config] Tests: " + str(tests))
    gadgetSimulatoradress = None

    # check if test set is defined as env variable
    if os.getenv("TEST_SET") != None and len(os.getenv("TEST_SET")) > 0 :
        test_set = os.getenv("TEST_SET").split(',')
        if len(test_set) > 0 :
            tests = list(set(tests) & set(test_set))
            logEvent("[env] Tests: " + str(tests))

    # parse command arguments
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, '', ['tests=', 'gadgetSimulatoraddress='])

        for o, a in opts:
            # overwrite tests from command line
            if o == "--tests":
                tests = a.split(',')
                logEvent("[argv] Tests: " + str(tests))
            if o == "--gadgetSimulatoraddress":
                gadgetSimulatoradress = a.split(',')[0]
                logEvent("[argv] gadgetSimulatoraddress: " + str(gadgetSimulatoradress))

    except:
        logEvent("[E] Error parsing arguments")
        traceback.print_exc()

    if(len(tests)):
        logEvent("Tests to be executed: " + str(tests))
    else:
            logEvent("[E] Test set is empty ")
            exitCode = ExitCode.Skipped

    suite = []

    if platform.lower().startswith('win'):

        for test in tests:
            if   test == 'unittest':
                suite.append(winUnit())
            elif test == 'gTeam':
                suite.append(wingTeam())
            elif test == 'rTeam':
                suite.append(winrTeam())
            elif test == 'renrTeam':
                suite.append(winrenrTeam())
            elif test == 'renpTeam':
                suite.append(winrenpTeam())
            elif test == 'Congestion':
                suite.append(winCongestion())
            else:
                logEvent("[E] Unknown win test: " + test)
                exitCode = ExitCode.Skipped

        for test in suite:
            test.run()

        for test in suite:
            test.parse()
            test.convertToXML()

        if (len(suite)):
            test = suite[-1]
            test.generateConsolidationReport()
            backupResults(test.posttestsrcdir, test.posttestdstdir, platform)

    elif platform.lower().startswith('gadget_arm'):
        # Remove test dir
        if os.path.exists(basedir + cfg.details.settings.common.posttestsrcdir):
            logEvent ("INFO: Removing existing result dir: " + basedir + cfg.details.settings.common.posttestsrcdir)
            try:
                shutil.rmtree(basedir + cfg.details.settings.common.posttestsrcdir)
            except Exception as e:
                logEvent ("WARNING: Unable to remove old results dir: " + basedir + cfg.details.settings.common.posttestsrcdir)

        for test in tests:
            if 'SMtest' in test:
                logEvent ("INFO: SMtest tests are selected to be executed")
                suite.append(gadgetDeviceSMTest(test))
            elif 'unittest' in test:
                logEvent ("INFO: SMtest unittest is selected to be executed")
                suite.append(gadgetDeviceUnitTest(test))
            elif 'gTeam' in test:
                logEvent ("INFO: SMtest gTeam is selected to be executed")
                suite.append(gadgetDeviceSMTest(test))
            elif 'rTeam' in test:
                logEvent ("INFO: SMtest gTeam is selected to be executed")
                suite.append(gadgetDeviceSMTest(test))
            elif 'imu' in test:
                logEvent ("INFO: SMtest IMU is selected to be executed")
                suite.append(gadgetDeviceSMTest(test))
            else:
                logEvent("[E] Unknown gadget_arm test: " + test)
                exitCode = ExitCode.Skipped

        for test in suite:
            logEvent ("INFO: Executing " + test.getName())
            test.run()
        for test in suite:
            test.parse()
            test.convertToXML()

        if (len(suite)):
            test = suite[-1]
            logEvent ("INFO: Archiving results:")
            backupResults(test.gadget_posttestsrcdir, test.posttestdstdir, platform)

    elif platform.lower().startswith('gadget_x86'):
        # Remove test dir
        if os.path.exists(basedir + cfg.details.settings.common.gadget_posttestsrcdir):
            logEvent ("INFO: Removing existing result dir: " + basedir + cfg.details.settings.common.gadget_posttestsrcdir)
            try:
                shutil.rmtree(basedir + cfg.details.settings.common.gadget_posttestsrcdir)
            except Exception as e:
                logEvent ("WARNING: Unable to remove old results dir: " + basedir + cfg.details.settings.common.gadget_posttestsrcdir)

        for test in tests:
            if   test == 'unittest':
                logEvent ("INFO: unit tests are selected to be executed")
                suite.append(gadgetUnit())
            elif test == 'gTeam':
                logEvent ("INFO: gTeam tests are selected to be executed")
                suite.append(gadgetgTeam())
            elif test == 'rTeam':
                logEvent ("INFO: rTeam tests are selected to be executed")
                suite.append(gadgetrTeam())
            elif test == 'Congestion':
                logEvent ("INFO: Congestion tests are selected to be executed")
                suite.append(gadgetCongestion(gadgetSimulatoradress))
            else:
                logEvent("[E] Unknown gadget test: " + test)
                exitCode = ExitCode.Skipped
            # Temporarily disabling rendering tests for gadget
            """elif test == 'renpTeam':
                logEvent ("INFO: renpTeam tests are selected to be executed")
                suite.append(gadgetrenpTeam())
            elif test == 'renrTeam':
                logEvent ("INFO: renrTeam tests are selected to be executed")
                suite.append(gadgetrenrTeam())"""

        for test in suite:
            logEvent ("INFO: Executing " + test.getName())
            test.run()

        if (len(suite)):
            logEvent ("INFO: Gathering results from SM")
            test = suite[-1]
            test.gatherResults()

        for test in suite:
            logEvent ("INFO: Parsing results for " + test.getName())
            test.parse()
            test.convertToXML()

        if (len(suite)):
            logEvent ("INFO: Parsing results")
            test = suite[-1]
            #test.gatherResults()
            logEvent ("INFO: Generating consolidated report")
            test.generateConsolidationReport()
            logEvent ("INFO: Archiving results:")
            backupResults(test.gadget_posttestsrcdir, test.posttestdstdir, platform)

logEvent ("INFO: Exiting with exitcode: " + str(exitCode))
exit(int(exitCode))
