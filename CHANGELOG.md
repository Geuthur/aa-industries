# Changelog

## [0.0.3] - IN DEVELOPMENT

### Added

- API System
  - Search API
    - `eveindustryactivitymaterial`
    - `evetypematerial`
    - `eveindustryactivityproduct`
  - Industry API
    - `get_blueprint_industry`
    - `get_blueprint_industry_summary`
    - `get_industry_material`
  - Helpers
    - `fix_fullerides`
    - `get_blueprint_from_eve_type`
    - `get_or_create_product_or_none`
    - `get_blueprint_materials`
    - `get_or_create_market_price`
- Lazy Functions
  - `get_character_portrait_url`
  - `get_corporation_logo_url`
  - `get_type_render_url`
  - `get_type_icon_url`
- Modal System
  - Standard Modal
- Javascript
  - Blueprint Search
  - Industrymaterials
  - Modal System
- Django Commands
  - `industries_update_industry`
  - `industries_update_prices`

## [0.0.2] - 2025-02-06

### Change

- Update AA to 4.6.1
- Update Pre Commit

### Added

- Translation
- Python 3.13 Support
- Cache Buster by [@ppfeufer](https://github.com/ppfeufer)

## [0.0.1] - 2024-08-xx

### Added

- Initial public release
