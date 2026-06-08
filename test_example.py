import re
import pathlib
import sys
import pytest

from pa6webtest.pages.pa6web import PA6Web
from pa6webtest.locators.common import text, MAIN_MENU, MENU_LABEL, SCHEDULER_EVENTS_XPATH, SUBMENU_LIST, GRID_TABLE


REP_UUID = 'bc68a7bc-a5c4-4520-ae1e-8139d824bc45'
PRJ_UUID = 'c6c298c2-419a-480e-b815-5511847125d4'
REPORT_NAME = 'Filter Upstream T49817'
REPORT_REGEX = fr'{REPORT_NAME}.*\.pdf'

MENU_LABELS_XPATH = MAIN_MENU + SUBMENU_LIST + MENU_LABEL

task_name = f"Export '{REPORT_NAME}' ({REP_UUID}) report publication to file"
spin = '.spin'


# Scheduler method
def get_scheduler_events(open_scheduler):
    return open_scheduler.locator(SCHEDULER_EVENTS_XPATH)


@pytest.fixture(scope='module')
def publication_create(open_report, browser):
    open_report.create_publication()
    browser.pages[-1]


def test_add_event(publication_create, open_scheduler):
    open_scheduler.main_menu_click('Add event > Add event to execute at specified time')
    events = get_scheduler_events(open_scheduler).inner_text()
    assert 'TimeEvent' in events


def test_add_task(open_scheduler):
    all_events = get_scheduler_events(open_scheduler)
    time_event = all_events.locator(text('TimeEvent'))
    time_event.first.context_menu_click('Add task > Export publication to file')
    modal_window = open_scheduler.modal_window()
    modal_window.locator(text(REPORT_NAME)).last.click()
    modal_window.button('Open').click()
    # нужно снова кликнуть на событие, иначе assert не сработает
    time_event.first.click()    
    open_scheduler.waiting(1000)
    content = all_events.inner_text()
    assert REP_UUID in content


# fixture to delete created tasks
@pytest.fixture()
def tasks_remove(open_scheduler):
    yield
    open_scheduler.locator(text('TimeEvent')).context_menu_click('Delete')
    modal_window = open_scheduler.modal_window()
    assert modal_window.is_visible()
    assert 'Are you sure you want to delete the selected item?' in modal_window.text_content()
    open_scheduler.confirm('Yes')
    open_scheduler.waiting(1000)


# fixture to delete exported files
@pytest.fixture()
def files_remove(open_scheduler, browser):
    yield
    open_scheduler.main_menu_click('My applications > PolyAnalyst Drive')
    polyanalyst_drive = PA6Web((browser.pages[1]))
    files = polyanalyst_drive.locator(GRID_TABLE).last.inner_text().split('\n')
    reports = [file for file in files if file.startswith(REPORT_NAME)]
    for report in reports:
        polyanalyst_drive.locator(text(report)).last.context_menu_click('Delete...')
        modal_window = polyanalyst_drive.modal_window()
        assert modal_window.is_visible()
        assert f'Are you sure you want to delete {report}.pdf?' in modal_window.text_content()
        polyanalyst_drive.confirm('Yes')        
        polyanalyst_drive.waiting(1000)
    polyanalyst_drive.page.close()


def test_publication_export(open_scheduler, tasks_remove, files_remove):        
    open_scheduler.locator(text(task_name)).first.click()
    open_scheduler.locator(text('PNG')).first.click()
    open_scheduler.locator(text('PDF')).first.click()
    open_scheduler.locator(text(task_name)).first.context_menu_click('Test (immediate execution)')    
    open_scheduler.locator(spin).object.wait_for(state='detached', timeout=0)
    assert open_scheduler.locator(spin).is_hidden()
    etalon_path = (pathlib.Path(__file__).parents[1] / 'test_etalons' / 'Filter Upstream T49817.pdf')
    assert re.match(REPORT_REGEX, etalon_path.name)


if __name__ == "__main__":
    sys.path.append(str(pathlib.Path(__file__).parents[1]))
    from run_test import run_test

    sys.exit(run_test(__file__))
