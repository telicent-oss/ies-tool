# Changelog

## [3.0.0](https://github.com/telicent-oss/ies-tool/compare/v2.0.1...v3.0.0) (2026-02-24)


### ⚠ BREAKING CHANGES

* default data namespace setting ([#52](https://github.com/telicent-oss/ies-tool/issues/52))
* Moved to short_uuid format to save space in messages ([#45](https://github.com/telicent-oss/ies-tool/issues/45))

### Features

* allow plugin warnings to be brought back into tool ([#41](https://github.com/telicent-oss/ies-tool/issues/41)) ([cb9ec05](https://github.com/telicent-oss/ies-tool/commit/cb9ec05f421c60352c0ee2e1dcbf2d60dfdaa2c7))
* Basic stuff around prefix management in plug-ins ([#42](https://github.com/telicent-oss/ies-tool/issues/42)) ([9edf271](https://github.com/telicent-oss/ies-tool/commit/9edf271ff586e6cb443a550ef1801f40ffa71f32))
* checking whether plugin can validate ([#40](https://github.com/telicent-oss/ies-tool/issues/40)) ([a8cdac6](https://github.com/telicent-oss/ies-tool/commit/a8cdac6435f6abe64f26666258528f12b0540bb8))
* Plugin restructure ([#46](https://github.com/telicent-oss/ies-tool/issues/46)) ([0ffd1cc](https://github.com/telicent-oss/ies-tool/commit/0ffd1cce5544743c6cc522bd00c6147e785ec7dd))


### Bug Fixes

* - bug fixes around default base types ([#7](https://github.com/telicent-oss/ies-tool/issues/7)) ([deb19c0](https://github.com/telicent-oss/ies-tool/commit/deb19c078eb76ca423de2e415b0efa368795c190))
* 70 - Wrong fucntion call to end_event 69 - Change logic around birth state in Person. Add ability to specify DOB POD in create_person fn ([#5](https://github.com/telicent-oss/ies-tool/issues/5)) ([2efdc99](https://github.com/telicent-oss/ies-tool/commit/2efdc9928b4fdcc488c0a47dfdf4e0b6ab093fb8))
* allow plugins to work ([#15](https://github.com/telicent-oss/ies-tool/issues/15)) ([78b4e20](https://github.com/telicent-oss/ies-tool/commit/78b4e20a1ec64f1b11f6b42097b7b1c0984ff50c))
* allow plugins to work ([#39](https://github.com/telicent-oss/ies-tool/issues/39)) ([3b9eca5](https://github.com/telicent-oss/ies-tool/commit/3b9eca5776ac80e65306a0edf0430b5f021092de))
* Better management of additional classes ([#35](https://github.com/telicent-oss/ies-tool/issues/35)) ([6499ce6](https://github.com/telicent-oss/ies-tool/commit/6499ce63f52cd3f94e8f5332f88b2532c2002239))
* default data namespace setting ([#52](https://github.com/telicent-oss/ies-tool/issues/52)) ([189eda7](https://github.com/telicent-oss/ies-tool/commit/189eda74d504b7d92dfa67fae4566b3b1afb4751))
* less lenient datetime validator ([#26](https://github.com/telicent-oss/ies-tool/issues/26)) ([7a78206](https://github.com/telicent-oss/ies-tool/commit/7a78206c6a32bcc339482848ff72515b23512ae0))
* literal type of representations and default Geopoint precision ([#25](https://github.com/telicent-oss/ies-tool/issues/25)) ([f156c32](https://github.com/telicent-oss/ies-tool/commit/f156c326e993aaa49f03d55cd849cafc563c110e))
* only warn once ([#49](https://github.com/telicent-oss/ies-tool/issues/49)) ([893cb49](https://github.com/telicent-oss/ies-tool/commit/893cb49b9e2bb7a96e293cfe8e3dfd25be214d83))
* remove print statements in event participant code ([#44](https://github.com/telicent-oss/ies-tool/issues/44)) ([51065d5](https://github.com/telicent-oss/ies-tool/commit/51065d506e2c7edc5d758c1c3908f23386a69591))
* update iso4217parse dependency ([#50](https://github.com/telicent-oss/ies-tool/issues/50)) ([ab8b1e2](https://github.com/telicent-oss/ies-tool/commit/ab8b1e24a4861d08b8a208b566940d78a09e3a31))
* update particular period uri generation inline with 4.3 spec ([#34](https://github.com/telicent-oss/ies-tool/issues/34)) ([9286334](https://github.com/telicent-oss/ies-tool/commit/9286334d1a4bce01baa4afc0955dc4ec9ba9fae8))
* update to iso3166 country namespace ([#31](https://github.com/telicent-oss/ies-tool/issues/31)) ([b24a50f](https://github.com/telicent-oss/ies-tool/commit/b24a50feba04098429127070fde9e5715360ef4c))
* updated shacl from 4.2.0 to 4.3.0 ([#22](https://github.com/telicent-oss/ies-tool/issues/22)) ([45f966f](https://github.com/telicent-oss/ies-tool/commit/45f966f8f129849ac705cf340b20e738e05aa0da))


### Miscellaneous

* **main:** release 1.0.2 ([#10](https://github.com/telicent-oss/ies-tool/issues/10)) ([65e7ab3](https://github.com/telicent-oss/ies-tool/commit/65e7ab3f7537ea1e88eb6a47fc98fa21fde815b9))
* **main:** release 1.0.3 ([#13](https://github.com/telicent-oss/ies-tool/issues/13)) ([2b17d9d](https://github.com/telicent-oss/ies-tool/commit/2b17d9db1a0b4e30182aae2852790f824adf2830))
* **main:** release 1.0.4 ([#16](https://github.com/telicent-oss/ies-tool/issues/16)) ([b549874](https://github.com/telicent-oss/ies-tool/commit/b549874e25b2182a95323f61f2e91e83efe95d18))
* **main:** release 1.0.5 ([#28](https://github.com/telicent-oss/ies-tool/issues/28)) ([7aada41](https://github.com/telicent-oss/ies-tool/commit/7aada41989213b031fdc387e16bc559fb0ceb050))
* **main:** release 1.1.0 ([#32](https://github.com/telicent-oss/ies-tool/issues/32)) ([3325672](https://github.com/telicent-oss/ies-tool/commit/33256723ac78b2dcf419f37fe630d2602ac8d352))
* **main:** release 2.0.0 ([#43](https://github.com/telicent-oss/ies-tool/issues/43)) ([143eddf](https://github.com/telicent-oss/ies-tool/commit/143eddf929f7618e7b6341c9f4f7ed673ad2a6dc))
* **main:** release 2.0.1 ([#51](https://github.com/telicent-oss/ies-tool/issues/51)) ([9ef91b3](https://github.com/telicent-oss/ies-tool/commit/9ef91b31e486d2f9648ba88170ebc2cfd2399231))
* update dependency of pycountry to 24.6.1 ([#24](https://github.com/telicent-oss/ies-tool/issues/24)) ([5fda223](https://github.com/telicent-oss/ies-tool/commit/5fda22389e08e5c72f82ee5d27fffd67667da163))
* updated requests ([#12](https://github.com/telicent-oss/ies-tool/issues/12)) ([1208d8c](https://github.com/telicent-oss/ies-tool/commit/1208d8ca3af832435454a9f258f6412f44b2e805))


### Performance improvements

* Moved to short_uuid format to save space in messages ([#45](https://github.com/telicent-oss/ies-tool/issues/45)) ([732a1ac](https://github.com/telicent-oss/ies-tool/commit/732a1ac9dea3fec93dabae1e009a9e01b6b5bbe1))

## [2.0.1](https://github.com/telicent-oss/ies-tool/compare/v2.0.0...v2.0.1) (2026-02-10)


### Bug Fixes

* only warn once ([#49](https://github.com/telicent-oss/ies-tool/issues/49)) ([893cb49](https://github.com/telicent-oss/ies-tool/commit/893cb49b9e2bb7a96e293cfe8e3dfd25be214d83))
* update iso4217parse dependency ([#50](https://github.com/telicent-oss/ies-tool/issues/50)) ([ab8b1e2](https://github.com/telicent-oss/ies-tool/commit/ab8b1e24a4861d08b8a208b566940d78a09e3a31))

## [2.0.0](https://github.com/telicent-oss/ies-tool/compare/v1.1.0...v2.0.0) (2025-07-29)


### ⚠ BREAKING CHANGES

* Moved to short_uuid format to save space in messages ([#45](https://github.com/telicent-oss/ies-tool/issues/45))

### Features

* Basic stuff around prefix management in plug-ins ([#42](https://github.com/telicent-oss/ies-tool/issues/42)) ([9edf271](https://github.com/telicent-oss/ies-tool/commit/9edf271ff586e6cb443a550ef1801f40ffa71f32))
* Plugin restructure ([#46](https://github.com/telicent-oss/ies-tool/issues/46)) ([0ffd1cc](https://github.com/telicent-oss/ies-tool/commit/0ffd1cce5544743c6cc522bd00c6147e785ec7dd))


### Bug Fixes

* remove print statements in event participant code ([#44](https://github.com/telicent-oss/ies-tool/issues/44)) ([51065d5](https://github.com/telicent-oss/ies-tool/commit/51065d506e2c7edc5d758c1c3908f23386a69591))


### Performance improvements

* Moved to short_uuid format to save space in messages ([#45](https://github.com/telicent-oss/ies-tool/issues/45)) ([732a1ac](https://github.com/telicent-oss/ies-tool/commit/732a1ac9dea3fec93dabae1e009a9e01b6b5bbe1))

## [1.1.0](https://github.com/telicent-oss/ies-tool/compare/v1.0.5...v1.1.0) (2025-06-30)


### Features

* allow plugin warnings to be brought back into tool ([#41](https://github.com/telicent-oss/ies-tool/issues/41)) ([cb9ec05](https://github.com/telicent-oss/ies-tool/commit/cb9ec05f421c60352c0ee2e1dcbf2d60dfdaa2c7))
* checking whether plugin can validate ([#40](https://github.com/telicent-oss/ies-tool/issues/40)) ([a8cdac6](https://github.com/telicent-oss/ies-tool/commit/a8cdac6435f6abe64f26666258528f12b0540bb8))


### Bug Fixes

* allow plugins to work ([#39](https://github.com/telicent-oss/ies-tool/issues/39)) ([3b9eca5](https://github.com/telicent-oss/ies-tool/commit/3b9eca5776ac80e65306a0edf0430b5f021092de))
* Better management of additional classes ([#35](https://github.com/telicent-oss/ies-tool/issues/35)) ([6499ce6](https://github.com/telicent-oss/ies-tool/commit/6499ce63f52cd3f94e8f5332f88b2532c2002239))
* update particular period uri generation inline with 4.3 spec ([#34](https://github.com/telicent-oss/ies-tool/issues/34)) ([9286334](https://github.com/telicent-oss/ies-tool/commit/9286334d1a4bce01baa4afc0955dc4ec9ba9fae8))
* update to iso3166 country namespace ([#31](https://github.com/telicent-oss/ies-tool/issues/31)) ([b24a50f](https://github.com/telicent-oss/ies-tool/commit/b24a50feba04098429127070fde9e5715360ef4c))
* updated shacl from 4.2.0 to 4.3.0 ([#22](https://github.com/telicent-oss/ies-tool/issues/22)) ([45f966f](https://github.com/telicent-oss/ies-tool/commit/45f966f8f129849ac705cf340b20e738e05aa0da))

## [1.0.5](https://github.com/telicent-oss/ies-tool/compare/v1.0.4...v1.0.5) (2025-04-01)


### Bug Fixes

* less lenient datetime validator ([#26](https://github.com/telicent-oss/ies-tool/issues/26)) ([7a78206](https://github.com/telicent-oss/ies-tool/commit/7a78206c6a32bcc339482848ff72515b23512ae0))
* literal type of representations and default Geopoint precision ([#25](https://github.com/telicent-oss/ies-tool/issues/25)) ([f156c32](https://github.com/telicent-oss/ies-tool/commit/f156c326e993aaa49f03d55cd849cafc563c110e))


### Miscellaneous

* update dependency of pycountry to 24.6.1 ([#24](https://github.com/telicent-oss/ies-tool/issues/24)) ([5fda223](https://github.com/telicent-oss/ies-tool/commit/5fda22389e08e5c72f82ee5d27fffd67667da163))

## [1.0.4](https://github.com/telicent-oss/ies-tool/compare/v1.0.3...v1.0.4) (2024-10-18)


### Bug Fixes

* - bug fixes around default base types ([#7](https://github.com/telicent-oss/ies-tool/issues/7)) ([deb19c0](https://github.com/telicent-oss/ies-tool/commit/deb19c078eb76ca423de2e415b0efa368795c190))
* 70 - Wrong fucntion call to end_event 69 - Change logic around birth state in Person. Add ability to specify DOB POD in create_person fn ([#5](https://github.com/telicent-oss/ies-tool/issues/5)) ([2efdc99](https://github.com/telicent-oss/ies-tool/commit/2efdc9928b4fdcc488c0a47dfdf4e0b6ab093fb8))
* allow plugins to work ([#15](https://github.com/telicent-oss/ies-tool/issues/15)) ([78b4e20](https://github.com/telicent-oss/ies-tool/commit/78b4e20a1ec64f1b11f6b42097b7b1c0984ff50c))


### Miscellaneous

* **main:** release 1.0.2 ([#10](https://github.com/telicent-oss/ies-tool/issues/10)) ([65e7ab3](https://github.com/telicent-oss/ies-tool/commit/65e7ab3f7537ea1e88eb6a47fc98fa21fde815b9))
* **main:** release 1.0.3 ([#13](https://github.com/telicent-oss/ies-tool/issues/13)) ([2b17d9d](https://github.com/telicent-oss/ies-tool/commit/2b17d9db1a0b4e30182aae2852790f824adf2830))
* updated requests ([#12](https://github.com/telicent-oss/ies-tool/issues/12)) ([1208d8c](https://github.com/telicent-oss/ies-tool/commit/1208d8ca3af832435454a9f258f6412f44b2e805))

## [1.0.3](https://github.com/telicent-oss/ies-tool/compare/v1.0.2...v1.0.3) (2024-08-27)


### Miscellaneous

* updated requests ([#12](https://github.com/telicent-oss/ies-tool/issues/12)) ([1208d8c](https://github.com/telicent-oss/ies-tool/commit/1208d8ca3af832435454a9f258f6412f44b2e805))

## [1.0.2](https://github.com/telicent-oss/ies-tool/compare/v1.0.1...v1.0.2) (2024-05-13)


### Bug Fixes

* bug fixes around default base types ([#7](https://github.com/telicent-oss/ies-tool/issues/7)) ([deb19c0](https://github.com/telicent-oss/ies-tool/commit/deb19c078eb76ca423de2e415b0efa368795c190))
* 70 - Wrong fucntion call to end_event 69 - Change logic around birth state in Person. Add ability to specify DOB POD in create_person fn ([#5](https://github.com/telicent-oss/ies-tool/issues/5)) ([2efdc99](https://github.com/telicent-oss/ies-tool/commit/2efdc9928b4fdcc488c0a47dfdf4e0b6ab093fb8))

## 1.0.1 (2024-02-29)


### Features

* Initial release
