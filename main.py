import os
import time
import keyboard
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from selenium.webdriver.common.action_chains import ActionChains


def STT():
    apikey = 'tqytT0wUDusv4hGwf3sxV_x8-KW2BblSI1qbIRIluMp6'
    url = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/0dff1284-e4e7-49fe-a95a-b6dff6c9df50'
    # Setup Service
    authenticator = IAMAuthenticator(apikey)
    stt = SpeechToTextV1(authenticator=authenticator)
    stt.set_service_url(url)
    # Perform conversion

    for file in os.listdir(os.getcwd()):
        if file.endswith('.wav'):
            voice = os.path.join(os.getcwd(), file)
            print(voice)
            with open(voice, 'rb') as f:
                res = stt.recognize(audio=f, content_type='audio/wav', model='en-US_NarrowbandModel',
                                    continuous=False).get_result()
            text = res['results'][0]['alternatives'][0]['transcript']
            return text


def Down_Submit(a_link, p_elem):
    for file in os.listdir():
        if file.endswith('.wav') or file.endswith('.png'):
            os.remove(file)
    driver.execute_script(f"window.open('{a_link}');"), time.sleep(3)
    actionChains = ActionChains(driver)
    actionChains.move_to_element(p_elem).context_click().perform()
    for c in 'search':
        keyboard.press_and_release(c)
    keyboard.press('enter')
    time.sleep(3)
    driver.switch_to.window(driver.window_handles[1])
    img_link = driver.find_element_by_css_selector('.card-section img').get_attribute('src')
    driver.get(img_link)
    driver.get_screenshot_as_file('./captcha.png')
    driver.switch_to.window(driver.window_handles[0])
    close_free_tabs()
    text = STT()
    if not text:
        text = 'None'
    print('text is ', text)
    driver.find_element(By.CSS_SELECTOR, '#grantSchedulingFormID\:captchaCode').send_keys(text), time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, '#grantSchedulingFormID\:grantSchedulingContinueBtnID').click()


def solution():
    audio_link = driver.find_element(By.CSS_SELECTOR, '#exampleCaptcha_SoundLink').get_attribute('href')
    img_elem = driver.find_element(By.XPATH, '//img[contains(@id,"CaptchaImage")]')
    Down_Submit(audio_link, img_elem), time.sleep(3)


def validate():
    validation = True
    try:
        warn_message = driver.find_element(By.CSS_SELECTOR, 'span.ui-messages-warn-summary').text
        if warn_message == 'O captcha deve ser válido':
            validation = False
    except:
        pass
    if not validation:
        driver.find_element(By.CSS_SELECTOR, 'img.BDC_ReloadIcon').click(), time.sleep(2)
        audio_link = driver.find_element(By.CSS_SELECTOR, '#exampleCaptcha_SoundLink').get_attribute('href')
        img_elem = driver.find_element(By.XPATH, '//img[contains(@id,"CaptchaImage")]')
        captcha_elem = driver.find_element(By.CSS_SELECTOR, '#grantSchedulingFormID\:captchaCode')
        captcha_elem.send_keys(Keys.CONTROL, 'a')
        captcha_elem.send_keys(Keys.DELETE)
        Down_Submit(audio_link, img_elem)
    try:
        warn_message = driver.find_element(By.CSS_SELECTOR, 'span.ui-messages-warn-summary').text
        if warn_message == 'O captcha deve ser válido':
            validate()
    except:
        pass


def lanch_browser(url):
    driver.get(url)
    driver.maximize_window()


def close_free_tabs():
    tabs = driver.window_handles
    current_tab = driver.current_window_handle
    for tab in tabs:
        driver.switch_to.window(tab)
        if tab == current_tab:
            continue
        else:
            driver.close()
    driver.switch_to.window(current_tab)


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    # options.add_extension('.\\unlock.crx')
    prefs = {'download.default_directory': f'{os.getcwd()}'}
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('prefs', prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('start-maximized')

    url = 'https://agendamentosonline.mne.pt/AgendamentosOnline/index.jsf'
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 15)
    driver.get(url)

    '''Form Filling'''
    # Accept
    driver.find_element(By.CSS_SELECTOR, 'button#j_idt71').click()
    # Efetuar agendamento
    driver.find_element(By.XPATH, '//span[contains(text(),"Efetuar")]').click()
    # Nº b. i
    driver.find_element(By.XPATH, '//input[@id = "scheduleForm:tabViewId:ccnum"]').send_keys(9058392233)
    # Data de nascimento
    driver.find_element(By.XPATH, '//input[@id = "scheduleForm:tabViewId:dataNascimento_input"]').send_keys('24-04-1987')
    # Pesquisar
    driver.find_element(By.XPATH, '//span[contains(text(),"Pesquisar")]').click()
    # Posto
    Post_elem = driver.find_element(By.XPATH,
                                    '//div[@id="scheduleForm:postcons_panel"]//ul[contains(@class,"ui-widget-content")]/li[2]')
    driver.execute_script("arguments[0].click();", Post_elem)
    # Categoria do Ato Consular
    Cat_elem = driver.find_element(By.XPATH,
                                   '//div[@id="scheduleForm:categato_panel"]//ul[contains(@class,"ui-widget-content")]/li[3]')
    driver.execute_script("arguments[0].click();", Cat_elem)
    # Ato Consular
    Consular_elem = driver.find_element(By.XPATH,
                                        '//div[@id="scheduleForm:atocons_panel"]//ul[contains(@class,"ui-widget-content")]/li[2]')
    driver.execute_script("arguments[0].click();", Consular_elem)
    # Adicionar Ato Consular
    driver.find_element(By.XPATH, '//span[contains(text(),"Ato Consular")]').click()
    # declaro condições
    driver.find_element(By.CSS_SELECTOR, 'div.ui-chkbox-box.ui-widget').click()
    try:
        driver.find_element(By.CSS_SELECTOR, 'button#j_idt263').click()
    except:
        pass
    # Calendarizar
    driver.find_element(By.XPATH, '//span[contains(text(),"Calendarizar")]').click()
    # Captcha Solutilon
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[for="grantSchedulingFormID:captchaCode"]')))
    solution()
    validate()
