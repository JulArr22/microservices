# -*- coding: utf-8 -*-
"""Functions that interact with the data."""
import logging

logger = logging.getLogger(__name__)

# Machine functions ##################################################################################
machine_status = "Machine Status: Idle"

async def set_status_of_machine(status):
    global machine_status
    machine_status = status

async def get_status_of_machine():
    return machine_status
