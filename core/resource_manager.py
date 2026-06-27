import os, json, re
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from core.composite_sprite_parser import CompositeSprite, parse_sprites_rpy_file
from paths import BASE_DIR, CONFIG_FILE
from pathlib import Path

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
AUDIO_EXTS = {'.mp3', '.ogg', '.wav', '.flac', '.opus'}


SOURCES = ("default", "custom")


def filename_to_var(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if name and name[0].isdigit():
        name = '_' + name
    return name.lower()


@dataclass
class ResourceEntry:
    var_name: str
    rel_path: str
    abs_path: str
    filename: str
    display_name: str
    category: str
    group_path: str = ""  # подпапка внутри категории, например "us/normal" для sprites/us/normal/smile.png ("" — файл лежит прямо в корне категории)
    source: str = "custom"  # "default" | "custom" — из какой из двух корневых папок ресурс пришёл
    game_path: str = ""  # путь относительно папки игры в Ren'Py, например "bg/forest.png" (без префикса source/ — используется в image/define)

    def group_parts(self) -> List[str]:
        return [p for p in self.group_path.split('/') if p]


@dataclass
class ResourceConfig:
    custom_name: str = ""
    custom_var: str = ""


@dataclass
class ResourcesConfig:
    resources_path: str = "resources"
    overrides: Dict[str, ResourceConfig] = field(default_factory=dict)


class ResourceManager:
    CATEGORIES = {
        'bg':      ('Фоны (BG)',  IMAGE_EXTS),
        'cg':      ('CG',         IMAGE_EXTS),
        'sprites': ('Спрайты',    IMAGE_EXTS),
        'music':   ('Музыка',     AUDIO_EXTS),
        'sounds':  ('Звуки',      AUDIO_EXTS),
    }
    RENPY_PREFIX = {
        'bg': 'bg', 'cg': 'cg', 'sprites': '',
        'music': '', 'sounds': 'sfx_',
    }
    # Категории, где допускаются вложенные папки (произвольная глубина),
    # например resources/sprites/<персонаж>/<вариация>/<файл>.png
    NESTED_CATEGORIES = {'sprites'}

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        
        self.base_dir = str(BASE_DIR)
        self.config_path = str(CONFIG_FILE)
        self.config = self._load_config()
        self.resources: Dict[str, List[ResourceEntry]] = {cat: [] for cat in self.CATEGORIES}
        self.composite_sprites: List[CompositeSprite] = []

    def _load_config(self) -> ResourcesConfig:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cfg = ResourcesConfig()
                cfg.resources_path = data.get('resources_path', 'resources')
                for k, v in data.get('overrides', {}).items():
                    cfg.overrides[k] = ResourceConfig(**v)
                return cfg
            except Exception:
                pass
        return ResourcesConfig()

    def save_config(self):
        data = {
            'resources_path': self.config.resources_path,
            'overrides': {k: asdict(v) for k, v in self.config.overrides.items()}
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_overrides(self, path: str):
        """Сохраняет ТОЛЬКО переопределения имён (без пути к ресурсам, который
        специфичен для конкретного проекта) в отдельный JSON-файл — чтобы
        можно было перенести их в другой проект или сохранить как резервную
        копию именования ресурсов."""
        data = {
            'overrides': {k: asdict(v) for k, v in self.config.overrides.items()}
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_overrides(self, path: str, merge: bool = True) -> int:
        """Загружает переопределения имён из файла, созданного export_overrides.
        merge=True — добавляет/перезаписывает поверх текущих (по rel_path);
        merge=False — полностью заменяет текущий набор переопределений.
        Возвращает количество загруженных записей. Не сканирует ресурсы и не
        сохраняет config сам — это должна сделать вызывающая сторона после
        (rescan + save_config), потому что переопределения для путей, которых
        нет в текущем проекте, всё равно безопасно хранить — они просто не
        применятся, пока такой файл не появится."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        loaded = {k: ResourceConfig(**v) for k, v in data.get('overrides', {}).items()}
        if not merge:
            self.config.overrides.clear()
        self.config.overrides.update(loaded)
        return len(loaded)

    

    def get_resources_root(self):
        p = Path(self.config.resources_path)

        if p.is_absolute():
            return str(p)

        return str(BASE_DIR / p)

    def get_source_root(self, source: str) -> str:
        """Корень конкретного источника, например resources/default или
        resources/custom. Структура внутри идентична: <source>/bg/, /cg/,
        /sprites/, /music/, /sounds/."""
        return os.path.join(self.get_resources_root(), source)

    def scan(self):
        for cat, (_, exts) in self.CATEGORIES.items():
            self.resources[cat] = []
            for source in SOURCES:
                source_root = self.get_source_root(source)
                cat_dir = os.path.join(source_root, cat)
                if not os.path.isdir(cat_dir):
                    os.makedirs(cat_dir, exist_ok=True)
                    continue
                if cat in self.NESTED_CATEGORIES:
                    self._scan_nested(cat, cat_dir, exts, source)
                else:
                    self._scan_flat(cat, cat_dir, exts, source)
        self._scan_composite_sprites()

    def _scan_composite_sprites(self):
        """Если в <default|custom>/sprites/sprites.rpy есть составные
        спрайты (ConditionSwitch / im.MatrixColor с im.Composite слоями) —
        парсим их отдельно (из обоих источников сразу, если файл есть в
        обоих) и убираем использованные в них файлы из обычного плоского
        списка self.resources['sprites'], чтобы один и тот же файл не
        показывался дважды (как отдельный слой и как часть составного
        спрайта). Файлы, не упомянутые в sprites.rpy, продолжают работать
        как раньше — обычными папочными спрайтами. Составные спрайты не
        попадают в generate_define_block независимо от источника — они уже
        объявлены в самом sprites.rpy."""
        self.composite_sprites = []
        used_rel_paths_by_source = {"default": set(), "custom": set()}

        for source in SOURCES:
            rpy_path = os.path.join(self.get_source_root(source), 'sprites', 'sprites.rpy')
            if not os.path.isfile(rpy_path):
                continue
            try:
                parsed = parse_sprites_rpy_file(rpy_path, source=source)
            except Exception:
                continue
            self.composite_sprites.extend(parsed)
            for cs in parsed:
                for layer in cs.layers:
                    used_rel_paths_by_source[source].add(layer.rel_path.replace('\\', '/'))

        def entry_rel_path(e: ResourceEntry) -> str:
            return f"{e.group_path}/{e.filename}" if e.group_path else e.filename

        filtered = []
        for e in self.resources['sprites']:
            used = used_rel_paths_by_source.get(e.source, set())
            if entry_rel_path(e) not in used:
                filtered.append(e)
        self.resources['sprites'] = filtered

    def _scan_flat(self, cat: str, cat_dir: str, exts: set, source: str):
        for fn in sorted(os.listdir(cat_dir)):
            full = os.path.join(cat_dir, fn)
            if not os.path.isfile(full):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            self.resources[cat].append(self._make_entry(cat, cat_dir, fn, group_path="", source=source))

    def _scan_nested(self, cat: str, cat_dir: str, exts: set, source: str):
        """Рекурсивно обходит папку категории на любую глубину, сохраняя
        относительный путь подпапки (group_path) для построения дерева
        персонаж -> вариация -> спрайт в GUI."""
        for dirpath, dirnames, filenames in os.walk(cat_dir):
            dirnames.sort()
            group_path = os.path.relpath(dirpath, cat_dir).replace('\\', '/')
            if group_path == '.':
                group_path = ""
            for fn in sorted(filenames):
                ext = os.path.splitext(fn)[1].lower()
                if ext not in exts:
                    continue
                if fn.lower() == 'sprites.rpy':
                    continue
                self.resources[cat].append(self._make_entry(cat, dirpath, fn, group_path=group_path, source=source))

    def _make_entry(self, cat: str, dir_abs: str, fn: str, group_path: str, source: str) -> ResourceEntry:
        abs_path = os.path.join(dir_abs, fn)
        # rel_path хранится с префиксом source — нужен как уникальный ключ
        # overrides (иначе одинаковые относительные пути в default/ и
        # custom/ были бы неразличимы). game_path — путь БЕЗ префикса
        # source, ровно такой, какой должен попасть в сгенерированный код
        # (файлы физически копируются/совмещаются в общую папку игры).
        game_path = os.path.relpath(abs_path, self.get_source_root(source)).replace('\\', '/')
        rel_path = f"{source}/{game_path}"
        override = self.config.overrides.get(rel_path, ResourceConfig())

        if override.custom_var:
            base_var = override.custom_var
        else:
            base_var = self._auto_var(cat, fn, group_path)

        display = override.custom_name if override.custom_name else os.path.splitext(fn)[0]
        return ResourceEntry(
            var_name=base_var, rel_path=rel_path, abs_path=abs_path,
            filename=fn, display_name=display, category=cat, group_path=group_path,
            source=source, game_path=game_path,
        )

    def _auto_var(self, cat: str, fn: str, group_path: str) -> str:
        """Автоматическое имя ресурса (если не задано своё через overrides).
        Формат зависит от категории:
        - bg/cg:     "bg bus_stop" / "cg d1_food_normal" — имя ЧЕРЕЗ ПРОБЕЛ
                     (как у составных спрайтов: show bg bus_stop).
        - sprites:   как раньше — конкатенация подчёркиванием с учётом
                     подпапок персонажа/вариации (sprites_us_normal_smile).
        - music:     music_list["name"] — ссылка на словарь треков, который
                     уже определён в проекте Ren'Py, мы его не генерируем.
        - sounds:    sfx_name — как раньше, просто с новым префиксом."""
        name = filename_to_var(fn)
        if cat in ('bg', 'cg'):
            return f"{self.RENPY_PREFIX[cat]} {name}"
        if cat == 'music':
            return f'music_list["{name}"]'
        if cat == 'sprites':
            parts = [p for p in group_path.split('/') if p and p != '.']
            name_parts = [filename_to_var(p) for p in parts] + [name]
            return "_".join(name_parts)
        # sounds (и любая прочая будущая категория без особого формата)
        return self.RENPY_PREFIX.get(cat, '') + name

    def get(self, category: str) -> List[ResourceEntry]:
        return self.resources.get(category, [])

    def get_folders(self, category: str, parent_path: str = "") -> List[str]:
        """Возвращает имена непосредственных подпапок внутри parent_path для
        категории (только для NESTED_CATEGORIES). Например, для sprites и
        parent_path="" вернёт ['un', 'us'], а для parent_path="us" — ['close', 'far', 'normal']
        (если они существуют как папки), отсортированные по алфавиту."""
        if category not in self.NESTED_CATEGORIES:
            return []
        seen = set()
        for e in self.resources.get(category, []):
            parts = e.group_parts()
            parent_parts = [p for p in parent_path.split('/') if p]
            if parts[:len(parent_parts)] != parent_parts:
                continue
            if len(parts) > len(parent_parts):
                seen.add(parts[len(parent_parts)])
        return sorted(seen)

    def get_entries_in_folder(self, category: str, folder_path: str = "") -> List[ResourceEntry]:
        """Возвращает файлы (ResourceEntry), лежащие НЕПОСРЕДСТВЕННО в указанной
        папке (не в её подпапках). Для плоских категорий folder_path игнорируется."""
        if category not in self.NESTED_CATEGORIES:
            return self.resources.get(category, [])
        folder_parts = [p for p in folder_path.split('/') if p]
        return [e for e in self.resources.get(category, []) if e.group_parts() == folder_parts]

    def find_by_var(self, var: str) -> Optional[ResourceEntry]:
        for entries in self.resources.values():
            for e in entries:
                if e.var_name == var:
                    return e
        return None

    def get_composite_characters(self) -> List[str]:
        """Список персонажей (первое слово имени), у которых есть составные
        спрайты из sprites.rpy, отсортированный по алфавиту."""
        return sorted(set(cs.character for cs in self.composite_sprites))

    def get_composite_positions(self, character: str) -> List[str]:
        """Доступные позиции (far/close/normal) для персонажа, в фиксированном
        порядке far -> close -> normal (а не алфавитном) — это привычный
        порядок 'от дальнего плана к ближнему' для художников по сценам."""
        order = ["far", "close", "normal"]
        present = set(cs.position for cs in self.composite_sprites if cs.character == character)
        return [p for p in order if p in present]

    def get_composite_sprites(self, character: str, position: str) -> List[CompositeSprite]:
        """Составные спрайты персонажа в данной позиции, отсортированные по
        составу (variant_parts) для предсказуемого порядка в карусели."""
        result = [
            cs for cs in self.composite_sprites
            if cs.character == character and cs.position == position
        ]
        result.sort(key=lambda cs: cs.display_name)
        return result

    def find_composite_by_name(self, full_name: str) -> Optional[CompositeSprite]:
        for cs in self.composite_sprites:
            if cs.full_name == full_name:
                return cs
        return None

    def resolve_layer_path(self, rel_path: str, source: str = "custom") -> str:
        """Абсолютный путь к файлу слоя составного спрайта (rel_path —
        относительно <source>/sprites/, например 'far/cs/cs_1_body.png').
        source берётся из CompositeSprite.source — каждый sprites.rpy ищет
        свои слои в той же папке (default или custom), где сам лежит."""
        return os.path.join(self.get_source_root(source), 'sprites', rel_path)

    def set_override(self, rel_path: str, name: str = "", var: str = ""):
        self.config.overrides[rel_path] = ResourceConfig(custom_name=name, custom_var=var)
        self.save_config()

    def generate_define_block(self) -> str:
        lines = ["# ===== Определения ресурсов =====", ""]
        for cat, entries in self.resources.items():
            # В define/image попадают только ресурсы из custom/ — те, что
            # лежат в default/, считаются уже объявленными где-то ещё
            # (например встроены в базовый шаблон проекта) и не дублируются.
            # music исключена полностью: там var_name это music_list["..."] —
            # ссылка на словарь треков, который уже существует в проекте
            # Ren'Py, а не переменная, которую нам нужно объявлять.
            if cat == 'music':
                continue
            custom_entries = [e for e in entries if e.source == "custom"]
            if not custom_entries:
                continue
            label, _ = self.CATEGORIES[cat]
            lines.append(f"# {label}")
            for e in custom_entries:
                if cat in ('bg', 'cg', 'sprites'):
                    lines.append(f'image {e.var_name} = "{e.game_path}"')
                else:
                    lines.append(f'define {e.var_name} = "{e.game_path}"')
            lines.append("")
        if self.composite_sprites:
            lines.append("# Составные спрайты (персонаж/позиция/эмоция) уже определены")
            lines.append("# в sprites.rpy — убедитесь, что этот файл подключён к проекту")
            lines.append("# Ren'Py, отдельных image здесь не нужно (для default и custom")
            lines.append("# источников одинаково).")
            lines.append("")
        return "\n".join(lines)
