import os
import time

from main import Driver


def quick_lunch(url):
    driver_ = Driver(headless=False, page_load=False)
    driver_.driver.implicitly_wait(1)
    driver_.open(url)
    driver_.fill_up_form(os.environ['id_number'], os.environ['birthdate'])


if __name__ == '__main__':
    appointments_url = 'https://agendamentosonline.mne.pt/AgendamentosOnline/app/scheduleAppointmentForm.jsf'
    quick_lunch(appointments_url)
    time.sleep(500)
