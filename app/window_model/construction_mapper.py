from __future__ import annotations

from app.wh.runtime.construction_offer import ConstructionOffer
from app.wh.runtime.construction_project import ConstructionProject
from app.wh.runtime.construction_schema import ConstructionSchema
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


class ConstructionMapper:
    """Map construction schema and offer into the canonical semantic WindowModel."""

    def map_project(
        self,
        project: ConstructionProject,
    ) -> tuple[WindowModel, WindowTopology]:
        return self.map(
            project.schema,
            project.offer,
        )

    def map(
        self,
        schema: ConstructionSchema,
        offer: ConstructionOffer | None = None,
    ) -> tuple[WindowModel, WindowTopology]:
        properties = {
            "width": schema.width,
            "height": schema.height,
            "schema": schema.schema,
            "cells": len(schema.segments),
        }

        if offer is not None:
            properties.update(
                {
                    "color_inside": offer.color_inside,
                    "color_outside": offer.color_outside,
                    "profile_manufacturer": offer.profile.manufacturer,
                    "profile_system": offer.profile.system,
                    "glass_type": offer.glass.type,
                    "glass_thickness_mm": offer.glass.thickness_mm,
                    "glass_warm_edge": offer.glass.warm_edge,
                    "glass_swisspacer": offer.glass.swisspacer,
                    "glass_security_p4": offer.glass.security_p4,
                    "security_rc2": offer.security.rc2,
                    "security_contacts": offer.security.contacts,
                    "hardware_hidden_hinges": offer.hardware.hidden_hinges,
                    "hardware_v_perfect": offer.hardware.v_perfect,
                    "roller_shutter": offer.accessories.roller_shutter,
                    "sill": offer.accessories.sill,
                    "mosquito_net": offer.accessories.mosquito_net,
                    "extension_mm": offer.accessories.extension_mm,
                    "connector": offer.accessories.connector,
                }
            )

        model = WindowModel(properties=properties)
        topology = WindowTopology()

        frame = model.add_element(
            "frame",
            WindowElementType.FRAME,
        )
        topology.add(
            frame,
            side=WindowSide.CENTER,
            role="FRAME",
        )

        for index, segment in enumerate(schema.segments):
            side = WindowSide.LEFT if index == 0 else WindowSide.RIGHT
            side_name = side.value.lower()
            opening = segment.opening.value

            cell = model.add_element(
                f"cell_{side_name}",
                WindowElementType.MULLION,
                parent_id=frame.id,
                role="CELL",
            )
            topology.add(
                cell,
                side=side,
                position_index=index,
                role="CELL",
            )

            sash = model.add_element(
                f"sash_{side_name}",
                WindowElementType.SASH,
                parent_id=cell.id,
                opening=opening,
                width_ratio=segment.width_ratio,
                height_ratio=segment.height_ratio,
            )
            topology.add(
                sash,
                side=side,
                position_index=index,
                opening=opening,
            )

            glass = model.add_element(
                f"glass_{side_name}",
                WindowElementType.GLASS,
                parent_id=sash.id,
                panes=3,
            )
            topology.add(
                glass,
                side=side,
                position_index=index,
            )

            hardware_system = "unknown"
            if offer is not None and offer.profile.system:
                hardware_system = offer.profile.system

            hardware = model.add_element(
                f"hardware_{side_name}",
                WindowElementType.HARDWARE,
                parent_id=sash.id,
                system=hardware_system,
            )
            topology.add(
                hardware,
                side=side,
                position_index=index,
            )

        return model, topology
