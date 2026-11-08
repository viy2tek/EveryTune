import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .public_http import public_url


class SourceDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^custom_[a-z0-9_]{1,40}$")
    name: str = Field(min_length=1, max_length=100)
    format: Literal["json", "html", "external"] = "json"
    method: Literal["GET", "POST"] = "GET"
    request_encoding: Literal["form", "json"] = "form"
    endpoint: str = Field(max_length=2000)
    category: str = Field(default="Personalizadas", min_length=1, max_length=100)
    provider_group: Literal['streaming','community'] = 'community'
    download_selector: str | None = Field(default=None,max_length=300)
    query_param: str = Field(default="q", pattern=r"^[a-zA-Z0-9_.-]{1,80}$")
    query_in_path: bool = False
    respect_robots: bool = False
    params: dict[str, str] = Field(default_factory=dict, max_length=20)
    results_path: str = Field(default="results", max_length=300)
    results_optional: bool = False
    fields: dict[str, str] = Field(default_factory=lambda: {"title":"title", "artist":"artist", "url":"url", "id":"id"}, max_length=15)
    credits_path: str | None = Field(default=None, max_length=200)
    link_template: str | None = Field(default=None, max_length=2000)
    kind: Literal["track", "album", "video", "archive_item", "catalogue_post"] = "track"
    duration_unit: Literal["seconds", "milliseconds"] = "seconds"
    limit_param: str | None = Field(default="limit", pattern=r"^[a-zA-Z0-9_.-]{1,80}$")
    page_param: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_.-]{1,80}$")
    page_mode: Literal["page", "offset", "index"] = "page"
    page_start: int = Field(default=1, ge=0, le=1)
    auth: Literal["none", "header", "query"] = "none"
    auth_name: str = Field(default="Authorization", pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    auth_prefix: Literal["", "Bearer ", "Token "] = "Bearer "
    interval: float = Field(default=1, ge=0.5, le=120)
    ttl: int = Field(default=900, ge=60, le=86400)

    @field_validator("endpoint")
    @classmethod
    def endpoint_public(cls, value):
        url = public_url(value)
        if url.query or url.fragment:
            raise ValueError("Separe parâmetros da URL; não inclua query, fragmento ou segredos")
        return str(url)

    @model_validator(mode="after")
    def validate_mapping(self):
        if self.download_selector:
            import soupsieve
            try:soupsieve.compile(self.download_selector)
            except Exception:raise ValueError('Seletor CSS de downloads inválido') from None
        if self.format=="external" and self.method!="GET":
            raise ValueError("Atalhos externos só podem usar GET")
        if self.format=="external" and self.auth!="none":
            raise ValueError("Pesquisa externa não recebe chaves de API")
        if self.auth_name.lower() in {"host", "cookie", "origin", "referer", "content-length", "transfer-encoding", "connection"}:
            raise ValueError("Cabeçalho de autenticação não permitido")
        allowed = {"title","artist","album","url","id","artwork","duration","year","license","credit_name","credit_role","credit_id"}
        if set(self.fields)-allowed or any(len(v)>300 for v in self.fields.values()):
            raise ValueError("Mapeamento de campos inválido")
        if self.format != "external" and ("title" not in self.fields or not ("url" in self.fields or self.link_template)):
            raise ValueError("Defina título e link da origem")
        if any(re.search(r"token|secret|password|api.?key|authorization", k, re.I) or len(k)>80 or len(v)>300 for k,v in self.params.items()):
            raise ValueError("Parâmetros inválidos; configure chaves na seção de autenticação")
        if self.link_template:
            if set(re.findall(r"\{([^{}]+)\}", self.link_template)) - {"id"}:
                raise ValueError("O link pode usar apenas {id}")
            public_url(self.link_template.replace("{id}", "example"))
        if self.format=="html":
            import soupsieve
            try:
                soupsieve.compile(self.results_path)
                if self.download_selector:
                    soupsieve.compile(self.download_selector)
                for value in self.fields.values():
                    if value.startswith("="):
                        continue
                    selector = value.rsplit("@",1)[0] if "@" in value else value
                    if selector:
                        soupsieve.compile(selector)
            except Exception:
                raise ValueError("Seletor CSS inválido; revise o mapeamento HTML") from None
        return self

    @property
    def credential_key(self):
        return self.id + "_token"
