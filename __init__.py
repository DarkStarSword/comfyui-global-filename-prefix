import os
import datetime
import folder_paths
from server import PromptServer
from aiohttp import web

NODE_CLASS_MAPPINGS = {}
WEB_DIRECTORY = "web"


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

print("[global_filename_prefix] loaded successfully")
