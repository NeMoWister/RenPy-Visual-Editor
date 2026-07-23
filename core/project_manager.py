                       
import json, os
from typing import Optional
from .models import (Project, Scene, SceneNode, Character, NodeType, SpritePosition, NodeGroup)


def _sp_to_dict(p):
    return {'xalign': p.xalign, 'yalign': p.yalign, 'zoom': p.zoom}


def node_to_dict(n: SceneNode) -> dict:
    return {
        'node_id': n.node_id, 'node_type': n.node_type.value,
        'character_var': n.character_var, 'text': n.text,
        'bg_var': n.bg_var, 'cg_var': n.cg_var, 'transition': n.transition,
        'sprite_var': n.sprite_var, 'sprite_expression': n.sprite_expression,
        'sprite_position': _sp_to_dict(n.sprite_position), 'sprite_tag': n.sprite_tag,
        'hide_group': n.hide_group,
        'music_var': n.music_var, 'sound_var': n.sound_var,
        'music_fadeout': n.music_fadeout, 'music_fadein': n.music_fadein,
        'audio_loop': n.audio_loop,
        'label_name': n.label_name, 'jump_target': n.jump_target,
        'pause_duration': n.pause_duration, 'python_code': n.python_code,
        'menu_prompt': n.menu_prompt, 'menu_choices': n.menu_choices,
        'comment_text': n.comment_text,
        'window_action': n.window_action,
        'ambience_var': n.ambience_var, 'ambience_fadein': n.ambience_fadein,
        'ambience_fadeout': n.ambience_fadeout,
        'color_tag': n.color_tag,
        'custom_template_id': n.custom_template_id, 'custom_params': n.custom_params,
    }


def node_from_dict(d: dict, new_id: bool = False) -> SceneNode:
    n = SceneNode()
    if not new_id:
        n.node_id = d.get('node_id', n.node_id)
    n.node_type = NodeType(d.get('node_type', 'dialogue'))
    n.character_var = d.get('character_var')
    n.text = d.get('text', '')
    n.bg_var = d.get('bg_var')
    n.cg_var = d.get('cg_var')
    n.transition = d.get('transition', 'dissolve')
    n.sprite_var = d.get('sprite_var')
    n.sprite_expression = d.get('sprite_expression')
    n.sprite_position = _sp_from_dict(d.get('sprite_position', {}))
    n.sprite_tag = d.get('sprite_tag')
    n.hide_group = d.get('hide_group')
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
    n.window_action = d.get('window_action', 'show')
    n.ambience_var = d.get('ambience_var')
    n.ambience_fadein = d.get('ambience_fadein', 0.0)
    n.ambience_fadeout = d.get('ambience_fadeout', 0.0)
    n.color_tag = d.get('color_tag')
    n.custom_template_id = d.get('custom_template_id', '')
    n.custom_params = dict(d.get('custom_params', {}))
    return n


def _sp_from_dict(d):
    return SpritePosition(d.get('xalign', 0.5), d.get('yalign', 1.0), d.get('zoom', 1.0))


def project_to_dict(project: Project) -> dict:
    def gr(g): return {
        'group_id': g.group_id, 'title': g.title, 'node_ids': list(g.node_ids),
        'collapsed': g.collapsed, 'color': g.color,
    }
    def sc(s): return {
        'scene_id': s.scene_id, 'name': s.name, 'nodes': [node_to_dict(n) for n in s.nodes],
        'groups': [gr(g) for g in s.groups],
    }
    def ch(c): return {'name': c.name, 'variable': c.variable, 'color': c.color, 'image_tag': c.image_tag}
    return {
        'title': project.title, 'label_name': project.label_name,
        'resources_path': project.resources_path,
        'characters': [ch(c) for c in project.characters],
        'scenes': [sc(s) for s in project.scenes],
    }


def project_from_dict(data: dict) -> Project:
    def gr(d):
        g = NodeGroup()
        g.group_id = d.get('group_id', g.group_id)
        g.title = d.get('title', 'Группа')
        g.node_ids = list(d.get('node_ids', []))
        g.collapsed = d.get('collapsed', False)
        g.color = d.get('color', '#ff8c3d')
        return g
    def sc(d):
        s = Scene()
        s.scene_id = d.get('scene_id', s.scene_id)
        s.name = d.get('name', 'Сцена')
        s.nodes = [node_from_dict(n) for n in d.get('nodes', [])]
        s.groups = [gr(g) for g in d.get('groups', [])]
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
