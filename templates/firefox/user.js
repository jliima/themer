user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
user_pref("browser.uidensity", {{ firefox.compact | int }});
user_pref("layout.css.prefers-color-scheme.content-override", {{ is-light }});
user_pref("browser.display.background_color.dark", "{{ bg }}");
