import argparse, sys
from os import environ
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from concurrent.futures import ThreadPoolExecutor

class customParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)
parser = customParser(prog='multiCookie', description='Python 3 script to get session cookies given a credentials file')
parser.add_argument('u', help='Login URL')
parser.add_argument('i', help='CSS id selector of the identifier input (username/email)')
parser.add_argument('p', help='CSS id selector of the password input')
parser.add_argument('b', help='CSS id selector of the button to submit the form')
parser.add_argument('c', help='Name of the session cookie(s) to obtain (if there are several separate by commas: "cookie1,cookie2")')
parser.add_argument('f', help='File with creds, format should be "email/username password" (delimiter is the space and one cred per line)')
parser.add_argument('-t', '--threads', help='Number of threads to open browsers with Selenium (by default, 4)', type=int, default=4)
parser.add_argument('-s', '--sleep', help='Seconds to sleep between relevant requests (by default, 3)', type=int, default=3)
parser.add_argument('-p', '--proxy', help='Send traffic through a proxy (by default, Burp)', nargs='?', default=None, const='127.0.0.1:8080')
args = parser.parse_args()

try:
    with open(args.f) as credsListFile:
        credsList = credsListFile.read().splitlines()
except Exception as e:
        print(e)
        exit(1)

if ',' in args.c:
    cookiesToGet = args.c.split(',')
else:
    cookiesToGet = [args.c]

environ['WDM_LOG_LEVEL'] = '0'

credsDict = {}
for cred in credsList:
    credsDict.update({cred.split()[0]:cred.split()[-1]})

print('[!] The file {} contains {} credentials'.format(args.f, len(credsDict)))
print('[!] {} threads to open browsers with Selenium'.format(args.threads))
print('[!] {} seconds of sleep set between relevant requests'.format(args.sleep))
print('[!] Getting cookies... Please wait\n')

def getCookie(identifier, password, credentialId):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('ignore-certificate-errors')
    options.add_argument('disable-extensions')

    if args.proxy is not None:
        options.add_argument('--proxy-server={}'.format(args.proxy))

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    driver.get(args.u)
    sleep(args.sleep)

    def findElement(argumentName, argumentVariable):
        try:
            return driver.find_element(By.ID, argumentVariable)
        except NoSuchElementException:
            print('[{}] {} not found'.format(credentialId, argumentName))
            exit(1)

    identifierInput = findElement('Identifier input', args.i)
    passwordInput = findElement('Password input', args.p)
    submitButton = findElement('Submit button', args.b)

    identifierInput.send_keys(identifier)
    passwordInput.send_keys(password)
    submitButton.click()
    sleep(args.sleep)

    allCookiesDict = driver.get_cookies()
    for cookieDict in allCookiesDict:
        for cookieToGet in cookiesToGet:
            if cookieDict.get('name') == cookieToGet:
                print('[{}] {} {}={}'.format(credentialId, identifier, cookieToGet, cookieDict.get('value')))

    driver.quit()

credentialId = 0
with ThreadPoolExecutor(max_workers=args.threads) as executor:
    for cred in credsDict:
        credentialId+=1
        executor.submit(getCookie, cred, credsDict[cred], credentialId)
