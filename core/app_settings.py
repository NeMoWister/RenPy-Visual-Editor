                       
"""
Общие настройки приложения, не привязанные к конкретному проекту сценария.
Хранятся в секции "app_settings" общего файла editor_config.json (см.
core/unified_config.py) - в базовой папке приложения (рядом с .exe или
main.py, см. core/paths.py).
"""
from dataclasses import dataclass, asdict

from core.unified_config import load_section, save_section


@dataclass
class AppSettings:
    check_updates_on_startup: bool = True
                                                                         
                                                                   
                              
    last_update_check: str = ""
                                                                       
                                                                      
                                                                    
    skipped_version: str = ""
                                                                       
                                                                      
                                                                
    window_geometry: str = ""
    window_state: str = ""
    autosave_enabled: bool = True
    autosave_interval_sec: int = 180
                                                                         
                                                                   
                                                                      
                                                                    
                                                                     
                                  
    nvl_codegen_style: str = "character"
    language: str = "ru"
    theme: str = "ember"

    @classmethod
    def load(cls, base_dir: str) -> "AppSettings":
        data = load_section(base_dir, "app_settings")
        try:
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception:
            return cls()

    def save(self, base_dir: str):
        save_section(base_dir, "app_settings", asdict(self))
