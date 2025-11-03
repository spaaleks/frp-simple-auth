from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AllowCfg(BaseModel):
    proxyTypes: List[str] = Field(default_factory=lambda: ["http", "https"])
    remotePorts: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)


class UserCfg(BaseModel):
    user: str
    password: str
    allow: AllowCfg


class GlobalDeny(BaseModel):
    proxyTypes: List[str] = Field(default_factory=list)
    remotePorts: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)


class AppCfg(BaseModel):
    globalDeny: GlobalDeny = Field(default_factory=GlobalDeny)
    users: List[UserCfg]


class FrpLogin(BaseModel):
    model_config = ConfigDict(extra="allow")
    user: str
    privilege_key: Optional[str] = None
    run_id: Optional[str] = None
    metas: Dict[str, str] = Field(default_factory=dict)
    client_address: Optional[str] = None


class FrpLoginReq(BaseModel):
    model_config = ConfigDict(extra="allow")
    content: FrpLogin


class FrpNewProxyUser(BaseModel):
    model_config = ConfigDict(extra="allow")
    user: str
    metas: Dict[str, str] = Field(default_factory=dict)


class FrpTransport(BaseModel):
    model_config = ConfigDict(extra="allow")
    use_encryption: Optional[bool] = None
    use_compression: Optional[bool] = None


class FrpNewProxy(BaseModel):
    model_config = ConfigDict(extra="allow")
    user: FrpNewProxyUser
    metas: Dict[str, str] = Field(default_factory=dict)
    proxy_name: str
    proxy_type: str
    remote_port: Optional[int] = None
    custom_domains: Optional[List[str]] = None
    http_user: Optional[str] = None
    http_pwd: Optional[str] = None
    transport: Optional[FrpTransport] = None


class FrpNewProxyReq(BaseModel):
    model_config = ConfigDict(extra="allow")
    content: FrpNewProxy
