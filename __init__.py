import os
import json
import datetime
import folder_paths
from server import PromptServer
from aiohttp import web

NODE_CLASS_MAPPINGS = {}
WEB_DIRECTORY = "web"
CATEGORY = "Global Filename Prefix"


# Note the UI also defines default values that would usually trump these.
# Remember to keep them both in sync to avoid any surprises from edge cases.
CONFIG = {
    "enabled": True,
    "strip_directories": False,
    "timestamp_format": "%Y-%m-%d %H-%M-%S",
    "template": "{timestamp} {prefix}",
}


ORIGINAL_FUNC = folder_paths.get_save_image_path


def build_prefix(timestamp, original_prefix):
    directory, basename = os.path.split(original_prefix)

    if CONFIG["strip_directories"]:
        directory = ""

    class SafeDict(dict):
        def __missing__(self, key):
            return ""

    new_prefix = CONFIG["template"].format_map(
        SafeDict(
            timestamp=timestamp,
            prefix=basename,
        )
    )

    # normalize spacing
    new_prefix = " ".join(new_prefix.split())

    if directory:
        return os.path.join(directory, new_prefix)

    return new_prefix


def patched_get_save_image_path(*args, **kwargs):

    if not CONFIG["enabled"]:
        return ORIGINAL_FUNC(*args, **kwargs)

    timestamp = datetime.datetime.now().strftime(
        CONFIG["timestamp_format"]
    )

    if "filename_prefix" in kwargs:

        kwargs["filename_prefix"] = build_prefix(
            timestamp,
            kwargs["filename_prefix"]
        )

        return ORIGINAL_FUNC(*args, **kwargs)

    elif len(args) >= 1:

        args = list(args)

        args[0] = build_prefix(
            timestamp,
            args[0]
        )

        return ORIGINAL_FUNC(*args, **kwargs)

    else:

        kwargs["filename_prefix"] = timestamp

        return ORIGINAL_FUNC(*args, **kwargs)


folder_paths.get_save_image_path = patched_get_save_image_path

@PromptServer.instance.routes.post("/global_filename_prefix/settings")
async def update_settings(request):

    data = await request.json()

    CONFIG.update(data)

    print("[global_filename_prefix] settings updated:", CONFIG)

    return web.json_response({"status": "ok"})

def load_settings():
    '''
    Loads the settings from comfy.settings.json on startup to ensure that the
    user settings are respected even if the UI does not call update_settings
    (e.g. if the queue manager extension resumes after restarting ComfyUI, or
    the user starts a workflow without refreshing the browser)
    '''

    # There doesn't seem to be a python API to access these (only a web request
    # API), so for now just reading them directly. Assuming the "default" user
    # - handling edge cases involving multi users is getting too niche.
    settings_path = (
        os.path.join(
            folder_paths.get_user_directory(),
            "default",
            "comfy.settings.json")
    )

    if not os.path.isfile(settings_path):
        return

    try:

        with open(settings_path, "r") as f:
            data = json.load(f)

        for key in CONFIG:

            full_key = f"{CATEGORY}.{key}"

            if full_key in data:
                CONFIG[key] = data[full_key]

        print(
            "[global_filename_prefix] loaded settings from comfy.settings.json:",
            CONFIG,
        )

    except Exception as e:

        print(
            "[global_filename_prefix] failed to load settings:",
            e,
        )

load_settings()
print("[global_filename_prefix] loaded successfully")
