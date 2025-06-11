import pytest
from types import SimpleNamespace
from dom_heal import extractor

class DummyElement:
    def __init__(self, tag_name, attrs, text=''):
        self.tag_name = tag_name
        self._attrs = attrs
        self.text = text
    def get_attribute(self, name):
        return self._attrs.get(name)

class DummyDriver:
    def __init__(self, elements, xpath_values=None, data_attrs=None):
        self._elements = elements
        self.xpath_values = xpath_values or {}
        self.data_attrs = data_attrs or {}
        self.ready_state = 'complete'
        self.quit_called = False
        self.last_url = None

    def get(self, url):
        self.last_url = url

    def execute_script(self, script, *args):
        if script == "return document.readyState":
            return self.ready_state
        if script == extractor.JS_OBTER_XPATH:
            return self.xpath_values.get(args[0], "/dummy")
        if script == extractor.JS_OBTER_DATA_ATTRS:
            return self.data_attrs.get(args[0], {})
        return None

    def find_elements(self, by, query):
        return self._elements

    def quit(self):
        self.quit_called = True

def test_carregar_pagina_waits_complete(monkeypatch):
    driver = SimpleNamespace()
    driver.get = lambda url: setattr(driver, 'last_url', url)
    driver.execute_script = lambda cmd: 'complete' if cmd == "return document.readyState" else None
    monkeypatch.setattr(extractor.time, 'sleep', lambda s: None)
    extractor.carregar_pagina(driver, "http://test", tempo_max=1, wait_after_load=0.5)
    assert driver.last_url == "http://test"

def test_carregar_pagina_timeout(monkeypatch):
    driver = SimpleNamespace()
    driver.get = lambda url: None
    calls = {'n': 0}
    def exec_script(cmd):
        if cmd == "return document.readyState":
            calls['n'] += 1
            return 'loading' if calls['n'] < 3 else 'complete'
        return None
    driver.execute_script = exec_script
    monkeypatch.setattr(extractor.time, 'sleep', lambda s: None)
    extractor.carregar_pagina(driver, "http://test", tempo_max=5, wait_after_load=0)
    assert calls['n'] >= 3

def test_montar_info_elemento_sem_placeholder_e_aria():
    elem = DummyElement('input', {'id':'i1','class':'c','name':'n','type':'t'}, text=' txt ')
    xpath_map = {elem: '/html/body/input[1]'}
    driver = DummyDriver([elem], xpath_values=xpath_map)
    info = extractor.montar_info_elemento(driver, elem)
    expected = {
        'tag': 'input', 'id': 'i1', 'class': 'c',
        'text': 'txt', 'name': 'n', 'type': 't',
        'aria_label': '', 'placeholder': '',
        'xpath': '/html/body/input[1]'
    }
    assert all(info[k] == expected[k] for k in expected)
    assert set(info.keys()) >= set(expected.keys())

def test_montar_info_com_data_attrs():
    elem = DummyElement('div', {}, text='')
    xpath_map = {elem: '/html/body/div[1]'}
    data_attrs = {elem: {'data_a': 'v'}}
    driver = DummyDriver([elem], xpath_values=xpath_map, data_attrs=data_attrs)
    info = extractor.montar_info_elemento(driver, elem)
    assert info['data_a'] == 'v'

def test_obter_xpath_direct():
    elem = DummyElement('div', {}, '')
    xpath_map = {elem: '/html/body/div[1]'}
    driver = DummyDriver([], xpath_values=xpath_map)
    xp = extractor.obter_xpath(driver, elem)
    assert xp == '/html/body/div[1]'

def test_extrair_dom_with_driver():
    elems = [
        DummyElement('a', {'id':'i','class':'cl','name':'nm',
                            'type':'t','aria-label':'al','placeholder':'ph'},
                     text='abc'),
        DummyElement('span', {}, text='')
    ]
    xpath_map = {elems[0]: '/a[1]', elems[1]: '/span[1]'}
    data_attrs = {elems[0]: {'data_test': 'v1'}, elems[1]: {}}
    dummy = DummyDriver(elems, xpath_values=xpath_map, data_attrs=data_attrs)
    result = extractor.extrair_dom("http://x", driver=dummy)
    assert isinstance(result, list) and len(result) == 2
    first = result[0]
    assert first['id'] == 'i'
    assert first['aria_label'] == 'al'
    assert first['placeholder'] == 'ph'
    assert first['data_test'] == 'v1'
    assert dummy.quit_called is False

def test_extrair_dom_without_driver(monkeypatch):
    class FakeDriver(DummyDriver):
        def __init__(self):
            super().__init__([])
    fake = FakeDriver()
    monkeypatch.setattr(extractor, 'criar_driver', lambda: fake)
    monkeypatch.setattr(extractor, 'carregar_pagina', lambda d, u: None)
    monkeypatch.setattr(extractor, 'obter_elementos', lambda d: [])
    result = extractor.extrair_dom("http://y")
    assert result == []
    assert fake.quit_called is True
