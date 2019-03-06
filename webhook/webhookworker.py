import json
import logging
import requests
import time

from utils.gamemechanicutil import get_raid_boss_cp

log = logging.getLogger(__name__)


class WebhookWorker:
    def __init__(self, args, db_wrapper):
        self._worker_interval_sec = 10
        self._args = args
        self._db_wrapper = db_wrapper
        self._last_check = int(time.time())

    def __payload_type_count(self, payload):
        count = {}

        for elem in payload:
            count[elem["type"]] = count.get(elem["type"], 0) + 1

        return count

    def __send_webhook(self, payload):
        # get list of urls
        webhooks = self._args.webhook_url.replace(" ", "").split(",")

        for webhook in webhooks:
            # url cleanup
            url = webhook.strip()

            log.debug("Sending to webhook %s", url)
            log.debug("Payload: %s" % str(payload))
            try:
                response = requests.post(
                    url,
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=5,
                )
                if response.status_code != 200:
                    log.warning(
                        "Got status code other than 200 OK from webhook destination: %s"
                        % str(response.status_code)
                    )
                else:
                    log.debug(
                        "Element count: %s"
                        % json.dumps(self.__payload_type_count(payload))
                    )
                    log.info("Successful sent to webhook")
            except Exception as e:
                log.warning("Exception occured while sending webhook: %s" % str(e))

    def __prepare_raid_data(self, raid_data):
        ret = []

        for raid in raid_data:
            raid_payload = {
                "latitude": raid["latitude"],
                "longitude": raid["longitude"],
                "level": raid["level"],
                "pokemon_id": raid["pokemon_id"],
                "team_id": raid["team_id"],
                "cp": raid["cp"],
                "move_1": raid["move_1"],
                "move_2": raid["move_2"],
                "start": raid["start"],
                "end": raid["end"],
                "name": raid["name"],
            }

            if raid["cp"] is None:
                raid_payload["cp"] = get_raid_boss_cp(raid["pokemon_id"])

            if raid["pokemon_id"] is None:
                raid_payload["pokemon_id"] = 0

            if raid["gym_id"] is not None:
                raid_payload["gym_id"] = raid["gym_id"]

            if raid["url"] is not None and raid["url"]:
                raid_payload["url"] = raid["url"]

            if raid["weather_boosted_condition"] is not None:
                raid_payload["weather"] = raid["weather_boosted_condition"]

            # create finale message
            entire_payload = {"type": "raid", "message": raid_payload}

            # add to payload
            ret.append(entire_payload)

        return ret

    def __prepare_mon_data(self, mon_data):
        ret = []

        for mon in mon_data:
            mon_payload = {
                "encounter_id": mon["encounter_id"],
                "pokemon_id": mon["pokemon_id"],
                "last_modified_time": mon["last_modified"],
                "spawnpoint_id": mon["spawnpoint_id"],
                "latitude": mon["latitude"],
                "longitude": mon["longitude"],
                "disappear_time": mon["disappear_time"],
            }

            tth = despawn_time_unix - last_modified_time
            mon_payload["time_until_hidden_ms"] = tth

            if mon["pokemon_level"] is not None:
                mon_payload["pokemon_level"] = mon["pokemon_level"]

            if mon["cp_multiplier"] is not None:
                mon_payload["cp_multiplier"] = mon["cp_multiplier"]

            if mon["form"] is not None:
                mon_payload["form"] = mon["form"]

            if mon["cp"] is not None:
                mon_payload["cp"] = mon["cp"]

            if mon["individual_attack"] is not None:
                mon_payload["individual_attack"] = mon["individual_attack"]

            if mon["individual_defense"] is not None:
                mon_payload["individual_defense"] = mon["individual_defense"]

            if mon["individual_stamina"] is not None:
                mon_payload["individual_stamina"] = mon["individual_stamina"]

            if mon["move_1"] is not None:
                mon_payload["move_1"] = mon["move_1"]

            if mon["move_2"] is not None:
                mon_payload["move_2"] = mon["move_2"]

            if mon["height"] is not None:
                mon_payload["height"] = mon["height"]

            if mon["weight"] is not None:
                mon_payload["weight"] = mon["weight"]

            if mon["gender"] is not None:
                mon_payload["gender"] = mon["gender"]

            if mon["weather_boosted_condition"] is not None:
                mon_payload["boosted_weather"] = mon["weather_boosted_condition"]

            # create finale message
            entire_payload = {"type": "pokemon", "message": mon_payload}

            # add to payload
            ret.append(entire_payload)

        return ret

    def run_worker(self):
        try:
            while True:
                raids = self._db_wrapper.get_raids_changed_since(self._last_check)
                # mon = self._db_wrapper.get_mon_changed_since(self._last_check)
                # weather = self._db_wrapper.get_weather_changed_since(self._last_check)

                # self.__send_webhook(raids + mon + weather)
                self.__send_webhook(raids)

                self._last_check = int(time.time())
                time.sleep(self._worker_interval_sec)
        except KeyboardInterrupt:
            # graceful exit
            pass
