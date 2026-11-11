# NDA taxonomy and DMS metadata

- [Read the mapping decisions and DMS design](Taxonomy_and_DMS.md)
- [Inspect the 15 rule mappings and 16 held-out issue instances](sali_issue_crosswalk.json)
- [Inspect the fictional DMS metadata record](dms_metadata_example.json)
- [Inspect the 20 selected official SALI source concepts](sources/selected_sali_concepts.json)
- [Inspect the upstream verification result](sources/verification_result.json)

```sh
python3 validate_taxonomy.py
python3 validate_taxonomy.py --verify-upstream
```

The default check is offline. The second verifies the pinned official ontology. SALI topics support classification; local policies, permissions, retention and approval remain separate controls.
