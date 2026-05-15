import re
import pathlib
import sys
import pytest

from polyanalyst6api import API
from pa6webtest.locators.common import MAIN_MENU, MENU_LABEL, SCHEDULER_EVENTS_XPATH, SUBMENU_LIST


REP_UUID = 'bc68a7bc-a5c4-4520-ae1e-8139d824bc45'
PRJ_UUID = 'c6c298c2-419a-480e-b815-5511847125d4'
REPORT_NAME = 'Filter Upstream T49817'
REPORT_REGEX = fr'{REPORT_NAME}.*\.pdf'
GET_FILES_JSON_DATA = {"path": "@administrator@", "mask": "|pdf"}
HOST = 'https://localhost:5043'

MENU_LABELS_XPATH = MAIN_MENU + SUBMENU_LIST + MENU_LABEL

open_report_actions = ('Add task', 'Export publication to file', 'Root', REPORT_NAME, 'Open')
add_task_actions = ('Test (immediate execution)', )
export_formats = ('PNG', 'JPG', 'PDF', 'PPTX', 'ZIP')
task_name = f"Export '{REPORT_NAME}' ({REP_UUID}) report publication to file"
credentials = {'username': 'administrator', 'password': ''}


@pytest.fixture(scope='module')
def publication_create(open_report, browser):
    open_report.create_publication()
    browser.pages[-1]


@pytest.mark.parametrize("menu, sub_menu_index, name", [
    ("Add event", 0, "TimeEvent"),
    ("Add event", 1, "SrvStartEvent")
], ids=["TimeEvent", "SrvStartEvent"])
def test_add_event(publication_create, open_scheduler, menu, sub_menu_index, name):
    open_scheduler.main_menu_click(menu)
    submenu_items = open_scheduler.page.locator(MENU_LABELS_XPATH)
    submenu_items.nth(sub_menu_index).click()
    open_scheduler.waiting(3000)
    events = open_scheduler.page.locator(SCHEDULER_EVENTS_XPATH).all_inner_texts()
    assert name in events[0].split('\n')


@pytest.mark.parametrize("event_type", [('TimeEvent'), ('SrvStartEvent')])
def test_add_task(open_scheduler, event_type):
    open_scheduler.page.locator(f"text={event_type}").first.click()
    open_scheduler.page.locator(f"text={event_type}").first.click(button='right')
    for action in open_report_actions[:-1]:
        open_scheduler.page.locator(f"text={action}").last.click()
    open_scheduler.page.locator(f"text={open_report_actions[-1]}").last.click()
    open_scheduler.page.locator(f"text={event_type}").first.click()
    open_scheduler.waiting(3000)
    content = open_scheduler.page.locator(SCHEDULER_EVENTS_XPATH).all_inner_texts()
    assert any(REP_UUID in str for str in content)


@pytest.fixture(scope='module')
def tasks_remove(open_scheduler):
    yield
    event_type = ['TimeEvent', 'SrvStartEvent']
    for event in event_type:
        open_scheduler.page.locator(f"text={event}").first.click()
        open_scheduler.page.locator(f"text={event}").first.click(button='right')
        open_scheduler.page.locator("text='Delete'").last.click()
        modal_window = open_scheduler.modal_window()
        assert modal_window.is_visible()
        assert 'Are you sure you want to delete the selected item?' in modal_window.text_content()
        open_scheduler.confirm('Yes')


@pytest.mark.parametrize("task_name, order", [(task_name, 0), (task_name, 1)])
def test_publication_export(tasks_remove, open_scheduler, task_name, order):
    open_scheduler.page.locator(f"text={task_name}").nth(order).click()
    open_scheduler.page.locator('//*[@class="group"]').click()
    open_scheduler.page.locator(f"text={export_formats[2]}").first.click()
    open_scheduler.page.locator(f"text={task_name}").nth(order).click(button='right')
    open_scheduler.page.locator(f"text={add_task_actions[0]}").first.click()
    open_scheduler.waiting(3000)
    amount_of_arrow_icons = open_scheduler.page.locator('.spin').count()
    for i in range(amount_of_arrow_icons):
        open_scheduler.page.locator('.spin').nth(i).wait_for(state='detached', timeout=0)
    assert open_scheduler.page.locator('.spin').count() == 0


@pytest.fixture(scope='module')
def api():
    with API(HOST, credentials['username'], credentials['password'], verify=False) as api:
        yield api


@pytest.fixture(scope='module')
def files_remove(api):
    files = []
    yield files
    for file in files:
        api.request('/polyanalyst/api/v1.0/file/delete', method='post', json={"path": "@administrator@", "name": file})


def test_publication_file_exported(api, files_remove):
    home_folder = api.request('/polyanalyst/api/v1.0/folder/list', method='get', json=GET_FILES_JSON_DATA)
    file_names = [item['name'] for item in home_folder[1]['items']]
    etalon_path = (pathlib.Path(__file__).parents[1] / 'test_etalons' / 'Filter Upstream T49817.pdf')
    etalon_name = etalon_path.name
    for name in file_names:        
        assert re.match(REPORT_REGEX, etalon_name)
        files_remove.append(name)    


if __name__ == "__main__":
    sys.path.append(str(pathlib.Path(__file__).parents[1]))
    from run_test import run_test

    sys.exit(run_test(__file__))
