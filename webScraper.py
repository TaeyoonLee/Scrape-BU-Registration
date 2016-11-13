'''
Selenium 2.53.1
Python 3.4.4
Make sure you have the chrome driver downloaded in this folder before running
Run this: chcp 65001 before running and printing everything in cmd to be able to print in cmd
'''

import time
import json
import pprint
import pickle
import getpass
import requests
import selenium
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

start_time = time.time()

#make sure chrome driver is in PATH variable or in the this directory
#download chrome driver at https://sites.google.com/a/chromium.org/chromedriver/downloads
driver = webdriver.Chrome()

#navigate driver to registration page
driver.get("https://www.bu.edu/link/bin/uiscgi_studentlink.pl/1477856296?ModuleName=reg/option/_start.pl&ViewSem=Spring%202017&KeySem=20174")

#authenticate using Kerberos username and password to gain access to registration pages
#loop until valid username password combination is entered
while True:

	#prompt for username
	username = input("Please input username: ")

	#put username in input field
	inputUsername = driver.find_element_by_name("user")
	inputUsername.send_keys(username)

	#prompt to get password
	password = getpass.getpass()

	#put password in input field and send "ENTER"
	inputPassword = driver.find_element_by_id("password")
	inputPassword.send_keys(password)
	inputPassword.send_keys(Keys.ENTER)

	try:
		#if this element exists, re-run loop to re-input credentials
		error = driver.find_element_by_class_name("error")
		print("Username or password incorrect")
		print("")
	except:
		#if the element doesn't exist, then log in was successful
		break

#navigate to planning to see all possible classes
#implicitly wait to for "plan" button to appear
driver.implicitly_wait(10)
driver.find_element_by_link_text("Plan").click()
driver.find_element_by_link_text("Add").click()

#select school from dropdown menu
#will expand this to accomodate all schools but for now, just CAS and computer science
inputSchool = Select(driver.find_element_by_css_selector("select[name=College]"))
inputSchool.select_by_visible_text('CAS')
inputDepartment = driver.find_element_by_css_selector("input[name=Dept]")
inputDepartment.send_keys("")
inputCourseNumber = driver.find_element_by_css_selector("input[name=Course]")
inputCourseNumber.send_keys("")
driver.find_element_by_css_selector("input[value=Go]").click()

#initialize dictionary to save data into
#initialize counters to keep track of how many pages scraped and how many times logged out
data = {}
classCount = 0
logoutCount = 0

#loop until alert on last page occurs
while True:
	try:
		#maybe find a better selector than this
		table = driver.find_element_by_css_selector("body > form:nth-child(5) > table:nth-child(1)")

		'''
		#"//tr" grab all tr
		#"/td" grab td's of all immediate children
		#[contains(text(), 'Lecture')] filters result where it contains text "Lecture"
		#"/.." returns parent of preceding statements
		# rows = table.find_elements_by_xpath("//tr/td[contains(text(),'Lecture')]/..")
		'''

		#"//tr" recursively searches for all tr on page
		#"/td" get above's td elements
		#"[text()='Lecture' or text()='Independent' or text()='Directed Study']" makes sure the td text is either Lecture, Independent or Directed Study
		#"/.." grabs the parents of this entire expression
		rows = table.find_elements_by_xpath("//tr/td[text()='Lecture' or text()='Independent' or text()='Directed Study']/..")


		#iterate through all rows on the page that are lectures, independent, or directed study
		for row in rows:

			#grab all tds and do some processing to grab just the professor name and lecture times
			tds = row.find_elements_by_tag_name("td")
			lectureTimes = str(tds[10].text) + " " + str(tds[11].text) + "-" + str(tds[12].text)

			#sometimes no professor name is specified on the registration page
			try:
				professorName = str(tds[3].text).split("\n")[1]
			except:
				professorName = "N/A"

			#grab all the links in the row
			#usually the first link in the row is the link to the class page but sometimes the "class is blocked/full" flag appears as a link
			#just pop off the link that goes to the "why is this class blocked" page from the list of links
			classLinks = row.find_elements_by_tag_name("a")
			if classLinks[0].text == "":
				classLinks.pop(0)
			courseNumber = str(classLinks[0].text)

			#use requests to get the html text from the desired link
			r = requests.get(classLinks[0].get_attribute('href'))
			soup = BeautifulSoup(r.text, 'html.parser')

			#grab necessary data from class page
			descRow = soup.findAll("tr", {"align": "left"})
			for counter, item in enumerate(descRow):
				if counter == 1:
					courseTitle = item.get_text().split("\n")[2]
				if counter == 2:
					courseDescription = item.get_text().split("\n")[2]

			#add data to dictionary
			data[courseNumber] = {"courseTitle": courseTitle, "courseDescription": courseDescription, "lectureTimes": lectureTimes, "professor": professorName}

			print("")
			print("Course Number: " + courseNumber)
			print("professor: " + professorName)
			print("Lecture Times: " + lectureTimes)
			print("Course Description: " + courseDescription)
			print("")

			#increment counter
			classCount += 1

		#click next button for next page of classes
		driver.find_element_by_xpath("//input[@value = 'Continue Search from:' and @type = 'button']").click()

		#alert will pop up when hitting the last page, this will handle it and break from the loop
		try:
			WebDriverWait(driver, 3).until(EC.alert_is_present(),'Timed out waiting for PA creation ' + 'confirmation popup to appear.')
			alert = driver.switch_to_alert()
			alert.accept()
			break
		except TimeoutException:
			pass
	except:

		#if you get logged out by Kerberos
		print
		print("Re-inputting credentials")
		print
		logoutCount += 1
		inputUsername = driver.find_element_by_name("user")
		inputUsername.send_keys(username)
		inputPassword = driver.find_element_by_id("password")
		inputPassword.send_keys(password)
		inputPassword.send_keys(Keys.ENTER)

#print the data out
# pprint.pprint(data)

#write dictionary to classes.json file
with open("classes.json", "w") as f:
	f.write(json.dumps({"classes": data}))

elapsed_time = time.time() - start_time

print("")
print("Number of classes scraped: " + str(classCount))
print("Number of times logged out: " + str(logoutCount))
print("Time elapsed: " + str(elapsed_time))
print("")
print("Finished")
driver.close()