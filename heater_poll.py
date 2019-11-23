#!/usr/bin/python3

import json
import logging
import logging
import time

from heater_program import Program
from relay import Relay
import settings_handler
import util


logger_name = 'thermostat'
logging.basicConfig(
    format='{levelname:<8} {asctime} - {message}',
    style='{'
)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)


def read_settings(path_to_settings):

    with open(path_to_settings) as f:
        settings_file = json.load(f)

    return settings_file


def poll(path_to_settings, heater_switch, current):

    settings = read_settings(path_to_settings)
    manual_on = settings['manual']
    manual_off = not settings['manual']
    auto_on = settings['auto']
    auto_off = not settings['auto']
    prog_no = settings['program']

    if manual_on:
        if not heater_switch.stats: # heater is not ON
            heater_switch.on()
        time.sleep(1)
        return 1

    elif manual_off and auto_on:
        # time_to_wait = 5
        program = Program(settings['program'])
        logger.debug(f"Loaded program {program_number}.")

        logger.debug(
            f"It is {current['formatted_time']} on {current['weekday'].title()}."
        )
        # # compensate waiting time
        # time_to_wait = util.five_o(
        #     current['seconds'], current['microseconds']
        # )
        # relay vs program relation
        time_elapsed = util.program_vs_relay(
            program.program[current['weekday']][str(current['hours'])],
            heater_switch,
            time_elapsed
        )
        # finally, wait for 5 minutes
        heater_switch.catch_sleep(time_to_wait, time_elapsed)

    elif manual_off and auto_off:
        if heater_switch.stats:
            logger.debug("Received signal to turn heater OFF.")
            heater_switch.off()


def main():

    path_to_settings = 'settings.json'
    heater_switch = Relay('36')
    time_elapsed = 0
    last_current = None

    while True:

        # check each loop for when we are in history
        current = util.get_now()

        if last_current['day'] != current['day']:
            logger.debug('Entered another day in history.')
            util.write_log(
                {
                    "date": "{} {}".format(
                        last_current['weekday'],
                        last_current['formatted_time']
                    ),
                    "time_elapsed": time_elapsed
                }
            )
            time_elapsed = 0

        time_elapsed += poll(path_to_settings, heater_switch, current)
        settings_handler.main(util.format_seconds(time_elapsed))
        last_current = current


if __name__ == '__main__':
    main()