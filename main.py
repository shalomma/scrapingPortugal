import os
import time
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from anticaptchaofficial.imagecaptcha import imagecaptcha
from PIL import Image


def set_options():
    options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': f'{os.getcwd()}'}
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('prefs', prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('start-maximized')
    return options


def fill_up_form(id_number, birthdate):
    # Accept
    driver.find_element(By.CSS_SELECTOR, 'button#j_idt71').click()
    # Efetuar agendamento
    driver.find_element(By.XPATH, '//span[contains(text(),"Efetuar")]').click()
    # Nº b. i
    driver.find_element(By.XPATH, '//input[@id = "scheduleForm:tabViewId:ccnum"]').send_keys(id_number)
    # Data de nascimento
    driver.find_element(By.XPATH,
                        '//input[@id = "scheduleForm:tabViewId:dataNascimento_input"]').send_keys(birthdate)
    # Pesquisar
    driver.find_element(By.XPATH, '//span[contains(text(),"Pesquisar")]').click()
    # Posto
    post_elem = \
        driver.find_element(By.XPATH,
                            '//div[@id="scheduleForm:postcons_panel"]//ul[contains(@class,"ui-widget-content")]/li[2]')
    driver.execute_script("arguments[0].click();", post_elem)
    # Categoria do Ato Consular
    cat_elem = \
        driver.find_element(By.XPATH,
                            '//div[@id="scheduleForm:categato_panel"]//ul[contains(@class,"ui-widget-content")]/li[3]')
    driver.execute_script("arguments[0].click();", cat_elem)
    # Ato Consular
    consular_elem = \
        driver.find_element(By.XPATH,
                            '//div[@id="scheduleForm:atocons_panel"]//ul[contains(@class,"ui-widget-content")]/li[2]')
    driver.execute_script("arguments[0].click();", consular_elem)
    # Adicionar Ato Consular
    driver.find_element(By.XPATH, '//span[contains(text(),"Ato Consular")]').click()
    # declaro condições
    driver.find_element(By.CSS_SELECTOR, 'div.ui-chkbox-box.ui-widget').click()
    try:
        driver.find_element(By.CSS_SELECTOR, 'button#j_idt263').click()
    except ElementNotInteractableException:
        pass
    # Calendarizar
    driver.find_element(By.XPATH, '//span[contains(text(),"Calendarizar")]').click()
    # Captcha Solution
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[for="grantSchedulingFormID:captchaCode"]')))


def download_captcha_image():
    time.sleep(3)
    # driver.find_element(By.XPATH, '//*[@id="grantSchedulingDialogID"]').screenshot(img_file)
    driver.save_screenshot(img_file)
    time.sleep(3)


def solve_captcha():
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key(os.environ['anti_key'])

    im = Image.open(img_file)
    im1 = im.crop((700, 500, 1700, 1000))
    im1.save(img_file)

    text = solver.solve_and_return_solution(img_file)
    if text != 0:
        print("captcha text " + text)
    else:
        print("task finished with error " + solver.error_code)
        time.sleep(10)
    return text


def enter_captcha(text):
    print('enter captcha')
    captcha_code = driver.find_element(By.CSS_SELECTOR, r'#grantSchedulingFormID\:captchaCode')
    captcha_code.clear()
    captcha_code.send_keys(text)
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, r'#grantSchedulingFormID\:grantSchedulingContinueBtnID').click()


def reload_captcha():
    driver.find_element(By.XPATH, '//*[@id="exampleCaptcha_ReloadIcon"]').click()


def valid():
    try:
        time.sleep(2)
        warn_message = driver.find_element(By.CSS_SELECTOR, 'span.ui-messages-warn-summary').text
        if warn_message == 'O captcha deve ser válido':
            print('not valid solution')
            return False
        else:
            raise Exception('unknown warning message')
    except NoSuchElementException:
        print('valid solution')
        return True


def appointments():
    text = driver.find_element(By.XPATH, '//*[@id="scheduleForm:j_idt164"]/div[2]/table/tbody/tr[1]/td').text
    print('Appointment:', text)
    if text == 'De momento não existem vagas disponíveis, por favor tente mais tarde.':
        return False
    else:
        return True


def set_appointment():
    # Para finalizar a marcação, deve clicar no botão “Confirmar Agendamento”.
    # 1. calender window 2. click Confirmar Agendamento 3. Confirmar Agendamento
    # //*[@id="scheduleForm:submitScheduleBtn"]/span
    # //*[@id="confirmForm:confSaveScheduleButton"]/span
    return NotImplemented


def back_to_captcha():
    driver.find_element(By.XPATH,
                        '//div[@id="scheduleForm:j_idt164"]//span[contains(text(),"Voltar")]').click()
    driver.find_element(By.XPATH, '//span[contains(text(),"Calendarizar")]').click()


if __name__ == '__main__':
    url = 'https://agendamentosonline.mne.pt/AgendamentosOnline/index.jsf'
    img_file = 'captcha.png'

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=set_options())
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 15)
    driver.get(url)

    fill_up_form(os.environ['id_number'], os.environ['birthdate'])

    download_captcha_image()
    solution_text = solve_captcha()

    while True:
        enter_captcha(solution_text)
        if not valid():
            reload_captcha()
            download_captcha_image()
            solution_text = solve_captcha()
        else:
            if appointments():
                print('Hooray')
            else:
                back_to_captcha()
                time.sleep(5)
