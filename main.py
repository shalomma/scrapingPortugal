import os
import random
import time
import yagmail
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import \
    NoSuchElementException, ElementNotInteractableException, TimeoutException, NoSuchWindowException
from anticaptchaofficial.imagecaptcha import imagecaptcha


class Driver:
    def __init__(self, headless=True, page_load=True):
        self.driver = webdriver.Chrome(ChromeDriverManager().install(),
                                       desired_capabilities=self.set_desired_capabilities(page_load),
                                       options=self.set_options(headless))
        self.wait = WebDriverWait(self.driver, timeout=10)
        self.driver.implicitly_wait(5)

    def open(self, url):
        self.driver.get(url)

    def close(self):
        self.driver.close()

    def quit(self):
        self.driver.quit()

    @staticmethod
    def set_desired_capabilities(page_load):
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "normal" if page_load else "none"
        return caps

    @staticmethod
    def set_options(headless):
        options = webdriver.ChromeOptions()
        prefs = {'download.default_directory': f'{os.getcwd()}'}
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        if headless:
            options.add_argument('start-maximized')
            options.add_argument("headless")
            options.add_argument("window-size=2880,1800")
            options.add_argument("start-maximized")
            options.add_argument("disable-gpu")
            options.add_argument('disable-extensions')
            options.add_argument('no-sandbox')
        return options

    def fill_up_form(self, id_number, birthdate, delay=0):
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[for="scheduleForm:tabViewId:ccnum"]')))
        self.quasi_random_delay(0, delay)
        self.driver.find_element(By.XPATH, '//input[@id = "scheduleForm:tabViewId:ccnum"]').send_keys(id_number)
        self.quasi_random_delay(0, delay)
        self.driver.find_element(
            By.XPATH, '//input[@id = "scheduleForm:tabViewId:dataNascimento_input"]').send_keys(birthdate)
        self.driver.find_element(By.XPATH, '//*[@id="scheduleForm:tabViewId:searchIcon"]/span').click()  # Pesquisar
        post_elem = \
            self.driver.find_element(
                By.XPATH, '//div[@id="scheduleForm:postcons_panel"]//ul[contains(@class,"ui-widget-content")]/li[2]')
        self.driver.execute_script("arguments[0].click();", post_elem)  # Posto
        cat_elem = \
            self.driver.find_element(
                By.XPATH, '//div[@id="scheduleForm:categato_panel"]//ul[contains(@class,"ui-widget-content")]/li[3]')
        self.driver.execute_script("arguments[0].click();", cat_elem)  # Categoria do Ato Consular
        consular_elem = \
            self.driver.find_element(
                By.XPATH, '//div[@id="scheduleForm:atocons_panel"]//ul[contains(@class,"ui-widget-content")]/li[2]')
        self.driver.execute_script("arguments[0].click();", consular_elem)  # Ato Consular
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Ato Consular")]').click()
        self.driver.find_element(By.CSS_SELECTOR, 'div.ui-chkbox-box.ui-widget').click()  # checkbox
        try:
            self.driver.find_element(By.CSS_SELECTOR, 'button#j_idt263').click()
        except ElementNotInteractableException:
            pass
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Calendarizar")]').click()

    def enter_captcha(self, text):
        print('enter captcha')
        captcha_code = self.driver.find_element(By.CSS_SELECTOR, r'#grantSchedulingFormID\:captchaCode')
        captcha_code.clear()
        captcha_code.send_keys(text)
        self.driver.find_element(By.CSS_SELECTOR, r'#grantSchedulingFormID\:grantSchedulingContinueBtnID').click()

    def download(self, file):
        time.sleep(3)
        screenshot_as_bytes = \
            self.driver.find_element(By.XPATH, '//*[@id="exampleCaptcha_CaptchaImageDiv"]').screenshot_as_png
        with open(file, 'wb') as f:
            f.write(screenshot_as_bytes)

    def reload_captcha(self):
        self.driver.find_element(By.XPATH, '//*[@id="exampleCaptcha_ReloadIcon"]').click()

    def valid(self):
        try:
            print('Checking validity: ', end='', flush=True)
            time.sleep(2)
            warn_message = self.driver.find_element(By.CSS_SELECTOR, 'span.ui-messages-warn-summary').text
            if warn_message == 'O captcha deve ser válido':
                print('not valid')
                return False
            else:
                raise Exception('unknown warning message')
        except NoSuchElementException:
            print('valid')
            return True

    def are_appointments(self):
        text = self.driver.find_element(By.XPATH, '//*[@id="scheduleForm:j_idt164"]/div[2]/table/tbody/tr[1]/td').text
        if text == 'De momento não existem vagas disponíveis, por favor tente mais tarde.':
            print(text.encode('ascii', 'ignore').decode('ascii'))
            return False
        else:
            print('#' * 80)
            print('Appointment!')
            print('#' * 80)
            return True

    @staticmethod
    def set_appointment():
        # Para finalizar a marcação, deve clicar no botão “Confirmar Agendamento”.
        # 1. calender window 2. click Confirmar Agendamento 3. Confirmar Agendamento
        # //*[@id="scheduleForm:submitScheduleBtn"]/span
        # //*[@id="confirmForm:confSaveScheduleButton"]/span
        raise NotImplemented

    def back_to_captcha(self):
        self.driver.find_element(
            By.XPATH, '//div[@id="scheduleForm:j_idt164"]//span[contains(text(),"Voltar")]').click()
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Calendarizar")]').click()

    @staticmethod
    def quasi_random_delay(seconds, noise=0):
        seconds += random.randint(0, noise)
        for i in range(seconds, 0, -1):
            print(f"{i // 60:02d}:{i % 60:02d}", end="\r", flush=True)
            time.sleep(1)


class CaptchaSolver:
    def __init__(self, dst_file):
        self.dst_file = dst_file
        self.solver = imagecaptcha()
        self.solver.set_verbose(1)
        self.solver.set_key(os.environ['anti_key'])

    def __call__(self):
        text = self.solver.solve_and_return_solution(self.dst_file)
        if text != 0:
            print("captcha text " + text)
        else:
            print("task finished with error " + self.solver.error_code)
            time.sleep(10)
        return text


class Alerter:
    def __init__(self):
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        self.client = Client(account_sid, auth_token)
        self.yag = yagmail.SMTP(os.environ['email'])

    def whatsapp(self, text, n_times=1):
        for i in range(n_times, 0, -1):
            self.client.messages.create(
                body=text,
                from_=f"whatsapp:+{os.environ['twilio_whatsapp']}",
                to=f"whatsapp:+{os.environ['my_whatsapp']}"
            )
            time.sleep(3)

    def email(self, text):
        self.yag.send(
            to=os.environ['email'],
            subject=text,
            contents=''
        )


def quick_lunch(url):
    driver_ = Driver(headless=False)
    driver_.driver.implicitly_wait(1)
    driver_.open(url)
    driver_.fill_up_form(os.environ['id_number'], os.environ['birthdate'])


if __name__ == '__main__':
    img_file = 'captcha.png'

    captcha_solver = CaptchaSolver(img_file)
    alerter = Alerter()

    while True:
        driver = Driver(headless=False, page_load=True)
        driver.open(os.environ['appointments_url'])
        driver.fill_up_form(os.environ['id_number'], os.environ['birthdate'], 5)

        driver.download(img_file)
        solution_text = captcha_solver()

        counter = 0
        valid_counter = 0
        try:
            while True:
                counter += 1
                print('try ', counter)
                driver.enter_captcha(solution_text)
                if not driver.valid():
                    if valid_counter == 4:
                        break
                    driver.reload_captcha()
                    driver.download(img_file)
                    solution_text = captcha_solver()
                    valid_counter += 1
                else:
                    valid_counter = 0
                    if driver.are_appointments():
                        alerter.whatsapp('Your appointment code is here', 4)
                        alerter.email('There are Appointments!')
                        # quick_lunch(os.environ['appointments_url'])
                        # driver.set_appointment()
                        driver.quasi_random_delay(90, 30)
                    else:
                        driver.back_to_captcha()
                    driver.quasi_random_delay(120)
        except KeyboardInterrupt:
            pass
        except (NoSuchElementException, ElementNotInteractableException, TimeoutException, NoSuchWindowException):
            alerter.whatsapp('Your appointment code is broken')
            alerter.email('Something went wrong...')
            driver.quasi_random_delay(120)
        driver.quit()
