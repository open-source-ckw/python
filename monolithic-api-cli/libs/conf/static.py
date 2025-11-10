"""
This file is created to provide direct access of configuration and mantain configurable nature of app
How to use?
just import conf_static and start using it, its just an instance of ConfService
this mantain multiple instance creation and make it centrialised using "module as a singleton" in python

from libs.conf.static import conf_static
print(conf_static.app_name)

all static.py files in entire project follow the same pattern
this is not required  but as per use case

USE DI FOR BUSSINESS LOGIC THIS IS JUST FOR SOME COMPEX SCNARIO 
WHERE MANTAINING CONFIGURABLE NATURE OF APP BECOME BOTTLE NECK
"""
from typing import Final
from libs.conf.service import ConfService

conf_static: Final = ConfService()