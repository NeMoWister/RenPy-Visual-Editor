"""
Единый файл переводов интерфейса.

Чтобы добавить новый язык - просто добавьте его код (например "de") в
каждую (или только в нужные вам) запись ниже. Ключ записи - произвольная
уникальная строка вида "область.имя", значение - словарь {код_языка: текст}.

Пример добавления немецкого:

    "menu.file": {"ru": "Файл", "en": "File", "de": "Datei"},

Никакой другой код менять не нужно - тумблер языка в настройках и функция
tr() из core/i18n.py подхватят новый язык автоматически.
"""

TRANSLATIONS = {
                                          
    "settings.tab.appearance": {"ru": "🎨 Оформление", "en": "🎨 Appearance"},
    "settings.appearance.theme_label": {"ru": "Тема оформления:", "en": "Theme:"},
    "settings.appearance.info": {
        "ru": "Тема применяется сразу и сохраняется для следующего запуска. "
              "Добавить свою тему можно в ui/theme.py (см. комментарий в начале файла).",
        "en": "The theme applies immediately and is remembered for the next launch. "
              "You can add your own theme in ui/theme.py (see the comment at the top of the file).",
    },
    "settings.appearance.fluent_missing": {
        "ru": "Пакет PyQt6-Fluent-Widgets не установлен - используется встроенная "
              "система тем. Установите его (pip install PyQt6-Fluent-Widgets), "
              "чтобы также включить компоненты и анимации QFluentWidgets.",
        "en": "The PyQt6-Fluent-Widgets package is not installed - falling back to "
              "the built-in theming system. Install it (pip install PyQt6-Fluent-Widgets) "
              "to also enable QFluentWidgets components and animations.",
    },

                                        
    "settings.tab.language": {"ru": "🌐 Язык", "en": "🌐 Language"},
    "settings.language.label": {"ru": "Язык интерфейса:", "en": "Interface language:"},
    "settings.language.info": {
        "ru": "Изменения применятся после перезапуска редактора.",
        "en": "Changes will take effect after restarting the editor.",
    },

                                       
    "editor_settings.title": {"ru": "Настройки редактора", "en": "Editor Settings"},
    "editor_settings.tab.hotkeys": {"ru": "⌨ Горячие клавиши", "en": "⌨ Hotkeys"},
    "editor_settings.tab.autosave": {"ru": "💾 Автосохранение", "en": "💾 Autosave"},
    "editor_settings.tab.codegen": {"ru": "📝 Генерация кода", "en": "📝 Code Generation"},
    "editor_settings.save_close": {"ru": "Сохранить и закрыть", "en": "Save and Close"},
    "editor_settings.hotkeys.info": {
        "ru": "Клавиши для быстрого добавления нод нужного типа сразу после "
              "выбранной ноды в текущей сцене (без похода в комбобокс типа).",
        "en": "Keys for quickly adding a node of the desired type right after "
              "the selected node in the current scene (without using the type combobox).",
    },
    "editor_settings.hotkeys.col_action": {"ru": "Действие", "en": "Action"},
    "editor_settings.hotkeys.col_key": {"ru": "Клавиша", "en": "Key"},
    "editor_settings.hotkeys.reset": {"ru": "Сброс", "en": "Reset"},
    "editor_settings.hotkeys.reset_all": {
        "ru": "Сбросить все клавиши к стандартным",
        "en": "Reset all keys to defaults",
    },
    "editor_settings.hotkeys.conflict_title": {"ru": "Конфликт клавиш", "en": "Key Conflict"},
    "editor_settings.hotkeys.conflict_text": {
        "ru": "Клавиша «{key}» уже занята действием «{action}». Выберите другую комбинацию.",
        "en": "Key \"{key}\" is already used by action \"{action}\". Please choose another combination.",
    },
    "editor_settings.autosave.checkbox": {
        "ru": "Автоматически сохранять черновик проекта",
        "en": "Automatically save a project draft",
    },
    "editor_settings.autosave.interval_label": {
        "ru": "Интервал автосохранения (секунд):",
        "en": "Autosave interval (seconds):",
    },
    "editor_settings.autosave.info": {
        "ru": "Автосохранение пишет черновик проекта в отдельный служебный файл "
              "(не поверх вашего .repj) каждые N секунд, если есть несохранённые "
              "изменения. Если редактор закроется аварийно (сбой/отключение "
              "питания), при следующем запуске будет предложено восстановить "
              "этот черновик. При обычном сохранении (Ctrl+S) черновик очищается.",
        "en": "Autosave writes a project draft to a separate service file "
              "(not over your .repj) every N seconds if there are unsaved "
              "changes. If the editor closes unexpectedly (crash/power loss), "
              "you will be offered to restore this draft on next launch. "
              "A regular save (Ctrl+S) clears the draft.",
    },
    "editor_settings.codegen.group": {
        "ru": "Переключение NVL/ADV (нода «📖 Режим NVL/ADV»)",
        "en": "NVL/ADV Switching (\"📖 NVL/ADV Mode\" node)",
    },
    "editor_settings.codegen.character_mode": {
        "ru": "Через персонажа-компаньона (по умолчанию)",
        "en": "Via companion character (default)",
    },
    "editor_settings.codegen.function_mode": {
        "ru": "Через $ set_mode_nvl() / $ set_mode_adv()",
        "en": "Via $ set_mode_nvl() / $ set_mode_adv()",
    },
    "editor_settings.codegen.character_info": {
        "ru": "Для каждого персонажа автоматически генерируется NVL-версия "
              "(define ..._nvl = Character(..., kind=nvl.NVLCharacter)), реплики "
              "в NVL-режиме говорят через неё, вход/очистка - через nvl clear.",
        "en": "An NVL version is automatically generated for each character "
              "(define ..._nvl = Character(..., kind=nvl.NVLCharacter)), lines "
              "in NVL mode are spoken through it, enter/clear - via nvl clear.",
    },
    "editor_settings.codegen.function_info": {
        "ru": "Реплики остаются обычными (var \"текст\"), а вход/выход из NVL "
              "превращается в $ set_mode_nvl() / $ set_mode_adv() - эти функции "
              "нужно определить самостоятельно в проекте (редактор их не создаёт). "
              "«Очистить экран NVL» по-прежнему даёт nvl clear в обоих вариантах. "
              "При импорте .rpy обратно оба варианта распознаются автоматически.",
        "en": "Lines remain regular (var \"text\"), and entering/exiting NVL "
              "becomes $ set_mode_nvl() / $ set_mode_adv() - these functions "
              "need to be defined by you in the project (the editor does not create them). "
              "\"Clear NVL screen\" still produces nvl clear in both variants. "
              "When importing .rpy back, both variants are recognized automatically.",
    },

                                     
    "main_window.title": {"ru": "RenPy Visual Script Editor", "en": "RenPy Visual Script Editor"},
    "main_window.title_with_project": {
        "ru": "RenPy Visual Script Editor - {title}{marker}",
        "en": "RenPy Visual Script Editor - {title}{marker}",
    },

                        
    "menu.file": {"ru": "Файл", "en": "File"},
    "menu.file.new": {"ru": "Новый проект", "en": "New Project"},
    "menu.file.new_short": {"ru": "Новый", "en": "New"},
    "menu.file.open": {"ru": "Открыть...", "en": "Open..."},
    "menu.file.open_short": {"ru": "Открыть", "en": "Open"},
    "menu.file.save": {"ru": "Сохранить", "en": "Save"},
    "menu.file.save_as": {"ru": "Сохранить как...", "en": "Save As..."},
    "menu.file.quit": {"ru": "Выход", "en": "Quit"},

                          
    "menu.edit": {"ru": "Правка", "en": "Edit"},
    "menu.edit.command_palette": {"ru": "Командная палитра...", "en": "Command Palette..."},
    "menu.edit.undo": {"ru": "Отменить", "en": "Undo"},
    "menu.edit.redo": {"ru": "Повторить", "en": "Redo"},
    "menu.edit.find_replace": {"ru": "Найти и заменить...", "en": "Find and Replace..."},
    "menu.edit.history": {"ru": "История действий...", "en": "Action History..."},
    "menu.edit.editor_settings": {
        "ru": "Настройки редактора (клавиши, автосохранение)...",
        "en": "Editor Settings (hotkeys, autosave)...",
    },

                          
    "menu.project": {"ru": "Проект", "en": "Project"},
    "menu.project.characters": {"ru": "Персонажи...", "en": "Characters..."},
    "menu.project.characters_short": {"ru": "Персонажи", "en": "Characters"},
    "menu.project.resources": {"ru": "Настройки ресурсов...", "en": "Resource Settings..."},
    "menu.project.tags": {"ru": "Категории тегов (фоны/CG)...", "en": "Tag Categories (backgrounds/CG)..."},
    "menu.project.code_templates": {"ru": "Шаблоны пользовательских нод...", "en": "Custom Node Templates..."},
    "menu.project.presentation": {"ru": "Режим презентации", "en": "Presentation Mode"},
    "menu.project.timing": {"ru": "Проверка тайминга...", "en": "Timing Check..."},
    "menu.project.spellcheck": {"ru": "Проверка реплик...", "en": "Spellcheck Lines..."},
    "menu.project.import_paths": {"ru": "Импорт путей из .rpy...", "en": "Import Paths from .rpy..."},
    "menu.project.import_script": {"ru": "Импорт скрипта из .rpy...", "en": "Import Script from .rpy..."},
    "menu.project.screenplay": {
        "ru": "Экспорт/импорт текста для вычитки...",
        "en": "Export/Import Text for Proofreading...",
    },
    "menu.project.git": {"ru": "Версионирование проекта (Git)...", "en": "Project Versioning (Git)..."},
    "menu.project.download_resources": {
        "ru": "Скачать ресурсы для модификаций...",
        "en": "Download Resources for Mods...",
    },
    "menu.project.download_resources_short": {"ru": "Скачать ресурсы", "en": "Download Resources"},
    "menu.project.rescan": {"ru": "Переиндексировать ресурсы", "en": "Rescan Resources"},
    "menu.project.rescan_short": {"ru": "Переиндексировать", "en": "Rescan"},
    "menu.project.rename": {"ru": "Переименовать проект...", "en": "Rename Project..."},
    "menu.project.main_label": {"ru": "Главная метка (label)...", "en": "Main Label..."},

                             
    "menu.generation": {"ru": "Генерация", "en": "Generation"},
    "menu.generation.preview": {"ru": "Просмотр кода...", "en": "Preview Code..."},
    "menu.generation.preview_short": {"ru": "Генерировать", "en": "Generate"},
    "menu.generation.export": {"ru": "Экспорт .rpy...", "en": "Export .rpy..."},
    "menu.generation.export_short": {"ru": "Экспорт .rpy", "en": "Export .rpy"},
    "menu.generation.export_split": {
        "ru": "Экспорт в несколько файлов (по главам/актам)...",
        "en": "Export to Multiple Files (by chapters/acts)...",
    },
    "menu.generation.export_defines": {"ru": "Экспорт блока defines...", "en": "Export Defines Block..."},
    "menu.generation.export_resource_defines": {
        "ru": "Экспорт defines ресурсов...",
        "en": "Export Resource Defines...",
    },
    "menu.generation.export_project": {
        "ru": "Экспорт проекта (сценарий + используемые ресурсы)...",
        "en": "Export Project (script + used resources)...",
    },
    "menu.generation.export_project_short": {"ru": "Экспорт проекта", "en": "Export Project"},

                              
    "menu.stats": {"ru": "Статистика", "en": "Statistics"},
    "menu.stats.dialogue": {
        "ru": "Статистика реплик по персонажам...",
        "en": "Line Statistics by Character...",
    },

                           
    "menu.help": {"ru": "Справка", "en": "Help"},
    "menu.help.guide": {"ru": "Руководство пользователя...", "en": "User Guide..."},
    "menu.help.guide_short": {"ru": "Руководство", "en": "Guide"},
    "menu.help.check_updates": {"ru": "Проверить обновления...", "en": "Check for Updates..."},
    "menu.help.autoupdate": {
        "ru": "Проверять обновления при запуске",
        "en": "Check for updates on startup",
    },

                                                        
    "toolbar.main": {"ru": "Основная панель", "en": "Main Toolbar"},
    "scene.rename_tooltip": {"ru": "Переименовать сцену", "en": "Rename Scene"},
    "scene.delete_tooltip": {"ru": "Удалить сцену", "en": "Delete Scene"},
    "node.duplicate_tooltip": {"ru": "Дублировать", "en": "Duplicate"},
    "node.move_up_tooltip": {"ru": "Переместить вверх", "en": "Move Up"},
    "node.move_down_tooltip": {"ru": "Переместить вниз", "en": "Move Down"},
    "node.delete_tooltip": {"ru": "Удалить", "en": "Delete"},
    "node.group_color_menu": {"ru": "Цвет группы", "en": "Group Color"},
    "node.label_color_menu": {"ru": "Цвет метки ноды", "en": "Node Label Color"},
    "dialog.spellcheck_progress_title": {"ru": "Проверка реплик", "en": "Checking Lines"},
    "dialog.reimport_title": {"ru": "Повторный импорт", "en": "Re-import"},

                                          
    "res_download.title": {"ru": "Ресурсы для модификаций", "en": "Resources for Mods"},
    "res_download.heading": {
        "ru": "Ресурсы, необходимые для создания модификаций",
        "en": "Resources needed to create mods",
    },
    "res_download.info": {
        "ru": "Архив скачать и распаковать в папку, где лежит .exe.",
        "en": "Download the archive and extract it into the folder where the .exe is located.",
    },
    "menu.help.guide_title": {"ru": "Руководство пользователя", "en": "User Guide"},
                                      
    "res_usage.title": {"ru": "Где используется: {name}", "en": "Used in: {name}"},
    "res_usage.not_used": {
        "ru": "Ресурс «{var}» нигде не используется в текущем проекте.",
        "en": "Resource \"{var}\" is not used anywhere in the current project.",
    },
    "res_usage.found": {
        "ru": "Найдено {count} {word} использования - var: {var}",
        "en": "Found {count} {word} - var: {var}",
    },
    "res_usage.dblclick_tooltip": {
        "ru": "Двойной клик - перейти к ноде",
        "en": "Double-click to go to the node",
    },
    "res_usage.go_to_node": {"ru": "➡ Перейти к ноде", "en": "➡ Go to Node"},

                                     
    "history.title": {"ru": "История действий", "en": "Action History"},
    "history.info": {
        "ru": "Последние действия (сверху - самое недавнее). Выберите шаг и "
              "нажмите «Отменить до этого шага», чтобы вернуться в состояние "
              "ПЕРЕД ним - все более поздние действия будут отменены разом.",
        "en": "Recent actions (most recent on top). Select a step and click "
              "\"Undo to This Step\" to return to the state BEFORE it - all "
              "later actions will be undone at once.",
    },
    "history.refresh": {"ru": "🔄 Обновить", "en": "🔄 Refresh"},
    "history.undo_to_step": {"ru": "⏪ Отменить до этого шага", "en": "⏪ Undo to This Step"},
    "history.close": {"ru": "Закрыть", "en": "Close"},
    "history.empty": {
        "ru": "(история пуста - отменять нечего)",
        "en": "(history is empty - nothing to undo)",
    },
    "history.confirm_title": {"ru": "Подтверждение", "en": "Confirm"},
    "history.confirm_text": {
        "ru": "Отменить {count} {word} и вернуться в состояние перед «{label}»?",
        "en": "Undo {count} {word} and return to the state before \"{label}\"?",
    },

                              
    "update.title": {"ru": "Доступно обновление", "en": "Update Available"},
    "update.new_version": {"ru": "Вышла новая версия: {version}", "en": "New version released: {version}"},
    "update.current_version": {"ru": "Текущая версия: {version}", "en": "Current version: {version}"},
    "update.no_notes": {"ru": "(описание изменений не указано)", "en": "(no changelog provided)"},
    "update.disable_autocheck": {
        "ru": "Не проверять обновления автоматически при запуске",
        "en": "Don't check for updates automatically on startup",
    },
    "update.later": {"ru": "Напомнить позже", "en": "Remind Me Later"},
    "update.download": {"ru": "⬇ Скачать обновление", "en": "⬇ Download Update"},

                                      
    "dstats.title": {"ru": "Статистика реплик по персонажам", "en": "Line Statistics by Character"},
    "dstats.col_character": {"ru": "Персонаж", "en": "Character"},
    "dstats.col_lines": {"ru": "Реплик", "en": "Lines"},
    "dstats.col_percent": {"ru": "% от всех", "en": "% of Total"},
    "dstats.col_words": {"ru": "Слов", "en": "Words"},
    "dstats.col_chars": {"ru": "Символов", "en": "Characters"},
    "dstats.note": {
        "ru": "Подсказка: Реплики считаются во всем проекте, "
              "вне зависимости от выбранного лейбла.",
        "en": "Tip: lines are counted across the whole project, "
              "regardless of the selected label.",
    },
    "dstats.refresh": {"ru": "🔄 Обновить", "en": "🔄 Refresh"},
    "dstats.close": {"ru": "Закрыть", "en": "Close"},
    "dstats.summary": {
        "ru": "Всего реплик: {total}   •   Персонажей с репликами: {chars}",
        "en": "Total lines: {total}   •   Characters with lines: {chars}",
    },
    "dstats.empty": {
        "ru": "В проекте пока нет ни одной реплики диалога.",
        "en": "The project doesn't have any dialogue lines yet.",
    },

                             
    "code_preview.title": {"ru": "Сгенерированный код Ren'Py", "en": "Generated Ren'Py Code"},
    "code_preview.font_size": {"ru": "Размер шрифта:", "en": "Font size:"},
    "code_preview.tab_full": {"ru": "Полный сценарий (.rpy)", "en": "Full Script (.rpy)"},
    "code_preview.tab_defines": {"ru": "Defines / Characters", "en": "Defines / Characters"},
    "code_preview.copy": {"ru": "📋 Копировать", "en": "📋 Copy"},
    "code_preview.save": {"ru": "💾 Сохранить .rpy", "en": "💾 Save .rpy"},
    "code_preview.close": {"ru": "Закрыть", "en": "Close"},
    "code_preview.copied_title": {"ru": "Скопировано", "en": "Copied"},
    "code_preview.copied_text": {"ru": "Код скопирован в буфер обмена", "en": "Code copied to clipboard"},
    "code_preview.save_dialog_title": {"ru": "Сохранить .rpy", "en": "Save .rpy"},
    "code_preview.all_files": {"ru": "Все файлы", "en": "All Files"},
    "code_preview.done_title": {"ru": "Готово", "en": "Done"},
    "code_preview.saved_text": {"ru": "Файл сохранён:\n{path}", "en": "File saved:\n{path}"},
    "code_preview.error_title": {"ru": "Ошибка", "en": "Error"},

                                  
    "screenplay.title": {"ru": "Экспорт/импорт текста для вычитки", "en": "Export/Import Text for Proofreading"},
    "screenplay.info": {
        "ru": "Экспортируйте текст, отдайте редактору/сценаристу на вычитку (можно править "
              "в любом текстовом редакторе), затем вставьте отредактированный текст сюда "
              "и нажмите «Импортировать правки». Строки в [квадратных скобках] и хвостовые "
              "метки {#...} - служебные, их менять не нужно.",
        "en": "Export the text, hand it to an editor/writer for proofreading (it can be "
              "edited in any text editor), then paste the edited text back here "
              "and click \"Import Edits\". Lines in [square brackets] and trailing "
              "{#...} tags are technical - don't change them.",
    },
    "screenplay.save_to_file": {"ru": "💾 Сохранить в файл...", "en": "💾 Save to File..."},
    "screenplay.load_from_file": {"ru": "📂 Загрузить из файла...", "en": "📂 Load from File..."},
    "screenplay.rebuild": {"ru": "🔄 Пересобрать из текущего проекта", "en": "🔄 Rebuild from Current Project"},
    "screenplay.import_edits": {"ru": "⬅ Импортировать правки в проект", "en": "⬅ Import Edits into Project"},
    "screenplay.close": {"ru": "Закрыть", "en": "Close"},
    "screenplay.save_dialog_title": {"ru": "Сохранить текст для вычитки", "en": "Save Text for Proofreading"},
    "screenplay.text_files": {"ru": "Текстовый файл", "en": "Text File"},
    "screenplay.all_files": {"ru": "Все файлы", "en": "All Files"},
    "screenplay.done_title": {"ru": "Готово", "en": "Done"},
    "screenplay.saved_text": {"ru": "Сохранено:\n{path}", "en": "Saved:\n{path}"},
    "screenplay.error_title": {"ru": "Ошибка", "en": "Error"},
    "screenplay.load_dialog_title": {"ru": "Загрузить текст с правками", "en": "Load Edited Text"},
    "screenplay.updated_lines": {"ru": "Обновлено реплик/строк: {count}.", "en": "Updated lines: {count}."},
    "screenplay.unmatched_more": {"ru": " и ещё {count}", "en": " and {count} more"},
    "screenplay.unmatched_text": {
        "ru": "\n\nНе найдено в текущем проекте (устарели/удалены): {count}\n{shown}{more}",
        "en": "\n\nNot found in the current project (outdated/removed): {count}\n{shown}{more}",
    },
    "screenplay.import_done_title": {"ru": "Импорт завершён", "en": "Import Complete"},

                                    
    "find_replace.title": {"ru": "Найти и заменить по всему сценарию", "en": "Find and Replace in Entire Script"},
    "find_replace.find_label": {"ru": "Найти:", "en": "Find:"},
    "find_replace.replace_label": {"ru": "Заменить на:", "en": "Replace with:"},
    "find_replace.case_sensitive": {"ru": "Учитывать регистр", "en": "Case sensitive"},
    "find_replace.whole_word": {"ru": "Только целые слова", "en": "Whole words only"},
    "find_replace.include_comments": {"ru": "Включая комментарии", "en": "Include comments"},
    "find_replace.enter_text": {"ru": "Введите текст для поиска.", "en": "Enter text to search for."},
    "find_replace.replace_all": {"ru": "Заменить всё", "en": "Replace All"},
    "find_replace.close": {"ru": "Закрыть", "en": "Close"},
    "find_replace.found_count": {"ru": "Найдено совпадений: {count}", "en": "Matches found: {count}"},
    "find_replace.no_matches": {"ru": "Совпадений не найдено.", "en": "No matches found."},
    "find_replace.confirm_title": {"ru": "Подтверждение", "en": "Confirm"},
    "find_replace.confirm_text": {
        "ru": "Заменить все совпадения «{find}» → «{replace}» "
              "({count} мест)? Это действие можно отменить через Ctrl+Z.",
        "en": "Replace all occurrences of \"{find}\" \u2192 \"{replace}\" "
              "({count} places)? This action can be undone with Ctrl+Z.",
    },
    "find_replace.done_title": {"ru": "Готово", "en": "Done"},
    "find_replace.done_text": {"ru": "Произведено замен: {count}.", "en": "Replacements made: {count}."},

                                     
    "timing.title": {"ru": "Проверка тайминга", "en": "Timing Check"},
    "timing.unit_hms": {"ru": "{h}ч {m:02d}м {s:02d}с", "en": "{h}h {m:02d}m {s:02d}s"},
    "timing.unit_ms": {"ru": "{m}м {s:02d}с", "en": "{m}m {s:02d}s"},
    "timing.unit_s": {"ru": "{s}с", "en": "{s}s"},
    "timing.summary": {
        "ru": "Реплик: <b>{lines}</b> &nbsp;\u00b7&nbsp; "
              "Итого по прикидке: <b>{total}</b> &nbsp;\u00b7&nbsp; "
              "В среднем на реплику: <b>{avg:.1f}с</b>",
        "en": "Lines: <b>{lines}</b> &nbsp;\u00b7&nbsp; "
              "Estimated total: <b>{total}</b> &nbsp;\u00b7&nbsp; "
              "Average per line: <b>{avg:.1f}s</b>",
    },
    "timing.note": {
        "ru": "Оценка приблизительная: время реплики считается по длине текста "
              "(\u224822 симв/сек чтения, от 1.2 до 6 сек на реплику), паузы - по "
              "длительности pause-нод. В разветвлениях меню берётся один "
              "представительный путь (первый вариант с вписанными нодами, иначе "
              "первый вариант с переходом), а не все ветки сразу.",
        "en": "The estimate is approximate: line time is based on text length "
              "(\u224822 chars/sec reading speed, 1.2 to 6 sec per line), pauses - "
              "based on pause node durations. In menu branches, one representative "
              "path is taken (the first option with inline nodes, otherwise the "
              "first option with a jump), not all branches at once.",
    },
    "timing.by_character": {"ru": "По персонажам", "en": "By Character"},
    "timing.col_character": {"ru": "Персонаж", "en": "Character"},
    "timing.col_lines": {"ru": "Реплик", "en": "Lines"},
    "timing.col_time": {"ru": "Время", "en": "Time"},
    "timing.by_scene": {"ru": "По сценам", "en": "By Scene"},
    "timing.col_scene": {"ru": "Сцена", "en": "Scene"},
    "timing.longest_lines": {"ru": "Самые длинные реплики", "en": "Longest Lines"},
    "timing.col_text": {"ru": "Текст", "en": "Text"},

                                
    "cmd_palette.placeholder": {"ru": "Введите название команды...", "en": "Type a command name..."},
    "cmd_palette.nothing_found": {"ru": "Ничего не найдено", "en": "Nothing found"},

                                         
    "spellcheck.title": {"ru": "Проверка реплик", "en": "Checking Lines"},
    "spellcheck.summary": {
        "ru": "Реплик с замечаниями: {lines}  \u00b7  всего замечаний: {issues}",
        "en": "Lines with issues: {lines}  \u00b7  total issues: {issues}",
    },
    "spellcheck.dblclick_tooltip": {"ru": "Двойной клик - перейти к ноде", "en": "Double-click to go to the node"},
    "spellcheck.none_found": {"ru": "Замечаний не найдено 🎉", "en": "No issues found 🎉"},
    "spellcheck.words_hint": {
        "ru": "Опечатки в выбранной реплике - можно сразу добавить в личный словарь:",
        "en": "Typos in the selected line - you can add them to your personal dictionary right away:",
    },
    "spellcheck.select_line_above": {"ru": "(выберите реплику выше)", "en": "(select a line above)"},
    "spellcheck.go_to_node": {"ru": "➡ Перейти к ноде", "en": "➡ Go to Node"},
    "spellcheck.rescan": {"ru": "🔄 Пересканировать", "en": "🔄 Rescan"},
    "spellcheck.rescan_tooltip": {
        "ru": "Например, после добавления слов в словарь",
        "en": "For example, after adding words to the dictionary",
    },
    "spellcheck.banner_ru_only": {
        "ru": "ℹ Орфография для русского проверяется через pymorphy3. Для "
              "английского языка библиотека pyspellchecker не установлена "
              "(pip install pyspellchecker).",
        "en": "ℹ Russian spelling is checked via pymorphy3. For English, the "
              "pyspellchecker library is not installed "
              "(pip install pyspellchecker).",
    },
    "spellcheck.banner_none": {
        "ru": "ℹ Ни pymorphy3, ни pyspellchecker не установлены - орфография по "
              "словарю не проверяется (pip install pymorphy3 pymorphy3-dicts-ru "
              "pyspellchecker).",
        "en": "ℹ Neither pymorphy3 nor pyspellchecker is installed - dictionary-based "
              "spelling is not checked (pip install pymorphy3 pymorphy3-dicts-ru "
              "pyspellchecker).",
    },
    "spellcheck.ru_unavailable": {
        "ru": "русский недоступен ({reason})",
        "en": "Russian unavailable ({reason})",
    },
    "spellcheck.en_unavailable": {
        "ru": "английский недоступен ({reason})",
        "en": "English unavailable ({reason})",
    },
    "spellcheck.reason_unknown": {"ru": "причина неизвестна", "en": "reason unknown"},
    "spellcheck.pyspellchecker_missing": {
        "ru": "pyspellchecker не установлен",
        "en": "pyspellchecker not installed",
    },
    "spellcheck.banner_partial": {
        "ru": "⚠ Проверка орфографии работает частично: {problems}. "
              "Если это собранный .exe - словари/данные pymorphy3 или "
              "pyspellchecker не были включены в сборку (это файлы данных, "
              "PyInstaller их не подхватывает автоматически).",
        "en": "⚠ Spell checking works partially: {problems}. "
              "If this is a built .exe - pymorphy3 or pyspellchecker dictionaries/data "
              "were not included in the build (these are data files, "
              "PyInstaller does not pick them up automatically).",
    },
    "spellcheck.banner_tech_checks": {
        "ru": " Доступны технические проверки: незакрытые теги {{b}}/{{i}}/{{color}}, "
              "повторы слов, лишние пробелы и знаки препинания.",
        "en": " Technical checks are available: unclosed tags {{b}}/{{i}}/{{color}}, "
              "repeated words, extra spaces and punctuation.",
    },
    "spellcheck.no_spelling_issues": {
        "ru": "(в этой реплике нет замечаний по орфографии)",
        "en": "(no spelling issues in this line)",
    },
    "spellcheck.add_word_tooltip": {
        "ru": "Добавить это слово в личный словарь (больше не будет считаться опечаткой)",
        "en": "Add this word to your personal dictionary (it will no longer be flagged as a typo)",
    },
    "spellcheck.word_added": {"ru": "✓ «{word}» добавлено", "en": "✓ \"{word}\" added"},

                                    
    "split_export.title": {"ru": "Экспорт в несколько файлов", "en": "Export to Multiple Files"},
    "split_export.rule_box": {"ru": "Правило разбиения", "en": "Splitting Rule"},
    "split_export.rb_label": {
        "ru": "По меткам верхнего уровня (label) - ближе всего к главам/актам",
        "en": "By top-level labels - closest to chapters/acts",
    },
    "split_export.rb_scene": {
        "ru": "По сценам редактора - один файл на каждую сцену",
        "en": "By editor scenes - one file per scene",
    },
    "split_export.rb_count": {"ru": "Фиксированное число сцен на файл:", "en": "Fixed number of scenes per file:"},
    "split_export.scenes_per_file": {"ru": "сцен/файл", "en": "scenes/file"},
    "split_export.dir_not_selected": {"ru": "Папка не выбрана", "en": "Folder not selected"},
    "split_export.pick_dir": {"ru": "📁 Выбрать папку...", "en": "📁 Choose Folder..."},
    "split_export.will_be_created": {"ru": "Будет создано:", "en": "Will be created:"},
    "split_export.note": {
        "ru": "Все файлы вместе - это один сценарий: между ними расставляются "
              "автоматические переходы (jump), так что смотреть его целиком "
              "нужно как всегда, начиная с первого файла. Если какой-то файл в "
              "папке уже существует и отличается - перед перезаписью будет "
              "показан дифф (как при обычном экспорте).",
        "en": "All the files together form one script: automatic jumps are "
              "placed between them, so it should still be played through as "
              "usual, starting from the first file. If a file already exists "
              "in the folder and differs, a diff will be shown before "
              "overwriting it (as with a regular export).",
    },
    "split_export.cancel": {"ru": "Отмена", "en": "Cancel"},
    "split_export.export": {"ru": "Экспортировать", "en": "Export"},
    "split_export.error_prefix": {"ru": "Ошибка: {error}", "en": "Error: {error}"},
    "split_export.pick_dir_title": {"ru": "Папка для экспорта", "en": "Folder for Export"},
    "split_export.write_error_title": {"ru": "Ошибка записи", "en": "Write Error"},
    "split_export.done_title": {"ru": "Экспорт завершён", "en": "Export Complete"},
    "split_export.written_count": {"ru": "Записано файлов: {count}.", "en": "Files written: {count}."},
    "split_export.skipped": {
        "ru": "\nПропущено: {count} ({names})",
        "en": "\nSkipped: {count} ({names})",
    },

                                      
    "code_templates.title": {"ru": "Шаблоны генерации кода", "en": "Code Generation Templates"},
    "code_templates.no_jinja2": {
        "ru": "⚠ Пакет jinja2 не установлен - кастомные шаблоны сохранятся, но "
              "НЕ будут применяться при генерации кода, пока вы не установите его "
              "(pip install jinja2). Без него используется стандартная генерация.",
        "en": "⚠ The jinja2 package is not installed - custom templates will be "
              "saved, but will NOT be applied during code generation until you "
              "install it (pip install jinja2). Standard generation is used without it.",
    },
    "code_templates.indent": {"ru": "Отступ:", "en": "Indent:"},
    "code_templates.spaces": {"ru": "Пробелы", "en": "Spaces"},
    "code_templates.tab": {"ru": "Табуляция", "en": "Tab"},
    "code_templates.width": {"ru": "Ширина:", "en": "Width:"},
    "code_templates.comment_prefix": {"ru": "Префикс комментария:", "en": "Comment prefix:"},
    "code_templates.node_type": {"ru": "Тип ноды:", "en": "Node type:"},
    "code_templates.jinja_template": {
        "ru": "Jinja2-шаблон (одна нода → строка/строки):",
        "en": "Jinja2 template (one node \u2192 line/lines):",
    },
    "code_templates.reset_default": {"ru": "Сбросить к стандартному", "en": "Reset to Default"},
    "code_templates.preview_label": {"ru": "Предпросмотр (пример данных):", "en": "Preview (sample data):"},
    "code_templates.save_close": {"ru": "Сохранить и закрыть", "en": "Save and Close"},
    "code_templates.available_vars": {
        "ru": "Доступные переменные: {vars}",
        "en": "Available variables: {vars}",
    },
    "code_templates.preview_unavailable": {
        "ru": "(предпросмотр недоступен без пакета jinja2)",
        "en": "(preview unavailable without the jinja2 package)",
    },
    "code_templates.template_error": {"ru": "Ошибка шаблона:\n{error}", "en": "Template error:\n{error}"},

                                    
    "import_paths.title": {"ru": "Импорт путей из .rpy", "en": "Import Paths from .rpy"},
    "import_paths.hint": {
        "ru": "Выберите один или несколько .rpy файлов существующего проекта Ren'Py "
              "(например, определения ресурсов или весь сценарий). Редактор найдёт "
              "там простые присвоения вида image/define = \"путь\", определения "
              "персонажей Character(...) и словарь music_list, сопоставит пути с "
              "файлами в resources/ и предложит переименовать переменные ресурсов "
              "так, как они уже названы в вашем проекте.",
        "en": "Select one or more .rpy files from an existing Ren'Py project "
              "(e.g. resource definitions or the whole script). The editor will "
              "find simple assignments like image/define = \"path\", "
              "Character(...) definitions and the music_list dictionary, match "
              "the paths to files in resources/, and offer to rename resource "
              "variables to match what's already used in your project.",
    },
    "import_paths.pick_files": {"ru": "📄 Выбрать .rpy файлы...", "en": "📄 Choose .rpy Files..."},
    "import_paths.pick_folder": {"ru": "📁 Выбрать папку (рекурсивно)...", "en": "📁 Choose Folder (recursive)..."},
    "import_paths.no_files": {"ru": "Файлы не выбраны.", "en": "No files selected."},
    "import_paths.col_check": {"ru": "✓", "en": "✓"},
    "import_paths.col_category": {"ru": "Категория", "en": "Category"},
    "import_paths.col_path": {"ru": "Путь", "en": "Path"},
    "import_paths.col_old": {"ru": "Было", "en": "Before"},
    "import_paths.col_new": {"ru": "Будет", "en": "After"},
    "import_paths.col_line": {"ru": "Строка", "en": "Line"},
    "import_paths.tab_renames": {"ru": "Переименования ({count})", "en": "Renames ({count})"},
    "import_paths.col_rpy_name": {"ru": "Имя в .rpy", "en": "Name in .rpy"},
    "import_paths.tab_unmatched": {"ru": "Не найдено на диске ({count})", "en": "Not Found on Disk ({count})"},
    "import_paths.col_variable": {"ru": "Переменная", "en": "Variable"},
    "import_paths.col_name": {"ru": "Имя", "en": "Name"},
    "import_paths.col_color": {"ru": "Цвет", "en": "Color"},
    "import_paths.tab_characters": {"ru": "Персонажи ({count})", "en": "Characters ({count})"},
    "import_paths.close": {"ru": "Закрыть", "en": "Close"},
    "import_paths.apply_checked": {"ru": "✓ Применить отмеченное", "en": "✓ Apply Checked"},
    "import_paths.pick_files_title": {"ru": "Выберите .rpy файлы", "en": "Select .rpy Files"},
    "import_paths.pick_folder_title": {"ru": "Выберите папку с .rpy файлами", "en": "Select Folder with .rpy Files"},
    "import_paths.dialog_title": {"ru": "Импорт путей", "en": "Import Paths"},
    "import_paths.no_rpy_found": {
        "ru": "В выбранной папке не найдено .rpy файлов.",
        "en": "No .rpy files found in the selected folder.",
    },
    "import_paths.status": {
        "ru": "Обработано файлов: {files}. Найдено переименований: {renames}.",
        "en": "Files processed: {files}. Renames found: {renames}.",
    },
    "import_paths.read_errors": {"ru": " Ошибки чтения: {count}.", "en": " Read errors: {count}."},
    "import_paths.applied_result": {
        "ru": "Применено переименований: {renames}.\nИмпортировано персонажей: {chars}.",
        "en": "Renames applied: {renames}.\nCharacters imported: {chars}.",
    },

                                     
    "import_script.title": {"ru": "Импорт .rpy сценария", "en": "Import .rpy Script"},
    "import_script.hint": {
        "ru": "Выберите .rpy файл сценария. Редактор распознает известные конструкции "
              "(scene/show/hide/play/stop/menu/jump/return/диалог) и создаст "
              "соответствующие узлы. Всё нераспознанное сохраняется как Python-узел "
              "и не теряется при экспорте обратно.",
        "en": "Select an .rpy script file. The editor will recognize known "
              "constructs (scene/show/hide/play/stop/menu/jump/return/dialogue) "
              "and create corresponding nodes. Anything unrecognized is stored "
              "as a Python node and is not lost on export back.",
    },
    "import_script.open_file": {"ru": "📄 Открыть .rpy файл...", "en": "📄 Open .rpy File..."},
    "import_script.no_file": {"ru": "Файл не выбран", "en": "No file selected"},
    "import_script.found_scenes": {"ru": "Найденные сцены и узлы:", "en": "Found scenes and nodes:"},
    "import_script.all": {"ru": "Все", "en": "All"},
    "import_script.none": {"ru": "Ни одной", "en": "None"},
    "import_script.col_scene_node": {"ru": "Сцена / Узел", "en": "Scene / Node"},
    "import_script.unrecognized_label": {
        "ru": "Нераспознанные строки (будут PYTHON-узлами):",
        "en": "Unrecognized lines (will become PYTHON nodes):",
    },
    "import_script.unrecognized_placeholder": {
        "ru": "Нераспознанного нет - отлично!",
        "en": "Nothing unrecognized - great!",
    },
    "import_script.needs_resource_label": {
        "ru": "⚠ Импортированы, но ресурс не найден - нужно добавить:",
        "en": "⚠ Imported, but resource not found - needs to be added:",
    },
    "import_script.needs_resource_placeholder": {
        "ru": "Все ресурсы найдены - отлично!",
        "en": "All resources found - great!",
    },
    "import_script.cancel": {"ru": "Отмена", "en": "Cancel"},
    "import_script.import_selected": {"ru": "⬇ Импортировать выбранные сцены", "en": "⬇ Import Selected Scenes"},
    "import_script.open_file_title": {"ru": "Открыть .rpy файл", "en": "Open .rpy File"},
    "import_script.read_error_title": {"ru": "Ошибка чтения", "en": "Read Error"},
    "import_script.stats": {
        "ru": "Сцен: {scenes}  |  Узлов: {nodes}  |  Распознано: {pct:.0f}%  |  Нераспознано (raw): {raw}",
        "en": "Scenes: {scenes}  |  Nodes: {nodes}  |  Recognized: {pct:.0f}%  |  Unrecognized (raw): {raw}",
    },
    "import_script.line_prefix": {"ru": "Строка {line}: {text}", "en": "Line {line}: {text}"},
    "import_script.needs_res_line": {
        "ru": "Строка {line}: {text}  \u2192  ресурс «{var}»",
        "en": "Line {line}: {text}  \u2192  resource \"{var}\"",
    },
    "import_script.dialog_title": {"ru": "Импорт", "en": "Import"},
    "import_script.no_scenes_selected": {"ru": "Не выбрано ни одной сцены.", "en": "No scenes selected."},

                                        
    "git_scene_commit.unexpected_error": {"ru": "Неожиданная ошибка: {error}", "en": "Unexpected error: {error}"},
    "git_scene_commit.title": {"ru": "Commit по сценам", "en": "Commit by Scenes"},
    "git_scene_commit.read_failed": {"ru": "Не удалось прочитать файл проекта.", "en": "Failed to read the project file."},
    "git_scene_commit.no_changes": {"ru": "Нет изменённых сцен - коммитить нечего.", "en": "No changed scenes - nothing to commit."},
    "git_scene_commit.close": {"ru": "Закрыть", "en": "Close"},
    "git_scene_commit.info": {
        "ru": "Отметьте сцены, которые нужно включить в этот снепшот. Остальные "
              "изменения (не отмеченные) останутся в рабочей копии как есть - "
              "просто не попадут в этот коммит, их можно будет закоммитить позже.",
        "en": "Check the scenes to include in this snapshot. The remaining "
              "(unchecked) changes will stay in the working copy as is - they "
              "just won't be included in this commit and can be committed later.",
    },
    "git_scene_commit.status_added": {"ru": "🆕 новая", "en": "🆕 new"},
    "git_scene_commit.status_modified": {"ru": "✏ изменена", "en": "✏ modified"},
    "git_scene_commit.status_removed": {"ru": "🗑 удалена", "en": "🗑 removed"},
    "git_scene_commit.check_all": {"ru": "Отметить все", "en": "Check All"},
    "git_scene_commit.check_none": {"ru": "Снять все", "en": "Uncheck All"},
    "git_scene_commit.message_label": {"ru": "Сообщение коммита:", "en": "Commit message:"},
    "git_scene_commit.message_placeholder": {
        "ru": "напр. «Глава 1 - правки текста»",
        "en": "e.g. \"Chapter 1 - text fixes\"",
    },
    "git_scene_commit.cancel": {"ru": "Отмена", "en": "Cancel"},
    "git_scene_commit.commit_selected": {"ru": "💾 Закоммитить выбранное", "en": "💾 Commit Selected"},
    "git_scene_commit.nothing_selected_title": {"ru": "Ничего не выбрано", "en": "Nothing Selected"},
    "git_scene_commit.nothing_selected_text": {"ru": "Отметьте хотя бы одну сцену.", "en": "Check at least one scene."},
    "git_scene_commit.default_message": {"ru": "Снепшот (по выбранным сценам)", "en": "Snapshot (by selected scenes)"},
    "git_scene_commit.progress_prepare": {"ru": "Подготовка...", "en": "Preparing..."},
    "git_scene_commit.progress_title": {"ru": "Git - коммит по сценам", "en": "Git - Commit by Scenes"},
    "git_scene_commit.progress_adding": {
        "ru": "Добавление файлов в коммит... {done}/{total}",
        "en": "Adding files to commit... {done}/{total}",
    },
    "git_scene_commit.progress_committing": {"ru": "Коммит...", "en": "Committing..."},
    "git_scene_commit.error_title": {"ru": "Ошибка", "en": "Error"},
    "git_scene_commit.done_title": {"ru": "Готово", "en": "Done"},
    "git_scene_commit.done_text": {
        "ru": "Закоммичено сцен: {committed} из {total} изменённых.\n\n"
              "Остальные изменения остались в рабочей копии - закоммитьте их позже.",
        "en": "Scenes committed: {committed} out of {total} changed.\n\n"
              "The remaining changes are still in the working copy - commit them later.",
    },

                                    
    "diff.merge_title": {"ru": "Построчный merge - {name}", "en": "Line-by-line Merge - {name}"},
    "diff.merge_info": {
        "ru": "Для каждого отличающегося куска выберите: оставить версию из файла на "
              "диске (ваши ручные правки) или принять версию, которую сгенерировал "
              "редактор. Одинаковые участки merge не трогает.",
        "en": "For each differing chunk, choose whether to keep the version from "
              "the file on disk (your manual edits) or accept the version "
              "generated by the editor. Identical sections are left untouched by the merge.",
    },
    "diff.accept_new": {"ru": "✅ Принять новую версию", "en": "✅ Accept New Version"},
    "diff.keep_old": {"ru": "↩ Оставить как в файле", "en": "↩ Keep as in File"},
    "diff.no_lines": {"ru": "(строк не было)", "en": "(there were no lines)"},
    "diff.lines_removed": {"ru": "(строки удаляются)", "en": "(lines are removed)"},
    "diff.from_disk": {"ru": "Из файла на диске:", "en": "From the file on disk:"},
    "diff.generated_by_editor": {"ru": "Сгенерировано редактором:", "en": "Generated by the editor:"},
    "diff.identical_no_merge": {
        "ru": "Файлы построчно идентичны - merge не нужен.",
        "en": "Files are line-by-line identical - no merge needed.",
    },
    "diff.cancel": {"ru": "Отмена", "en": "Cancel"},
    "diff.apply_merge": {"ru": "Применить merge ({count} хунков)", "en": "Apply Merge ({count} hunks)"},
    "diff.preview_title": {"ru": "Проверка изменений - {name}", "en": "Review Changes - {name}"},
    "diff.overwrite_warning": {
        "ru": "Файл «{path}» уже существует и отличается от того, что "
              "сгенерирует редактор. Если в нём есть ручные правки, сделанные мимо "
              "редактора (например, напрямую в Ren'Py) - они будут потеряны при "
              "перезаписи. Красным - что удалится, зелёным - что добавится.",
        "en": "The file \"{path}\" already exists and differs from what the "
              "editor will generate. If it contains manual edits made outside "
              "the editor (e.g. directly in Ren'Py) - they will be lost on "
              "overwrite. Red - what will be removed, green - what will be added.",
    },
    "diff.save_copy": {"ru": "💾 Сохранить копию рядом", "en": "💾 Save a Copy Nearby"},
    "diff.merge_button": {"ru": "🔀 Построчный merge...", "en": "🔀 Line-by-line Merge..."},
    "diff.overwrite_button": {"ru": "⚠ Перезаписать существующий файл", "en": "⚠ Overwrite Existing File"},
    "diff.stats": {
        "ru": "Добавлено строк: {added}   \u2022   Удалено строк: {removed}",
        "en": "Lines added: {added}   \u2022   Lines removed: {removed}",
    },
    "diff.fromfile_label": {"ru": "текущий файл на диске", "en": "current file on disk"},
    "diff.tofile_label": {"ru": "то, что сгенерирует редактор", "en": "what the editor will generate"},
    "diff.identical_lines": {"ru": "(файлы идентичны построчно)", "en": "(files are line-by-line identical)"},
    "diff.save_copy_title": {"ru": "Сохранить копию рядом", "en": "Save a Copy Nearby"},
    "diff.all_files": {"ru": "Все файлы", "en": "All Files"},

                            
    "tags.picker_title": {"ru": "Теги: {name}", "en": "Tags: {name}"},
    "tags.no_categories": {
        "ru": "Категорий тегов пока нет. Создайте их через "
              "«Проект → Категории тегов...», затем вернитесь сюда.",
        "en": "There are no tag categories yet. Create them via "
              "\"Project \u2192 Tag Categories...\", then come back here.",
    },
    "tags.no_tags_in_category": {"ru": "(нет тегов в этой категории)", "en": "(no tags in this category)"},
    "tags.cancel": {"ru": "Отмена", "en": "Cancel"},
    "tags.save": {"ru": "Сохранить", "en": "Save"},
    "tags.manager_title": {"ru": "Категории тегов (для фонов и CG)", "en": "Tag Categories (for backgrounds and CG)"},
    "tags.manager_hint": {
        "ru": "Создайте категорию (например, «Локация» или «Время суток»), а внутри "
              "неё - теги («пляж», «лес», «день», «ночь»). У одного фона/CG может "
              "быть сразу несколько тегов из разных категорий.",
        "en": "Create a category (e.g. \"Location\" or \"Time of Day\"), and "
              "tags inside it (\"beach\", \"forest\", \"day\", \"night\"). A "
              "single background/CG can have several tags from different categories.",
    },
    "tags.categories_label": {"ru": "Категории:", "en": "Categories:"},
    "tags.new_category_placeholder": {"ru": "Новая категория...", "en": "New category..."},
    "tags.rename": {"ru": "✎ Переименовать", "en": "✎ Rename"},
    "tags.delete": {"ru": "✕ Удалить", "en": "✕ Delete"},
    "tags.tags_in_category_label": {"ru": "Теги в категории:", "en": "Tags in category:"},
    "tags.new_tag_placeholder": {"ru": "Новый тег...", "en": "New tag..."},
    "tags.delete_tag": {"ru": "✕ Удалить тег", "en": "✕ Delete Tag"},
    "tags.close": {"ru": "Закрыть", "en": "Close"},
    "tags.rename_category_title": {"ru": "Переименовать категорию", "en": "Rename Category"},
    "tags.new_name_label": {"ru": "Новое имя:", "en": "New name:"},
    "tags.delete_category_title": {"ru": "Удалить категорию", "en": "Delete Category"},
    "tags.delete_category_confirm": {
        "ru": "Удалить категорию «{name}» и все её теги? Теги будут сняты со всех "
              "ресурсов, которым они были назначены.",
        "en": "Delete the category \"{name}\" and all its tags? The tags will "
              "be removed from all resources they were assigned to.",
    },

                                  
    "characters.group_title": {"ru": "Персонаж", "en": "Character"},
    "characters.name_label": {"ru": "Имя:", "en": "Name:"},
    "characters.variable_label": {"ru": "Переменная:", "en": "Variable:"},
    "characters.color_label": {"ru": "Цвет:", "en": "Color:"},
    "characters.image_tag_label": {"ru": "Image tag:", "en": "Image tag:"},
    "characters.image_tag_placeholder": {"ru": "Необязательно", "en": "Optional"},
    "characters.title": {"ru": "Персонажи", "en": "Characters"},
    "characters.list_label": {"ru": "Список персонажей:", "en": "Character list:"},
    "characters.add": {"ru": "+ Добавить", "en": "+ Add"},
    "characters.delete": {"ru": "✕ Удалить", "en": "✕ Delete"},
    "characters.export": {"ru": "⬆ Экспорт...", "en": "⬆ Export..."},
    "characters.export_tooltip": {
        "ru": "Сохранить список персонажей в отдельный JSON-файл, "
              "чтобы перенести в другой проект или сделать резервную копию.",
        "en": "Save the character list to a separate JSON file, "
              "to move it to another project or make a backup.",
    },
    "characters.import": {"ru": "⬇ Импорт...", "en": "⬇ Import..."},
    "characters.import_tooltip": {
        "ru": "Загрузить персонажей из файла, ранее сохранённого через «Экспорт».",
        "en": "Load characters from a file previously saved via \"Export\".",
    },
    "characters.reset_list": {"ru": "🗑 Сбросить список", "en": "🗑 Reset List"},
    "characters.reset_tooltip": {
        "ru": "Удалить ВСЕХ персонажей из текущего проекта.",
        "en": "Delete ALL characters from the current project.",
    },
    "characters.apply": {"ru": "💾 Применить", "en": "💾 Apply"},
    "characters.new_name": {"ru": "Новый", "en": "New"},
    "characters.nothing_to_export_title": {"ru": "Нечего экспортировать", "en": "Nothing to Export"},
    "characters.list_empty": {"ru": "Список персонажей пуст.", "en": "The character list is empty."},
    "characters.export_title": {"ru": "Экспорт персонажей", "en": "Export Characters"},
    "characters.all_files": {"ru": "Все файлы", "en": "All Files"},
    "characters.done_title": {"ru": "Готово", "en": "Done"},
    "characters.exported_text": {
        "ru": "Экспортировано {count} персонажей в:\n{path}",
        "en": "Exported {count} characters to:\n{path}",
    },
    "characters.export_error_title": {"ru": "Ошибка экспорта", "en": "Export Error"},
    "characters.import_title": {"ru": "Импорт персонажей", "en": "Import Characters"},
    "characters.merge_title": {"ru": "Как объединить?", "en": "How to Merge?"},
    "characters.merge_text": {
        "ru": "Добавить импортированных персонажей к текущим "
              "(совпадающие по переменной будут перезаписаны)?\n\n"
              "Да - добавить/обновить.\nНет - полностью заменить текущий список.",
        "en": "Add imported characters to the current ones "
              "(those matching by variable will be overwritten)?\n\n"
              "Yes - add/update.\nNo - completely replace the current list.",
    },
    "characters.empty_file_title": {"ru": "Пустой файл", "en": "Empty File"},
    "characters.empty_file_text": {"ru": "В файле не найдено персонажей.", "en": "No characters found in the file."},
    "characters.imported_text": {"ru": "Импортировано {count} персонажей.", "en": "{count} characters imported."},
    "characters.import_error_title": {"ru": "Ошибка импорта", "en": "Import Error"},
    "characters.nothing_to_reset_title": {"ru": "Нечего сбрасывать", "en": "Nothing to Reset"},
    "characters.list_already_empty": {
        "ru": "Список персонажей уже пуст.",
        "en": "The character list is already empty.",
    },
    "characters.reset_confirm_title": {"ru": "Сбросить список персонажей?", "en": "Reset Character List?"},
    "characters.reset_confirm_text": {
        "ru": "Удалить всех {count} персонажей из проекта? "
              "Узлы диалогов, ссылающиеся на них, останутся, но без привязки к персонажу.\n\n"
              "Это действие нельзя отменить.",
        "en": "Delete all {count} characters from the project? "
              "Dialogue nodes referencing them will remain, but without a character link.\n\n"
              "This action cannot be undone.",
    },
    "characters.reset_done_text": {"ru": "Список персонажей сброшен.", "en": "Character list has been reset."},
    "characters.error_title": {"ru": "Ошибка", "en": "Error"},
    "characters.name_var_required": {
        "ru": "Имя и переменная обязательны",
        "en": "Name and variable are required",
    },

                           
    "git.unexpected_error": {"ru": "Неожиданная ошибка: {error}", "en": "Unexpected error: {error}"},
    "git.dialog_title": {"ru": "Git", "en": "Git"},
    "git.progress_prepare": {"ru": "Подготовка...", "en": "Preparing..."},
    "git.commit_progress_title": {"ru": "Git - коммит", "en": "Git - Commit"},
    "git.progress_adding": {
        "ru": "Добавление файлов в коммит... {done}/{total}",
        "en": "Adding files to commit... {done}/{total}",
    },
    "git.progress_committing": {"ru": "Коммит...", "en": "Committing..."},
    "git.panel_title": {"ru": "Версионирование проекта (Git)", "en": "Project Versioning (Git)"},
    "git.repo_label": {"ru": "Репозиторий: {path}", "en": "Repository: {path}"},
    "git.not_found_warning": {
        "ru": "⚠ Программа 'git' не найдена автоматически (ни в PATH, ни в стандартных "
              "папках установки, ни в реестре). Если Git установлен, но не находится "
              "автоматически - часто это из-за того, что exe запущен из проводника со "
              "«старым» PATH - укажите путь к git.exe вручную ниже.",
        "en": "⚠ The 'git' program was not found automatically (not in PATH, "
              "standard install folders, or the registry). If Git is installed "
              "but not found automatically - often this is because the exe was "
              "launched from Explorer with a \"stale\" PATH - specify the path "
              "to git.exe manually below.",
    },
    "git.path_placeholder": {"ru": "напр. C:\\Program Files\\Git\\cmd\\git.exe", "en": "e.g. C:\\Program Files\\Git\\cmd\\git.exe"},
    "git.browse": {"ru": "Обзор...", "en": "Browse..."},
    "git.apply_and_check": {"ru": "Применить и проверить", "en": "Apply and Check"},
    "git.tab_snapshots": {"ru": "📝 Снепшоты", "en": "📝 Snapshots"},
    "git.tab_graph": {"ru": "🌳 Граф", "en": "🌳 Graph"},
    "git.tab_tags": {"ru": "🏷 Теги", "en": "🏷 Tags"},
    "git.tab_github": {"ru": "☁ GitHub", "en": "☁ GitHub"},
    "git.tab_lfs": {"ru": "📦 LFS", "en": "📦 LFS"},
    "git.close": {"ru": "Закрыть", "en": "Close"},
    "git.init_repo_here": {"ru": "Инициализировать репозиторий здесь", "en": "Initialize Repository Here"},
    "git.update_gitignore": {"ru": "📄 Обновить .gitignore шаблон", "en": "📄 Update .gitignore Template"},
    "git.gitignore_tooltip": {
        "ru": "Дописывает рекомендованные исключения (кэш, автосохранение, "
              "__pycache__ и т.п.) в .gitignore. Существующий файл не "
              "перезаписывается целиком - спросит подтверждение.",
        "en": "Appends recommended exclusions (cache, autosave, "
              "__pycache__, etc.) to .gitignore. The existing file is not "
              "overwritten entirely - it will ask for confirmation.",
    },
    "git.unsaved_changes_label": {"ru": "Несохранённые изменения в рабочей папке:", "en": "Unsaved changes in the working folder:"},
    "git.commit_msg_placeholder": {
        "ru": "Описание снепшота, напр. «Глава 2 - конец»",
        "en": "Snapshot description, e.g. \"Chapter 2 - ending\"",
    },
    "git.make_snapshot": {"ru": "💾 Сделать снепшот", "en": "💾 Make Snapshot"},
    "git.commit_by_scenes": {"ru": "📦 Commit по сценам...", "en": "📦 Commit by Scenes..."},
    "git.commit_by_scenes_tooltip": {
        "ru": "Выбрать, какие именно изменённые сцены попадут в этот снепшот, "
              "а какие останутся несохранёнными для отдельного коммита позже.",
        "en": "Choose which changed scenes go into this snapshot, "
              "and which stay uncommitted for a separate commit later.",
    },
    "git.history_label": {"ru": "История снепшотов:", "en": "Snapshot history:"},
    "git.show_diff": {"ru": "👁 Показать дифф этого снепшота", "en": "👁 Show This Snapshot's Diff"},
    "git.restore_version": {"ru": "⏪ Восстановить эту версию", "en": "⏪ Restore This Version"},
    "git.graph_hint": {
        "ru": "История по всем веткам (не только текущей) - точки на дорожках "
              "показывают ветвления/слияния, бейджи - имена веток и HEAD.",
        "en": "History across all branches (not just the current one) - dots "
              "on lanes show branches/merges, badges show branch names and HEAD.",
    },
    "git.show_selected_diff": {"ru": "👁 Показать дифф выбранного коммита", "en": "👁 Show Selected Commit's Diff"},
    "git.nothing_selected_title": {"ru": "Ничего не выбрано", "en": "Nothing Selected"},
    "git.click_commit_in_graph": {"ru": "Кликните на коммит в графе.", "en": "Click a commit in the graph."},
    "git.commit_diff_title": {"ru": "Дифф коммита", "en": "Commit Diff"},
    "git.snapshot_diff_title": {"ru": "Дифф снепшота", "en": "Snapshot Diff"},
    "git.tags_hint": {
        "ru": "Теги - маркировка версий сценария (v1.0, v1.1, «демо для издателя» и т.п.), "
              "привязана к конкретному коммиту.",
        "en": "Tags mark script versions (v1.0, v1.1, \"publisher demo\", etc.), "
              "tied to a specific commit.",
    },
    "git.tag_name_placeholder": {"ru": "напр. v1.0", "en": "e.g. v1.0"},
    "git.tag_msg_placeholder": {"ru": "Сообщение релиза (необязательно)", "en": "Release message (optional)"},
    "git.create_tag_head": {"ru": "🏷 Создать тег на HEAD", "en": "🏷 Create Tag on HEAD"},
    "git.delete_selected": {"ru": "🗑 Удалить выбранный", "en": "🗑 Delete Selected"},
    "git.push_selected": {"ru": "⬆ Отправить выбранный", "en": "⬆ Push Selected"},
    "git.push_all_tags": {"ru": "⬆ Отправить все теги", "en": "⬆ Push All Tags"},
    "git.enter_name_title": {"ru": "Укажите имя", "en": "Enter a Name"},
    "git.enter_tag_name": {"ru": "Введите имя тега, например v1.0", "en": "Enter a tag name, e.g. v1.0"},
    "git.tag_create_failed": {"ru": "Не удалось создать тег", "en": "Failed to Create Tag"},
    "git.delete_tag_title": {"ru": "Удалить тег?", "en": "Delete Tag?"},
    "git.delete_tag_confirm": {"ru": "Удалить тег «{name}»?", "en": "Delete tag \"{name}\"?"},
    "git.error_title": {"ru": "Ошибка", "en": "Error"},
    "git.select_tag_in_list": {"ru": "Выберите тег в списке.", "en": "Select a tag in the list."},
    "git.tag_push_failed": {"ru": "Push тега не удался", "en": "Tag Push Failed"},
    "git.done_title": {"ru": "Готово", "en": "Done"},
    "git.tag_pushed": {"ru": "Тег отправлен.", "en": "Tag pushed."},
    "git.tags_push_failed": {"ru": "Push тегов не удался", "en": "Tags Push Failed"},
    "git.tags_pushed": {"ru": "Теги отправлены.", "en": "Tags pushed."},
    "git.lfs_info": {
        "ru": "Git LFS хранит большие бинарные файлы (спрайты, аудио, видео) отдельно "
              "от истории текстовых изменений - обычный git-репозиторий с ними быстро "
              "раздувается, LFS этого не допускает. Отметьте, какие типы файлов "
              "проекта нужно вести через LFS.",
        "en": "Git LFS stores large binary files (sprites, audio, video) "
              "separately from the text-change history - a regular git "
              "repository would quickly bloat with them, LFS prevents that. "
              "Check which types of project files should be tracked via LFS.",
    },
    "git.file_types_box": {"ru": "Типы файлов", "en": "File Types"},
    "git.lfs_apply": {"ru": "📦 Применить (git lfs track)", "en": "📦 Apply (git lfs track)"},
    "git.lfs_status_label": {"ru": "Статус LFS:", "en": "LFS Status:"},
    "git.nothing_to_do_title": {"ru": "Ничего не выбрано", "en": "Nothing Selected"},
    "git.select_file_type": {"ru": "Отметьте хотя бы один тип файлов.", "en": "Check at least one file type."},
    "git.failed_title": {"ru": "Не удалось", "en": "Failed"},
    "git.lfs_applied_note": {
        "ru": "{out}\n\nНе забудьте закоммитить .gitattributes (обычный снепшот подхватит его).",
        "en": "{out}\n\nDon't forget to commit .gitattributes (a regular snapshot will pick it up).",
    },
    "git.lfs_not_found": {
        "ru": "⚠ Git LFS не найден в системе. Установите расширение: https://git-lfs.com",
        "en": "⚠ Git LFS not found on the system. Install the extension: https://git-lfs.com",
    },
    "git.lfs_installed": {"ru": "✓ Git LFS установлен.", "en": "✓ Git LFS is installed."},
    "git.pick_git_exe_title": {"ru": "Укажите путь к git.exe", "en": "Specify the Path to git.exe"},
    "git.all_files": {"ru": "Все файлы", "en": "All Files"},
    "git.found_and_connected": {"ru": "Git найден и подключён.", "en": "Git found and connected."},
    "git.not_starting_at_path": {
        "ru": "По этому пути git не запускается:\n{path}",
        "en": "Git does not start at this path:\n{path}",
    },
    "git.gitignore_write_failed": {"ru": "Не удалось записать .gitignore", "en": "Failed to Write .gitignore"},
    "git.gitignore_already_ok": {
        "ru": "В .gitignore уже есть все рекомендованные исключения.",
        "en": ".gitignore already has all the recommended exclusions.",
    },
    "git.gitignore_lines_added": {
        "ru": "Добавлено строк в .gitignore: {count}",
        "en": "Lines added to .gitignore: {count}",
    },
    "git.default_commit_msg": {"ru": "Снепшот проекта", "en": "Project Snapshot"},
    "git.snapshot_failed": {"ru": "Не удалось создать снепшот", "en": "Failed to Create Snapshot"},
    "git.no_changes_to_snapshot": {"ru": "Нет изменений для снепшота", "en": "No changes to snapshot"},
    "git.unavailable_title": {"ru": "Недоступно", "en": "Unavailable"},
    "git.no_project_file": {
        "ru": "Не удалось определить файл проекта для частичного коммита.",
        "en": "Could not determine the project file for a partial commit.",
    },
    "git.file_not_found_title": {"ru": "Файл не найден", "en": "File Not Found"},
    "git.project_file_not_found": {
        "ru": "Не найден файл проекта: {path}",
        "en": "Project file not found: {path}",
    },
    "git.restore_version_title": {"ru": "Восстановить версию?", "en": "Restore Version?"},
    "git.restore_confirm": {
        "ru": "Восстановить файлы проекта к состоянию «{name}»?\n\n"
              "Текущие несохранённые изменения в рабочей папке будут ЗАМЕНЕНЫ. "
              "Это создаст новый снепшот с восстановленным содержимым - история "
              "не удаляется, при желании можно откатить и сам откат.\n\n"
              "После восстановления перезагрузите проект в редакторе (Файл → Открыть).",
        "en": "Restore the project files to the state \"{name}\"?\n\n"
              "The current unsaved changes in the working folder will be "
              "REPLACED. This will create a new snapshot with the restored "
              "content - history is not deleted, and the restore itself can "
              "be reverted if needed.\n\n"
              "After restoring, reload the project in the editor (File \u2192 Open).",
    },
    "git.restored_note": {
        "ru": "Файлы восстановлены. Откройте проект заново (Файл → Открыть), "
              "чтобы редактор подхватил восстановленную версию .repj.",
        "en": "Files restored. Reopen the project (File \u2192 Open) so the "
              "editor picks up the restored .repj version.",
    },
    "git.token_info": {
        "ru": "Токен доступа GitHub (Personal Access Token, права 'repo') нужен для "
              "push/pull в приватный репозиторий. Он сохраняется ЛОКАЛЬНО в открытом "
              "виде в настройках редактора на этом компьютере - не используйте токен "
              "с лишними правами.",
        "en": "A GitHub Personal Access Token ('repo' scope) is needed for "
              "push/pull to a private repository. It is stored LOCALLY in "
              "plain text in the editor's settings on this computer - do not "
              "use a token with excessive permissions.",
    },
    "git.remote_url_label": {"ru": "URL репозитория (https://github.com/user/repo.git):", "en": "Repository URL (https://github.com/user/repo.git):"},
    "git.token_label": {"ru": "Personal Access Token:", "en": "Personal Access Token:"},
    "git.save_and_link_remote": {"ru": "Сохранить и привязать удалённый репозиторий", "en": "Save and Link Remote Repository"},
    "git.push": {"ru": "⬆ Отправить (push)", "en": "⬆ Push"},
    "git.pull": {"ru": "⬇ Получить (pull)", "en": "⬇ Pull"},
    "git.push_failed": {"ru": "Push не удался", "en": "Push Failed"},
    "git.pull_failed": {"ru": "Pull не удался", "en": "Pull Failed"},
    "git.pull_done_note": {
        "ru": "Изменения получены. Переоткройте проект (Файл → Открыть).",
        "en": "Changes fetched. Reopen the project (File \u2192 Open).",
    },
    "git.current_remote": {"ru": "Текущий удалённый репозиторий: {url}", "en": "Current remote repository: {url}"},
    "git.not_configured": {"ru": "(не настроен)", "en": "(not configured)"},
    "git.repo_initialized": {
        "ru": "Git-репозиторий уже инициализирован в этой папке.",
        "en": "A Git repository is already initialized in this folder.",
    },
    "git.repo_not_initialized": {
        "ru": "В папке проекта ещё нет Git-репозитория.",
        "en": "There is no Git repository in the project folder yet.",
    },

                                 
    "res_config.title": {"ru": "Настройки ресурсов", "en": "Resource Settings"},
    "res_config.path_group": {"ru": "Путь к папке ресурсов", "en": "Resources Folder Path"},
    "res_config.path_placeholder": {"ru": "resources", "en": "resources"},
    "res_config.browse": {"ru": "📁 Обзор", "en": "📁 Browse"},
    "res_config.info": {
        "ru": "Структура: resources/default/... и resources/custom/...\n"
              "Внутри каждой - bg/  cg/  sprites/  music/  sounds/ (одинаковая структура в обеих).\n"
              "Разница: объявления (image/define) генерируются ТОЛЬКО для ресурсов из custom/ - "
              "default/ считается уже объявленным где-то ещё и не дублируется в коде.\n"
              "Спрайты можно раскладывать по подпапкам персонажей и вариаций, например:\n"
              "resources/custom/sprites/us/normal/smile.png\n"
              "Имена переменных генерируются из имён файлов (и пути подпапки). Ниже можно задать свои.",
        "en": "Structure: resources/default/... and resources/custom/...\n"
              "Inside each - bg/  cg/  sprites/  music/  sounds/ (identical structure in both).\n"
              "Difference: declarations (image/define) are generated ONLY for "
              "resources from custom/ - default/ is considered already declared "
              "elsewhere and is not duplicated in code.\n"
              "Sprites can be organized into character/variation subfolders, e.g.:\n"
              "resources/custom/sprites/us/normal/smile.png\n"
              "Variable names are generated from file names (and subfolder path). "
              "You can set your own below.",
    },
    "res_config.fav_recent_check": {
        "ru": "Показывать «Избранное» и «Недавние» вверху карусели ресурсов",
        "en": "Show \"Favorites\" and \"Recent\" at the top of the resource carousel",
    },
    "res_config.overrides_group": {"ru": "Переопределения имён, теги и использование", "en": "Name Overrides, Tags and Usage"},
    "res_config.col_file": {"ru": "Файл", "en": "File"},
    "res_config.col_source": {"ru": "Источник", "en": "Source"},
    "res_config.col_auto_var": {"ru": "Авто-переменная", "en": "Auto Variable"},
    "res_config.col_custom_name": {"ru": "Своё имя", "en": "Custom Name"},
    "res_config.col_custom_var": {"ru": "Своя переменная", "en": "Custom Variable"},
    "res_config.col_tags": {"ru": "Теги", "en": "Tags"},
    "res_config.col_usage": {"ru": "Использование", "en": "Usage"},
    "res_config.col_volume": {"ru": "Громкость", "en": "Volume"},
    "res_config.save_overrides": {"ru": "💾 Сохранить переопределения", "en": "💾 Save Overrides"},
    "res_config.export_to_file": {"ru": "⬆ Экспорт в файл...", "en": "⬆ Export to File..."},
    "res_config.export_tooltip": {
        "ru": "Сохранить набор переопределённых имён в отдельный JSON-файл, "
              "чтобы перенести в другой проект или сделать резервную копию.",
        "en": "Save the set of overridden names to a separate JSON file, "
              "to move it to another project or make a backup.",
    },
    "res_config.import_from_file": {"ru": "⬇ Импорт из файла...", "en": "⬇ Import from File..."},
    "res_config.import_tooltip": {
        "ru": "Загрузить переопределённые имена из файла, ранее сохранённого "
              "через «Экспорт в файл».",
        "en": "Load overridden names from a file previously saved via "
              "\"Export to File\".",
    },
    "res_config.reset_overrides": {"ru": "🗑 Сбросить переопределения", "en": "🗑 Reset Overrides"},
    "res_config.reset_tooltip": {
        "ru": "Полностью удалить все свои имена/переменные - ресурсы вернутся "
              "к автоматически сгенерированным именам.",
        "en": "Completely remove all custom names/variables - resources will "
              "revert to automatically generated names.",
    },
    "res_config.volume_tooltip": {
        "ru": "Громкость по умолчанию для этого трека/канала (0.0–1.0).\n"
              "Если оставить 1.00 - параметр volume не попадёт в сгенерированный код.",
        "en": "Default volume for this track/channel (0.0-1.0).\n"
              "If left at 1.00, the volume parameter won't appear in the generated code.",
    },
    "res_config.usage_tooltip": {
        "ru": "Показать все места использования этого ресурса и перейти к ноде",
        "en": "Show all usages of this resource and jump to the node",
    },
    "res_config.usage_unavailable": {
        "ru": "Недоступно: проект не передан в диалог",
        "en": "Unavailable: project was not passed to the dialog",
    },
    "res_config.tags_button": {"ru": "🏷 Теги...", "en": "🏷 Tags..."},
    "res_config.pick_folder": {"ru": "Выберите папку ресурсов", "en": "Select Resources Folder"},
    "res_config.done_title": {"ru": "Готово", "en": "Done"},
    "res_config.overrides_saved": {"ru": "Переопределения сохранены", "en": "Overrides saved"},
    "res_config.nothing_to_export_title": {"ru": "Нечего экспортировать", "en": "Nothing to Export"},
    "res_config.overrides_empty": {
        "ru": "Список переопределений пуст - нет ни одного "
              "своего имени или переменной.",
        "en": "The overrides list is empty - there is not a single "
              "custom name or variable.",
    },
    "res_config.export_title": {"ru": "Экспорт переопределений", "en": "Export Overrides"},
    "res_config.all_files": {"ru": "Все файлы", "en": "All Files"},
    "res_config.exported_text": {
        "ru": "Экспортировано {count} переопределений в:\n{path}",
        "en": "Exported {count} overrides to:\n{path}",
    },
    "res_config.export_error_title": {"ru": "Ошибка экспорта", "en": "Export Error"},
    "res_config.import_title": {"ru": "Импорт переопределений", "en": "Import Overrides"},
    "res_config.merge_title": {"ru": "Как объединить?", "en": "How to Merge?"},
    "res_config.merge_text": {
        "ru": "Добавить импортированные переопределения к текущим "
              "(совпадающие файлы будут перезаписаны)?\n\n"
              "Да - добавить/обновить.\nНет - полностью заменить текущий список.",
        "en": "Add the imported overrides to the current ones "
              "(matching files will be overwritten)?\n\n"
              "Yes - add/update.\nNo - completely replace the current list.",
    },
    "res_config.imported_text": {"ru": "Импортировано {count} переопределений.", "en": "{count} overrides imported."},
    "res_config.import_error_title": {"ru": "Ошибка импорта", "en": "Import Error"},
    "res_config.nothing_to_reset_title": {"ru": "Нечего сбрасывать", "en": "Nothing to Reset"},
    "res_config.overrides_already_empty": {
        "ru": "Список переопределений уже пуст.",
        "en": "The overrides list is already empty.",
    },
    "res_config.reset_confirm_title": {"ru": "Сбросить переопределения?", "en": "Reset Overrides?"},
    "res_config.reset_confirm_text": {
        "ru": "Удалить все {count} переопределённых имён/переменных? "
              "Ресурсы вернутся к автоматически сгенерированным именам.\n\n"
              "Это действие нельзя отменить.",
        "en": "Delete all {count} overridden names/variables? "
              "Resources will revert to automatically generated names.\n\n"
              "This action cannot be undone.",
    },
    "res_config.reset_done_text": {"ru": "Все переопределения сброшены.", "en": "All overrides have been reset."},

                                             
    "custom_nodes.name_param_placeholder": {"ru": "имя_параметра", "en": "param_name"},
    "custom_nodes.label_in_form_placeholder": {"ru": "Подпись в форме", "en": "Label in form"},
    "custom_nodes.default_value_placeholder": {"ru": "значение по умолчанию", "en": "default value"},
    "custom_nodes.title": {"ru": "Шаблоны пользовательских нод", "en": "Custom Node Templates"},
    "custom_nodes.tab_templates": {"ru": "Шаблоны", "en": "Templates"},
    "custom_nodes.tab_help": {"ru": "📖 Справка", "en": "📖 Help"},
    "custom_nodes.close": {"ru": "Закрыть", "en": "Close"},
    "custom_nodes.no_jinja2": {
        "ru": "⚠ Пакет jinja2 не установлен - шаблоны сохранятся, но НЕ будут "
              "применяться при генерации кода (pip install jinja2).",
        "en": "⚠ The jinja2 package is not installed - templates will be saved, "
              "but will NOT be applied during code generation (pip install jinja2).",
    },
    "custom_nodes.templates_label": {"ru": "Шаблоны:", "en": "Templates:"},
    "custom_nodes.new": {"ru": "+ Новый", "en": "+ New"},
    "custom_nodes.delete": {"ru": "Удалить", "en": "Delete"},
    "custom_nodes.name_label": {"ru": "Название:", "en": "Name:"},
    "custom_nodes.desc_label": {"ru": "Описание (подсказка в форме ноды):", "en": "Description (hint in the node form):"},
    "custom_nodes.params_label": {"ru": "Параметры:", "en": "Parameters:"},
    "custom_nodes.add_param": {"ru": "+ Добавить параметр", "en": "+ Add Parameter"},
    "custom_nodes.jinja_template_label": {"ru": "Jinja2-шаблон кода:", "en": "Jinja2 code template:"},
    "custom_nodes.preview_label": {"ru": "Предпросмотр (с значениями по умолчанию):", "en": "Preview (with default values):"},
    "custom_nodes.new_template_name": {"ru": "Новый шаблон {n}", "en": "New Template {n}"},
    "custom_nodes.delete_template_title": {"ru": "Удалить шаблон?", "en": "Delete Template?"},
    "custom_nodes.delete_template_confirm": {
        "ru": "Удалить шаблон «{name}»? "
              "Уже вставленные ноды этого типа не удалятся, но перестанут находить шаблон.",
        "en": "Delete the template \"{name}\"? "
              "Already inserted nodes of this type won't be deleted, but will "
              "no longer find the template.",
    },

                                                
    "mw.scenes_group": {"ru": "Сцены", "en": "Scenes"},
    "mw.new_label_button": {"ru": "Новый label", "en": "New label"},
    "mw.branch_label": {"ru": "Ветка меню", "en": "Menu Branch"},
    "mw.scene_elements_group": {"ru": "Элементы сцены", "en": "Scene Elements"},
    "mw.add_button": {"ru": "Добавить", "en": "Add"},
    "mw.new_scene_title": {"ru": "Новая сцена", "en": "New Scene"},
    "mw.name_label": {"ru": "Название:", "en": "Name:"},
    "mw.undo.scene_added": {"ru": "Добавлена сцена «{name}»", "en": "Added scene \"{name}\""},
    "mw.rename_title": {"ru": "Переименовать", "en": "Rename"},
    "mw.new_name_label": {"ru": "Новое название:", "en": "New name:"},
    "mw.undo.scene_renamed": {
        "ru": "Сцена «{old}» переименована в «{new}»",
        "en": "Scene \"{old}\" renamed to \"{new}\"",
    },
    "mw.cannot_title": {"ru": "Нельзя", "en": "Not Allowed"},
    "mw.need_one_scene": {"ru": "Должна быть хотя бы одна сцена", "en": "There must be at least one scene"},
    "mw.delete_scene_title": {"ru": "Удалить сцену", "en": "Delete Scene"},
    "mw.delete_scene_confirm": {"ru": "Удалить сцену «{name}»?", "en": "Delete scene \"{name}\"?"},
    "mw.undo.scene_deleted": {"ru": "Удалена сцена «{name}»", "en": "Deleted scene \"{name}\""},
    "mw.undo.node_added": {"ru": "Добавлена нода", "en": "Added node"},
    "mw.undo.node_added_dialogue": {"ru": "Добавлена нода: 💬 Реплика", "en": "Added node: 💬 Line"},
    "mw.undo.node_duplicated": {"ru": "Дублирована нода: {preview}", "en": "Duplicated node: {preview}"},
    "mw.undo.node_moved_up": {"ru": "Нода перемещена вверх: {preview}", "en": "Node moved up: {preview}"},
    "mw.undo.node_edited": {"ru": "Нода изменена: {preview}", "en": "Node edited: {preview}"},
    "mw.undo.node_moved_down": {"ru": "Нода перемещена вниз: {preview}", "en": "Node moved down: {preview}"},
    "mw.undo.node_deleted": {"ru": "Удалена нода: {preview}", "en": "Deleted node: {preview}"},
    "mw.undo.nodes_deleted": {"ru": "Удалено нод: {count}", "en": "Deleted nodes: {count}"},
    "mw.undo.connection_removed": {"ru": "Связь удалена", "en": "Connection removed"},
    "mw.undo.nodes_recolored": {"ru": "Изменён цвет {count} нод(ы)", "en": "Changed color of {count} node(s)"},
    "mw.undo.branch_duplicated": {
        "ru": "Дублирована ветка ({count} нод, начиная с «{preview}»)",
        "en": "Duplicated branch ({count} nodes, starting from \"{preview}\")",
    },
    "mw.undo.nodes_pasted": {"ru": "Вставлено нод: {count}", "en": "Pasted nodes: {count}"},
    "mw.undo.group_created": {"ru": "Создана группа «{title}» ({count} нод)", "en": "Created group \"{title}\" ({count} nodes)"},
    "mw.undo.ungrouped": {"ru": "Разгруппировано: «{title}»", "en": "Ungrouped: \"{title}\""},
    "mw.undo.group_collapsed": {"ru": "Свёрнута группа «{title}»", "en": "Collapsed group \"{title}\""},
    "mw.undo.group_expanded": {"ru": "Развёрнута группа «{title}»", "en": "Expanded group \"{title}\""},
    "mw.undo.group_renamed": {
        "ru": "Группа «{old}» переименована в «{new}»",
        "en": "Group \"{old}\" renamed to \"{new}\"",
    },
    "mw.undo.group_recolored": {"ru": "Изменён цвет группы «{title}»", "en": "Changed color of group \"{title}\""},
    "mw.ctx.toggle_group": {"ru": "Свернуть/развернуть группу", "en": "Collapse/Expand Group"},
    "mw.ctx.rename_group": {"ru": "Переименовать группу...", "en": "Rename Group..."},
    "mw.ctx.ungroup": {"ru": "Разгруппировать", "en": "Ungroup"},
    "mw.ctx.no_label": {"ru": "Без метки", "en": "No Label"},
    "mw.ctx.copy": {"ru": "Копировать (Ctrl+C)", "en": "Copy (Ctrl+C)"},
    "mw.ctx.paste_after": {"ru": "Вставить после (Ctrl+V)", "en": "Paste After (Ctrl+V)"},
    "mw.ctx.dup_branch": {
        "ru": "Дублировать блок диалога (до label/return/конца)",
        "en": "Duplicate Dialogue Block (to label/return/end)",
    },
    "mw.ctx.present_from_here": {"ru": "▶ Запустить прогон отсюда", "en": "▶ Play Through From Here"},
    "mw.ctx.group_selected": {"ru": "Сгруппировать выбранные ноды ({count})", "en": "Group Selected Nodes ({count})"},
    "mw.group_title_dialog": {"ru": "Название группы", "en": "Group Name"},
    "mw.cannot_group_title": {"ru": "Нельзя сгруппировать", "en": "Cannot Group"},
    "mw.cannot_group_text": {
        "ru": "Можно сгруппировать только идущие подряд ноды.",
        "en": "Only consecutive nodes can be grouped.",
    },
    "mw.new_group_title": {"ru": "Новая группа", "en": "New Group"},
    "mw.new_group_name_label": {"ru": "Название группы (акт/глава):", "en": "Group name (act/chapter):"},
    "mw.new_group_default": {"ru": "Акт", "en": "Act"},

                                                 
    "mw.preview_title": {"ru": "Предпросмотр сцены", "en": "Scene Preview"},
    "mw.zoom_label": {"ru": "Масштаб:", "en": "Zoom:"},
    "mw.sprite_drag_hint": {
        "ru": "Спрайт можно тащить мышью, чтобы сдвинуть, или кликнуть по нему "
              "(без перетаскивания), чтобы убрать со сцены.",
        "en": "You can drag a sprite with the mouse to move it, or click it "
              "(without dragging) to remove it from the scene.",
    },
    "mw.no_step_selected": {"ru": "Нет выбранного шага сцены.", "en": "No scene step selected."},
    "mw.step_of": {"ru": "Шаг {n} из {total}: {preview}", "en": "Step {n} of {total}: {preview}"},

                                                                     
    "mw.hotkey.dialogue_added": {"ru": "Добавлена реплика", "en": "Added a line"},
    "mw.hotkey.narration_added": {"ru": "Добавлено повествование", "en": "Added narration"},
    "mw.hotkey.show_sprite_added": {"ru": "Добавлен показ спрайта", "en": "Added show sprite"},
    "mw.hotkey.hide_sprite_added": {"ru": "Добавлено скрытие спрайта", "en": "Added hide sprite"},
    "mw.hotkey.show_bg_added": {"ru": "Добавлен показ фона", "en": "Added show background"},
    "mw.hotkey.pause_added": {"ru": "Добавлена пауза", "en": "Added pause"},
    "mw.hotkey.menu_added": {"ru": "Добавлено меню", "en": "Added menu"},
    "mw.crash_recovery_title": {"ru": "Восстановление после сбоя", "en": "Crash Recovery"},
    "mw.crash_recovery_text": {
        "ru": "Обнаружены несохранённые изменения из прошлой сессии "
              "(«{title}»), похоже, редактор закрылся аварийно.\n\n"
              "Восстановить их?",
        "en": "Unsaved changes from a previous session were found "
              "(\"{title}\"), it looks like the editor closed unexpectedly.\n\n"
              "Restore them?",
    },
    "mw.restored_from_autosave": {
        "ru": "Восстановлено из автосохранения - не забудьте сохранить (Ctrl+S)",
        "en": "Restored from autosave - don't forget to save (Ctrl+S)",
    },
    "mw.restore_error_title": {"ru": "Ошибка восстановления", "en": "Restore Error"},
    "mw.undo_count": {"ru": "Отменено действий: {depth}", "en": "Actions undone: {depth}"},

                                                             
    "mw.status_ready": {"ru": "Готов", "en": "Ready"},
    "mw.status_resources": {
        "ru": "  BG:{bg}  CG:{cg}  Спрайты:{sprites}  Музыка:{music}  Звуки:{sounds}  ",
        "en": "  BG:{bg}  CG:{cg}  Sprites:{sprites}  Music:{music}  Sounds:{sounds}  ",
    },
    "mw.default_scene_name": {"ru": "Сцена 1", "en": "Scene 1"},
    "mw.default_project_title": {"ru": "Проект", "en": "Project"},
    "mw.project_label": {"ru": "Проект: {title}{marker}", "en": "Project: {title}{marker}"},
    "mw.undo.change_default": {"ru": "Изменение", "en": "Change"},
    "mw.undo.field_edit_default": {"ru": "Правка поля", "en": "Field edit"},
    "mw.undone_label": {"ru": "Отменено: {label}", "en": "Undone: {label}"},
    "mw.redone_label": {"ru": "Повторено: {label}", "en": "Redone: {label}"},
    "mw.new_project_title": {"ru": "Новый проект", "en": "New Project"},
    "mw.new_project_confirm": {
        "ru": "Создать новый проект? Несохранённые данные будут потеряны.",
        "en": "Create a new project? Unsaved data will be lost.",
    },
    "mw.project_name_label": {"ru": "Название проекта:", "en": "Project name:"},
    "mw.default_project_name": {"ru": "Мой проект", "en": "My Project"},
    "mw.new_project_created": {"ru": "Новый проект создан", "en": "New project created"},
    "mw.open_project_title": {"ru": "Открыть проект", "en": "Open Project"},
    "mw.all_files": {"ru": "Все файлы", "en": "All Files"},
    "mw.loaded_label": {"ru": "Загружен: {path}", "en": "Loaded: {path}"},
    "mw.error_title": {"ru": "Ошибка", "en": "Error"},
    "mw.load_failed": {"ru": "Не удалось загрузить проект", "en": "Failed to load the project"},
    "mw.saved_label": {"ru": "Сохранено: {path}", "en": "Saved: {path}"},
    "mw.save_failed": {"ru": "Не удалось сохранить проект", "en": "Failed to save the project"},
    "mw.save_project_title": {"ru": "Сохранить проект", "en": "Save Project"},
    "mw.rename_project_title": {"ru": "Переименовать проект", "en": "Rename Project"},
    "mw.undo.project_renamed": {"ru": "Переименован проект", "en": "Renamed project"},
    "mw.main_label_title": {"ru": "Главная метка", "en": "Main Label"},
    "mw.main_label_field": {"ru": "Имя label для входа:", "en": "Entry label name:"},
    "mw.characters_count": {"ru": "Персонажей: {count}", "en": "Characters: {count}"},
    "mw.spellcheck_progress_text": {"ru": "Проверка реплик...", "en": "Checking lines..."},
    "mw.cancel": {"ru": "Отмена", "en": "Cancel"},
    "mw.spellcheck_progress_detail": {
        "ru": "Проверка реплик... {done}/{total}",
        "en": "Checking lines... {done}/{total}",
    },

                                                                                 
    "mw.save_project_first_title": {"ru": "Сначала сохраните проект", "en": "Save the Project First"},
    "mw.save_project_first_text": {
        "ru": "Версионирование работает с папкой, где лежит файл проекта. "
              "Сначала сохраните проект (Ctrl+S), затем откройте версионирование снова.",
        "en": "Versioning works with the folder where the project file is "
              "located. Save the project first (Ctrl+S), then open versioning again.",
    },
    "mw.undo.screenplay_import": {"ru": "Импорт правок из текста для вычитки", "en": "Import edits from proofreading text"},
    "mw.undo.find_replace": {"ru": "Найти и заменить", "en": "Find and Replace"},
    "mw.mass_replace_applied": {"ru": "Массовая замена текста применена.", "en": "Mass text replacement applied."},
    "mw.reimport_collision_text": {
        "ru": "{count} импортируемых сцен уже есть в проекте по имени метки "
              "({names}{more}).\n\nЧто сделать с совпадающими?",
        "en": "{count} imported scenes already exist in the project by label "
              "name ({names}{more}).\n\nWhat to do with the matching ones?",
    },
    "mw.reimport_more_suffix": {"ru": " и ещё {count}", "en": " and {count} more"},
    "mw.reimport_replace": {"ru": "🔄 Заменить содержимое", "en": "🔄 Replace Content"},
    "mw.reimport_skip": {"ru": "⏭ Пропустить совпадающие", "en": "⏭ Skip Matching"},
    "mw.reimport_dupe": {"ru": "➕ Всё равно добавить как дубликаты", "en": "➕ Add as Duplicates Anyway"},
    "mw.reimport_cancel": {"ru": "Отмена", "en": "Cancel"},
    "mw.import_added": {"ru": "добавлено сцен: {count}", "en": "scenes added: {count}"},
    "mw.import_replaced": {"ru": "заменено: {count}", "en": "replaced: {count}"},
    "mw.import_skipped": {"ru": "пропущено (уже есть): {count}", "en": "skipped (already exist): {count}"},
    "mw.import_prefix": {"ru": "Импорт - {parts}", "en": "Import - {parts}"},
    "mw.chars_import_added": {"ru": "добавлено новых: {count}", "en": "new added: {count}"},
    "mw.chars_import_matched_by_name": {
        "ru": "совпало по имени (дубликаты не созданы): {count}",
        "en": "matched by name (no duplicates created): {count}",
    },
    "mw.chars_import_already_existed": {
        "ru": "уже было (та же переменная): {count}",
        "en": "already existed (same variable): {count}",
    },
    "mw.chars_import_prefix": {"ru": "Импорт персонажей - {parts}", "en": "Character import - {parts}"},
    "mw.updates_title": {"ru": "Обновления", "en": "Updates"},
    "mw.update_check_in_progress": {"ru": "Проверка уже выполняется, подождите.", "en": "A check is already in progress, please wait."},
    "mw.latest_version_installed": {
        "ru": "У вас установлена последняя версия (текущая: {version}).",
        "en": "You have the latest version installed (current: {version}).",
    },

                                             
    "node_hint.dialogue": {
        "ru": "💬 Реплика персонажа - станет строкой вида: имя_переменной \"текст\"",
        "en": "💬 Character line - becomes a line like: variable_name \"text\"",
    },
    "node_hint.narration": {
        "ru": "📖 Повествование от автора - строка текста без указания персонажа",
        "en": "📖 Narration - a line of text without a character",
    },
    "node_hint.show_bg": {
        "ru": "🖼 Показывает фон (show bg с опциональным переходом)",
        "en": "🖼 Shows a background (show bg with an optional transition)",
    },
    "node_hint.scene": {
        "ru": "🎬 Полная смена сцены (scene - сбрасывает все показанные спрайты)",
        "en": "🎬 Full scene change (scene - resets all shown sprites)",
    },
    "node_hint.show_sprite": {
        "ru": "🧍 Показывает спрайт персонажа в заданной позиции",
        "en": "🧍 Shows a character sprite at a given position",
    },
    "node_hint.hide_sprite": {
        "ru": "🚫 Скрывает ранее показанный спрайт",
        "en": "🚫 Hides a previously shown sprite",
    },
    "node_hint.show_cg": {"ru": "🖼 Показывает CG-иллюстрацию", "en": "🖼 Shows a CG illustration"},
    "node_hint.hide_cg": {"ru": "🗑 Скрывает CG-иллюстрацию", "en": "🗑 Hides a CG illustration"},
    "node_hint.play_music": {"ru": "🎵 Запускает фоновую музыку (play music)", "en": "🎵 Starts background music (play music)"},
    "node_hint.stop_music": {"ru": "🔇 Останавливает музыку", "en": "🔇 Stops music"},
    "node_hint.play_sound": {"ru": "🔊 Проигрывает звуковой эффект один раз", "en": "🔊 Plays a sound effect once"},
    "node_hint.play_ambience": {"ru": "🌬 Запускает фоновый эмбиенс-звук", "en": "🌬 Starts a background ambience sound"},
    "node_hint.stop_ambience": {"ru": "🔇 Останавливает эмбиенс", "en": "🔇 Stops ambience"},
    "node_hint.label": {
        "ru": "🏷 Метка - точка, на которую можно перейти через jump",
        "en": "🏷 Label - a point that can be jumped to via jump",
    },
    "node_hint.jump": {"ru": "➡ Безусловный переход на другую метку", "en": "➡ Unconditional jump to another label"},
    "node_hint.menu": {"ru": "📋 Меню выбора для игрока", "en": "📋 Choice menu for the player"},
    "node_hint.python": {"ru": "🐍 Произвольный Python-код ($ или python:)", "en": "🐍 Arbitrary Python code ($ or python:)"},
    "node_hint.pause": {"ru": "⏸ Пауза (по времени или до клика игрока)", "en": "⏸ Pause (timed or until player click)"},
    "node_hint.return": {"ru": "⏹ Возврат из label (return)", "en": "⏹ Return from label (return)"},
    "node_hint.comment": {
        "ru": "# Комментарий - не попадает в игру, только для заметок в редакторе",
        "en": "# Comment - doesn't appear in the game, only for notes in the editor",
    },
    "node_hint.window": {
        "ru": "🪟 Управление текстовым окном (window show/hide/auto)",
        "en": "🪟 Text window control (window show/hide/auto)",
    },
    "node_hint.with_transition": {
        "ru": "🎞 Отдельная команда перехода (with transition)",
        "en": "🎞 Standalone transition command (with transition)",
    },
    "node_hint.raw": {
        "ru": "🧩 Нераспознанный при импорте код - сохранён как есть",
        "en": "🧩 Code not recognized during import - kept as is",
    },
    "node_hint.custom": {
        "ru": "🧬 Пользовательская нода по вашему шаблону (Проект → Шаблоны пользовательских нод)",
        "en": "🧬 Custom node from your template (Project \u2192 Custom Node Templates)",
    },
    "mw.group_collapsed_suffix": {"ru": "   (свёрнуто)", "en": "   (collapsed)"},
    "mw.group_header": {"ru": "{title}   \u00b7   {count} {word}{suffix}", "en": "{title}   \u00b7   {count} {word}{suffix}"},

                                                                                   
    "mw.resources_rescanned": {
        "ru": "Ресурсы переиндексированы: {count} файлов",
        "en": "Resources re-scanned: {count} files",
    },
    "mw.menu_branch_no_text": {"ru": "(без текста)", "en": "(no text)"},
    "mw.menu_branch_scene_name": {"ru": "Ветка меню: {text}", "en": "Menu Branch: {text}"},
    "mw.menu_branch_label": {"ru": "✏️ Ветка меню: «{text}»", "en": "✏️ Menu Branch: \"{text}\""},
    "mw.not_found_title": {"ru": "Не найдено", "en": "Not Found"},
    "mw.usage_scene_gone": {
        "ru": "Сцена с этим использованием больше не существует.",
        "en": "The scene with this usage no longer exists.",
    },
    "mw.usage_branch_gone": {
        "ru": "Ветка меню, ведущая к использованию, больше не найдена.",
        "en": "The menu branch leading to this usage was not found.",
    },
    "mw.usage_node_gone": {
        "ru": "Нода с этим использованием больше не найдена.",
        "en": "The node with this usage was not found.",
    },
    "mw.undo.node_edit": {"ru": "Правка ноды: {hint}", "en": "Node edit: {hint}"},
    "mw.undo.sprite_move": {"ru": "Перемещение спрайта: {hint}", "en": "Sprite move: {hint}"},

                                         
    "mw.export_title": {"ru": "Экспорт", "en": "Export"},
    "mw.no_scenes_to_export": {"ru": "В проекте нет ни одной сцены.", "en": "The project has no scenes."},
    "mw.export_script_title": {"ru": "Экспорт сценария", "en": "Export Script"},

    "export_project.title": {"ru": "Экспорт проекта", "en": "Export Project"},    "export_project.dir_not_selected": {"ru": "Папка не выбрана", "en": "No folder selected"},
    "export_project.pick_dir": {"ru": "Выбрать папку...", "en": "Choose Folder..."},
    "export_project.pick_dir_title": {"ru": "Папка для экспорта проекта", "en": "Folder for Project Export"},
    "export_project.split_box": {"ru": "Сценарий", "en": "Script"},
    "export_project.rb_single": {"ru": "Один файл (script.rpy)", "en": "Single file (script.rpy)"},
    "export_project.defines_box": {"ru": "Что включить в defines.rpy", "en": "What to include in defines.rpy"},
    "export_project.cb_characters": {"ru": "Персонажи", "en": "Characters"},
    "export_project.cb_transitions": {"ru": "Кастомные переходы", "en": "Custom transitions"},
    "export_project.cb_resources": {
        "ru": "Определения ресурсов (image/define для bg/cg/спрайтов/звуков)",
        "en": "Resource defines (image/define for bg/cg/sprites/sounds)",
    },
    "export_project.summary_label": {"ru": "Что будет экспортировано:", "en": "What will be exported:"},
    "export_project.summary_single_script": {"ru": "Сценарий: 1 файл (script.rpy)", "en": "Script: 1 file (script.rpy)"},
    "export_project.summary_split_scripts": {
        "ru": "Сценарий: {count} файл(ов)", "en": "Script: {count} file(s)",
    },
    "export_project.summary_defines": {"ru": "Определения: defines.rpy", "en": "Definitions: defines.rpy"},
    "export_project.summary_assets": {
        "ru": "Ресурсы для копирования (только используемые): {count}",
        "en": "Resources to copy (used only): {count}",
    },
    "export_project.summary_missing": {
        "ru": "Не найдены на диске ({count}) - НЕ будут скопированы:",
        "en": "Not found on disk ({count}) - will NOT be copied:",
    },
    "export_project.summary_unresolved": {
        "ru": "Использованы, но не найдены как ресурс ({count}):",
        "en": "Used but not found as a resource ({count}):",
    },
    "export_project.note": {
        "ru": "Файлы ресурсов копируются ровно по тем путям, что указаны в сгенерированном коде "
              "(bg/..., cg/..., transitions/... и т.д.) - результат можно класть прямо в game/ Ren'Py проекта.",
        "en": "Resource files are copied exactly to the paths referenced in the generated code "
              "(bg/..., cg/..., transitions/... etc.) - the result can be dropped straight into a Ren'Py project's game/.",
    },
    "export_project.error_title": {"ru": "Ошибка экспорта", "en": "Export Error"},
    "export_project.done_summary": {
        "ru": "Экспортировано в:\n{path}\n\nФайлов сценария: {scripts}\nСкопировано ресурсов: {assets}",
        "en": "Exported to:\n{path}\n\nScript files: {scripts}\nResources copied: {assets}",
    },
    "export_project.done_warning": {
        "ru": "Не скопировано (нет файла на диске): {missing}\nНе найдено как ресурс: {unresolved}",
        "en": "Not copied (missing on disk): {missing}\nNot found as a resource: {unresolved}",
    },

    "export_defines.title": {"ru": "Экспорт defines", "en": "Export Defines"},
    "export_defines.what_box": {"ru": "Что включить", "en": "What to include"},
    "export_defines.cb_used_only": {
        "ru": "Только используемые в сценарии (иначе - все ресурсы проекта)",
        "en": "Used in the script only (otherwise - all project resources)",
    },
    "export_defines.preview_label": {"ru": "Предпросмотр:", "en": "Preview:"},
    "export_defines.save_as": {"ru": "Сохранить как...", "en": "Save As..."},
    "export_defines.save_title": {"ru": "Сохранить defines.rpy", "en": "Save defines.rpy"},
    "mw.all_files2": {"ru": "Все файлы", "en": "All Files"},
    "mw.export_cancelled": {"ru": "Экспорт отменён", "en": "Export cancelled"},
    "mw.exported_label": {"ru": "Экспортировано: {path}", "en": "Exported: {path}"},
    "mw.done_title": {"ru": "Готово", "en": "Done"},
    "mw.script_saved_text": {"ru": "Сценарий сохранён:\n{path}", "en": "Script saved:\n{path}"},
    "mw.export_defines_title": {"ru": "Экспорт defines", "en": "Export Defines"},
    "mw.defines_exported": {"ru": "Defines экспортированы: {path}", "en": "Defines exported: {path}"},
    "mw.export_resource_defines_title": {"ru": "Экспорт defines ресурсов", "en": "Export Resource Defines"},
    "mw.resource_defines_saved": {"ru": "Defines ресурсов сохранены: {path}", "en": "Resource defines saved: {path}"},
    "mw.exit_title": {"ru": "Выход", "en": "Exit"},
    "mw.save_before_exit": {"ru": "Сохранить проект перед выходом?", "en": "Save the project before exiting?"},

                                
    "waveform.select_file_hint": {"ru": "Выберите файл, чтобы увидеть волну", "en": "Select a file to see the waveform"},
    "waveform.no_ffmpeg_hint": {
        "ru": "Волна недоступна для этого формата - перемотка и fade всё равно работают "
              "(для mp3/ogg/flac установите: pip install miniaudio soundfile)",
        "en": "Waveform unavailable for this format - seeking and fade still work "
              "(for mp3/ogg/flac install: pip install miniaudio soundfile)",
    },
    "node_graph.border_color_menu": {"ru": "Цвет рамки", "en": "Border Color"},
    "node_graph.align_nodes": {"ru": "Выровнять ноды", "en": "Align nodes"},
    "node_graph.align_nodes_tooltip": {"ru": "Автоматически расставить все ноды деревом по label/jump/menu-связям",
                                        "en": "Automatically arrange all nodes as a tree by label/jump/menu links"},
    "node_graph.mode_toggle_tooltip": {"ru": "Переключить между списком и графовым режимом редактора",
                                        "en": "Switch between list and graph editor mode"},
    "node_graph.list_mode": {"ru": "Список", "en": "List"},
    "node_graph.graph_mode": {"ru": "Граф", "en": "Graph"},
    "node_graph.add_node": {"ru": "Нода", "en": "Node"},
    "node_graph.add_node_tooltip": {"ru": "Добавить новую ноду после выбранной",
                                     "en": "Add a new node after the selected one"},
    "node_graph.edit_node": {"ru": "Нода", "en": "Node"},
    "node_graph.double_click_hint": {"ru": "  ·  двойной клик по ноде - редактировать в главном окне",
                                      "en": "  ·  double-click a node to edit it in the main window"},
    "node_edit.character": {"ru": "Персонаж", "en": "Character"},
    "node_edit.text": {"ru": "Текст", "en": "Text"},
    "node_edit.label_name": {"ru": "Имя label", "en": "Label name"},
    "node_edit.jump_target": {"ru": "Цель (label)", "en": "Jump target"},
    "node_edit.bg_var": {"ru": "Фон (var)", "en": "Background (var)"},
    "node_edit.transition": {"ru": "Переход", "en": "Transition"},
    "node_edit.sprite_var": {"ru": "Спрайт (var)", "en": "Sprite (var)"},
    "node_edit.sprite_expression": {"ru": "Выражение", "en": "Expression"},
    "node_edit.sprite_tag": {"ru": "Tag", "en": "Tag"},
    "node_edit.hide_group": {"ru": "Группа", "en": "Group"},
    "node_edit.cg_var": {"ru": "CG (var)", "en": "CG (var)"},
    "node_edit.music_var": {"ru": "Музыка (var)", "en": "Music (var)"},
    "node_edit.fadein": {"ru": "Fade in (мс)", "en": "Fade in (ms)"},
    "node_edit.fadeout": {"ru": "Fade out (мс)", "en": "Fade out (ms)"},
    "node_edit.sound_var": {"ru": "Звук (var)", "en": "Sound (var)"},
    "node_edit.ambience_var": {"ru": "Амбиент (var)", "en": "Ambience (var)"},
    "node_edit.python_code": {"ru": "Python код", "en": "Python code"},
    "node_edit.raw_code": {"ru": "Сырой код", "en": "Raw code"},
    "node_edit.pause_duration": {"ru": "Длительность (сек)", "en": "Duration (sec)"},
    "node_edit.comment_text": {"ru": "Комментарий", "en": "Comment"},
    "node_edit.window_action": {"ru": "Действие окна", "en": "Window action"},
    "node_edit.menu_prompt": {"ru": "Вопрос меню", "en": "Menu prompt"},
    "node_edit.choice_text": {"ru": "текст варианта", "en": "choice text"},
    "node_edit.choice_jump": {"ru": "цель (label)", "en": "jump target"},
    "node_edit.choice_add": {"ru": "Добавить вариант", "en": "Add choice"},
    "node_edit.narrator_option": {"ru": "- Рассказчик -", "en": "- Narrator -"},
    "node_edit.hide_var": {"ru": "Конкретный спрайт", "en": "Specific sprite"},
    "node_edit.loop": {"ru": "Зациклить", "en": "Loop"},
    "node_edit.play_tooltip": {"ru": "Прослушать", "en": "Play"},
    "node_edit.stop_tooltip": {"ru": "Остановить", "en": "Stop"},
    "node_edit.length_ok": {"ru": "Длина текста: {count} - норм", "en": "Text length: {count} - fine"},
    "node_edit.length_ugly": {"ru": "Длина текста: {count} - многовато",
                               "en": "Text length: {count} - getting long"},
    "node_edit.length_overflow": {"ru": "Длина текста: {count} - не влезет на экран",
                                   "en": "Text length: {count} - won't fit on screen"},

                                    
    "present.hint_continue": {"ru": "клик / пробел ▶", "en": "click / space ▶"},
    "present.hint_reveal": {"ru": "клик - показать целиком", "en": "click - reveal all"},
    "present.backlog_title": {"ru": "История реплик (Tab - закрыть)", "en": "Line History (Tab to close)"},
    "present.window_title": {"ru": "Презентация - {title}", "en": "Presentation - {title}"},
    "present.speed_tooltip": {
        "ru": "Скорость печати текста ([ медленнее / ] быстрее)",
        "en": "Text typing speed ([ slower / ] faster)",
    },
    "present.autoplay_off": {"ru": "▶ Автопрогон: выкл", "en": "▶ Autoplay: off"},
    "present.autoplay_state": {"ru": "▶ Автопрогон: {state}", "en": "▶ Autoplay: {state}"},
    "present.autoplay_on_word": {"ru": "вкл", "en": "on"},
    "present.autoplay_off_word": {"ru": "выкл", "en": "off"},
    "present.prev_line_button": {"ru": "⏮ Пред. реплика (←)", "en": "⏮ Prev Line (←)"},
    "present.backlog_button": {"ru": "📜 История (Tab)", "en": "📜 History (Tab)"},
    "present.skip_step_button": {"ru": "⏭ Пропустить шаг", "en": "⏭ Skip Step"},
    "present.exit_button": {"ru": "✕ Выход (Esc)", "en": "✕ Exit (Esc)"},
    "present.no_scenes": {
        "ru": "В проекте нет ни одной сцены с нодами.",
        "en": "The project has no scenes with nodes.",
    },
    "present.speed_instant": {"ru": "мгновенно", "en": "instant"},
    "present.speed_button": {"ru": "⚡ Скорость текста: {label}", "en": "⚡ Text Speed: {label}"},

                                  
    "carousel.remove_favorite": {"ru": "Убрать из избранного", "en": "Remove from Favorites"},
    "carousel.clear_selection": {"ru": "✕ Убрать выбор", "en": "✕ Clear selection"},
    "carousel.add_favorite": {"ru": "Добавить в избранное", "en": "Add to Favorites"},
    "carousel.import_failed_title": {"ru": "Не удалось импортировать", "en": "Import Failed"},
    "carousel.import_failed_text": {
        "ru": "Эти файлы пропущены (неподходящее расширение для этой категории):\n{files}",
        "en": "These files were skipped (unsuitable extension for this category):\n{files}",
    },
    "carousel.group_label": {"ru": "Группировать:", "en": "Group by:"},
    "carousel.no_grouping": {"ru": "Без группировки", "en": "No Grouping"},
    "carousel.nothing_found": {"ru": "Ничего не найдено", "en": "Nothing found"},
    "carousel.pos_far": {"ru": "Дальний план (far)", "en": "Far (far)"},
    "carousel.pos_close": {"ru": "Крупный план (close)", "en": "Close (close)"},
    "carousel.pos_normal": {"ru": "Средний план (normal)", "en": "Normal (normal)"},

                                             
    "ne.call_vs_jump_tooltip": {
        "ru": "По умолчанию переход на метку делается через jump.\n\n"
              "Разница между jump и call важна, если внутри метки что-то присваивается "
              "и затем стоит return:\n"
              "• jump - просто переходит на метку и забывает, откуда пришёл. Если в той "
              "метке встретится return, Ren'Py решит, что сценарий закончился, и игра "
              "выйдет в главное меню.\n"
              "• call - переходит на метку, но запоминает место вызова. После return "
              "игра вернётся обратно, на следующую строку после этого варианта меню.\n\n"
              "Включите галочку «call», если метка должна вернуть игрока сюда же после "
              "return, а не выкинуть в главное меню.",
        "en": "By default, jumping to a label is done via jump.\n\n"
              "The difference between jump and call matters if something is "
              "assigned inside the label and then there's a return:\n"
              "\u2022 jump - simply jumps to the label and forgets where it came "
              "from. If a return is encountered in that label, Ren'Py will "
              "decide the script has ended, and the game will exit to the main menu.\n"
              "\u2022 call - jumps to the label but remembers the call site. "
              "After return, the game will go back to the line right after this menu option.\n\n"
              "Check the \"call\" box if the label should return the player "
              "here after return, instead of kicking them out to the main menu.",
    },
    "ne.choice_text_placeholder": {"ru": "Текст варианта", "en": "Choice text"},
    "ne.choice_label_placeholder": {"ru": "метка (если jump/call)", "en": "label (if jump/call)"},
    "ne.call_checkbox": {
        "ru": "call (вернуться сюда после return, а не в jump)",
        "en": "call (return here after return, instead of jump)",
    },
    "ne.branch_button_tooltip": {
        "ru": "Открывает эту ветку как полноценный список нод (диалоги, показ спрайтов, "
              "музыка, вложенное меню и т.д.) - так же, как редактируется обычная сцена. "
              "Если ветка не пустая, она выполняется вместо jump/call и «Тела варианта».",
        "en": "Opens this branch as a full-fledged node list (dialogue, sprite "
              "shows, music, nested menu, etc.) - the same way a regular scene "
              "is edited. If the branch is not empty, it runs instead of "
              "jump/call and the \"Choice Body\".",
    },
    "ne.body_placeholder": {
        "ru": "Код варианта - будет вставлен как есть (scene, show, диалог, jump, ...)",
        "en": "Choice code - will be inserted as-is (scene, show, dialogue, jump, ...)",
    },
    "ne.body_toggle_expanded": {"ru": "▼ Тело варианта (inline-сценарий)", "en": "▼ Choice Body (inline script)"},
    "ne.body_toggle_collapsed": {"ru": "▶ Тело варианта (inline-сценарий)", "en": "▶ Choice Body (inline script)"},
    "ne.branch_button_text": {"ru": "🧩 Ветка: {count} {word} - открыть в редакторе ▸", "en": "🧩 Branch: {count} {word} - open in editor ▸"},
    "ne.branch_button_empty": {"ru": "🧩 Вписать сценарий (ноды) в эту ветку ▸", "en": "🧩 Write script (nodes) into this branch ▸"},

                                                                      
    "ne.panel_title": {"ru": "Панель параметров", "en": "Parameters Panel"},
    "ne.node_type_label": {"ru": "Тип ноды:", "en": "Node type:"},
    "ne.node_type_tooltip": {
        "ru": "Тип ноды определяет, какая команда Ren'Py будет сгенерирована "
              "(реплика, показ фона, переход, пауза и т.д.)",
        "en": "The node type determines which Ren'Py command will be "
              "generated (line, show background, transition, pause, etc.)",
    },
    "ne.apply_button": {"ru": "✔ Применить изменения", "en": "✔ Apply Changes"},
    "ne.character_group": {"ru": "Персонаж", "en": "Character"},
    "ne.narrator_option": {"ru": "- нарратор -", "en": "- narrator -"},
    "ne.character_combo_tooltip": {
        "ru": "Кто говорит эту реплику. «- нарратор -» - реплика без персонажа "
              "(показывается без имени, обычно курсивом/по-другому в теме игры)",
        "en": "Who says this line. \"- narrator -\" - a line without a "
              "character (shown without a name, usually in italics/differently in the game theme)",
    },
    "ne.dialogue_text_group": {"ru": "Текст реплики", "en": "Line Text"},
    "ne.tag_italic_tooltip": {"ru": "Курсив {i}...{/i}", "en": "Italic {i}...{/i}"},
    "ne.tag_bold_tooltip": {"ru": "Жирный {b}...{/b}", "en": "Bold {b}...{/b}"},
    "ne.tag_underline_tooltip": {"ru": "Подчёркнутый {u}...{/u}", "en": "Underline {u}...{/u}"},
    "ne.tag_whisper_tooltip": {
        "ru": "Шёпот (уменьшенный, приглушённый курсив)",
        "en": "Whisper (reduced, muted italic)",
    },
    "ne.tag_size_tooltip": {"ru": "Размер шрифта {size=+10}...{/size}", "en": "Font size {size=+10}...{/size}"},
    "ne.tag_color_tooltip": {"ru": "Цвет текста {color=#ffcf40}...{/color}", "en": "Text color {color=#ffcf40}...{/color}"},
    "ne.tag_wait_tooltip": {"ru": "Пауза с ожиданием клика {w}", "en": "Pause waiting for click {w}"},
    "ne.tag_nowait_tooltip": {"ru": "Продолжить без ожидания {nw}", "en": "Continue without waiting {nw}"},
    "ne.dialogue_text_tooltip": {
        "ru": "Текст реплики/повествования. Можно использовать теги Ren'Py "
              "({i}, {b}, {color=...} и т.п.) - см. панель тегов выше.",
        "en": "The line/narration text. You can use Ren'Py tags "
              "({i}, {b}, {color=...}, etc.) - see the tag panel above.",
    },
    "ne.dialogue_text_placeholder": {"ru": "Введите текст реплики...", "en": "Enter line text..."},

                                                                       
    "ne.tag_symbols_note": {
        "ru": " (+{count} симв. тегов формата, не считаются)",
        "en": " (+{count} formatting tag chars, not counted)",
    },
    "ne.length_ok": {"ru": "✓ {count} симв.{note} - уместится в диалоговое окно нормально.", "en": "✓ {count} chars{note} - will fit the dialogue window fine."},
    "ne.length_ugly": {
        "ru": "⚠ {count} симв.{note} - влезет, но может выглядеть некрасиво (мелкий текст/много строк). Стоит сократить.",
        "en": "⚠ {count} chars{note} - will fit, but may look ugly (small text/many lines). Consider shortening.",
    },
    "ne.length_overflow": {
        "ru": "✕ {count} симв.{note} - скорее всего НЕ влезет в стандартное диалоговое окно. Разбейте реплику на несколько.",
        "en": "✕ {count} chars{note} - most likely will NOT fit the standard dialogue window. Split the line into several.",
    },
    "ne.select_cg": {"ru": "Выберите CG", "en": "Select CG"},
    "ne.select_bg": {"ru": "Выберите фон", "en": "Select Background"},
    "ne.no_files_in_resources": {
        "ru": "Нет файлов в resources/{cat}/. Добавьте изображения и нажмите F5.",
        "en": "No files in resources/{cat}/. Add images and press F5.",
    },
    "ne.transition_label": {"ru": "Переход:", "en": "Transition:"},
    "ne.transition_tooltip": {
        "ru": "Анимация перехода Ren'Py (with dissolve и т.п.). Пусто - мгновенная смена без анимации.",
        "en": "Ren'Py transition animation (with dissolve, etc.). Empty - instant change without animation.",
    },
    "ne.sprite_group": {"ru": "Спрайт", "en": "Sprite"},
    "ne.composite_sprites_label": {"ru": "Составные спрайты (sprites.rpy):", "en": "Composite Sprites (sprites.rpy):"},
    "carousel.position_zoom_label": {"ru": "Позиция (масштаб)", "en": "Position (zoom)"},
    "carousel.attributes_label": {"ru": "Атрибуты", "en": "Attributes"},
    "carousel.attribute_n_label": {"ru": "Атрибут {n}", "en": "Attribute {n}"},
    "carousel.attribute_n_optional_label": {"ru": "Атрибут {n} (необязательный)", "en": "Attribute {n} (optional)"},
    "carousel.no_matching_sprite": {"ru": "Нет спрайта с таким набором атрибутов", "en": "No sprite matches this attribute set"},
    "ne.plain_sprites_label": {"ru": "Обычные спрайты (отдельные файлы):", "en": "Plain Sprites (individual files):"},
    "ne.no_sprite_files": {
        "ru": "Нет файлов в resources/sprites/. Разложите спрайты по папкам персонажей "
              "(например resources/sprites/us/normal/), либо добавьте sprites.rpy "
              "с составными спрайтами, и нажмите F5.",
        "en": "No files in resources/sprites/. Organize sprites into character "
              "folders (e.g. resources/sprites/us/normal/), or add sprites.rpy "
              "with composite sprites, and press F5.",
    },
    "ne.sprite_anchor_label": {"ru": "Позиция на сцене (якорь):", "en": "Position on Scene (anchor):"},
    "ne.sprite_group_hint": {
        "ru": "Если несколько спрайтов показываются друг за другом с одним и тем же "
              "переходом, при экспорте они объединяются в один блок \"show ... \\n show ... \\n with ...\".",
        "en": "If several sprites are shown one after another with the same "
              "transition, on export they get merged into one block \"show ... \\n show ... \\n with ...\".",
    },
    "ne.hide_sprite_group": {"ru": "Скрыть спрайт", "en": "Hide Sprite"},
    "ne.hide_whole_char": {
        "ru": "Скрыть персонажа целиком (клик на папку - без захода внутрь):",
        "en": "Hide the whole character (click the folder - without entering it):",
    },
    "ne.or_pick_specific_sprite": {"ru": "- или выбрать конкретный спрайт -", "en": "- or pick a specific sprite -"},

                                                                    
    "ne.textbox_group": {"ru": "Текстовое окно", "en": "Text Window"},
    "ne.action_label": {"ru": "Действие:", "en": "Action:"},
    "ne.transition_optional_label": {"ru": "Переход (необязательно):", "en": "Transition (optional):"},
    "ne.with_effect_group": {"ru": "Эффект (with)", "en": "Effect (with)"},
    "ne.with_effect_hint": {
        "ru": "Самостоятельная инструкция \"with переход\" - применяет эффект ко "
              "всему экрану, не привязываясь к конкретному show/scene/hide "
              "(например, эффект тряски vpunch после реплики).",
        "en": "A standalone \"with transition\" instruction - applies an "
              "effect to the whole screen, not tied to a specific "
              "show/scene/hide (e.g. a vpunch shake effect after a line).",
    },
    "ne.nvl_action_enter": {"ru": "enter - Войти в NVL-режим", "en": "enter - Enter NVL mode"},
    "ne.nvl_action_clear": {"ru": "clear - Очистить экран NVL (остаться в NVL)", "en": "clear - Clear NVL screen (stay in NVL)"},
    "ne.nvl_action_exit": {"ru": "exit - Вернуться в ADV", "en": "exit - Return to ADV"},
    "ne.nvl_mode_group": {"ru": "Режим NVL/ADV", "en": "NVL/ADV Mode"},
    "ne.nvl_mode_hint": {
        "ru": "Переключает стиль показа текста: ADV - обычное окно диалога внизу "
              "экрана (по умолчанию); NVL - во весь экран, реплики накапливаются "
              "друг под другом, как в визуальной новелле/книге. Действует на все "
              "реплики после этой ноды, пока не встретится нода \"Вернуться в ADV\".",
        "en": "Switches the text display style: ADV - regular dialogue "
              "window at the bottom of the screen (default); NVL - full "
              "screen, lines accumulate one below another, like in a visual "
              "novel/book. Applies to all lines after this node until a "
              "\"Return to ADV\" node is encountered.",
    },
    "ne.nvl_clear_hint": {
        "ru": "В код это превращается в `nvl clear` (для «войти»/«очистить») и "
              "переключение реплик на NVL-версию персонажа (define ..._nvl, "
              "генерируется автоматически) либо обратно на обычную.",
        "en": "In code this turns into `nvl clear` (for \"enter\"/\"clear\") "
              "and switches lines to the character's NVL version (define "
              "..._nvl, generated automatically) or back to the regular one.",
    },
    "ne.raw_code_group": {"ru": "Необработанный код (импортирован дословно)", "en": "Raw Code (imported verbatim)"},
    "ne.raw_code_hint": {
        "ru": "Этот блок не удалось распознать как одну из известных команд "
              "редактора при импорте .rpy - он сохранён дословно и будет "
              "воспроизведён в коде в точности как есть, без изменений.",
        "en": "This block could not be recognized as one of the editor's "
              "known commands during .rpy import - it is stored verbatim "
              "and will be reproduced in the code exactly as is, unchanged.",
    },
    "ne.custom_node_group": {"ru": "Пользовательская нода", "en": "Custom Node"},
    "ne.no_custom_templates": {
        "ru": "Пока нет ни одного шаблона пользовательской ноды. Создайте его в "
              "«Проект → Шаблоны пользовательских нод...», затем выберите здесь.",
        "en": "There are no custom node templates yet. Create one via "
              "\"Project \u2192 Custom Node Templates...\", then select it here.",
    },
    "ne.template_label": {"ru": "Шаблон:", "en": "Template:"},
    "ne.fadein_sec_label": {"ru": "Fade in (сек):", "en": "Fade in (sec):"},
    "ne.fadeout_sec_label": {"ru": "Fade out (сек):", "en": "Fade out (sec):"},
    "ne.listen_from_start": {"ru": " (с начала)", "en": " (from the start)"},
    "ne.listen_from_fifth": {"ru": " (с 1/5 от начала трека)", "en": " (from 1/5 into the track)"},

                                                     
    "mw.back_to_scene": {"ru": "← Назад к сцене", "en": "← Back to Scene"},

                                                        
    "node_type.dialogue": {"ru": "💬 Диалог", "en": "💬 Dialogue"},
    "node_type.narration": {"ru": "📖 Нарратор", "en": "📖 Narration"},
    "node_type.scene": {"ru": "🎬 Сцена (scene)", "en": "🎬 Scene (scene)"},
    "node_type.show_bg": {"ru": "🖼 Фон (show)", "en": "🖼 Background (show)"},
    "node_type.show_cg": {"ru": "🎨 CG (show)", "en": "🎨 CG (show)"},
    "node_type.show_sprite": {"ru": "👤 Показать спрайт", "en": "👤 Show Sprite"},
    "node_type.hide_sprite": {"ru": "❌ Скрыть спрайт", "en": "❌ Hide Sprite"},
    "node_type.window": {"ru": "🪟 Текстовое окно (show/hide)", "en": "🪟 Text Window (show/hide)"},
    "node_type.with_transition": {"ru": "✨ Эффект (with)", "en": "✨ Effect (with)"},
    "node_type.nvl_mode": {"ru": "📖 Режим NVL/ADV", "en": "📖 NVL/ADV Mode"},
    "node_type.play_music": {"ru": "🎵 Музыка", "en": "🎵 Music"},
    "node_type.stop_music": {"ru": "🔇 Стоп музыка", "en": "🔇 Stop Music"},
    "node_type.play_sound": {"ru": "🔊 Звук", "en": "🔊 Sound"},
    "node_type.play_ambience": {"ru": "🌬 Эмбиенс (play)", "en": "🌬 Ambience (play)"},
    "node_type.stop_ambience": {"ru": "🌬 Эмбиенс (stop)", "en": "🌬 Ambience (stop)"},
    "node_type.label": {"ru": "🏷 Метка (label)", "en": "🏷 Label (label)"},
    "node_type.jump": {"ru": "↪ Переход (jump)", "en": "↪ Jump (jump)"},
    "node_type.menu": {"ru": "📋 Меню выбора", "en": "📋 Choice Menu"},
    "node_type.pause": {"ru": "⏸ Пауза", "en": "⏸ Pause"},
    "node_type.return_": {"ru": "⏹ Return", "en": "⏹ Return"},
    "node_type.python": {"ru": "🐍 Python код", "en": "🐍 Python Code"},
    "node_type.raw": {"ru": "🧩 Необработанный код (импорт)", "en": "🧩 Raw Code (import)"},
    "node_type.custom": {"ru": "🧬 Пользовательская нода...", "en": "🧬 Custom Node..."},

                                                                         
    "preview.bg": {"ru": "🖼 Фон: {var}  [{trans}]", "en": "🖼 Background: {var}  [{trans}]"},
    "preview.scene": {"ru": "🎬 Сцена: {var}  [{trans}]", "en": "🎬 Scene: {var}  [{trans}]"},
    "preview.no_transition": {"ru": "без перехода", "en": "no transition"},
    "preview.sprite": {"ru": "👤 Спрайт: {var}{expr}{trans}", "en": "👤 Sprite: {var}{expr}{trans}"},
    "preview.hide_char": {"ru": "👻 Скрыть: персонаж «{name}» (все спрайты)", "en": "👻 Hide: character \"{name}\" (all sprites)"},
    "preview.hide_sprite": {"ru": "👻 Скрыть: {var}", "en": "👻 Hide: {var}"},
    "preview.music": {"ru": "🎵 Музыка: {var}", "en": "🎵 Music: {var}"},
    "preview.stop_music": {"ru": "🔇 Стоп музыка", "en": "🔇 Stop Music"},
    "preview.sound": {"ru": "🔊 Звук: {var}", "en": "🔊 Sound: {var}"},
    "preview.cg": {"ru": "🖼 CG: {var}", "en": "🖼 CG: {var}"},
    "preview.hide_cg": {"ru": "🗑 Скрыть CG", "en": "🗑 Hide CG"},
    "preview.label": {"ru": "🏷 Метка: {name}", "en": "🏷 Label: {name}"},
    "preview.jump": {"ru": "➡ Прыжок: {target}", "en": "➡ Jump: {target}"},
    "preview.menu": {"ru": "📋 Меню: {prompt}", "en": "📋 Menu: {prompt}"},
    "preview.python": {"ru": "🐍 Python: {code}", "en": "🐍 Python: {code}"},
    "preview.pause_click": {"ru": "клик", "en": "click"},
    "preview.pause": {"ru": "⏸ Пауза ({dur})", "en": "⏸ Pause ({dur})"},
    "preview.return": {"ru": "⏹ Return (выход в главное меню / возврат из call)", "en": "⏹ Return (exit to main menu / return from call)"},
    "preview.window_show": {"ru": "Показать", "en": "Show"},
    "preview.window_hide": {"ru": "Скрыть", "en": "Hide"},
    "preview.window": {"ru": "🪟 Текстовое окно: {action}{trans}", "en": "🪟 Text Window: {action}{trans}"},
    "preview.ambience": {"ru": "🌬 Эмбиенс: {var}", "en": "🌬 Ambience: {var}"},
    "preview.stop_ambience": {"ru": "🔇 Стоп эмбиенс", "en": "🔇 Stop Ambience"},
    "preview.with_transition": {"ru": "✨ Эффект: with {trans}", "en": "✨ Effect: with {trans}"},
    "preview.nvl_enter": {"ru": "📖 Войти в NVL-режим", "en": "📖 Enter NVL Mode"},
    "preview.nvl_clear": {"ru": "📖 Очистить экран NVL", "en": "📖 Clear NVL Screen"},
    "preview.nvl_exit": {"ru": "💬 Вернуться в ADV", "en": "💬 Return to ADV"},
    "preview.nvl_default": {"ru": "📖 NVL", "en": "📖 NVL"},
    "preview.raw": {"ru": "🧩 Импорт (неразпознано): {code}", "en": "🧩 Import (unrecognized): {code}"},

                                                   
    "hotkey.add_dialogue": {"ru": "Добавить ноду: 💬 Реплика", "en": "Add Node: 💬 Line"},
    "hotkey.add_narration": {"ru": "Добавить ноду: 📖 Повествование", "en": "Add Node: 📖 Narration"},
    "hotkey.add_show_sprite": {"ru": "Добавить ноду: 🧍 Показать спрайт", "en": "Add Node: 🧍 Show Sprite"},
    "hotkey.add_hide_sprite": {"ru": "Добавить ноду: 🚫 Скрыть спрайт", "en": "Add Node: 🚫 Hide Sprite"},
    "hotkey.add_show_bg": {"ru": "Добавить ноду: 🖼 Показать фон", "en": "Add Node: 🖼 Show Background"},
    "hotkey.add_pause": {"ru": "Добавить ноду: ⏸ Пауза", "en": "Add Node: ⏸ Pause"},
    "hotkey.add_menu": {"ru": "Добавить ноду: 📋 Меню выбора", "en": "Add Node: 📋 Choice Menu"},
    "hotkey.duplicate_node": {"ru": "Дублировать текущую ноду", "en": "Duplicate Current Node"},
    "hotkey.move_node_up": {"ru": "Переместить ноду вверх", "en": "Move Node Up"},
    "hotkey.move_node_down": {"ru": "Переместить ноду вниз", "en": "Move Node Down"},

                                                
    "spell.unpaired_closing_tag": {"ru": "Непарный закрывающий тег {{/{name}}}", "en": "Unpaired closing tag {{/{name}}}"},
    "spell.unclosed_tag": {"ru": "Незакрытый тег {{{name}}} - нет {{/{name}}}", "en": "Unclosed tag {{{name}}} - missing {{/{name}}}"},
    "spell.double_space": {"ru": "Двойной пробел", "en": "Double space"},
    "spell.space_before_punct": {"ru": "Пробел перед «{ch}»", "en": "Space before \"{ch}\""},
    "spell.repeated_punct": {"ru": "Повтор знаков препинания: «{seg}»", "en": "Repeated punctuation: \"{seg}\""},
    "spell.repeated_word": {"ru": "Повтор слова подряд: «{word}»", "en": "Repeated word: \"{word}\""},
    "spell.possible_typo": {"ru": "Возможно, опечатка: «{word}»", "en": "Possible typo: \"{word}\""},

    "ne.add_choice_button": {"ru": "+ Добавить вариант", "en": "+ Add Choice"},
    "mw.node_search_placeholder": {
        "ru": "🔎 Поиск по репликам / спрайтам / персонажам...",
        "en": "🔎 Search lines / sprites / characters...",
    },

                                         
    "ne.audio_music_title": {"ru": "Аудио (музыка)", "en": "Audio (Music)"},
    "ne.audio_sound_title": {"ru": "Аудио (звук)", "en": "Audio (Sound)"},
    "ne.audio_ambience_title": {"ru": "Аудио (эмбиенс)", "en": "Audio (Ambience)"},
    "ne.file_label": {"ru": "Файл:", "en": "File:"},
    "ne.listen_file_tooltip": {"ru": "Прослушать выбранный файл", "en": "Listen to the selected file"},
    "ne.stop_listening_tooltip": {"ru": "Остановить прослушивание", "en": "Stop listening"},
    "ne.loop_checkbox": {"ru": "Зациклить (loop)", "en": "Loop"},
    "ne.fadein_tooltip": {"ru": "Плавное нарастание громкости в начале (fadein N)", "en": "Gradual volume increase at the start (fadein N)"},
    "ne.fadeout_tooltip": {
        "ru": "Плавное затухание в конце трека (для музыки - если она доиграет "
              "до конца сама, не оборвётся раньше через stop music)",
        "en": "Gradual fade-out at the end of the track (for music - if it "
              "plays to the end on its own, not cut off earlier via stop music)",
    },
    "ne.waveform_label": {
        "ru": "Волна (клик - перемотка, перетаскивание маркеров - fadein/fadeout):",
        "en": "Waveform (click to seek, drag markers for fadein/fadeout):",
    },
    "ne.stop_music_title": {"ru": "Стоп музыка", "en": "Stop Music"},
    "ne.stop_ambience_title": {"ru": "Стоп эмбиенс", "en": "Stop Ambience"},

                                                          
    "ne.label_group": {"ru": "Метка", "en": "Label"},
    "ne.label_name_field": {"ru": "Имя метки:", "en": "Label name:"},
    "ne.jump_group": {"ru": "Переход", "en": "Jump"},
    "ne.jump_target_label": {"ru": "Цель перехода:", "en": "Jump target:"},
    "ne.label_name_placeholder": {"ru": "имя метки", "en": "label name"},
    "ne.jump_target_tooltip": {
        "ru": "Имя label, на которую нужно перейти (jump). Должна существовать "
              "где-то в сценарии - иначе Ren'Py выдаст ошибку при запуске игры.",
        "en": "The name of the label to jump to. It must exist somewhere in "
              "the script - otherwise Ren'Py will throw an error when the game starts.",
    },
    "ne.menu_group": {"ru": "Меню выбора", "en": "Choice Menu"},
    "ne.menu_question_label": {"ru": "Вопрос/фраза перед меню:", "en": "Question/phrase before the menu:"},
    "ne.optional_placeholder": {"ru": "Необязательно", "en": "Optional"},
    "ne.menu_options_label": {"ru": "Варианты ответов:", "en": "Answer choices:"},
    "ne.menu_call_hint": {
        "ru": "По умолчанию переход на метку - jump. Включайте «call» у варианта, "
              "если после return в этой метке игрок должен вернуться обратно в меню, "
              "а не вылететь в главное меню (так ведёт себя jump + return).",
        "en": "By default, the jump to a label is via jump. Enable \"call\" "
              "on an option if, after return in that label, the player "
              "should come back to the menu instead of being kicked to the "
              "main menu (that's how jump + return behaves).",
    },
    "ne.pause_group": {"ru": "Пауза", "en": "Pause"},
    "ne.pause_duration_label": {
        "ru": "Длительность в секундах (0 - ждать клика игрока):",
        "en": "Duration in seconds (0 - wait for player click):",
    },
    "ne.pause_duration_tooltip": {
        "ru": "Длительность паузы в секундах. 0 - пауза до клика игрока "
              "(эквивалент голой команды pause).",
        "en": "Pause duration in seconds. 0 - pause until player click "
              "(equivalent to a bare pause command).",
    },
    "ne.pause_hint": {
        "ru": "0 секунд - pause без числа: сцена ждёт клика игрока, "
              "как обычная реплика без текста. Больше 0 - pause N: "
              "ждёт указанное время и продолжает само.",
        "en": "0 seconds - pause with no number: the scene waits for the "
              "player's click, like a regular line with no text. More than "
              "0 - pause N: waits the specified time and continues automatically.",
    },
    "ne.return_hint": {
        "ru": "Эта нода просто вставляет return в сценарий, без параметров.\n\n"
              "Если до этого места дошли через jump - Ren'Py решит, что сценарий "
              "закончился, и игра выйдет в главное меню.\n"
              "Если дошли через call (например, из варианта меню с галочкой "
              "«call») - игра вернётся обратно сразу после места вызова.",
        "en": "This node simply inserts a return into the script, with no "
              "parameters.\n\nIf this point was reached via jump - Ren'Py "
              "will decide the script has ended, and the game will exit to "
              "the main menu.\nIf reached via call (e.g. from a menu option "
              "with \"call\" checked) - the game will return right after the call site.",
    },

    "res_download.open_link": {
        "ru": "🔗 Открыть ссылку в браузере",
        "en": "🔗 Open Link in Browser",
    },

                                            
    "ne.atl_button": {"ru": "🎬 ATL-преобразования…", "en": "🎬 ATL Transform…"},
    "ne.atl_button_active": {"ru": "🎬 ATL-преобразования (задано) …", "en": "🎬 ATL Transform (set) …"},
    "ne.atl_hint": {
        "ru": "Произвольный ATL-блок Ren'Py (linear/ease, pause, repeat, смена картинки, "
              "block: и т.п.) - если задан, используется вместо простых полей "
              "«якорь/зум» выше и честно проигрывается в предпросмотре и презентации.",
        "en": "A custom Ren'Py ATL block (linear/ease, pause, repeat, image swap, "
              "block:, etc.) - if set, it is used instead of the simple anchor/zoom "
              "fields above and is faithfully played back in preview and presentation.",
    },
    "atl.dialog_title": {"ru": "ATL-преобразования", "en": "ATL Transform"},
    "atl.hint": {
        "ru": "Впишите тело ATL-блока Ren'Py как оно идёт после \"show x:\" / \"scene x:\" "
              "(без самого заголовка) - поддерживаются xalign/yalign/pos/anchor/zoom/rotate/"
              "alpha, linear/ease-интерполяция, pause, repeat [N], смена картинки строкой "
              "\"имя\" [with переход], вложенные block:. Нераспознанные строки сохранятся в "
              "коде дословно, но не будут анимированы в предпросмотре.",
        "en": "Enter the body of a Ren'Py ATL block as it appears after \"show x:\" / "
              "\"scene x:\" (without the header itself) - xalign/yalign/pos/anchor/zoom/"
              "rotate/alpha, linear/ease interpolation, pause, repeat [N], image swap via a "
              "\"name\" [with transition] line, and nested block: are supported. Unrecognized "
              "lines are kept verbatim in the generated code but won't be animated in the preview.",
    },
    "atl.code_label": {"ru": "Код ATL:", "en": "ATL code:"},
    "atl.preview_label": {"ru": "Живой предпросмотр:", "en": "Live preview:"},
    "atl.play_button": {"ru": "\u25b6 Проиграть", "en": "\u25b6 Play"},
    "atl.clear_button": {"ru": "Очистить", "en": "Clear"},
    "atl.cancel": {"ru": "Отмена", "en": "Cancel"},
    "atl.save": {"ru": "Сохранить", "en": "Save"},
    "atl.loop_duration": {"ru": "цикл: {dur}с", "en": "loop: {dur}s"},
    "atl.infinite_loop": {"ru": "бесконечный цикл", "en": "infinite loop"},
    "atl.unrecognized_lines": {
        "ru": "⚠ не анимируются (сохранятся как есть): {lines}",
        "en": "⚠ not animated (kept verbatim): {lines}",
    },
    "atl.tab_text": {"ru": "Текст", "en": "Text"},
    "atl.tab_steps": {"ru": "Шаги", "en": "Steps"},

    "atl_steps.prop_xalign": {"ru": "Позиция X (xalign)", "en": "Position X (xalign)"},
    "atl_steps.prop_yalign": {"ru": "Позиция Y (yalign)", "en": "Position Y (yalign)"},
    "atl_steps.prop_zoom": {"ru": "Масштаб (zoom)", "en": "Zoom"},
    "atl_steps.prop_rotate": {"ru": "Поворот (rotate)", "en": "Rotate"},
    "atl_steps.prop_alpha": {"ru": "Прозрачность (alpha)", "en": "Alpha"},
    "atl_steps.warper_label": {"ru": "Тип:", "en": "Type:"},
    "atl_steps.duration_label": {"ru": "Время, с:", "en": "Duration, s:"},
    "atl_steps.add_step": {"ru": "+ Добавить шаг", "en": "+ Add step"},
    "atl_steps.remove_step": {"ru": "🗑 Удалить шаг", "en": "🗑 Remove step"},
    "atl_steps.repeat_forever": {"ru": "🔁 Зациклить (repeat)", "en": "🔁 Loop (repeat)"},
    "atl_steps.step_n": {"ru": "Шаг {n}", "en": "Step {n}"},
    "atl_steps.timeline_total": {"ru": "длительность: {total}с", "en": "duration: {total}s"},
    "atl_steps.lossy_import_warning": {
        "ru": "⚠ часть ATL-текста не выражается шагами (pos/anchor, смена картинки, "
              "block: и т.п.) и была отброшена в этом представлении - сам текст не "
              "изменён, пока вы не сохраните из вкладки «Шаги».",
        "en": "⚠ part of the ATL text can't be represented as steps (pos/anchor, image "
              "swap, block:, etc.) and was dropped from this view - the text itself is "
              "unchanged unless you save from the Steps tab.",
    },

    "ne.transition_button": {"ru": "🎬 Переход…", "en": "🎬 Transition…"},

    "trans.dialog_title": {"ru": "Настройка перехода", "en": "Transition Settings"},
    "trans.tab_preset": {"ru": "Готовый переход", "en": "Preset"},
    "trans.tab_custom": {"ru": "Свой переход", "en": "Custom"},
    "trans.preset_hint": {
        "ru": "Стандартные переходы Ren'Py, используемые в проекте:",
        "en": "Standard Ren'Py transitions used in the project:",
    },
    "trans.preset_none": {"ru": "- без перехода -", "en": "- no transition -"},
    "trans.preview_label": {"ru": "Предпросмотр:", "en": "Preview:"},
    "trans.replay_button": {"ru": "▶ Повторить", "en": "▶ Replay"},
    "trans.kind_label": {"ru": "Тип перехода:", "en": "Transition type:"},
    "trans.kind_dissolve": {"ru": "Dissolve (растворение)", "en": "Dissolve"},
    "trans.kind_fade": {"ru": "Fade (через цвет)", "en": "Fade (through color)"},
    "trans.kind_pixellate": {"ru": "Pixellate (пикселизация)", "en": "Pixellate"},
    "trans.kind_image_dissolve": {"ru": "ImageDissolve (по маске-картинке)", "en": "ImageDissolve (mask image)"},
    "trans.kind_wipe": {"ru": "Wipe/CropMove (вайп)", "en": "Wipe / CropMove"},
    "trans.kind_push": {"ru": "Push (сдвиг)", "en": "Push"},
    "trans.kind_punch": {"ru": "Punch (тряска экрана)", "en": "Punch (screen shake)"},
    "trans.duration_label": {"ru": "Длительность, с:", "en": "Duration, s:"},
    "trans.fade_out_label": {"ru": "Затухание (out), с:", "en": "Fade out, s:"},
    "trans.fade_hold_label": {"ru": "Удержание, с:", "en": "Hold, s:"},
    "trans.fade_in_label": {"ru": "Появление (in), с:", "en": "Fade in, s:"},
    "trans.fade_color_label": {"ru": "Цвет:", "en": "Color:"},
    "trans.pixellate_steps_label": {"ru": "Шагов пикселизации:", "en": "Pixellate steps:"},
    "trans.mask_label": {"ru": "Маска:", "en": "Mask:"},
    "trans.mask_none": {"ru": "не выбрана", "en": "not selected"},
    "trans.mask_browse": {"ru": "Обзор…", "en": "Browse…"},
    "trans.ramp_label": {"ru": "Мягкость края (ramp):", "en": "Edge softness (ramp):"},
    "trans.direction_label": {"ru": "Направление:", "en": "Direction:"},
    "trans.dir_left": {"ru": "Слева", "en": "Left"},
    "trans.dir_right": {"ru": "Справа", "en": "Right"},
    "trans.dir_up": {"ru": "Сверху", "en": "Up"},
    "trans.dir_down": {"ru": "Снизу", "en": "Down"},
    "trans.punch_axis_label": {"ru": "Ось тряски:", "en": "Shake axis:"},
    "trans.punch_h": {"ru": "Горизонтальная (hpunch)", "en": "Horizontal (hpunch)"},
    "trans.punch_v": {"ru": "Вертикальная (vpunch)", "en": "Vertical (vpunch)"},
    "trans.cancel": {"ru": "Отмена", "en": "Cancel"},
    "trans.save": {"ru": "Сохранить", "en": "Save"},
    "trans.preset_custom_label": {"ru": "★ {name} (свой)", "en": "★ {name} (custom)"},
    "trans.save_name_label": {"ru": "Имя для сохранения:", "en": "Save as name:"},
    "trans.save_name_placeholder": {"ru": "например, mask_spiral_fade", "en": "e.g. mask_spiral_fade"},
    "trans.save_name_hint": {
        "ru": "Переход сохранится под этим именем (объявится через define в общем "
              "файле дефайнов) и появится в списке готовых переходов - настраивать "
              "его заново в других местах проекта не понадобится. Если оставить "
              "пустым, имя будет предложено автоматически.",
        "en": "The transition will be saved under this name (declared via define in "
              "the shared defines file) and will show up in the preset list - no need "
              "to set it up again elsewhere in the project. Left empty, a name is "
              "suggested automatically.",
    },
    "trans.demo_note": {
        "ru": "ℹ Для наглядности здесь показан переход на случайный фон/CG проекта - "
              "в игре вместо него будет тот кадр, что действительно идёт следующим.",
        "en": "ℹ For clarity this shows a transition to a random background/CG from "
              "the project - in the actual game it will transition to whatever frame "
              "really comes next.",
    },
}
