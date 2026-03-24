const { app } = window.comfyAPI.app;

app.registerExtension({
    name: "global_filename_prefix",
    async setup() {
        const CATEGORY = "Global Filename Prefix";

        async function sendUpdate(payload) {
            await fetch("/global_filename_prefix/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        }

        // Enable toggle
        app.ui.settings.addSetting({
            id: CATEGORY + ".enabled",
            name: "Enable filename prefix injection",
            type: "boolean",
            defaultValue: true,
            onChange: async (value) => {
                await sendUpdate({ enabled: value });
            }
        });

        // Template editor
        app.ui.settings.addSetting({
            id: CATEGORY + ".template",
            name: "Filename prefix template",
            type: "text",
            defaultValue: "{timestamp} {prefix}",
            attrs: {
                placeholder: "{timestamp} {prefix}"
            },
            onChange: async (value) => {
                await sendUpdate({ template: value });
            }
        });

        // Timestamp format editor
        app.ui.settings.addSetting({
            id: CATEGORY + ".timestamp_format",
            name: "Timestamp format",
            type: "text",
            defaultValue: "%Y-%m-%d %H-%M-%S",
            attrs: {
                placeholder: "%Y-%m-%d %H-%M-%S"
            },
            onChange: async (value) => {
                await sendUpdate({ timestamp_format: value });
            }
        });

        app.ui.settings.addSetting({
            id: CATEGORY + ".strip_directories",
            name: "Ignore folder paths in node filename prefixes",
            type: "boolean",
            defaultValue: false,
            onChange: async (value) => {
                await sendUpdate({
                    strip_directories: value
                });
            }
        });
    }
});
