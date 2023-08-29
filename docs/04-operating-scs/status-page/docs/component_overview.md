# Component Overview

This represents a part of the decision process related to the overall structure the API wants to represent.

```mermaid
C4Component
  title status-page-openapi

  Container_Boundary(impacts, "Impacts") {
    Component(impactType, ImpactType, "ID, displayName, description")
    Component(impact, Impact, "type, reference")
    Component(impactComponentList, ImpactComponentList, "[]Impact", "Impacts reference components")
    Component(impactIncidentList, ImpactIncidentList, "<<readonly>>[]Impact", "Impacts reference incidents")

    Rel(impact, impactType, "has")
    Rel(impactComponentList, impact, "lists")
    Rel(impactIncidentList, impact, "lists")

    UpdateElementStyle(impact, $bgColor="green")
    UpdateElementStyle(impactComponentList, $bgColor="green")
    UpdateElementStyle(impactIncidentList, $bgColor="green")

    UpdateRelStyle(impact, impactType, "green", "green", $offsetY="-10")
    UpdateRelStyle(impactComponentList, impact, "green", "green", $offsetY="-15")
    UpdateRelStyle(impactIncidentList, impact, "green", "green")
  }

  Container_Boundary(incidents, "Incidents") {
    Component(incidentUpdate, IncidentUpdate, "order, displayName, description, createdAt")
    Component(incident, Incident, "ID, displayName, description, updates, affects, beganAt, endedAt, Phase")

    Rel(incident, incidentUpdate, "contains")
  }

  Container_Boundary(phases, "Phases") {
    Component(phaseReference, PhaseReference, "Phase, order, generation")
    Component(phase, Phase, "", "it is just a name")
    Component(phaseList, PhaseList, "generation, []Phase")

    Rel(phaseList, phase, "lists")
    Rel(phaseReference, phase, "references")
    Rel(phaseReference, phaseList, "references")

    UpdateElementStyle(phaseReference, $bgColor="green")
    UpdateElementStyle(phaseList, $bgColor="green")

    UpdateRelStyle(phaseList, phase, "green", "green", $offsetY="5")
    UpdateRelStyle(phaseReference, phase, "green", "green", $offsetX="-30", $offsetY="10")
    UpdateRelStyle(phaseReference, phaseList, "green", "green", $offsetY="5")

  }

  Container_Boundary(components, "Components") {
    Component(component, Component, "ID, displayName, Labels, activelyAffectedBy")
    Component(labels, Labels, "", "Key value pairs")

    Rel(component, labels, "contains")
  }

  %% global relations %%
  %% deprecated %%
  Rel(incident, impactType, "has")
  BiRel(component, incident, "affects / affected by")

  UpdateRelStyle(incident, impactType, "red", "red")
  UpdateRelStyle(component, incident, "red", "red", $offsetX="10")

  %% new %%
  Rel(incident, impactComponentList, "affects")
  Rel(component, impactIncidentList, "actively affected by", "only list active/open impacts")
  Rel(incident, phaseReference, "has")
  Rel(impact, component, "references", "from impactComponentList")
  Rel(impact, incident, "references", "from impactIncidentList")

  UpdateRelStyle(incident, impactComponentList, "green", "green")
  UpdateRelStyle(component, impactIncidentList, "green", "green", $offsetX="-180", $offsetY="-70")
  UpdateRelStyle(incident, phaseReference, "green", "green", $offsetX="-70", $offsetY="40")
  UpdateRelStyle(impact, component, "green", "green", $offsetX="-140")
  UpdateRelStyle(impact, incident, "green", "green", $offsetX="-100")

```

Color meaning:

- Blue: Existing structure
- Red: Deprecated / removed
- Green: New
