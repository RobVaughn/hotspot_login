# Unit tests for API (utils).

import ctypes, os, sys, io
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

try:
    ADMIN = os.getuid() == 0
except AttributeError:
    ADMIN = ctypes.windll.shell32.IsUserAnAdmin() != 0

#
# Helper functions for testing standard output/error messages.
#

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

class utilsTest(unittest.TestCase):

    def test_check(self):
        """ checkIF() - checks if interface is enabled. """

        self.assertTrue(hu.checkIF())
        self.assertTrue(hu.checkIF(cfg.IF))
        self.assertTrue(hu.checkIF(TESTIF))
        self.assertFalse(hu.checkIF(BADIF))

    def test_enable(self):
        """ enableIF() - enables a network interface. """

        if ADAPTER_TESTS and ADMIN:
            hu.disableIF()
            self.assertEqual(hu.enableIF(), 0)
            hu.disableIF(cfg.IF)
            self.assertEqual(hu.enableIF(cfg.IF), 0)
            # Already enabled, still returns 0.
            self.assertEqual(hu.enableIF(TESTIF), 0)
            self.assertEqual(hu.enableIF(BADIF), 1)
            # Always finish with interface enabled.
            hu.enableIF()
        elif not ADMIN:
            print("\nTests for enableIF() require Administrator privs.")
        else:
            print("\nEnable/disable tests can lock up some adapters. Set ADAPTER_TEST to True to run them.")

    def test_disable(self):
        """ disableIF() - disables a network interface. """

        if ADAPTER_TESTS and ADMIN:
            hu.enableIF()
            self.assertEqual(hu.disableIF(), 0)
            hu.enableIF(cfg.IF)
            self.assertTrue(hu.disableIF(cfg.IF), 0)
            # Already disabled, still returns 0.
            self.assertTrue(hu.disableIF(TESTIF), 0)
            self.assertFalse(hu.disableIF(BADIF), 1)
            # Always finish with interface enabled.
            hu.enableIF()
        elif not ADMIN:
            print("\nTests for disableIF() require Administrator privs.")
        else:
            print("\nEnable/disable tests can lock up some adapters. Set ADAPTER_TEST to True to run them.")

    def test_show(self):
        """ showNetwork() - displays available hotspots. """

        self.assertEqual(hu.showNetwork(), 0)
        self.assertEqual(hu.showNetwork(cfg.IF), 0)
        self.assertEqual(hu.showNetwork(TESTIF), 0)
        retcode, out, err = captureOutput(lambda:hu.showNetwork(BAD_SSID))
        self.assertEqual(retcode, 1)
        if 'no such wireless' in out:
            self.assertIn('no such wireless interface', out)
        else:
            self.assertIn('Unable to show available', out)

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

        self.assertTrue(hu.connect(cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN], cfg.IF))

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
