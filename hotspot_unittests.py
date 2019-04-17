# Unit tests for API (utils).

import sys, io, os, ctypes, subprocess
import unittest

from contextlib import contextmanager

import hotspot_config as cfg
import hotspot_utils as hu

# Running tests for enabling/disabling the network interface can hang/lock up some
# adapters such as the Qualcomm Atheros series, so tests must be turned on w/a flag.
# They also require Adminstrator privs on Windows.

ADAPTER_TESTS = False

# Test assertions are taken from the config file but can be hand-coded.
TESTIF = cfg.IF
BADIF = "InvalidIF"
TEST_SSID = cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN]['ssid']
BAD_SSID = "InvalidSSID"

ADMIN = False
try:
    ADMIN = os.getuid() == 0
except AttributeError:
    ADMIN = ctypes.windll.shell32.IsUserAnAdmin() != 0

# Helper functions for testing standard output/error messages.

@contextmanager
def getOutput():
    """ Capture stdout and stderr messages for assertion tests. """

    stdout, stderr = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr

    try:
        sys.stdout, sys.stderr = stdout, stderr
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def captureOutput(func, *args) -> (int, list, list):
    """ Capture stdout/stderr from a function call and return with exit code. """

    with getOutput() as (out, err):
        retcode = func()
    out = out.getvalue().splitlines()
    err = err.getvalue().splitlines()
    return(retcode, '\n'.join(out), '\n'.join(err))

class UtilsTests(unittest.TestCase):

    @unittest.skipUnless(ADMIN is False, "Non-Admin privs tests.")
    def test_admin_CLI(self):
        """ Testing error message on non-admin execution. """

        result = subprocess.run(['python', 'hotspot_login.py', '-d'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout).replace('\r',''))

    def test_main_CLI(self):
        """ Testing messages and results from main command line options. """

        result = subprocess.run(['python', 'hotspot_login.py'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Logged in', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', cfg.DEFAULT_LOGIN], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Logged in', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', 'InvalidLogin'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unknown hotspot', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', 'InvalidLogin', cfg.IF],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unknown hotspot', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', cfg.DEFAULT_LOGIN, BADIF],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        if cfg.OS == "Windows":
            expected = "name is not registered"
        elif cfg.OS == "Linux":
            expected = "Unknown interface"
        self.assertIn(expected, str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', 'InvalidLogin', BADIF],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unknown hotspot', str(result.stdout).replace('\r',''))
        
    def test_check(self):
        """ checkIF() - checks if interface is enabled. """

        self.assertTrue(hu.checkIF())
        self.assertTrue(hu.checkIF(cfg.IF))
        self.assertTrue(hu.checkIF(TESTIF))
        self.assertFalse(hu.checkIF(BADIF))

    def test_check_CLI(self):
        """ Testing messages and results from "check" (-c) command line option. """

        result = subprocess.run(['python', 'hotspot_login.py', '-c'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Interface ' + cfg.IF + ' is connected', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-c', cfg.IF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Interface ' + cfg.IF + ' is connected', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-c', TESTIF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Interface ' + cfg.IF + ' is connected', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-c', BADIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('is not connected', str(result.stdout))

    @unittest.skipUnless(ADMIN is False, "Testing non-admin privs.")
    def test_non_admin_CLI(self):
        """ Testing messages and results from -e/-d/-r command line options w/o admin privs. """

        result = subprocess.run(['python', 'hotspot_login.py', '-e'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Interface ' + cfg.IF + ' is enabled', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-e', cfg.IF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Interface ' + cfg.IF + ' is enabled', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-e', TESTIF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Interface ' + cfg.IF + ' is enabled', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-e', BADIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))

        result = subprocess.run(['python', 'hotspot_login.py', '-d'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-d', cfg.IF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-d', TESTIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-d', BADIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))

        result = subprocess.run(['python', 'hotspot_login.py', '-r'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-r', cfg.IF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-r', TESTIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))
        result = subprocess.run(['python', 'hotspot_login.py', '-r', BADIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Admin privileges are required', str(result.stdout))

    @unittest.skipUnless(ADMIN is True, "Requires admin privleges.")
    @unittest.skipUnless(ADAPTER_TESTS is True, "Adapter tests flag is not set.")
    def test_enable(self):
        """ enableIF() - enables a network interface. """

        hu.disableIF()
        self.assertEqual(hu.enableIF(), 0)
        hu.disableIF(cfg.IF)
        self.assertEqual(hu.enableIF(cfg.IF), 0)
        # Already enabled, still returns 0.
        self.assertEqual(hu.enableIF(TESTIF), 0)
        self.assertEqual(hu.enableIF(BADIF), 1)
        # Always finish with interface enabled.
        hu.enableIF()

    @unittest.skipUnless(ADMIN is True, "Requires admin privleges.")
    @unittest.skipUnless(ADAPTER_TESTS is True, "Adapter tests flag is not set.")
    def test_enable_CLI(self):
        """ Testing messages and results from "enable" (-e) command line option. """

        result = subprocess.run(['python', 'hotspot_login.py', '-e'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('enabled', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-e', cfg.IF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('enabled', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-e', TESTIF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('enabled', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-e', BADIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid', str(result.stdout).replace('\r',''))

    @unittest.skipUnless(ADMIN is True, "Requires admin privleges.")
    @unittest.skipUnless(ADAPTER_TESTS is True, "Adapter tests flag is not set.")
    def test_disable(self):
        """ disableIF() - disables a network interface. """

        hu.enableIF()
        self.assertEqual(hu.disableIF(), 0)
        hu.enableIF(cfg.IF)
        self.assertTrue(hu.disableIF(cfg.IF), 0)
        # Already disabled, still returns 0.
        self.assertTrue(hu.disableIF(TESTIF), 0)
        self.assertFalse(hu.disableIF(BADIF), 1)
        # Always finish with interface enabled.
        hu.enableIF()

    @unittest.skipUnless(ADMIN is True, "Requires admin privleges.")
    @unittest.skipUnless(ADAPTER_TESTS is True, "Adapter tests flag is not set.")
    def test_disable_CLI(self):
        """ Testing messages and results from "disable" (-d) command line option. """

        result = subprocess.run(['python', 'hotspot_login.py', '-d'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('disabled', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-d', cfg.IF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('disabled', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-d', TESTIF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('disabled', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-d', BADIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid', str(result.stdout).replace('\r',''))

    def test_show(self):
        """ getNetworks() - displays available hotspots. """

        retcode, out = hu.getNetworks()
        self.assertEqual(retcode, 0)
        self.assertIn('networks currently visible', out)
        retcode, out = hu.getNetworks(cfg.IF)
        self.assertEqual(retcode, 0)
        self.assertIn('networks currently visible', out)
        retcode, out = hu.getNetworks(cfg.IF)
        self.assertEqual(retcode, 0)
        self.assertIn('networks currently visible', out)
        retcode, out = hu.getNetworks(BAD_SSID)
        self.assertEqual(retcode, 4)
        if 'no such wireless' in out:
            self.assertIn('no such wireless interface', out)
        else:
            self.assertIn('Unable to show available', out)

    def test_show_CLI(self):
        """ Testing messages and results from "show" (-s) command line option. """

        result = subprocess.run(['python', 'hotspot_login.py', '-s'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('currently visible', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-s', cfg.IF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('currently visible', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-s', TESTIF], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('currently visible', str(result.stdout).replace('\r',''))
        result = subprocess.run(['python', 'hotspot_login.py', '-s', BADIF], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no such wireless interface', str(result.stdout).replace('\r',''))

    @unittest.skipUnless(cfg.OS == "Windows", "Windows functionality only.")
    def test_blocklist(self):
        """ getBlocklist() - retrieves a list of blocked SSIDs. """

        retcode, out, err = captureOutput(lambda:hu.getBlocklist())
        self.assertEqual(retcode, 0)
        self.assertIn('Block list on the system', out)
        hu.addBlocklist(BAD_SSID, force=True)
        retcode, out, err = captureOutput(lambda:hu.getBlocklist())
        self.assertEqual(retcode, 0)
        self.assertIn('SSID: "' + BAD_SSID + '"', out)
        hu.delBlocklist(BAD_SSID)
        retcode, out, err = captureOutput(lambda:hu.getBlocklist())
        self.assertEqual(retcode, 0)
        self.assertNotIn('SSID: "' + BAD_SSID + '"', out)

    @unittest.skipUnless(cfg.OS == "Windows", "Windows functionality only.")
    def test_blocklist_CLI(self):
        """ Testing messages and results from "blocklist" (-bl) command line option. """

        result = subprocess.run(['python', 'hotspot_login.py', '-bl'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Block list on the system', str(result.stdout).replace('\r',''))

    @unittest.skipUnless(cfg.OS == "Windows", "Windows functionality only.")
    @unittest.skipUnless(ADMIN is True, "Requires admin privleges.")
    def test_addblock(self):
        """ addBlocklist() - adds an SSID to the block list. """

        self.assertEqual(hu.addBlocklist(TEST_SSID), 0)
        self.assertEqual(retcode, 0)
        retcode, out, err = captureOutput(lambda:hu.getBlocklist())
        self.assertEqual(retcode, 0)
        self.assertIn('Added ' + TEST_SSID + '  to block list', out)
        self.assertEqual(hu.addBlocklist(BAD_SSID), 1)
        retcode, out, err = captureOutput(lambda:hu.getBlocklist())
        self.assertEqual(retcode, 0)
        self.assertNotIn(BAD_SSID, out)
        
    @unittest.skipUnless(cfg.OS == "Windows", "Windows functionality only.")
    @unittest.skipUnless(ADMIN is True, "Requires admin privleges.")
    def test_unblock(self):
        """ delBlocklist() - removes an SSID from the block list. """

        self.assertEqual(hu.delBlocklist(TEST_SSID), 0)
        retcode, out, err = captureOutput(lambda:hu.delBlocklist(BAD_SSID))
        self.assertEqual(retcode, 1)
        self.assertIn("Unable to find " + BAD_SSID + " in the block list", out)

    def test_check_connect(self):
        """ checkConnection() - checks if connected to a hotspot. """

        self.assertTrue(hu.checkConnection(cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN]['ssid']))
        self.assertTrue(hu.checkConnection(TEST_SSID))
        self.assertFalse(hu.checkConnection(BAD_SSID))

    def test_connect_to(self):
        """ connectToNetwork() - connects to a hotspot by SSID. """

        self.assertTrue(hu.connectToNetwork(cfg.IF, TEST_SSID))
        self.assertTrue(hu.connectToNetwork(TESTIF, TEST_SSID))
        self.assertFalse(hu.connectToNetwork(BADIF, TEST_SSID))

        retcode, out, err = captureOutput(lambda:hu.connectToNetwork(TESTIF, BAD_SSID))
        self.assertFalse(retcode)
        if 'Not connected to ' in out:
            self.assertIn('Not connected to ' + BAD_SSID, out)
        else:
            self.assertIn('There is no profile \"' + BAD_SSID, out)

    def test_connect(self):
        """ connect() - enables interface if necessary, connects and logs in via POST. """

        retcode, out, err = captureOutput(
            lambda:hu.connect(cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN], cfg.IF))
        self.assertTrue(retcode)
        self.assertIn('Logged in', out)

        cfg.SILENT = True
        retcode, out, err = captureOutput(
            lambda:hu.connect(cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN], cfg.IF))
        self.assertTrue(retcode)
        self.assertIs(len(out), 0)

        retcode, out, err = captureOutput(
            lambda:hu.connect(cfg.LOGIN_INFO['test'], cfg.IF))
        self.assertFalse(retcode)
        self.assertIn('There is no profile', out)

        retcode, out, err = captureOutput(
            lambda:hu.connect(cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN], BADIF))
        self.assertFalse(retcode)
        self.assertIn('Invalid interface', out)
        
if __name__ == '__main__':
    unittest.main()
