import os
import sys
import time
import yagmail
from PIL import Image
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from anticaptchaofficial.imagecaptcha import imagecaptcha


class Driver:
    def __init__(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=self.set_options())
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)

    def open(self, url):
        self.driver.get(url)

    def close(self):
        self.driver.close()

    @staticmethod
    def set_options():
        options = webdriver.ChromeOptions()
        prefs = {'download.default_directory': f'{os.getcwd()}'}
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument('start-maximized')
        return options

    def fill_up_form(self, id_number, birthdate):
        self.driver.find_element(By.CSS_SELECTOR, 'button#j_idt71').click()  # Accept
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Efetuar")]').click()  # Efetuar agendamento
        self.driver.find_element(By.XPATH, '//input[@id = "scheduleForm:tabViewId:ccnum"]').send_keys(id_number)
        self.driver.find_element(
            By.XPATH, '//input[@id = "scheduleForm:tabViewId:dataNascimento_input"]').send_keys(birthdate)
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Pesquisar")]').click()  # Pesquisar
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
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Ato Consular")]').click()  # Adicionar Ato Consular
        self.driver.find_element(By.CSS_SELECTOR, 'div.ui-chkbox-box.ui-widget').click()  # declaro condições
        try:
            self.driver.find_element(By.CSS_SELECTOR, 'button#j_idt263').click()
        except ElementNotInteractableException:
            pass
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Calendarizar")]').click()  # Calendarizar

        self.wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '[for="grantSchedulingFormID:captchaCode"]')))  # Captcha Solution

    def enter_captcha(self, text):
        print('enter captcha')
        captcha_code = self.driver.find_element(By.CSS_SELECTOR, r'#grantSchedulingFormID\:captchaCode')
        captcha_code.clear()
        captcha_code.send_keys(text)
        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR, r'#grantSchedulingFormID\:grantSchedulingContinueBtnID').click()

    def download(self, file):
        time.sleep(3)
        # driver.find_element(By.XPATH, '//*[@id="grantSchedulingDialogID"]').screenshot(img_file)
        # screenshot_as_bytes = \
        # driver.find_element(By.XPATH, '//*[@id="exampleCaptcha_CaptchaImageDiv"]').screenshot_as_png
        # with open(img_file, 'wb') as f:
        #     f.write(screenshot_as_bytes)
        self.driver.save_screenshot(file)
        self.crop(file)
        time.sleep(3)

    @staticmethod
    def crop(file):
        im = Image.open(file)
        im = im.crop((700, 500, 1700, 1000))
        im.save(file)

    def reload_captcha(self):
        self.driver.find_element(By.XPATH, '//*[@id="exampleCaptcha_ReloadIcon"]').click()

    def valid(self):
        try:
            time.sleep(2)
            warn_message = self.driver.find_element(By.CSS_SELECTOR, 'span.ui-messages-warn-summary').text
            if warn_message == 'O captcha deve ser válido':
                print('not valid solution')
                return False
            else:
                raise Exception('unknown warning message')
        except NoSuchElementException:
            print('valid solution')
            return True

    def are_appointments(self):
        text = self.driver.find_element(By.XPATH, '//*[@id="scheduleForm:j_idt164"]/div[2]/table/tbody/tr[1]/td').text
        print('Appointment:', text)
        if text == 'De momento não existem vagas disponíveis, por favor tente mais tarde.':
            return False
        else:
            return True

    @staticmethod
    def set_appointment():
        # Para finalizar a marcação, deve clicar no botão “Confirmar Agendamento”.
        # 1. calender window 2. click Confirmar Agendamento 3. Confirmar Agendamento
        # //*[@id="scheduleForm:submitScheduleBtn"]/span
        # //*[@id="confirmForm:confSaveScheduleButton"]/span
        return NotImplemented

    def back_to_captcha(self):
        self.driver.find_element(
            By.XPATH, '//div[@id="scheduleForm:j_idt164"]//span[contains(text(),"Voltar")]').click()
        self.driver.find_element(By.XPATH, '//span[contains(text(),"Calendarizar")]').click()


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

    def whatsapp(self, text):
        self.client.messages.create(
            body=text,
            from_=f"whatsapp:+{os.environ['twilio_whatsapp']}",
            to=f"whatsapp:+{os.environ['my_whatsapp']}"
        )

    def email(self, text):
        self.yag.send(
            to=os.environ['email'],
            subject=text,
            contents=''
        )


def delay(seconds):
    for i in range(seconds, 0, -1):
        print(f"{i // 60:02d}:{i % 60:02d}", end="\r", flush=True)
        time.sleep(1)


if __name__ == '__main__':
    appointments_url = 'https://agendamentosonline.mne.pt/AgendamentosOnline/index.jsf'
    img_file = 'captcha.png'

    driver = Driver()
    captcha_solver = CaptchaSolver(img_file)
    alerter = Alerter()

    while True:
        driver.open(appointments_url)
        driver.fill_up_form(os.environ['id_number'], os.environ['birthdate'])

        driver.download(img_file)
        solution_text = captcha_solver()

        counter = 0
        try:
            while True:
                counter += 1
                print('try ', counter)
                driver.enter_captcha(solution_text)
                if not driver.valid():
                    driver.reload_captcha()
                    driver.download(img_file)
                    solution_text = captcha_solver()
                else:
                    if driver.are_appointments():
                        alerter.whatsapp('There are Appointments!')
                        alerter.email('There are Appointments!')
                        driver.set_appointment()
                    else:
                        driver.back_to_captcha()
                        delay(5)
        except KeyboardInterrupt:
            sys.exit(0)
        except NoSuchElementException:
            alerter.whatsapp('process broke')
            driver.close()
