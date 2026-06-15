# OpenAPI to mappingProfile pipeline

`analyze_openapi_for_mapping_profile.py` converts an OpenAPI YAML/JSON file into reviewable ontology preparation artifacts.

It does not assume that API resources are business entities. The generated model keeps three layers separate:

- raw API layer: endpoints, operations, schemas, fields, effects, risks;
- `mappingProfile` layer: candidate bindings from generic API objects to canonical domains;
- canonical layer: existing business ontologies such as Serenity production, comptabilite, decisionnel, technique, missions.

Example:

```bash
python3 starterkit/scripts/analyze_openapi_for_mapping_profile.py \
  --input offre/box_openapi.json \
  --service-id box \
  --service-label Box \
  --output-dir generated/openapi_mapping_profile/box
```

Outputs:

- `<service>_openapi_ontology.json`: machine ontology artifact for the raw API layer;
- `<service>_mapping_profile.yaml`: proposed mappingProfile rules and review gates;
- `<service>_openapi_analysis.md`: human review report;
- `<service>_openapi_summary.json`: compact execution summary.

Use the generated `mappingProfile` as a proposal. Fill `target_entity_candidate`, key resolution rules, confidence policy, and validation gates before importing anything into MindBrain.
