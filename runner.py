from flask import Flask, make_response, send_file
import argparse
import codecs
import json
import pickle
import random
import time
from flask_executor import Executor
import zipfile
import traceback
from io import BytesIO

from randomizer.Enums.Settings import SettingsMap
from randomizer.Fill import Generate_Spoiler
from randomizer.Settings import Settings
from randomizer.SettingStrings import decrypt_settings_string_enum
from randomizer.Spoiler import Spoiler
from flask import request
app = Flask(__name__)
app.config['EXECUTOR_MAX_WORKERS'] = 1
executor = Executor(app)

def generate(generate_settings, file_name, gen_spoiler):
    """Gen a seed and write the file to an output file."""
    settings = Settings(generate_settings)
    spoiler = Spoiler(settings)        
    patch, spoiler = Generate_Spoiler(spoiler)
    return patch, spoiler


def start_gen():
    print("starting generation")
    start = time.time()
    presets = json.load(open("static/presets/preset_files.json"))
    default = json.load(open("static/presets/default.json"))
    found = False
    for file in presets.get("progression"):
        with open("static/presets/" + file, "r") as preset_file:
            data = json.load(preset_file)
            if "Season 1 Race Settings" == data.get("name"):
                setting_data = default
                for key in data:
                    setting_data[key] = data[key]
                setting_data.pop("name")
                setting_data.pop("description")
                found = True
    setting_data["seed"] = random.randint(0, 100000000)
    # Convert string data to enums where possible.
    for k, v in setting_data.items():
        if k in SettingsMap:
            if type(v) is list:
                values = []
                for val in v:
                    if type(val) is int:
                        values.append(SettingsMap[k](val))
                    else:
                        values.append(SettingsMap[k][val])
                setting_data[k] = values
            elif type(v) is int:
                setting_data[k] = SettingsMap[k](v)
            else:
                try:
                    setting_data[k] = SettingsMap[k][v]
                except Exception:
                    pass
    try:
        patch, spoiler = generate(setting_data, 'test', True)

    except Exception as e:
        print(traceback.format_exc())
    end = time.time()
    return patch, spoiler

@app.route('/start_generation')
def lambda_function():
    """CLI Entrypoint for generating seeds."""
    # Flask get the query string parameters as a dict.
    query_string = request.args.to_dict()
    # See if we have a query for gen_key.
    if query_string.get("gen_key"):
        gen_key = str(query_string.get("gen_key"))
        if executor.futures._futures.get(gen_key) and not executor.futures.done(gen_key):
            # We're not done generating yet.
            response = make_response(json.dumps({'status': executor.futures._state(gen_key)}), 200)
            response.mimetype = "application/json"
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        elif executor.futures._futures.get(gen_key):
            # We're done generating, return the data.
            future = executor.futures.pop(gen_key)
            resp_data = future.result()
            hash = resp_data[1].settings.seed_hash
            spoiler_log = resp_data[1].json
            patch = resp_data[0]
            # Zip all the data into a single file.
            # Create a new zip file
            zip_data = BytesIO()
            with zipfile.ZipFile(zip_data, "w") as zip_file:
                # Write each variable to the zip file
                zip_file.writestr("patch", patch)
                zip_file.writestr("hash", str(hash))
                zip_file.writestr("spoiler_log", str(spoiler_log))
            zip_data.seek(0)
            return send_file(zip_data, mimetype="application/zip", as_attachment=True, download_name=f"dk64r-{resp_data[1].settings.seed_id}.lanky")
        else:
            # We don't have a future for this key, so we need to start generating.
            executor.submit_stored(gen_key, start_gen)
            response = make_response(json.dumps({"start_time": gen_key}), 200)
            response.mimetype = "application/json"
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
    # Get the current time in milliseconds so we can use it as a key for the future.
    # And a random number to use as a modifier for the key so we don't have to worry about collisions.
    else:
        # We don't have a key, so we need to generate one.
        random_seed = random.randint(0, 100000000)
        start_time = str(int(round(time.time() * 1000)) + random_seed)
        executor.submit_stored(start_time, start_gen)
        response = make_response(json.dumps({"start_time": start_time}), 200)
        response.mimetype = "application/json"
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
