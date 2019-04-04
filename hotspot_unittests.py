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
BADIF = "Invalid-IF"
TEST_SSID = cfg.LOGIN_INFO[cfg.DEFAULT_LOGIN]['ssid']
BAD_SSID = "InvalidSSID"

try:
    ADMIN = os.getuid() == 0
except AttributeError:
    ADMIN = ctypes.windll.shell32.IsUserAnAdmin() != 0

@contextmanager
def captured_output():
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

    stdout = ""
    stderr = ""
    with captured_output() as (out, err):
        retcode = func()
    out = out.getvalue().splitlines()
    if len(out) > 0:
        stdout = out[0]
    err = err.getvalue().splitlines()
    if len(err) > 0:
        stderr = err[0]
    return(retcode, stdout, stderr)

class utilsTest(unittest.TestCase):

    def expecting(output:str) -> None:
        print("\nExpecting:", format(output))

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
            print("\nIF:", TESTIF)
            self.assertEqual(hu.enableIF(TESTIF), 0)
            self.assertEqual(hu.enableIF(BADIF), 1)
            # Always finish with interface enabled.
            hu.enableIF()
        elif not ADMIN:
            print("Tests for enableIF() require Administrator privs.")
        else:
            print("Enable/disable tests can lock up some adapters. Set ADAPTER_TEST to True to run them.")

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
            print("Tests for disableIF() require Administrator privs.")
        else:
            print("Enable/disable tests can lock up some adapters. Set ADAPTER_TEST to True to run them.")

    def test_show(self):
        """ showNetwork() - displays available hotspots. """

        self.assertEqual(hu.showNetwork(), 0)
        self.assertEqual(hu.showNetwork(cfg.IF), 0)
        self.assertEqual(hu.showNetwork(TESTIF), 0)
        retcode, out, err = captureOutput(lambda:hu.showNetwork(BAD_SSID))
        self.assertEqual(retcode, 1)
        self.assertIn('no such wireless interface', out[0])

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
        self.assertIn('There is no profile "' + BAD_SSID + '"', out)

        retcode, out, err = captureOutput(lambda:hu.connectToNetwork(BADIF, BAD_SSID))
        self.assertFalse(retcode)
        with self.subTest():
            self.assertIn('Failed to connect to ' + BAD_SSID, out)
#            self.assertIn('Logged in', out)
        with self.subTest():
            self.assertIn('There is no profile "' + BAD_SSID + '"', out)
#            self.assertIn('Already connected', out)

#        if 'Failed' in out:
#            self.assertIn('Failed to connect to ' + BAD_SSID, out)
#        else:
#            self.assertIn('There is no profile "' + BAD_SSID + '"', out)

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
