
import logging.config
import os
import pytest
from core.excel_reader import load_config, load_test_cases
from core.reporter import CustomHtmlReporter

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


def pytest_configure(config):
    """Register the custom HTML dashboard reporter."""
    config.pluginmanager.register(CustomHtmlReporter(), "custom_html_reporter")


EXCEL_PATH = os.getenv("TEST_DATA_PATH", r"C:\Users\ADMIN\Downloads\test_data3.xlsx")


@pytest.fixture(scope="session")
def config():
    return load_config(EXCEL_PATH)


@pytest.fixture(scope="session")
def all_test_cases():
    return load_test_cases(EXCEL_PATH)


@pytest.fixture(scope="session")
def context():
    # Shared mutable dict across the whole run, used for chained
    # values like {TC001.id} referenced by later rows.
    return {}



