"""Definition provenance for author Run; these references are not credentials."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlviz_storage.sql_script_repository import SqlDefinitionReference

from sqlviz_api.compose_contract import ComposeItem
from sqlviz_api.sql_script_contract import PanelRef

DefinitionRevision = Annotated[
    str, Field(pattern=r"^sql-definition-v1:[0-9a-f]{64}$", min_length=82, max_length=82)
]


class _ReferenceContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1] = 1

    @field_validator("version", mode="before")
    @classmethod
    def exact_version(cls, value: object) -> object:
        if type(value) is not int or value != 1:
            raise ValueError("Reference version must be integer 1")
        return value


class DefinitionReferenceInput(_ReferenceContract):
    dashboard_id: PanelRef
    revision: DefinitionRevision

    def to_domain(self) -> SqlDefinitionReference:
        return SqlDefinitionReference(self.dashboard_id, self.revision)


class ExecutionReferenceInput(_ReferenceContract):
    panel_id: PanelRef
    definition: DefinitionReferenceInput


class BoundComposeItem(ComposeItem):
    execution_reference: ExecutionReferenceInput


class BoundComposeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    definition: DefinitionReferenceInput
    panels: list[BoundComposeItem] = Field(max_length=256)

    @model_validator(mode="after")
    def consistent_references(self) -> Self:
        ids = [item.panel_id for item in self.panels]
        if len(ids) != len(set(ids)):
            raise ValueError("Each panel must appear only once")
        if any(
            item.execution_reference.panel_id != item.panel_id
            or item.execution_reference.definition != self.definition for item in self.panels
        ):
            raise ValueError("Composition references must match the definition and panels")
        return self
