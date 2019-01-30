# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 13:26:38 2019

@author: daniel
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#coding=utf8

def ask_yes_no(question):
    """
    Ask a yes or no questions.
    """
    response = None
    while response not in ('y', 'n'):
        response = input(question).lower()
    return response

ask_yes_no("Please input 'y' or 'n' for continue or abort the test:")