.
├── EMAIL_WARMING_MODULE
│   ├── __init__.py
│   ├── module.py
│   ├── models.py
│   ├── database.py
│   ├── pyproject.toml
│   ├── api
│   │   ├── __init__.py
│   │   └── routes
│   │       ├── __init__.py
│   │       └── warming.py
│   └── configs
│       ├── __init__.py
│       ├── seed_loader.py
│       └── presence_ia_seed.json
├── AI_INQUIRY_MODULE
│   ├── README.md
│   ├── TESTS
│   │   ├── .pytest_cache
│   │   │   ├── .gitignore
│   │   │   ├── CACHEDIR.TAG
│   │   │   ├── README.md
│   │   │   └── v
│   │   │       └── cache
│   │   │           └── nodeids
│   │   └── test_module.py
│   ├── __init__.py
│   └── module.py
├── AUTOSITES
│   ├── api
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── admin_ui.py
│   │       ├── blocks.py
│   │       ├── generate.py
│   │       ├── pages.py
│   │       └── sections.py
│   ├── generate.py
│   ├── img_scss_prompt.txt
│   ├── index.html
│   ├── manifest_to_content_prompt.txt
│   ├── manifests
│   │   └── home.json
│   ├── mock_to_seed_prompt.txt
│   ├── output
│   │   ├── home
│   │   │   └── index.html
│   │   └── presence_ia_test
│   │       └── index.html
│   ├── presence_ia_test.json
│   ├── seed_design_to_manifest_prompt.txt
│   └── styles.css
├── MARKETING_MODULE
│   ├── TESTS
│   │   ├── __init__.py
│   │   ├── test_crm.py
│   │   ├── test_models.py
│   │   ├── test_rotation.py
│   │   └── test_send.py
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── campaigns.py
│   │       ├── compliance.py
│   │       ├── crm.py
│   │       ├── domains.py
│   │       ├── mailboxes.py
│   │       ├── reporting.py
│   │       ├── rotation.py
│   │       ├── send.py
│   │       ├── sequences.py
│   │       ├── social.py
│   │       ├── warmup.py
│   │       └── webhooks.py
│   ├── channels
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── email
│   │   │   ├── __init__.py
│   │   │   └── providers
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       └── brevo.py
│   │   ├── sms
│   │   │   ├── __init__.py
│   │   │   └── providers
│   │   │       ├── __init__.py
│   │   │       └── twilio.py
│   │   └── social
│   │       ├── __init__.py
│   │       └── providers
│   │           ├── __init__.py
│   │           ├── instagram.py
│   │           └── pinterest.py
│   ├── configs
│   │   ├── __init__.py
│   │   ├── presence_ia_seed.json
│   │   ├── seed_loader.py
│   │   └── sublym_seed.json
│   ├── crm
│   │   ├── __init__.py
│   │   └── module.py
│   ├── database.py
│   ├── models.py
│   ├── module.py
│   └── pyproject.toml
├── MODEL_EXECUTOR
│   ├── MANIFEST.json
│   ├── README.md
│   ├── _DEPRECATED.md
│   ├── _STATUS.md
│   ├── config.yaml
│   ├── requirements.txt
│   ├── src
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── executor.py
│   │   └── providers
│   │       ├── __init__.py
│   │       └── base.py
│   └── tests
├── OUTBOUND_EMAIL_MODULE
│   ├── TESTS
│   │   ├── __init__.py
│   │   ├── test_compliance.py
│   │   ├── test_models.py
│   │   ├── test_rotation.py
│   │   └── test_send.py
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── campaigns.py
│   │       ├── compliance.py
│   │       ├── domains.py
│   │       ├── mailboxes.py
│   │       ├── reporting.py
│   │       ├── rotation.py
│   │       ├── send.py
│   │       ├── sequences.py
│   │       └── warmup.py
│   ├── configs
│   │   ├── presence_ia_seed.json
│   │   └── seed_loader.py
│   ├── database.py
│   ├── models.py
│   ├── module.py
│   ├── providers
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── brevo.py
│   └── pyproject.toml
├── README.md
├── VISUAL_ASSETS
│   ├── README.md
│   ├── examples
│   │   ├── generate_thalasso_dalle.py
│   │   └── generate_thalasso_replicate.py
│   ├── pyproject.toml
│   └── src
│       ├── __init__.py
│       ├── harmony.py
│       └── module.py
├── _archive
│   ├── demo_extraction_visuelle.html
│   ├── demo_myhealthprac_style.html
│   ├── output_myhealthprac
│   │   ├── demo.html
│   │   ├── demo_v2.html
│   │   ├── raw_styles.json
│   │   ├── screenshot.png
│   │   ├── theme.css
│   │   ├── theme_preset.json
│   │   ├── theme_preset_v2.json
│   │   ├── theme_v2.css
│   │   ├── variants
│   │   │   ├── amber_variant.json
│   │   │   ├── blue_variant.json
│   │   │   ├── comparison.html
│   │   │   ├── green_variant.json
│   │   │   ├── purple_variant.json
│   │   │   └── red_variant.json
│   │   └── visual_assets.json
│   ├── output_thalasso
│   │   ├── demo_thalasso_bento.html
│   │   ├── demo_thalasso_images.html
│   │   ├── demo_thalasso_prompts.html
│   │   ├── generated_images.json
│   │   ├── generated_images_replicate.json
│   │   ├── preset_thalasso.json
│   │   └── visual_assets.json
│   ├── pipeline_complet_v2.py
│   ├── pipeline_myhealthprac.py
│   ├── pipeline_simple.py
│   ├── test_myhealthprac.py
│   └── test_scraper_simple.py
├── _examples
│   └── example_pipeline.py
├── brand_generator
│   ├── MANIFEST.json
│   ├── _SUIVI.md
│   ├── brand_generator
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── direction_builder.py
│   │   ├── generator.py
│   │   ├── router.py
│   │   └── schemas.py
│   └── pyproject.toml
├── catalogue.json
├── color_psychology_engine
│   ├── MANIFEST.json
│   ├── _SUIVI.md
│   ├── color_psychology_engine
│   │   ├── __init__.py
│   │   ├── emotion_color_map.py
│   │   ├── industry_color_map.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── suggestion_resolver.py
│   │   └── weighting_engine.py
│   └── pyproject.toml
├── conversational_brief
│   ├── MANIFEST.json
│   ├── _SUIVI.md
│   ├── conversational_brief
│   │   ├── __init__.py
│   │   └── agent.py
│   └── pyproject.toml
├── design_dna_resolver
│   ├── MANIFEST.json
│   ├── _SUIVI.md
│   ├── design_dna_resolver
│   │   ├── __init__.py
│   │   ├── archetype_inference.py
│   │   ├── brief_parser.py
│   │   ├── concept_normalizer.py
│   │   ├── dna_builder.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── style_mapper.py
│   └── pyproject.toml
├── design_exploration_engine
│   ├── MANIFEST.json
│   ├── _SUIVI.md
│   ├── design_exploration_engine
│   │   ├── __init__.py
│   │   ├── archetype_variator.py
│   │   ├── direction_builder.py
│   │   ├── direction_generator.py
│   │   ├── palette_variator.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── typography_variator.py
│   └── pyproject.toml
├── logo_generator
│   ├── MANIFEST.json
│   ├── _SUIVI.md
│   ├── logo_generator
│   │   ├── __init__.py
│   │   ├── arbitration.py
│   │   ├── exporter.py
│   │   ├── generator.py
│   │   ├── prompt_builder.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── vector_optimizer.py
│   └── pyproject.toml
├── page_builder
│   ├── .gitignore
│   ├── .pytest_cache
│   │   ├── .gitignore
│   │   ├── CACHEDIR.TAG
│   │   ├── README.md
│   │   └── v
│   │       └── cache
│   │           └── nodeids
│   ├── CHANGELOG.md
│   ├── README.md
│   ├── examples
│   │   ├── demo_landing.html
│   │   ├── fastapi_example.py
│   │   ├── simple_landing.py
│   │   ├── test_blue.html
│   │   ├── test_design_tokens.py
│   │   ├── test_red.html
│   │   └── test_violet.html
│   ├── i18n
│   │   ├── en.json
│   │   └── fr.json
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── seeds
│   │   ├── README.md
│   │   └── demo_landing.json
│   ├── src
│   │   ├── __init__.py
│   │   ├── blocks
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── content.py
│   │   │   ├── cta.py
│   │   │   ├── faq.py
│   │   │   ├── footer.py
│   │   │   ├── hero.py
│   │   │   ├── image.py
│   │   │   ├── navbar.py
│   │   │   ├── pricing.py
│   │   │   ├── stat.py
│   │   │   ├── steps.py
│   │   │   └── testimonial.py
│   │   ├── builder.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── design_system.py
│   │   │   ├── i18n.py
│   │   │   └── schemas.py
│   │   ├── eurkai_page_builder.egg-info
│   │   │   ├── PKG-INFO
│   │   │   ├── SOURCES.txt
│   │   │   ├── dependency_links.txt
│   │   │   ├── requires.txt
│   │   │   └── top_level.txt
│   │   ├── fastapi_integration.py
│   │   ├── manifest
│   │   │   ├── __init__.py
│   │   │   ├── parser.py
│   │   │   └── schema.py
│   │   ├── modules
│   │   ├── renderer
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── css.py
│   │   │   ├── css_legacy.py
│   │   │   └── html.py
│   │   ├── router.py
│   │   └── scss
│   │       ├── _grid.scss
│   │       ├── _reset.scss
│   │       ├── _variables.scss
│   │       ├── blocks
│   │       │   ├── _content.scss
│   │       │   ├── _cta.scss
│   │       │   ├── _faq.scss
│   │       │   ├── _footer.scss
│   │       │   ├── _hero.scss
│   │       │   ├── _image.scss
│   │       │   ├── _navbar.scss
│   │       │   ├── _pricing.scss
│   │       │   ├── _stat.scss
│   │       │   ├── _steps.scss
│   │       │   └── _testimonials.scss
│   │       └── main.scss
│   ├── templates
│   │   ├── modules
│   │   └── sections
│   └── tests
│       ├── __init__.py
│       ├── test_blocks.py
│       ├── test_i18n.py
│       ├── test_manifest.py
│       └── test_schemas.py
├── palette_generator
│   ├── MANIFEST.json
│   ├── _SUIVI.md
│   ├── palette_generator
│   │   ├── __init__.py
│   │   ├── bw_palette_generator.py
│   │   ├── color_scale_generator.py
│   │   ├── color_utils.py
│   │   ├── contrast_validator.py
│   │   ├── generator.py
│   │   ├── harmony_engine.py
│   │   ├── metal_palette_generator.py
│   │   ├── palette_exporter.py
│   │   ├── palette_scenarios.py
│   │   ├── router.py
│   │   └── schemas.py
│   └── pyproject.toml
├── pipeline_validator
│   ├── _SUIVI.md
│   ├── __init__.py
│   ├── contracts.py
│   ├── router.py
│   └── validator.py
├── scraper
│   ├── examples
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── src
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── eurkai_scraper.egg-info
│   │   │   ├── PKG-INFO
│   │   │   ├── SOURCES.txt
│   │   │   ├── dependency_links.txt
│   │   │   ├── requires.txt
│   │   │   └── top_level.txt
│   │   ├── image_analyzer.py
│   │   └── scraper.py
│   └── tests
├── seed_builder
│   ├── README.md
│   ├── eurkai_seed_builder.egg-info
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   ├── dependency_links.txt
│   │   ├── entry_points.txt
│   │   ├── requires.txt
│   │   └── top_level.txt
│   ├── mockups
│   │   ├── 328aa094d2fb548810cda07bba2451e8.jpg
│   │   ├── 6409cdcdd9326351c8b16a7ec189e18d.jpg
│   │   ├── 862dceec4f8536e5205f98b7d064289e (1).jpg
│   │   ├── _done
│   │   └── cde659405b6bcce0d90deaa69466f1dd.jpg
│   ├── pyproject.toml
│   ├── seed_builder
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── cli.py
│   │   ├── schemas.py
│   │   └── watcher.py
│   └── seeds
├── theme_composer
│   ├── eurkai_theme_composer.egg-info
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   ├── dependency_links.txt
│   │   ├── requires.txt
│   │   └── top_level.txt
│   ├── examples
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── tests
│   └── theme_composer
│       ├── __init__.py
│       ├── composer.py
│       ├── eurkai_theme_composer.egg-info
│       │   ├── PKG-INFO
│       │   ├── SOURCES.txt
│       │   ├── dependency_links.txt
│       │   ├── requires.txt
│       │   └── top_level.txt
│       ├── font_matcher.py
│       ├── harmony_rules.py
│       └── style_presets.py
├── theme_generator
│   ├── _SPECS.md
│   ├── _SPECS_PLATFORM.md
│   ├── _SUIVI.md
│   ├── eurkai_theme_generator.egg-info
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   ├── dependency_links.txt
│   │   ├── requires.txt
│   │   └── top_level.txt
│   ├── examples
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── tests
│   └── theme_generator
│       ├── __init__.py
│       ├── eurkai_theme_generator.egg-info
│       │   ├── PKG-INFO
│       │   ├── SOURCES.txt
│       │   ├── dependency_links.txt
│       │   ├── requires.txt
│       │   └── top_level.txt
│       └── generator.py
├── tree-MODULES.md
└── visual_consistency_validator
    ├── MANIFEST.json
    ├── _SUIVI.md
    ├── pyproject.toml
    └── visual_consistency_validator
        ├── __init__.py
        ├── icon_style_checker.py
        ├── layout_checker.py
        ├── palette_checker.py
        ├── router.py
        ├── schemas.py
        ├── scoring_engine.py
        ├── typography_checker.py
        ├── validator.py
        └── visual_style_checker.py

104 directories, 376 files
