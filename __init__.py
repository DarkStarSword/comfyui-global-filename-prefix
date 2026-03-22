import os
import datetime
import folder_paths
from server import PromptServer
from aiohttp import web

NODE_CLASS_MAPPINGS = {}
WEB_DIRECTORY = "web"


CONFIG = {
    "enabled": True,
    "include_workflow": True,
    "timestamp_format": "%Y-%m-%d %H-%M-%S",
    "template": "{timestamp} {workflow} {prefix}",
}


ORIGINAL_FUNC = folder_paths.get_save_image_path


def extract_workflow_name(kwargs):

    try:
        extra = kwargs.get("extra_pnginfo", {})

        if isinstance(extra, dict) and "workflow" in extra:
            name = extra["workflow"].get("name")
            if name:
                return name

        prompt = kwargs.get("prompt", {})

        if isinstance(prompt, dict) and "workflow" in prompt:
            name = prompt["workflow"].get("name")
            if name:
                return name

    except Exception:
        pass

    return None


def build_prefix(timestamp, workflow, original_prefix):
    directory, basename = os.path.split(original_prefix)

    if CONFIG["strip_directories"]:
        directory = ""

    new_prefix = CONFIG["template"].format(
        timestamp=timestamp,
        workflow=workflow,
        prefix=basename,
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

    workflow = extract_workflow_name(kwargs)

    if "filename_prefix" in kwargs:

        kwargs["filename_prefix"] = build_prefix(
            timestamp,
            workflow,
            kwargs["filename_prefix"]
        )

        return ORIGINAL_FUNC(*args, **kwargs)

    elif len(args) >= 1:

        args = list(args)

        args[0] = build_prefix(
            timestamp,
            workflow,
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

print("[global_filename_prefix] prefix hook active (settings synced)")
