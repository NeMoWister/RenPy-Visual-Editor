import json, os
from typing import Optional
from .models import (Project, Scene, SceneNode, Character, NodeType, SpritePosition)


def project_to_dict(project: Project) -> dict:
    def sp(p): return {'xalign': p.xalign, 'yalign': p.yalign, 'zoom': p.zoom}
    def nd(n): return {
        'node_id': n.node_id, 'node_type': n.node_type.value,
        'character_var': n.character_var, 'text': n.text,
        'bg_var': n.bg_var, 'cg_var': n.cg_var, 'transition': n.transition,
        'sprite_var': n.sprite_var, 'sprite_expression': n.sprite_expression,
        'sprite_position': sp(n.sprite_position), 'sprite_tag': n.sprite_tag,
        'music_var': n.music_var, 'sound_var': n.sound_var,
        'music_fadeout': n.music_fadeout, 'music_fadein': n.music_fadein,
        'audio_loop': n.audio_loop,
        'label_name': n.label_name, 'jump_target': n.jump_target,
        'pause_duration': n.pause_duration, 'python_code': n.python_code,
        'menu_prompt': n.menu_prompt, 'menu_choices': n.menu_choices,
        'comment_text': n.comment_text,
    }
    def sc(s): return {'scene_id': s.scene_id, 'name': s.name, 'nodes': [nd(n) for n in s.nodes]}
    def ch(c): return {'name': c.name, 'variable': c.variable, 'color': c.color, 'image_tag': c.image_tag}
    return {
        'title': project.title, 'label_name': project.label_name,
        'resources_path': project.resources_path,
        'characters': [ch(c) for c in project.characters],
        'scenes': [sc(s) for s in project.scenes],
    }


def project_from_dict(data: dict) -> Project:
    def sp(d): return SpritePosition(d.get('xalign',0.5), d.get('yalign',1.0), d.get('zoom',1.0))
    def nd(d):
        n = SceneNode()
        n.node_id = d.get('node_id', n.node_id)
        n.node_type = NodeType(d.get('node_type', 'dialogue'))
        n.character_var = d.get('character_var')
        n.text = d.get('text', '')
        n.bg_var = d.get('bg_var')
        n.cg_var = d.get('cg_var')
        n.transition = d.get('transition', 'dissolve')
        n.sprite_var = d.get('sprite_var')
        n.sprite_expression = d.get('sprite_expression')
        n.sprite_position = sp(d.get('sprite_position', {}))
        n.sprite_tag = d.get('sprite_tag')
        n.music_var = d.get('music_var')
        n.sound_var = d.get('sound_var')
        n.music_fadeout = d.get('music_fadeout', 0)
        n.music_fadein = d.get('music_fadein', 0)
        n.audio_loop = d.get('audio_loop', False)
        n.label_name = d.get('label_name', '')
        n.jump_target = d.get('jump_target', '')
        n.pause_duration = d.get('pause_duration', 0.0)
        n.python_code = d.get('python_code', '')
        n.menu_prompt = d.get('menu_prompt', '')
        n.menu_choices = [tuple(x) for x in d.get('menu_choices', [])]
        n.comment_text = d.get('comment_text', '')
        return n
    def sc(d):
        s = Scene()
        s.scene_id = d.get('scene_id', s.scene_id)
        s.name = d.get('name', 'Сцена')
        s.nodes = [nd(n) for n in d.get('nodes', [])]
        return s
    def ch(d): return Character(d.get('name',''), d.get('variable',''), d.get('color','#ffffff'), d.get('image_tag'))
    p = Project()
    p.title = data.get('title', 'Проект')
    p.label_name = data.get('label_name', 'start')
    p.resources_path = data.get('resources_path', 'resources')
    p.characters = [ch(c) for c in data.get('characters', [])]
    p.scenes = [sc(s) for s in data.get('scenes', [])]
    return p


class ProjectManager:
    def __init__(self):
        self.current_path: Optional[str] = None
        self.project = Project()

    def new_project(self, title: str = "Новый проект") -> Project:
        self.project = Project(title=title)
        self.current_path = None
        return self.project

    def save(self, path: Optional[str] = None) -> bool:
        save_path = path or self.current_path
        if not save_path:
            return False
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(project_to_dict(self.project), f, ensure_ascii=False, indent=2)
            self.current_path = save_path
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    def load(self, path: str) -> Optional[Project]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.project = project_from_dict(data)
            self.current_path = path
            return self.project
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return None
