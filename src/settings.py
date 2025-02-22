# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:48
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from utils.toolbox import init_log, from_dict_to_model


@dataclass
class SiteKey:
    discord = "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34"
    epic = "91e4137f-95af-4bc9-97af-cdcedce21c8c"
    hcaptcha = "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2"
    hcaptcha_signup = "13257c82-e129-4f09-a733-2a7cb3102832"
    new_type_challenge = "ace50dd0-0d68-44ff-931a-63b670c7eed7"
    user = "c86d730b-300a-444c-a8c5-5312e7a93628"
    cloud_horse = "edc4ce89-8903-4906-80b1-7440ad9a69c8"
    top_level = "adafb813-8b5c-473f-9de3-485b4ad5aa09"


@dataclass
class LarkSettings:
    app_id: str
    app_secret: str
    webhook_uuid: str
    chat_id: str


@dataclass
class GitHubSettings:
    github_token: str
    github_owner: str
    github_repo: str

    def __post_init__(self):
        for ck in self.__dict__:
            os.environ[ck.upper()] = self.__dict__[ck]


@dataclass
class Firebird:
    path: str
    """
    path to firebird.json
    """

    focus_labels: Dict[str, str] = field(default_factory=dict)
    """
    HashMap: words in prompt --> model name
    # 采集器中的默认聚焦挑战，不在聚焦表中的挑战将被跳过
    """

    @classmethod
    def from_json(cls, sp: Path):
        template = {"focus_labels": {}, "path": f"{sp.absolute()}"}
        if not sp.exists():
            sp.write_text(json.dumps(template, indent=2, ensure_ascii=True))
        return from_dict_to_model(cls, json.loads(sp.read_text()))

    def flush(self):
        self.focus_labels = json.loads(Path(self.path).read_text())["focus_labels"]
        return self.focus_labels

    def to_json(self, items: Dict[str, str] | None = None):
        if items:
            self.focus_labels.update(items)
        Path(self.path).write_text(json.dumps(self.__dict__, indent=2, ensure_ascii=True))


@dataclass
class Config:
    lark: LarkSettings = None
    github: GitHubSettings = None

    @classmethod
    def from_json(cls, config_path: Path):
        try:
            _config: dict = json.loads(config_path.read_text())
        except FileNotFoundError:
            template = {
                "lark": {"app_id": "", "app_secret": "", "webhook_uuid": "", "chat_id": ""},
                "github": {"github_token": "", "github_owner": "", "github_repo": ""},
            }
            data = json.dumps(template, indent=4, allow_nan=True, ensure_ascii=True)
            config_path.write_text(data)
            print("✅ Please fill in the configuration and restart the project")
            sys.exit(1)

        try:
            lark = from_dict_to_model(LarkSettings, _config["lark"])
            github = from_dict_to_model(GitHubSettings, _config["github"])
        except KeyError:
            sys.exit(1)

        return cls(lark=lark, github=github)


@dataclass
class Project:
    src_dir = Path(__file__).parent
    root_dir = src_dir.parent

    config_path = src_dir.joinpath("config.json")
    firebird_path = src_dir.joinpath("firebird.json")

    logs_dir = root_dir.joinpath("logs")

    data_dir = root_dir.joinpath("database2023")
    canvas_backup_dir = data_dir.joinpath("canvas_backup")
    rainbow_backup_dir = data_dir.joinpath("rainbow_backup")
    workspace_dir = rainbow_backup_dir.joinpath("_challenge")

    def __post_init__(self):
        for ck in [self.canvas_backup_dir, self.rainbow_backup_dir]:
            ck.mkdir(777, parents=True, exist_ok=True)


project = Project()
init_log(
    runtime=project.logs_dir.joinpath("runtime.log"),
    error=project.logs_dir.joinpath("error.log"),
    serialize=project.logs_dir.joinpath("serialize.log"),
)
config = Config.from_json(project.config_path)
firebird = Firebird.from_json(project.firebird_path)
